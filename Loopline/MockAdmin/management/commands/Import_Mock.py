"""
import_mock_pdf.py
-------------------
Ingest a coaching-style mock-test PDF (questions / options / Ans / Sol, with
embedded diagrams in BOTH the question stem and the solution) into your
EXISTING Django models — no changes to models.py.

    Exam, Subject, Chapter, Question, QuestionOption, Solution, CorrectAnswer

Multi-image handling within the existing schema
-------------------------------------------------
  * Question.image_url    -> single ImageField.
                              Diagrams that appear BEFORE "Sol." on the page
                              (i.e. belong to the question stem) are stacked
                              vertically into ONE PNG and saved here.
  * Solution.image_url     -> JSONField, stored as {"images": [url, ...]}.
                              Diagrams that appear AFTER "Sol." on the page
                              are saved individually (not stacked, since a
                              solution can have several distinct graphs, e.g.
                              "Graph of LHS" / "Graph of RHS") and their URLs
                              go in this list.
  * QuestionOption.option_X_images -> JSONField, {"images": [url, ...]}.
                              Only used when an image appears while we are in
                              the "options" section (e.g. graph-choice
                              questions). See WARNING below.

HOW THE STEM vs SOLUTION SPLIT WORKS
-------------------------------------
Previously this script grouped "all images on a page" together, which throws
solution diagrams and stem diagrams into the same bucket. Fixed here by
walking each page as a single ordered stream of (text-line, y-position) and
(image, y-position) events, sorted top-to-bottom. Whichever section we were
in when an image's y-position comes up ("stem" / "options" / "sol") is what
it gets attached to. This matches your actual PDF layout, where e.g. Q8's
graph appears physically below "Sol." and above the next question number.

HOW TO RUN
----------
1. pip install pymupdf pillow --break-system-packages
2. Put this in e.g. yourapp/management/commands/import_mock_pdf.py
   (wrap run() in a Command.handle()), or run as one-off via:
       python manage.py shell -c "import import_mock_pdf as m; m.run('test.pdf', exam_id=1)"

REMAINING KNOWN LIMITATION
---------------------------
If an image appears WHILE we're in the "options" section (current.section ==
'options') — i.e. the options themselves are graphs, like Q42 in your sample
— this script cannot reliably tell which image belongs to option A vs B vs C
vs D from text alone (PyMuPDF gives no explicit "this image is inside option
row 3" link). It logs a WARNING and, as a safe default, assigns them in
left-to-right / top-to-bottom order to A, B, C, D. **Review these questions
manually** — get it wrong here and the exam shows the wrong graph next to
the wrong letter, which is worse than not showing an image at all.
"""

import re
import io
import logging
from dataclasses import dataclass, field

from django.core.management.base import BaseCommand, CommandError

import fitz  # PyMuPDF
from PIL import Image
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# adjusted for this project: models live in MockAdmin
from MockAdmin.models import (
    Exam, Subject, Chapter, Question, QuestionOption, Solution, CorrectAnswer,
)

logger = logging.getLogger("import_mock_pdf")

QUESTION_RE = re.compile(r'^\s*(\d{1,3})\.\s+(.*)')
# Some PDFs (this one included) render the question number as its own
# standalone text line/block, with the question text following as a
# SEPARATE line — e.g. the line is literally "9." with nothing after it,
# and "Number of real x satisfying..." is the next line/event entirely.
# QUESTION_RE above requires \s+ (at least one space) followed by content
# on the SAME line, so it never matches a bare "9." — that silently
# starves the whole parser (current stays None, every subsequent line is
# skipped via `if current is None: continue`, and parse_pdf() returns an
# empty list with no error at all). This second, stricter pattern (anchored
# to end-of-line with $) catches only the "number and nothing else" case,
# so it can't accidentally swallow decimals like "0.1 mole..." or "3.5 g"
# that happen to start a solution line — those always have same-line text
# after the dot, so they'd fail this pattern's trailing `$`.
QUESTION_NUM_ONLY_RE = re.compile(r'^\s*(\d{1,3})\.\s*$')
OPTION_RE = re.compile(r'^\(([A-D])\)\s*(.*)')
ANS_RE = re.compile(r'^Ans\.?\s*\(?([A-D0-9.\-/]+)\)?', re.I)
SOL_START_RE = re.compile(r'^Sol\.?\s*(.*)', re.I)
SUBJECT_HEADER_RE = re.compile(r'PART-[A-Z]:\s*([A-Z]+)', re.I)


@dataclass
class PendingQuestion:
    number: str
    text: str
    section: str = "stem"          # stem | options | ans | sol
    options: dict = field(default_factory=dict)
    answer: str = ""
    sol_lines: list = field(default_factory=list)
    stem_images: list = field(default_factory=list)   # list[PIL.Image]
    sol_images: list = field(default_factory=list)    # list[PIL.Image]
    option_images: dict = field(default_factory=dict)  # {"A": PIL.Image, ...}


def get_or_create_subject(exam, name):
    subject, _ = Subject.objects.get_or_create(exam=exam, subject_name=name.title())
    return subject


def pil_to_bytes(pil_img, fmt="PNG"):
    buf = io.BytesIO()
    pil_img.convert("RGB").save(buf, format=fmt)
    return buf.getvalue()


def stack_vertically(pil_images):
    if len(pil_images) == 1:
        return pil_images[0]
    widths, heights = zip(*(im.size for im in pil_images))
    canvas = Image.new("RGB", (max(widths), sum(heights)), "white")
    y = 0
    for im in pil_images:
        canvas.paste(im.convert("RGB"), (0, y))
        y += im.size[1]
    return canvas


def save_field_image(image_field_file, filename, pil_img):
    image_field_file.save(filename, ContentFile(pil_to_bytes(pil_img)), save=False)


def save_to_storage(pil_img, path):
    default_storage.save(path, ContentFile(pil_to_bytes(pil_img)))
    return default_storage.url(path)


def page_events(page):
    """
    Returns a single list of events for a page, sorted top-to-bottom by y0:
        ("line", y0, text)
        ("image", y0, PIL.Image)
    This is what lets us tell "this diagram came after the Sol. line" from
    "this diagram came before it" — position on the page is the only signal
    a scanned/rendered PDF gives us.
    """
    events = []

    text_dict = page.get_text("dict")
    for block in text_dict.get("blocks", []):
        for line in block.get("lines", []):
            spans_text = "".join(span["text"] for span in line.get("spans", []))
            text = spans_text.strip()
            if not text:
                continue
            y0 = line["bbox"][1]
            events.append(("line", y0, text))

    # Two artifacts show up in this exporter's PDFs that are NOT question
    # content and must never reach stem/sol/option image buckets:
    #  1. A full-page decorative border/background image, re-embedded on
    #     EVERY page. It covers ~100%+ of the page's bounding box, so a
    #     coverage-ratio check identifies it reliably regardless of xref.
    #  2. The same image xref placed at the exact same (rounded) coordinates
    #     several times on one page — seen with special math symbols that
    #     this PDF rasterizes instead of using real text/vector glyphs.
    #     These aren't diagrams; keeping only one copy per unique bbox
    #     avoids inflating stem_images/sol_images with duplicates.
    page_area = page.rect.width * page.rect.height
    seen_bboxes = set()

    for img in page.get_images(full=True):
        xref = img[0]
        try:
            bbox = page.get_image_bbox(img)
        except ValueError:
            continue  # image reused elsewhere on page / not directly placed

        area = bbox.width * bbox.height
        if page_area and area / page_area > 0.7:
            continue  # full-page background/border decoration — skip

        bbox_key = (round(bbox.x0), round(bbox.y0), round(bbox.x1), round(bbox.y1))
        if bbox_key in seen_bboxes:
            continue  # duplicate glyph/render at the same spot — skip
        seen_bboxes.add(bbox_key)

        raw = page.parent.extract_image(xref)
        try:
            pil_img = Image.open(io.BytesIO(raw["image"]))
        except Exception:
            continue
        events.append(("image", bbox.y0, pil_img))

    events.sort(key=lambda e: e[1])
    return events


def parse_pdf(pdf_path):
    doc = fitz.open(pdf_path)

    questions = []
    current = None
    current_subject = None
    last_option_key = None  # tracks which option we most recently saw, for
                             # attributing an image seen right after it

    for pno in range(len(doc)):
        for kind, y0, payload in page_events(doc[pno]):

            if kind == "line":
                line = payload

                header = SUBJECT_HEADER_RE.search(line)
                if header:
                    current_subject = header.group(1)
                    continue

                q_match = QUESTION_RE.match(line)
                q_num_only_match = None if q_match else QUESTION_NUM_ONLY_RE.match(line)
                if q_match or q_num_only_match:
                    if current:
                        questions.append((current, current_subject))
                    if q_match:
                        current = PendingQuestion(number=q_match.group(1), text=q_match.group(2))
                    else:
                        # bare "N." line — text arrives on the next line(s)
                        # and gets appended via the normal "section == stem"
                        # accumulation branch further down.
                        current = PendingQuestion(number=q_num_only_match.group(1), text="")
                    last_option_key = None
                    continue

                if current is None:
                    continue

                opt_match = OPTION_RE.match(line)
                if opt_match:
                    current.section = "options"
                    current.options[opt_match.group(1)] = opt_match.group(2)
                    last_option_key = opt_match.group(1)
                    continue

                ans_match = ANS_RE.match(line)
                if ans_match:
                    current.section = "ans"
                    current.answer = ans_match.group(1)
                    continue

                sol_match = SOL_START_RE.match(line)
                if sol_match:
                    current.section = "sol"
                    if sol_match.group(1):
                        current.sol_lines.append(sol_match.group(1))
                    continue

                if current.section == "sol":
                    current.sol_lines.append(line)
                elif current.section == "stem":
                    current.text += " " + line
                # stray lines during "options"/"ans" sections are ignored

            elif kind == "image":
                if current is None:
                    continue
                pil_img = payload

                if current.section == "stem":
                    current.stem_images.append(pil_img)
                elif current.section == "sol":
                    current.sol_images.append(pil_img)
                elif current.section == "options":
                    logger.warning(
                        "Q%s: image encountered while parsing OPTIONS (near "
                        "option %s) — this usually means the options ARE "
                        "graphs. Auto-assigning in order; VERIFY MANUALLY.",
                        current.number, last_option_key or "?"
                    )
                    # assign to next unfilled option slot, A→B→C→D
                    for key in ["A", "B", "C", "D"]:
                        if key not in current.option_images:
                            current.option_images[key] = pil_img
                            break
                else:
                    # image before we've even hit the first option/section
                    # marker for this question — treat as stem
                    current.stem_images.append(pil_img)

    if current:
        questions.append((current, current_subject))

    return questions


def run(pdf_path, exam_id):
    exam = Exam.objects.get(pk=exam_id)
    parsed_questions = parse_pdf(pdf_path)

    for q, subject_name in parsed_questions:
        if not subject_name:
            logger.warning("Q%s has no detected subject — skipping", q.number)
            continue

        subject = get_or_create_subject(exam, subject_name)
        is_mcq = bool(q.options)

        # update_or_create (not get_or_create): on a re-run, get_or_create's
        # "defaults" are only applied when the row is first CREATED — if the
        # question already exists, exam/language/status would silently keep
        # their old values instead of being refreshed. update_or_create
        # applies defaults on every run, matching/creating on the lookup
        # fields (subject, question_type, question_text) either way.
        question, created = Question.objects.update_or_create(
            subject=subject,
            question_type="MCQ" if is_mcq else "Numerical",
            question_text=q.text.strip(),
            defaults={"exam": exam, "language": "English", "status": "imported"},
        )

        # ---- stem image(s) -> Question.image_url (single field, so stack) ----
        if q.stem_images:
            stem_img = stack_vertically(q.stem_images)
            save_field_image(question.image_url, f"q_{question.question_id}.png", stem_img)
            question.save()

        # ---- options (text) + option images (JSONField, existing schema) ----
        if is_mcq:
            option_obj, _ = QuestionOption.objects.get_or_create(question=question)
            for key in ["A", "B", "C", "D"]:
                setattr(option_obj, f"option_{key}", q.options.get(key, ""))
                if key in q.option_images:
                    url = save_to_storage(
                        q.option_images[key],
                        f"jee_question_images/options/opt_{question.question_id}_{key}.png",
                    )
                    setattr(option_obj, f"option_{key}_images", {"images": [url]})
            option_obj.save()

        # ---- correct answer ----
        # update_or_create: if a re-parse fixes a misread "Ans." line, this
        # makes sure the corrected value actually overwrites the DB instead
        # of the first (possibly wrong) import silently sticking around.
        if q.answer:
            CorrectAnswer.objects.update_or_create(
                question=question,
                defaults={
                    "answer_value": q.answer,
                    "answer_type": "MCQ" if is_mcq else "Numerical",
                },
            )

        # ---- solution text + solution images (JSONField, existing schema) ----
        # update_or_create: this is the one that matters most for images —
        # with get_or_create, re-running the script after fixing a stem/sol
        # split bug would NOT update image_url on questions that already
        # have a Solution row, so old/wrong image URLs would stay forever.
        if q.sol_lines or q.sol_images:
            sol_image_urls = [
                save_to_storage(im, f"jee_question_images/solutions/sol_{question.question_id}_{i}.png")
                for i, im in enumerate(q.sol_images)
            ]
            Solution.objects.update_or_create(
                question=question,
                defaults={
                    "explaination_text": " ".join(q.sol_lines).strip(),
                    "hints": "",
                    "image_url": {"images": sol_image_urls} if sol_image_urls else {},
                },
            )

    logger.info("Imported %d questions from %s", len(parsed_questions), pdf_path)


class Command(BaseCommand):
    # Django's manage.py loader requires a class literally named `Command`
    # inheriting BaseCommand in any file under management/commands/ — a
    # file with only module-level functions (parse_pdf, run, etc.) is
    # importable but has no `Command` attribute, which is exactly the
    # AttributeError you hit. This wraps the existing run() so the CLI
    # takes --pdf and --exam-id instead of you writing a one-off shell -c.
    help = "Import a JEE-style mock-test PDF into Exam/Question/Solution/etc."

    def add_arguments(self, parser):
        parser.add_argument(
            "--pdf", required=True,
            help="Path to the PDF, as seen INSIDE the container (e.g. /app/selfstudys_com_file.pdf)",
        )
        parser.add_argument(
            "--exam-id", required=True, type=int,
            help="Primary key of an existing Exam row to attach the parsed questions to",
        )

    def handle(self, *args, **options):
        pdf_path = options["pdf"]
        exam_id = options["exam_id"]
        try:
            run(pdf_path, exam_id)
        except Exam.DoesNotExist:
            raise CommandError(
                f"No Exam with id={exam_id} exists. Create one first, e.g.:\n"
                f'  python manage.py shell -c "from MockAdmin.models import Exam; '
                f'Exam.objects.create(...)"'
            )