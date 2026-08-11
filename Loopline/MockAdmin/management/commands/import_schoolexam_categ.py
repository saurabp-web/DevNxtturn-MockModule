from django.core.management.base import BaseCommand
from MockAdmin.models import (
    ExamType,
    EducationLevel,
    SchoolExamCategory,
)


class Command(BaseCommand):
    help = "Import School Exam Categories"

    DATA = [
        {
            "education_level": "Class 1",
            "category_name": "School Admission",
            "description": "Admission to Class 1"
        },
        {
            "education_level": "Class 5",
            "category_name": "Scholarship Exam",
            "description": "Scholarship examinations after Class 5"
        },
        {
            "education_level": "Class 6",
            "category_name": "School Entrance Exam",
            "description": "Entrance examinations for Class 6"
        },
        {
            "education_level": "Class 8",
            "category_name": "Scholarship Exam",
            "description": "Scholarship examinations after Class 8"
        },
        {
            "education_level": "Class 9",
            "category_name": "Olympiad",
            "description": "National and International Olympiads"
        },
        {
            "education_level": "Class 10",
            "category_name": "Secondary Board Examination",
            "description": "Class 10 Board Examination"
        },
        {
            "education_level": "Class 10",
            "category_name": "Polytechnic Entrance",
            "description": "Diploma and Polytechnic Entrance"
        },
        {
            "education_level": "Class 10",
            "category_name": "ITI Admission",
            "description": "ITI Admission"
        },
        {
            "education_level": "Class 11",
            "category_name": "School Admission",
            "description": "Admission to Class 11"
        },
        {
            "education_level": "Class 12",
            "category_name": "Senior Secondary Board Examination",
            "description": "Class 12 Board Examination"
        },
        {
            "education_level": "Class 12",
            "category_name": "Scholarship Exam",
            "description": "Scholarship after Class 12"
        },
        {
            "education_level": "Class 12",
            "category_name": "Olympiad",
            "description": "Olympiads for Higher Secondary students"
        },
    ]

    def handle(self, *args, **kwargs):
        exam_type = ExamType.objects.get(type_name="School")

        created = 0
        updated = 0

        for item in self.DATA:
            education_level = EducationLevel.objects.get(
                education_level=item["education_level"]
            )

            _, is_created = SchoolExamCategory.objects.update_or_create(
                exam_type=exam_type,
                education_level=education_level,
                category_name=item["category_name"],
                defaults={
                    "description": item["description"]
                }
            )

            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Created: {created}, Updated: {updated}"
            )
        )