from django.core.management.base import BaseCommand
from MockAdmin.models import ExamType


class Command(BaseCommand):
    help = "Import Exam Types"

    EXAM_TYPES = [
        {
            "type_name": "School",
            "description": "School board examinations, school admissions, scholarship examinations, and Olympiads."
        },
        {
            "type_name": "Entrance",
            "description": "Entrance examinations for diploma, undergraduate, postgraduate, professional, and research programmes."
        },
        {
            "type_name": "Job",
            "description": "Government, PSU, Banking, Railway, Defence, Teaching, Judiciary, Police, and Private sector recruitment examinations."
        },
    ]

    def handle(self, *args, **kwargs):
        created = 0
        updated = 0

        for exam_type in self.EXAM_TYPES:
            _, is_created = ExamType.objects.update_or_create(
                type_name=exam_type["type_name"],
                defaults={
                    "description": exam_type["description"]
                }
            )

            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"""
Exam Types imported successfully!

Created : {created}
Updated : {updated}
Total   : {len(self.EXAM_TYPES)}
"""
            )
        )