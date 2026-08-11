import os
import sys
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Scrape MCQ questions from Testbook"

    def add_arguments(self, parser):
        parser.add_argument("--url", type=str, default=None)
        parser.add_argument("--exam", type=str, default="JEE")
        parser.add_argument("--subject", type=str, default="Mathematics")
        parser.add_argument("--chapter", type=str, default="Co-ordinate Geometry")
        parser.add_argument("--topic", type=str, default="General")
        parser.add_argument("--max", type=int, default=None)
        parser.add_argument("--difficulty", choices=["ai","rules","disabled"], default="rules")
        parser.add_argument("--batch-size", type=int, default=5)

    def handle(self, *args, **options):
        try:
            from testbook_scraper import run_scraper, SCRAPE_CONFIG
        except ImportError as e:
            self.stderr.write(self.style.ERROR(f"Import error: {e}"))
            sys.exit(1)
        config = {**SCRAPE_CONFIG}
        if options["url"]: config["urls"] = [options["url"]]
        config["exam_name"] = options["exam"]
        config["subject_name"] = options["subject"]
        config["chapter_name"] = options["chapter"]
        config["topic_name"] = options["topic"]
        config["max_questions"] = options["max"]
        config["difficulty_mode"] = options["difficulty"]
        config["ai_batch_size"] = options["batch_size"]
        config["anthropic_api_key"] = os.environ.get("ANTHROPIC_API_KEY","")
        self.stdout.write("Starting scraper...")
        try:
            run_scraper(config)
            self.stdout.write(self.style.SUCCESS("Done!"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {e}"))
            raise
