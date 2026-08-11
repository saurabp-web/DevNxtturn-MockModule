from django.core.management.base import BaseCommand
from MockAdmin.models import (
    ExamType,
    EducationLevel,
    EntranceExamCategory,
)


class Command(BaseCommand):
    help = "Import Entrance Exam Categories"

    ENTRANCE_CATEGORIES = [
        {
            "education_level": "Class 10",
            "category_name": "Polytechnic Entrance",
            "description": "Entrance examinations for Polytechnic Diploma programmes."
        },
        {
            "education_level": "Class 10",
            "category_name": "ITI Entrance",
            "description": "Entrance examinations for ITI courses."
        },
        {
            "education_level": "Class 10",
            "category_name": "Diploma Entrance",
            "description": "Diploma admission entrance examinations."
        },
        {
            "education_level": "Class 12",
            "category_name": "Engineering Entrance",
            "description": "Engineering entrance examinations for B.Tech, B.E. and related programmes."
        },
        {
            "education_level": "Class 12",
            "category_name": "Medical Entrance",
            "description": "Medical entrance examinations for MBBS, BDS, AYUSH and allied courses."
        },
        {
            "education_level": "Class 12",
            "category_name": "Nursing Entrance",
            "description": "Nursing entrance examinations."
        },
        {
            "education_level": "Class 12",
            "category_name": "Pharmacy Entrance",
            "description": "Pharmacy entrance examinations."
        },
        {
            "education_level": "Class 12",
            "category_name": "Agriculture Entrance",
            "description": "Agriculture and allied sciences entrance examinations."
        },
        {
            "education_level": "Class 12",
            "category_name": "Veterinary Entrance",
            "description": "Veterinary science entrance examinations."
        },
        {
            "education_level": "Class 12",
            "category_name": "Law Entrance",
            "description": "Law entrance examinations."
        },
        {
            "education_level": "Class 12",
            "category_name": "Management Entrance",
            "description": "Management entrance examinations."
        },
        {
            "education_level": "Class 12",
            "category_name": "Design Entrance",
            "description": "Design and Fine Arts entrance examinations."
        },
        {
            "education_level": "Class 12",
            "category_name": "Architecture Entrance",
            "description": "Architecture entrance examinations."
        },
        {
            "education_level": "Class 12",
            "category_name": "Hotel Management Entrance",
            "description": "Hotel Management and Hospitality entrance examinations."
        },
        {
            "education_level": "Class 12",
            "category_name": "Fashion Technology Entrance",
            "description": "Fashion Technology entrance examinations."
        },
        {
            "education_level": "Class 12",
            "category_name": "Aviation Entrance",
            "description": "Aviation and Aeronautical entrance examinations."
        },
        {
            "education_level": "Class 12",
            "category_name": "Maritime Entrance",
            "description": "Merchant Navy and Maritime entrance examinations."
        },
        {
            "education_level": "Class 12",
            "category_name": "Paramedical Entrance",
            "description": "Paramedical entrance examinations."
        },
        {
            "education_level": "Graduate",
            "category_name": "Postgraduate Engineering Entrance",
            "description": "M.Tech, ME and postgraduate engineering entrance examinations."
        },
        {
            "education_level": "Graduate",
            "category_name": "MBA Entrance",
            "description": "MBA and Management postgraduate entrance examinations."
        },
        {
            "education_level": "Graduate",
            "category_name": "MCA Entrance",
            "description": "Master of Computer Applications entrance examinations."
        },
        {
            "education_level": "Graduate",
            "category_name": "LLM Entrance",
            "description": "Master of Laws entrance examinations."
        },
        {
            "education_level": "Graduate",
            "category_name": "Postgraduate Medical Entrance",
            "description": "MD, MS, MDS and allied postgraduate medical entrance examinations."
        },
        {
            "education_level": "Graduate",
            "category_name": "Pharmacy PG Entrance",
            "description": "Postgraduate Pharmacy entrance examinations."
        },
        {
            "education_level": "Graduate",
            "category_name": "Education Entrance",
            "description": "B.Ed., M.Ed. and teacher education entrance examinations."
        },
        {
            "education_level": "Postgraduate",
            "category_name": "Doctoral Entrance",
            "description": "PhD admission entrance examinations."
        },
        {
            "education_level": "Postgraduate",
            "category_name": "Research Fellowship Entrance",
            "description": "Research fellowship and research programme entrance examinations."
        },
    ]

    def handle(self, *args, **kwargs):
        exam_type = ExamType.objects.get(type_name="Entrance")

        created = 0
        updated = 0

        for item in self.ENTRANCE_CATEGORIES:
            education_level = EducationLevel.objects.get(
                education_level=item["education_level"]
            )

            _, is_created = EntranceExamCategory.objects.update_or_create(
                exam_type=exam_type,
                education_level=education_level,
                category_name=item["category_name"],
                defaults={
                    "description": item["description"]
                },
            )

            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"""
Entrance Exam Categories imported successfully!

Created : {created}
Updated : {updated}
Total   : {len(self.ENTRANCE_CATEGORIES)}
"""
            )
        )