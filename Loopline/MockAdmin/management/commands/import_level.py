from django.core.management.base import BaseCommand
from MockAdmin.models import ExamLevel


class Command(BaseCommand):
    help = "Import Exam Levels"

    LEVELS = [
        {
            "level_name": "National",
            "description": "Exams conducted across India by Central Government or National agencies."
        },
        {
            "level_name": "State",
            "description": "Exams conducted by State Governments or State-level authorities."
        },
        {
            "level_name": "University",
            "description": "Exams conducted by universities for admission or recruitment."
        },
        {
            "level_name": "Institute",
            "description": "Exams conducted by autonomous institutes or educational institutions."
        },
        {
            "level_name": "District",
            "description": "Exams conducted by district-level authorities."
        },
        {
            "level_name": "Regional",
            "description": "Exams conducted within a specific region or zone."
        },
    ]

    def handle(self, *args, **kwargs):
        for level in self.LEVELS:
            ExamLevel.objects.update_or_create(
                level_name=level["level_name"],
                defaults={
                    "description": level["description"]
                }
            )

        self.stdout.write(self.style.SUCCESS("Exam levels imported successfully."))