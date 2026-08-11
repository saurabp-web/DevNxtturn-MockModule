import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from MockAdmin.models import (
    Exam,
    Subject,
    Chapter,
    Question,
    QuestionOption,
    CorrectAnswer,
    Solution,
)

class Command(BaseCommand):
    help = "Import Physics Questions from JSON"

    @transaction.atomic
    def handle(self, *args, **options):

        # ----------------------------
        # Load JSON File
        # ----------------------------
        json_path = Path(settings.BASE_DIR) / "src" / "data" / "neet_physics_questions.json"

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # ----------------------------
        # Create Exam
        # ----------------------------
        exam, _ = Exam.objects.get_or_create(
            exam_name="NEET UG",
            defaults={
                "exam_code": "NEET_UG",
                "exam_category": "Medical Entrance Exam",
                "exam_year": 2026,
                "conducting_body": "NTA",
                "estimated_time_hours": 3,
            },
        )

        # ----------------------------
        # Create Subject
        # ----------------------------
        subject, _ = Subject.objects.get_or_create(
            exam=exam,
            subject_name=data["subject"],      # Physics
            defaults={
                "teacher": None
            }
        )

        total_created = 0

        # ----------------------------
        # Loop through Chapters
        # ----------------------------
        for chapter_data in data["chapters"]:

            chapter, _ = Chapter.objects.get_or_create(
                subject=subject,
                chapter_name=chapter_data["chapter"]
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Processing Chapter : {chapter.chapter_name}"
                )
            )

            # ----------------------------
            # Loop through Questions
            # ----------------------------
            for q in chapter_data["questions"]:

                question, created = Question.objects.get_or_create(
                    exam=exam,
                    subject=subject,
                    chapter=chapter,
                    question_text=q["question_text"],
                    defaults={
                        "question_type": "MCQ",
                        "difficulty_level": q["difficulty_level"],
                        "language": "English",
                        "status": "active",
                    }
                )

                if created:

                    QuestionOption.objects.create(
                        question=question,
                        option_A=q["option_A"],
                        option_B=q["option_B"],
                        option_C=q["option_C"],
                        option_D=q["option_D"],
                    )

                    CorrectAnswer.objects.create(
                        question=question,
                        answer_value=q["correct_answer"],
                        answer_type="MCQ",
                    )

                    Solution.objects.create(
                        question=question,
                        explaination_text=q["explanation"],
                        hints=q["hints"],
                        user=None,
                    )

                    total_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully imported {total_created} questions."
            )
        )