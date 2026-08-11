"""
Django management command: scrape_neet_syllabus

Scrapes the NEET UG subject-wise syllabus (chapter names + topics) from
https://www.affinityeducation.in/neet-syllabus and saves it as a JSON file.

USAGE
-----
    python manage.py scrape_neet_syllabus
    python manage.py scrape_neet_syllabus --url https://www.affinityeducation.in/neet-syllabus
    python manage.py scrape_neet_syllabus --output neet_syllabus.json
    python manage.py scrape_neet_syllabus --pretty

INSTALLATION
------------
1. Put this file at: <your_app>/management/commands/scrape_neet_syllabus.py
   (create the two `management/` and `management/commands/` folders if they
   don't exist, and add an empty `__init__.py` in each — see setup notes
   at the bottom of this file for a ready-made shell snippet)
2. Add these to your requirements:
       requests
       beautifulsoup4
       lxml
3. Run: pip install requests beautifulsoup4 lxml
"""

import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand, CommandError

DEFAULT_URL = "https://www.affinityeducation.in/neet-syllabus"

# Heading text -> subject name. Matched case-insensitively against each
# heading's text (h2/h3/h4/h5) that appears above a syllabus table.
SUBJECT_HEADING_MAP = {
    "physics syllabus": "Physics",
    "biology syllabus": "Biology",
    "chemistry syllabus": "Chemistry",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def clean_text(text: str) -> str:
    """Collapse whitespace/newlines produced by nested tags into single spaces."""
    if text is None:
        return ""
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class Command(BaseCommand):
    help = "Scrape the NEET UG subject-wise syllabus (chapters + topics) and save as JSON."

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            type=str,
            default=DEFAULT_URL,
            help=f"Page URL to scrape (default: {DEFAULT_URL})",
        )
        parser.add_argument(
            "--output",
            type=str,
            default="neet_syllabus.json",
            help="Path to the output JSON file (default: neet_syllabus.json)",
        )
        parser.add_argument(
            "--pretty",
            action="store_true",
            help="Pretty-print the JSON output (indent=2). On by default; "
            "kept as a flag for explicitness.",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=20,
            help="HTTP request timeout in seconds (default: 20)",
        )

    def handle(self, *args, **options):
        url = options["url"]
        output_path = Path(options["output"])
        timeout = options["timeout"]

        self.stdout.write(f"Fetching {url} ...")
        html = self.fetch_html(url, timeout)

        self.stdout.write("Parsing syllabus tables ...")
        data = self.parse_syllabus(html, source_url=url)

        total_chapters = sum(len(v) for v in data["subjects"].values())
        if total_chapters == 0:
            raise CommandError(
                "No syllabus chapters were found. The page structure may have "
                "changed — inspect the HTML and update SUBJECT_HEADING_MAP / "
                "parse_syllabus() accordingly."
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f"Saved JSON to {output_path.resolve()}"))
        for subject, chapters in data["subjects"].items():
            self.stdout.write(f"  {subject}: {len(chapters)} chapters")

    # ------------------------------------------------------------------ #
    # Fetching
    # ------------------------------------------------------------------ #
    def fetch_html(self, url: str, timeout: int) -> str:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise CommandError(f"Failed to fetch {url}: {exc}") from exc
        return resp.text

    # ------------------------------------------------------------------ #
    # Parsing
    # ------------------------------------------------------------------ #
    def parse_syllabus(self, html: str, source_url: str) -> dict:
        soup = BeautifulSoup(html, "lxml")

        result = {
            "source_url": source_url,
            "subjects": {
                "Physics": [],
                "Biology": [],
                "Chemistry": [],
            },
        }

        # Every heading tag on the page (h2-h5), in document order, paired
        # with the tables that follow it. We map heading text -> subject via
        # SUBJECT_HEADING_MAP, then take the first <table> that appears after
        # that heading (before the next heading).
        headings = soup.find_all(re.compile(r"^h[2-5]$"))

        for heading in headings:
            heading_text = clean_text(heading.get_text()).lower()
            subject = None
            for key, subj_name in SUBJECT_HEADING_MAP.items():
                if key in heading_text:
                    subject = subj_name
                    break
            if not subject:
                continue

            table = self._find_next_table(heading)
            if table is None:
                continue

            chapters = self._parse_table(table)
            result["subjects"][subject] = chapters

        return result

    @staticmethod
    def _find_next_table(heading_tag):
        """Return the first <table> found after `heading_tag` in the DOM,
        stopping if another heading (h2-h5) is encountered first."""
        for sibling in heading_tag.find_all_next():
            if sibling.name and re.match(r"^h[2-5]$", sibling.name):
                # Reached the next heading section without finding a table.
                return None
            if sibling.name == "table":
                return sibling
        return None

    @staticmethod
    def _parse_table(table) -> list:
        """
        Parse a 2-column syllabus table into a list of:
            {"chapter": "...", "topics": "...", "topics_list": [...]}

        Handles both:
          - tables with a <thead>/<tbody>
          - tables using bold first-<td> markup without explicit <thead>
        Skips the header row automatically (detected by matching against
        known header labels or by row position).
        """
        rows = table.find_all("tr")
        chapters = []

        HEADER_LABELS = {
            "chapter",
            "topics",
            "topics covered",
            "important topics for neet",
        }

        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue

            col1 = clean_text(cells[0].get_text())
            col2 = clean_text(cells[1].get_text())

            if not col1 or not col2:
                continue

            # Skip header row(s)
            if col1.lower() in HEADER_LABELS and col2.lower() in HEADER_LABELS:
                continue
            if row.find("th") is not None and not row.find("td"):
                continue

            # Split topics into a list on commas / " and " for convenience
            topics_list = Command._split_topics(col2)

            chapters.append(
                {
                    "chapter": col1,
                    "topics": col2,
                    "topics_list": topics_list,
                }
            )

        return chapters

    @staticmethod
    def _split_topics(topics_str: str) -> list:
        """
        Split a comma/'and'-separated topics string into individual items,
        while keeping parenthetical content (e.g. "Alkenes (addition
        reactions)") intact rather than splitting inside the parentheses.
        """
        # Temporarily protect commas inside parentheses
        protected = []

        def _protect(match):
            protected.append(match.group(0))
            return f"__PROTECTED_{len(protected) - 1}__"

        temp = re.sub(r"\([^)]*\)", _protect, topics_str)

        # Replace " and " (as a separator, not inside a word) with a comma
        temp = re.sub(r"\s+and\s+", ", ", temp)

        parts = [p.strip() for p in temp.split(",")]

        restored = []
        for part in parts:
            for i, original in enumerate(protected):
                part = part.replace(f"__PROTECTED_{i}__", original)
            if part:
                restored.append(part)

        return restored


# ---------------------------------------------------------------------- #
# SETUP NOTES
# ---------------------------------------------------------------------- #
# If your app doesn't have the management command folders yet, create them
# (replace `yourapp` with your app's name):
#
#   mkdir -p yourapp/management/commands
#   touch yourapp/management/__init__.py
#   touch yourapp/management/commands/__init__.py
#
# Then place this file at:
#   yourapp/management/commands/scrape_neet_syllabus.py
#
# Run it with:
#   python manage.py scrape_neet_syllabus
# ---------------------------------------------------------------------- #