"""
Testbook MCQ Scraper
====================
Scrapes questions, options, correct answers, and explanations from Testbook
MCQ pages and saves them into your Django models:
  - Subject, Chapter, Topic (linked hierarchy)
  - Question (with image_url for diagram questions)
  - QuestionOption (A/B/C/D with option image JSON)
  - CorrectAnswer
  - Solution (explanation text + images)

Usage:
    python testbook_scraper.py

Requirements:
    pip install requests beautifulsoup4 lxml Pillow django

    Run inside your Django project:
        python manage.py shell < testbook_scraper.py
    OR as a management command (see bottom of file).

Configuration:
    Set SCRAPE_CONFIG at the top before running.
"""

import os
import re
import json
import time
import hashlib
import logging
import requests
import django

from io import BytesIO
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# CONFIGURE THESE BEFORE RUNNING
# ─────────────────────────────────────────────
SCRAPE_CONFIG = {
    # Target URL(s) — add more URLs for other chapters
    "urls": [
        "https://testbook.com/objective-questions/mcq-on-co-ordinate-geometry--5eea6a1039140f30f369e7fb",
        # Add more chapter URLs here:
        # "https://testbook.com/objective-questions/mcq-on-triangles--...",
    ],

    # Django model references — set these to match your existing DB records
    # These will be fetched/created automatically based on names below.
    "exam_name": "SSC",          # Must already exist in your Exam table
    "subject_name": "Mathematics",
    "chapter_name": "Co-ordinate Geometry",
    "topic_name": "General",     # Default topic if not detected per-question

    # Where to save downloaded images (relative to MEDIA_ROOT)
    "image_upload_dir": "jee_question_images",

    # Delay between page requests (seconds) — be respectful
    "request_delay": 1.5,

    # Max questions to scrape per URL (None = all)
    "max_questions": None,

    # question_type to assign
    "question_type": "MCQ",

    # language
    "language": "English",

    # ── Difficulty Classification ──────────────────────────────────────────
    # "ai"       → Use Claude API to classify each question (most accurate)
    # "rules"    → Fast heuristic-based classifier (no API calls needed)
    # "disabled" → All questions saved with difficulty_level = None
    "difficulty_mode": "ai",

    # Your Anthropic API key (or set env var ANTHROPIC_API_KEY)
    "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY", ""),

    # How many questions to classify per API call (batching saves tokens)
    # Recommended: 5–10. Reduce to 1 if you need per-question error isolation.
    "ai_batch_size": 5,

    # Subject context helps the AI calibrate difficulty correctly
    # e.g. "JEE Advanced Mathematics", "SSC CGL Quantitative Aptitude", "UPSC GS"
    "exam_context": "SSC CGL Mathematics - Co-ordinate Geometry",
}

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# DJANGO SETUP (when running as standalone script)
# ─────────────────────────────────────────────
def setup_django():
    """Call this if running outside manage.py shell."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")  # ← change this
    django.setup()


# ─────────────────────────────────────────────
# IMAGE DOWNLOADER
# ─────────────────────────────────────────────
def download_image(url: str, save_dir: str) -> str | None:
    """
    Download image from URL, save to MEDIA_ROOT/<save_dir>/<hash>.<ext>.
    Returns the relative path (suitable for ImageField / JSONField storage).
    Returns None on failure.
    """
    try:
        from django.conf import settings
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        # Determine extension
        content_type = response.headers.get("content-type", "")
        ext_map = {"image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif", "image/webp": ".webp"}
        ext = ext_map.get(content_type.split(";")[0].strip(), ".png")

        # Unique filename based on URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        filename = f"{url_hash}{ext}"

        full_dir = os.path.join(settings.MEDIA_ROOT, save_dir)
        os.makedirs(full_dir, exist_ok=True)
        full_path = os.path.join(full_dir, filename)

        if not os.path.exists(full_path):
            with open(full_path, "wb") as f:
                f.write(response.content)
            logger.info(f"  Downloaded image: {filename}")

        return os.path.join(save_dir, filename)

    except Exception as e:
        logger.warning(f"  Failed to download image {url}: {e}")
        return None


# ─────────────────────────────────────────────
# DIFFICULTY CLASSIFIER
# ─────────────────────────────────────────────

DIFFICULTY_LEVELS = ("Easy", "Medium", "Hard")


# ── Rule-based fallback ──────────────────────
# Heuristics based on language complexity, formula density, multi-step signals.
HARD_KEYWORDS = [
    "locus", "parametric", "eccentricity", "asymptote", "tangent", "normal",
    "chord of contact", "pair of tangents", "radical axis", "coaxial",
    "orthogonal", "pole", "polar", "reflection", "transformation",
    "combined equation", "homogeneous", "director circle", "auxiliary circle",
    "subtend", "concyclic", "collinear condition", "determinant",
    "minimize", "maximize", "area of triangle formed",
]
MEDIUM_KEYWORDS = [
    "slope", "midpoint", "distance", "section formula", "centroid",
    "incentre", "circumcentre", "orthocentre", "parallel", "perpendicular",
    "angle between", "intersection", "concurrent", "collinear",
    "ratio", "divides", "external division",
]
EASY_KEYWORDS = [
    "find the point", "x-coordinate", "y-coordinate", "origin",
    "x-axis", "y-axis", "quadrant", "distance formula", "simple",
    "which of the following points", "lies on",
]


def rule_based_difficulty(question_text: str, options: dict, explanation: str) -> str:
    """
    Estimate difficulty using keyword heuristics.
    Returns "Easy", "Medium", or "Hard".
    """
    combined = (question_text + " " + explanation).lower()

    # Count formula complexity: Greek letters, exponents, fractions as signals
    formula_signals = len(re.findall(r"[²³√∫∑∏αβγδθλ]|\\frac|\\sqrt|\^2|\^3", combined))

    # Count number of mathematical operations hinted in the question
    multi_step = len(re.findall(
        r"\b(then|hence|therefore|find|calculate|determine|evaluate)\b", combined
    ))

    hard_hits = sum(1 for kw in HARD_KEYWORDS if kw in combined)
    medium_hits = sum(1 for kw in MEDIUM_KEYWORDS if kw in combined)
    easy_hits = sum(1 for kw in EASY_KEYWORDS if kw in combined)

    score = (hard_hits * 3) + (medium_hits * 1) + (formula_signals * 2) + (multi_step * 0.5) - (easy_hits * 2)

    if score >= 5:
        return "Hard"
    elif score >= 2:
        return "Medium"
    else:
        return "Easy"


# ── AI-based classifier (Claude API) ────────
def _build_difficulty_prompt(batch: list[dict], exam_context: str) -> str:
    """Build the classification prompt for a batch of questions."""
    lines = [
        f"You are an expert educator assessing question difficulty for: {exam_context}.",
        "",
        "Classify each question below as exactly one of: Easy / Medium / Hard.",
        "",
        "Difficulty criteria:",
        "  Easy   — Direct formula application, single step, recall-based.",
        "  Medium — 2–3 steps, concept combination, moderate calculation.",
        "  Hard   — Multi-step reasoning, advanced concepts, tricky options,",
        "            coordinate geometry proofs, locus, or conics.",
        "",
        "Return ONLY a JSON array of objects, one per question, in the same order.",
        'Format: [{"index": 1, "difficulty": "Easy", "reason": "one line"}, ...]',
        "No markdown, no extra text.",
        "",
        "Questions:",
    ]
    for i, q in enumerate(batch, 1):
        opts = q.get("options", {})
        lines.append(f"\nQ{i}: {q['question_text'][:300]}")
        for label in ["A", "B", "C", "D"]:
            if opts.get(label):
                lines.append(f"  {label}) {opts[label][:120]}")
        if q.get("explanation_text"):
            lines.append(f"  [Explanation hint]: {q['explanation_text'][:200]}")

    return "\n".join(lines)


def classify_difficulty_ai(
    questions: list[dict],
    api_key: str,
    exam_context: str,
    batch_size: int = 5,
) -> list[str]:
    """
    Call Claude API to classify difficulty for a list of question dicts.
    Returns a list of difficulty strings in the same order as input.
    Falls back to rule-based on any error.

    Args:
        questions:    list of parsed question dicts
        api_key:      Anthropic API key
        exam_context: e.g. "JEE Advanced Maths"
        batch_size:   questions per API call

    Returns:
        list[str] — one of "Easy", "Medium", "Hard" per question
    """
    if not api_key:
        logger.warning("No ANTHROPIC_API_KEY set — falling back to rule-based difficulty.")
        return [rule_based_difficulty(q["question_text"], q["options"], q.get("explanation_text", ""))
                for q in questions]

    results = ["Medium"] * len(questions)  # safe default

    for batch_start in range(0, len(questions), batch_size):
        batch = questions[batch_start: batch_start + batch_size]
        prompt = _build_difficulty_prompt(batch, exam_context)

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",   # fast + cheap for classification
                    "max_tokens": 800,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            # Extract text from response
            raw = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    raw += block["text"]

            # Strip markdown fences if present
            raw = re.sub(r"```(?:json)?|```", "", raw).strip()

            classified = json.loads(raw)

            for item in classified:
                idx = item.get("index", 1) - 1  # convert 1-based → 0-based within batch
                global_idx = batch_start + idx
                level = item.get("difficulty", "Medium")
                if level not in DIFFICULTY_LEVELS:
                    level = "Medium"
                results[global_idx] = level
                logger.info(
                    f"    [AI] Q{global_idx+1} → {level}  ({item.get('reason', '')})"
                )

        except json.JSONDecodeError as e:
            logger.warning(f"  AI response JSON parse error: {e}. Using rule-based for this batch.")
            for i, q in enumerate(batch):
                results[batch_start + i] = rule_based_difficulty(
                    q["question_text"], q["options"], q.get("explanation_text", "")
                )
        except Exception as e:
            logger.warning(f"  AI classification failed: {e}. Using rule-based for this batch.")
            for i, q in enumerate(batch):
                results[batch_start + i] = rule_based_difficulty(
                    q["question_text"], q["options"], q.get("explanation_text", "")
                )

        time.sleep(0.5)  # avoid hammering the API

    return results


def classify_difficulty(questions: list[dict], config: dict) -> list[str]:
    """
    Top-level dispatcher. Reads config["difficulty_mode"] and routes accordingly.
    Returns list of difficulty strings aligned to input questions list.
    """
    mode = config.get("difficulty_mode", "ai")

    if mode == "disabled":
        logger.info("  Difficulty classification disabled.")
        return [None] * len(questions)

    elif mode == "rules":
        logger.info("  Using rule-based difficulty classification.")
        return [
            rule_based_difficulty(q["question_text"], q["options"], q.get("explanation_text", ""))
            for q in questions
        ]

    else:  # "ai"
        logger.info(f"  Using AI difficulty classification (batch_size={config.get('ai_batch_size', 5)})...")
        return classify_difficulty_ai(
            questions,
            api_key=config.get("anthropic_api_key", ""),
            exam_context=config.get("exam_context", "Competitive exam"),
            batch_size=config.get("ai_batch_size", 5),
        )


# ─────────────────────────────────────────────
# HTML FETCH
# ─────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_page(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


# ─────────────────────────────────────────────
# TEXT CLEANER
# ─────────────────────────────────────────────
def clean_text(element) -> str:
    """Extract clean text, collapsing whitespace."""
    if element is None:
        return ""
    text = element.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def extract_images_from_element(element, base_url="https://testbook.com") -> list[str]:
    """Return list of absolute image URLs found inside an element."""
    if element is None:
        return []
    images = []
    for img in element.find_all("img"):
        src = img.get("src", "").strip()
        if src and not src.startswith("data:"):
            images.append(urljoin(base_url, src))
    return images


# ─────────────────────────────────────────────
# PARSE A SINGLE QUESTION BLOCK
# ─────────────────────────────────────────────
def parse_question_block(block: BeautifulSoup) -> dict | None:
    """
    Parse one question block from the Testbook MCQ page.

    Returns a dict:
    {
        "question_text": str,
        "question_image_urls": [str],   # images IN the question stem
        "options": {                     # A/B/C/D texts
            "A": str, "B": str, "C": str, "D": str
        },
        "option_images": {              # image URLs per option
            "A": [str], "B": [str], "C": [str], "D": [str]
        },
        "correct_answer": str,          # "A", "B", "C", or "D"
        "explanation_text": str,
        "explanation_images": [str],
        "has_diagram": bool,
    }
    """
    result = {
        "question_text": "",
        "question_image_urls": [],
        "options": {"A": "", "B": "", "C": "", "D": ""},
        "option_images": {"A": [], "B": [], "C": [], "D": []},
        "correct_answer": "",
        "explanation_text": "",
        "explanation_images": [],
        "has_diagram": False,
    }

    # ── Question stem ──
    # Testbook wraps question text in <h4> or a paragraph after the heading
    q_heading = block.find(["h4", "h3"])
    if not q_heading:
        return None

    # Remove "Question N:" prefix
    q_text_raw = clean_text(q_heading)
    q_text_raw = re.sub(r"^Co-ordinate Geometry Question \d+[:\s]*", "", q_text_raw).strip()
    result["question_text"] = q_text_raw

    # Images in the question stem
    result["question_image_urls"] = extract_images_from_element(q_heading)
    if result["question_image_urls"]:
        result["has_diagram"] = True

    # Also check for an image immediately after the heading (common pattern)
    next_el = q_heading.find_next_sibling()
    if next_el and next_el.name == "p":
        imgs = extract_images_from_element(next_el)
        if imgs:
            result["question_image_urls"].extend(imgs)
            result["has_diagram"] = True

    # ── Options ──
    # Options are in an <ol> or <ul> after the question heading
    options_list = block.find(["ol", "ul"])
    if options_list:
        items = options_list.find_all("li", recursive=False)
        labels = ["A", "B", "C", "D"]
        for i, item in enumerate(items[:4]):
            label = labels[i]
            result["options"][label] = clean_text(item)
            result["option_images"][label] = extract_images_from_element(item)
            if result["option_images"][label]:
                result["has_diagram"] = True

    # ── Correct Answer ──
    # Pattern: "Option N : <text>" or "Option N :"
    answer_tag = block.find(string=re.compile(r"Option\s+[1-4]\s*:", re.I))
    if answer_tag:
        match = re.search(r"Option\s+([1-4])\s*:", str(answer_tag))
        if match:
            num = int(match.group(1))
            result["correct_answer"] = ["A", "B", "C", "D"][num - 1]

    # ── Explanation / Detailed Solution ──
    solution_section = block.find(
        lambda tag: tag.name in ["div", "section"] and
        "detailed solution" in (tag.get_text() or "").lower()
    )
    if not solution_section:
        # Fallback: look for paragraphs after "Detailed Solution" text
        ds_heading = block.find(string=re.compile(r"detailed solution", re.I))
        if ds_heading:
            solution_section = ds_heading.find_parent()

    if solution_section:
        result["explanation_text"] = clean_text(solution_section)
        result["explanation_images"] = extract_images_from_element(solution_section)
        if result["explanation_images"]:
            result["has_diagram"] = True

    # Minimum: question text must be non-empty
    if not result["question_text"]:
        return None

    return result


# ─────────────────────────────────────────────
# MAIN SCRAPER
# ─────────────────────────────────────────────
def scrape_testbook_mcq(url: str, config: dict) -> list[dict]:
    """
    Scrape all questions from one Testbook MCQ URL.
    Returns list of parsed question dicts.
    """
    logger.info(f"Fetching: {url}")
    soup = fetch_page(url)
    if not soup:
        return []

    questions = []

    # Each question is wrapped in a section/div.  Testbook uses <h4> headings
    # with "Co-ordinate Geometry Question N" pattern.
    # We find all such headings and treat siblings up to next heading as one block.
    all_headings = soup.find_all(
        ["h4", "h3"],
        string=re.compile(r"Question\s+\d+", re.I)
    )

    if not all_headings:
        logger.warning("No question headings found. The page structure may have changed.")
        return []

    logger.info(f"Found {len(all_headings)} question headings.")

    for idx, heading in enumerate(all_headings):
        if config.get("max_questions") and len(questions) >= config["max_questions"]:
            break

        # Collect the block: from this heading to the next heading (or end)
        block_elements = [heading]
        sibling = heading.find_next_sibling()
        while sibling:
            # Stop at next question heading
            if sibling.name in ["h4", "h3"] and re.search(r"Question\s+\d+", sibling.get_text()):
                break
            block_elements.append(sibling)
            sibling = sibling.find_next_sibling()

        # Wrap collected elements in a virtual container
        container = BeautifulSoup("<div></div>", "lxml").find("div")
        for el in block_elements:
            container.append(BeautifulSoup(str(el), "lxml").find(el.name) or el)

        parsed = parse_question_block(container)
        if parsed:
            parsed["source_url"] = url
            questions.append(parsed)
            logger.info(
                f"  Q{idx+1}: {parsed['question_text'][:60]}... "
                f"| Answer: {parsed['correct_answer']} "
                f"| Diagram: {parsed['has_diagram']}"
            )
        else:
            logger.warning(f"  Q{idx+1}: Could not parse block.")

        time.sleep(0.1)  # tiny delay between parses

    # ── Classify difficulty for all parsed questions in one batched pass ──
    if questions:
        logger.info(f"\nClassifying difficulty for {len(questions)} questions...")
        difficulty_labels = classify_difficulty(questions, config)
        for q, level in zip(questions, difficulty_labels):
            q["difficulty_level"] = level
            logger.info(f"  → '{q['question_text'][:50]}...' = {level}")

    return questions


# ─────────────────────────────────────────────
# DJANGO SAVE
# ─────────────────────────────────────────────
def get_or_create_hierarchy(config: dict):
    """
    Fetch or create Exam → Subject → Chapter → Topic chain.
    Returns (exam, subject, chapter, topic).
    """
    from MockAdmin.models import Exam, Subject, Chapter, Topic
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Get or create Exam using exam_name as the lookup key
    exam, _ = Exam.objects.get_or_create(
        exam_name=config["exam_name"],
        defaults={
            'exam_code': 'JEE2024',
            'exam_category': 'JEE',
            'exam_year': 2024,
            'conducting_body': 'NTA',
            'estimated_time_hours': 3,
        }
    )

    # Subject
    subject, _ = Subject.objects.get_or_create(
        exam=exam,
        subject_name=config["subject_name"],
        defaults={"teacher": None}
    )

    # Chapter
    chapter, _ = Chapter.objects.get_or_create(
        subject=subject,
        chapter_name=config["chapter_name"]
    )

    # Topic
    topic, _ = Topic.objects.get_or_create(
        chapter=chapter,
        topic_name=config["topic_name"]
    )

    return exam, subject, chapter, topic


def save_question_to_db(parsed: dict, exam, subject, chapter, topic, config: dict):
    """
    Save a single parsed question dict into all relevant Django models.
    Skips duplicate questions (unique constraint on subject+type+text).
    """
    from MockAdmin.models import (
        Question, QuestionOption, CorrectAnswer, Solution
    )

    image_dir = config["image_upload_dir"]

    # ── 1. Download question stem image if any ──
    question_image_path = None
    if parsed["question_image_urls"]:
        question_image_path = download_image(parsed["question_image_urls"][0], image_dir)

    # ── 2. Question ──
    try:
        question, created = Question.objects.get_or_create(
            subject=subject,
            question_type=config["question_type"],
            question_text=parsed["question_text"],
            defaults={
                "exam": exam,
                "chapter": chapter,
                "topic": topic,
                "difficulty_level": parsed.get("difficulty_level"),  # "Easy"/"Medium"/"Hard"/None
                "language": config["language"],
                "image_url": question_image_path or "",
                "status": "active",
            }
        )
        if not created:
            logger.info(f"    → Duplicate question, skipping: {parsed['question_text'][:50]}")
            return None
    except Exception as e:
        logger.error(f"    Error saving question: {e}")
        return None

    # ── 3. QuestionOption ──
    # Download option images
    option_images_json = {}
    for label in ["A", "B", "C", "D"]:
        urls = parsed["option_images"].get(label, [])
        downloaded = []
        for url in urls:
            path = download_image(url, image_dir)
            if path:
                downloaded.append(path)
        option_images_json[label] = downloaded

    try:
        QuestionOption.objects.get_or_create(
            question=question,
            defaults={
                "option_A": parsed["options"]["A"],
                "option_B": parsed["options"]["B"],
                "option_C": parsed["options"]["C"],
                "option_D": parsed["options"]["D"],
                "option_A_images": option_images_json.get("A", []),
                "option_B_images": option_images_json.get("B", []),
                "option_C_images": option_images_json.get("C", []),
                "option_D_images": option_images_json.get("D", []),
            }
        )
    except Exception as e:
        logger.error(f"    Error saving options: {e}")

    # ── 4. CorrectAnswer ──
    if parsed["correct_answer"]:
        try:
            CorrectAnswer.objects.get_or_create(
                question=question,
                defaults={
                    "answer_value": parsed["correct_answer"],
                    "answer_type": config["question_type"],
                }
            )
        except Exception as e:
            logger.error(f"    Error saving correct answer: {e}")

    # ── 5. Solution ──
    explanation_images_paths = []
    for url in parsed.get("explanation_images", []):
        path = download_image(url, image_dir)
        if path:
            explanation_images_paths.append(path)

    if parsed["explanation_text"]:
        try:
            Solution.objects.get_or_create(
                question=question,
                defaults={
                    "user": None,
                    "explaination_text": parsed["explanation_text"],
                    "image_url": explanation_images_paths,  # stored as JSON list
                    "hints": "",
                }
            )
        except Exception as e:
            logger.error(f"    Error saving solution: {e}")

    difficulty = parsed.get("difficulty_level") or "N/A"
    logger.info(
        f"    ✓ Saved Q#{question.question_id} [{difficulty}]: {parsed['question_text'][:50]}"
    )
    return question


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
def run_scraper(config=SCRAPE_CONFIG):
    """Main function: scrape all URLs and save to DB."""
    # setup_django()  # ← Uncomment if running as standalone script

    exam, subject, chapter, topic = get_or_create_hierarchy(config)
    logger.info(f"Hierarchy: {exam} → {subject} → {chapter} → {topic}")

    total_saved = 0
    total_diagram = 0
    difficulty_counts = {"Easy": 0, "Medium": 0, "Hard": 0, "N/A": 0}

    for url in config["urls"]:
        parsed_questions = scrape_testbook_mcq(url, config)
        logger.info(f"\nParsed {len(parsed_questions)} questions from {url}")

        for pq in parsed_questions:
            q = save_question_to_db(pq, exam, subject, chapter, topic, config)
            if q:
                total_saved += 1
                if pq["has_diagram"]:
                    total_diagram += 1
                level = pq.get("difficulty_level") or "N/A"
                difficulty_counts[level] = difficulty_counts.get(level, 0) + 1

        time.sleep(config["request_delay"])

    logger.info(f"\n{'='*50}")
    logger.info(f"Done! Saved {total_saved} questions ({total_diagram} with diagrams).")
    logger.info(f"Difficulty breakdown:")
    for level, count in difficulty_counts.items():
        if count:
            logger.info(f"  {level:6s}: {count}")
    logger.info(f"{'='*50}")


# ─────────────────────────────────────────────
# STANDALONE RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    setup_django()
    run_scraper()


# ─────────────────────────────────────────────
# OPTIONAL: Django Management Command wrapper
# Save as: your_app/management/commands/scrape_testbook.py
# Usage: python manage.py scrape_testbook --url <URL> --chapter "Co-ordinate Geometry"
# ─────────────────────────────────────────────
MANAGEMENT_COMMAND_TEMPLATE = '''
# your_app/management/commands/scrape_testbook.py

from django.core.management.base import BaseCommand
from testbook_scraper import run_scraper, SCRAPE_CONFIG


class Command(BaseCommand):
    help = "Scrape MCQ questions from Testbook and save to DB"

    def add_arguments(self, parser):
        parser.add_argument("--url", type=str, help="Testbook MCQ URL to scrape")
        parser.add_argument("--exam", type=str, default="SSC")
        parser.add_argument("--subject", type=str, default="Mathematics")
        parser.add_argument("--chapter", type=str, default="Co-ordinate Geometry")
        parser.add_argument("--topic", type=str, default="General")
        parser.add_argument("--max", type=int, default=None)
        parser.add_argument(
            "--difficulty",
            choices=["ai", "rules", "disabled"],
            default="ai",
            help="Difficulty classification mode (default: ai)"
        )
        parser.add_argument("--batch-size", type=int, default=5,
                            help="Questions per AI classification call (default: 5)")

    def handle(self, *args, **options):
        config = {**SCRAPE_CONFIG}
        if options["url"]:
            config["urls"] = [options["url"]]
        config["exam_name"] = options["exam"]
        config["subject_name"] = options["subject"]
        config["chapter_name"] = options["chapter"]
        config["topic_name"] = options["topic"]
        config["max_questions"] = options["max"]
        config["difficulty_mode"] = options["difficulty"]
        config["ai_batch_size"] = options["batch_size"]
        run_scraper(config)
        self.stdout.write(self.style.SUCCESS("Scraping complete!"))
'''