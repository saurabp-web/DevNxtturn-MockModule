"""
import_mock_json.py
--------------------
Ingest the ALREADY-EXTRACTED mock-test data — produced earlier as
    jee_main_2025_mock_test_1.json   (90 questions, text + solutions)
    images/                          (cropped diagrams: question / option / solution)
into your EXISTING Django models:

    Exam, MockExam, Subject, Chapter, Question, QuestionOption,
    Solution, CorrectAnswer

WHY THIS REPLACES import_mock_pdf.py
-------------------------------------
The previous script (import_mock_pdf.py) parsed the raw PDF directly with
PyMuPDF: reconstructing question/option/solution text from positioned text
spans, guessing stem-vs-option-vs-solution boundaries from y-coordinates,
attributing floating diagrams to the nearest "(X)" marker, and falling back
to Mathpix OCR for options whose fractions/roots got scrambled during text
extraction. All of that complexity existed to cope with reading an
unstructured PDF.

That work has already been done, once, by hand — the JSON file already has
clean question_text / options / answer / solution strings, and every
diagram has already been identified and cropped to its own small PNG (see
image_path / question_image / option_images / solution_image below). This
script is therefore a much smaller, purely mechanical loader: read the
JSON, open the referenced image files, and call the exact same Django
model-saving logic the old script used (same lookup keys, same lowercase
QuestionOption fields, same JSONField image_url shape, same
update_or_create semantics so re-running the import is safe).

None of the PyMuPDF / Mathpix / stem-vs-option-position-resolution code is
needed any more and has been removed. If a FUTURE mock test still only
exists as a raw PDF, use import_mock_pdf.py for that one and this script
for anything that's already gone through the JSON-extraction step.

EXPECTED INPUT LAYOUT
----------------------
    jee_main_2025_mock_test_1.json
    images/
        q8_solution.png
        q9_solution.png
        q10_solution.png
        q31_diagram.png
        q42_option_A.png, q42_option_B.png, q42_option_C.png, q42_option_D.png
        q43_option_A.png, ... q44_option_A.png, ...
        q50_diagram.png
        q58_diagram_question.png
        q58_diagram_solution.png

The JSON's image fields are paths relative to the JSON file's own
directory (e.g. "images/q42_option_A.png"), matching how the extraction
step wrote them — see --images-dir below if your copy lives elsewhere.

JSON SCHEMA (per question, as produced by the extraction step)
-----------------------------------------------------------------
    {
      "question_number": 8,
      "subject": "Mathematics" | "Physics" | "Chemistry",
      "section": "Section-I" | "Section-II",
      "question_type": "MCQ" | "Numerical",
      "question_text": "...",
      "options": {"A": "...", "B": "...", "C": "...", "D": "..."} | null,
      "answer": "A" | "155" | ...,
      "solution": "...",
      "question_image": "images/q50_diagram.png" | null,
      "option_images": {"A": "images/q42_option_A.png", ...} | null,
      "solution_image": "images/q8_solution.png" | null
    }

MODEL FIELD MAPPING (unchanged from import_mock_pdf.py)
------------------------------------------------------------
    Question.image_url      -> JSONField {"images": [url, ...]}   (stem diagrams)
    Solution.image_url       -> JSONField {"images": [url, ...]}   (solution diagrams)
    QuestionOption.option_images -> JSONField {"A": [url, ...], ...} (per-option diagrams)
    QuestionOption.option_a/b/c/d -> plain text options (lowercase real DB columns)
    CorrectAnswer.option_id  -> "A" for MCQ, or the numeric string for Numerical

Each of our JSON's `question_image` / `option_images[letter]` /
`solution_image` is a single path (one diagram per slot in this dataset),
so it's wrapped in a one-item list before being written, to match the
existing list-of-urls JSONField shape used by import_mock_pdf.py (which
supports multiple fragments per slot; we simply never have more than one
here).

OPTIONAL: LATEX-RENDERED TEXT
------------------------------
Same to_latex() best-effort converter as the previous script (turns
"4/3 t0" into "\\dfrac{4}{3} t_{0}", "10√33 − 50 s" into
"10\\sqrt{33} − 50 s", etc.), applied to question_text / each option /
the solution text IF your models have the matching *_latex columns
(question_text_latex, option_a_latex.../option_d_latex,
explaination_text_latex). Skipped silently if those columns don't exist —
nothing breaks either way. No Mathpix OCR step here: our option text is
already clean hand-transcribed text, not reconstructed from scrambled PDF
spans, so there is nothing left for OCR to fix.

HOW TO RUN
----------
1. Put this in e.g. MockAdmin/management/commands/import_mock_json.py
2. Copy jee_main_2025_mock_test_1.json and the images/ folder into the
   container (or wherever --json points), then:

       python manage.py import_mock_json \\
           --json /app/jee_main_2025_mock_test_1.json \\
           --exam-id 1 --mock-exam-id 1

   --images-dir defaults to the JSON file's own directory (i.e. it expects
   an images/ subfolder right next to the JSON). Pass --images-dir
   explicitly if you copied the images somewhere else:

       python manage.py import_mock_json \\
           --json /app/jee_main_2025_mock_test_1.json \\
           --images-dir /app/mock_images \\
           --exam-id 1 --mock-exam-id 1

   or as a one-off via shell:
       python manage.py shell -c "import import_mock_json as m; m.run('jee_main_2025_mock_test_1.json', exam_id=1, mockexam_id=1)"
"""

import os
import re
import io
import json
import logging

from dataclasses import dataclass, field

from django.core.management.base import BaseCommand, CommandError

from PIL import Image
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# adjusted for this project: models live in MockAdmin
from MockAdmin.models import (
    Exam, MockExam, Subject, Chapter, Question, QuestionOption, Solution, CorrectAnswer,
)

logger = logging.getLogger("import_mock_json")


# ---------------------------------------------------------------------------
# LaTeX conversion for option/question/solution text (unchanged from
# import_mock_pdf.py — see that file's docstring for exactly what this does
# and does not convert). Kept here so importing from JSON gets the same
# optional KaTeX/MathJax-renderable fields the PDF importer produced.
# ---------------------------------------------------------------------------
_LATEX_SQRT_PAREN_RE = re.compile(r'√\(([^)]+)\)')
_LATEX_SQRT_TOKEN_RE = re.compile(r'√\s*([A-Za-z0-9]+)')
_LATEX_FRACTION_RE = re.compile(
    r'(?<![\w/.])(-?\d+(?:\.\d+)?|[A-Za-z]\w*)\s*/\s*(\d+(?:\.\d+)?|[A-Za-z]\w*)(?![\w/.])'
)
_LATEX_SUBSCRIPT_RE = re.compile(r'\b([A-Za-z])(\d+)\b')


def to_latex(text):
    """
    Best-effort conversion of plain text into a LaTeX fragment renderable
    by KaTeX/MathJax, e.g.:
        "4/3 t0"          -> "\\dfrac{4}{3} t_{0}"
        "10√33 − 50 s"    -> "10\\sqrt{33} − 50 s"
        "√(x^2+y^2)"      -> "\\sqrt{x^2+y^2}"
    Returns the input unchanged if it's empty/None.
    """
    if not text:
        return text
    s = text
    s = _LATEX_SQRT_PAREN_RE.sub(r'\\sqrt{\1}', s)
    s = _LATEX_SQRT_TOKEN_RE.sub(r'\\sqrt{\1}', s)
    s = _LATEX_FRACTION_RE.sub(r'\\dfrac{\1}{\2}', s)
    s = _LATEX_SUBSCRIPT_RE.sub(r'\1_{\2}', s)
    return s


# ---------------------------------------------------------------------------
# Subject / Chapter helpers (unchanged from import_mock_pdf.py)
# ---------------------------------------------------------------------------
def get_or_create_subject(exam, name):
    subject, _ = Subject.objects.get_or_create(exam=exam, subject_name=name.title())
    return subject


# Question's real FK is `chapter` (Subject -> Chapter -> Question), not
# `subject` directly. Our JSON only carries a subject-level label
# ("Mathematics"/"Physics"/"Chemistry"), no per-question chapter, so every
# imported question lands under one catch-all chapter per subject, same as
# the PDF importer. Rename/re-file into real chapters later if you need
# chapter-level practice for these questions.
IMPORTED_CHAPTER_NAME = "Imported (Ungrouped)"


def get_or_create_chapter(subject):
    chapter, _ = Chapter.objects.get_or_create(
        subject=subject,
        chapter_name=IMPORTED_CHAPTER_NAME,
        defaults={"is_active": True},
    )
    return chapter


# ---------------------------------------------------------------------------
# Image loading / storage helpers
# ---------------------------------------------------------------------------
def pil_to_bytes(pil_img, fmt="PNG"):
    buf = io.BytesIO()
    pil_img.convert("RGB").save(buf, format=fmt)
    return buf.getvalue()


def save_to_storage(pil_img, path):
    default_storage.save(path, ContentFile(pil_to_bytes(pil_img)))
    return default_storage.url(path)


def load_image(images_dir, relative_path):
    """
    Open one of the extraction step's cropped PNGs (relative_path is
    whatever the JSON stored, e.g. "images/q42_option_A.png") as a PIL
    Image. Returns None (and logs a warning) instead of raising if the
    file is missing, so one missing/renamed file doesn't abort the whole
    import.
    """
    if not relative_path:
        return None
    # The JSON stores paths like "images/xyz.png" already rooted at
    # images_dir's parent; strip a leading "images/" if images_dir itself
    # already points AT the images folder, so both of these work:
    #   --images-dir /app/data            (contains an images/ subfolder)
    #   --images-dir /app/data/images     (points directly at the PNGs)
    candidates = [
        os.path.join(images_dir, relative_path),
        os.path.join(images_dir, os.path.basename(relative_path)),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return Image.open(path)
            except Exception as e:
                logger.warning("Could not open image %s: %s", path, e)
                return None
    logger.warning(
        "Image file not found (tried %s) — skipping this diagram.",
        " and ".join(candidates),
    )
    return None


# ---------------------------------------------------------------------------
# JSON loading
# ---------------------------------------------------------------------------
@dataclass
class LoadedQuestion:
    number: str
    subject: str
    question_type: str        # "MCQ" | "Numerical"
    text: str
    options: dict = field(default_factory=dict)   # {"A": "...", ...} (may be empty)
    answer: str = ""
    solution_text: str = ""
    stem_images: list = field(default_factory=list)      # list[PIL.Image]
    sol_images: list = field(default_factory=list)        # list[PIL.Image]
    option_images: dict = field(default_factory=dict)     # {"A": [PIL.Image, ...], ...}


def load_questions(json_path, images_dir):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    questions = []
    for q in data["questions"]:
        options = q.get("options") or {}
        is_mcq = q.get("question_type") == "MCQ" and bool(options)

        stem_img = load_image(images_dir, q.get("question_image"))
        sol_img = load_image(images_dir, q.get("solution_image"))

        option_images = {}
        raw_opt_images = q.get("option_images") or {}
        for letter, rel_path in raw_opt_images.items():
            img = load_image(images_dir, rel_path)
            if img is not None:
                option_images[letter] = [img]

        loaded = LoadedQuestion(
            number=str(q["question_number"]),
            subject=q["subject"],
            question_type="MCQ" if is_mcq else "Numerical",
            text=(q.get("question_text") or "").strip(),
            options=options,
            answer=str(q.get("answer") or "").strip(),
            solution_text=(q.get("solution") or "").strip(),
            stem_images=[stem_img] if stem_img is not None else [],
            sol_images=[sol_img] if sol_img is not None else [],
            option_images=option_images,
        )
        questions.append(loaded)

    return questions


# ---------------------------------------------------------------------------
# Main import
# ---------------------------------------------------------------------------
def run(json_path, exam_id, mockexam_id, images_dir=None):
    exam = Exam.objects.get(pk=exam_id)
    mock_exam = MockExam.objects.get(pk=mockexam_id)

    # Sanity check: the MockExam you're importing into should actually
    # belong to the Exam you passed — otherwise you'd silently attach
    # "JEE Main 2025 Mock Test - 1" questions under, say, NEET, which
    # would only surface as a confusing filter bug much later.
    if mock_exam.exam_id != exam.exam_id:
        raise ValueError(
            f"MockExam {mockexam_id} ({mock_exam.mockexam_name!r}) belongs to "
            f"exam_id={mock_exam.exam_id}, not exam_id={exam_id}. Pass the "
            f"matching --exam-id, or the correct --mock-exam-id."
        )

    images_dir = images_dir or os.path.dirname(os.path.abspath(json_path))

    loaded_questions = load_questions(json_path, images_dir)
    questions_with_option_images = []
    questions_with_stem_or_sol_images = []

    for q in loaded_questions:
        subject = get_or_create_subject(exam, q.subject)
        chapter = get_or_create_chapter(subject)
        is_mcq = q.question_type == "MCQ"

        question_text = q.text or f"[Q{q.number} - stem text missing, needs manual fix]"

        # update_or_create (not get_or_create): on a re-run, get_or_create's
        # "defaults" are only applied when the row is first CREATED — if the
        # question already exists, exam/mock_exam would silently keep their
        # old values instead of being refreshed. update_or_create applies
        # defaults on every run, matching/creating on the lookup fields
        # (chapter, question_type, question_text) either way.
        question, created = Question.objects.update_or_create(
            chapter=chapter,
            question_type="MCQ" if is_mcq else "Numerical",
            question_text=question_text,
            defaults={
                "exam": exam,
                "mock_exam": mock_exam,
                "is_active": True,
            },
        )
        if hasattr(question, "question_text_latex"):
            question.question_text_latex = to_latex(question_text)
            question.save()

        # ---- stem image(s) -> Question.image_url (JSONField, one url per diagram) ----
        if q.stem_images:
            stem_image_urls = [
                save_to_storage(im, f"jee_question_images/questions/q_{question.question_id}_{i}.png")
                for i, im in enumerate(q.stem_images)
            ]
            question.image_url = {"images": stem_image_urls}
            question.save()
            questions_with_stem_or_sol_images.append(q.number)

        # ---- options (text + per-option images) ----
        if is_mcq:
            option_obj, _ = QuestionOption.objects.get_or_create(
                question=question,
                defaults={"option_a": "", "option_b": "", "option_c": "", "option_d": ""},
            )
            option_obj.option_a = q.options.get("A", "")
            option_obj.option_b = q.options.get("B", "")
            option_obj.option_c = q.options.get("C", "")
            option_obj.option_d = q.options.get("D", "")

            # LaTeX-rendered mirror of each option, e.g. "4/3 t0" ->
            # "\dfrac{4}{3} t_{0}" — only written if these columns exist.
            if hasattr(option_obj, "option_a_latex"):
                for letter, field_name in (
                    ("A", "option_a_latex"), ("B", "option_b_latex"),
                    ("C", "option_c_latex"), ("D", "option_d_latex"),
                ):
                    setattr(option_obj, field_name, to_latex(q.options.get(letter, "")))

            # Persist graph-style options into QuestionOption.option_images:
            # {"A": ["url1.png"], "B": ["url2.png"], ...} — same shape as
            # import_mock_pdf.py (a list per letter, even though this
            # dataset only ever has one diagram per option slot).
            if q.option_images:
                option_obj.option_images = {
                    letter: [
                        save_to_storage(
                            img,
                            f"jee_question_images/options/q_{question.question_id}_opt_{letter}_{idx}.png",
                        )
                        for idx, img in enumerate(imgs)
                    ]
                    for letter, imgs in q.option_images.items()
                }
                questions_with_option_images.append(q.number)

            option_obj.save()

        # ---- correct answer ----
        # CorrectAnswer only has `option_id` — "A" (or "A,C" for
        # multi-select, not used in this dataset) for MCQ, or the numeric
        # string itself (e.g. "155") for Numerical questions.
        if q.answer:
            CorrectAnswer.objects.update_or_create(
                question=question,
                defaults={"option_id": q.answer},
            )

        # ---- solution text + solution image(s) (JSONField, existing schema) ----
        if q.solution_text or q.sol_images:
            sol_image_urls = [
                save_to_storage(im, f"jee_question_images/solutions/sol_{question.question_id}_{i}.png")
                for i, im in enumerate(q.sol_images)
            ]
            if sol_image_urls:
                questions_with_stem_or_sol_images.append(q.number)

            sol_defaults = {
                "explaination_text": q.solution_text,
                "hints": "",
                "image_url": {"images": sol_image_urls} if sol_image_urls else {},
            }
            solution_field_names = {f.name for f in Solution._meta.get_fields()}
            if "explaination_text_latex" in solution_field_names:
                sol_defaults["explaination_text_latex"] = to_latex(q.solution_text)
            Solution.objects.update_or_create(question=question, defaults=sol_defaults)

    if questions_with_option_images:
        logger.info(
            "%d question(s) had graph-style options, saved to "
            "QuestionOption.option_images: Q%s.",
            len(questions_with_option_images),
            ", Q".join(questions_with_option_images),
        )

    if questions_with_stem_or_sol_images:
        logger.info(
            "%d question(s) had stem/solution diagrams attached: Q%s.",
            len(set(questions_with_stem_or_sol_images)),
            ", Q".join(sorted(set(questions_with_stem_or_sol_images), key=int)),
        )

    logger.info(
        "Imported %d questions from %s into exam=%s, mock_exam=%s",
        len(loaded_questions), json_path, exam, mock_exam,
    )


class Command(BaseCommand):
    help = (
        "Import a pre-extracted mock-test JSON (+ its images/ folder) into "
        "Exam/MockExam/Question/Solution/etc. — use this for datasets that "
        "have already been through the JSON-extraction step, as opposed to "
        "import_mock_pdf.py which parses a raw PDF directly."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--json", required=True,
            help="Path to the extracted JSON file, as seen INSIDE the container "
                 "(e.g. /app/jee_main_2025_mock_test_1.json)",
        )
        parser.add_argument(
            "--images-dir", default=None,
            help="Directory containing the images/ folder referenced by the JSON. "
                 "Defaults to the same directory the JSON file itself is in.",
        )
        parser.add_argument(
            "--exam-id", required=True, type=int,
            help="Primary key of an existing Exam row (the parent exam, e.g. JEE Main) to attach the parsed questions to",
        )
        parser.add_argument(
            "--mock-exam-id", required=True, type=int,
            help="Primary key of an existing MockExam row (the specific mock test, e.g. 'JEE Main 2025 Mock Test - 1') these questions belong to",
        )

    def handle(self, *args, **options):
        json_path = options["json"]
        images_dir = options["images_dir"]
        exam_id = options["exam_id"]
        mockexam_id = options["mock_exam_id"]
        try:
            run(json_path, exam_id, mockexam_id, images_dir=images_dir)
        except Exam.DoesNotExist:
            raise CommandError(
                f"No Exam with id={exam_id} exists. Create one first, e.g.:\n"
                f'  python manage.py shell -c "from MockAdmin.models import Exam; '
                f'Exam.objects.create(...)"'
            )
        except MockExam.DoesNotExist:
            raise CommandError(
                f"No MockExam with id={mockexam_id} exists. Create one first, e.g.:\n"
                f'  python manage.py shell -c "from MockAdmin.models import MockExam; '
                f'MockExam.objects.create(exam_id={exam_id}, mockexam_name=\'...\')"'
            )
        except ValueError as e:
            raise CommandError(str(e))
        except FileNotFoundError as e:
            raise CommandError(f"Could not find file: {e}")
