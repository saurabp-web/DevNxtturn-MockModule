from django.core.management.base import BaseCommand
from MockAdmin.models import EducationLevel


class Command(BaseCommand):
    help = "Import Education Levels"

    EDUCATION_LEVELS = [
        {
            "education_level": "Class 1",
            "description": "Completed Class 1"
        },
        {
            "education_level": "Class 2",
            "description": "Completed Class 2"
        },
        {
            "education_level": "Class 3",
            "description": "Completed Class 3"
        },
        {
            "education_level": "Class 4",
            "description": "Completed Class 4"
        },
        {
            "education_level": "Class 5",
            "description": "Completed Class 5"
        },
        {
            "education_level": "Class 6",
            "description": "Completed Class 6"
        },
        {
            "education_level": "Class 7",
            "description": "Completed Class 7"
        },
        {
            "education_level": "Class 8",
            "description": "Completed Class 8"
        },
        {
            "education_level": "Class 9",
            "description": "Completed Class 9"
        },
        {
            "education_level": "Class 10",
            "description": "Completed Secondary School (SSC/Matric)"
        },
        {
            "education_level": "Class 11",
            "description": "Completed Class 11"
        },
        {
            "education_level": "Class 12",
            "description": "Completed Higher Secondary (HSC/Intermediate)"
        },
        {
            "education_level": "ITI",
            "description": "Industrial Training Institute qualification"
        },
        {
            "education_level": "Certificate",
            "description": "Certificate course qualification"
        },
        {
            "education_level": "Diploma",
            "description": "Diploma in any discipline"
        },
        {
            "education_level": "Polytechnic Diploma",
            "description": "Polytechnic diploma qualification"
        },
        {
            "education_level": "Undergraduate (Pursuing)",
            "description": "Currently pursuing a Bachelor's degree"
        },
        {
            "education_level": "Graduate",
            "description": "Completed Bachelor's degree"
        },
        {
            "education_level": "Postgraduate (Pursuing)",
            "description": "Currently pursuing a Master's degree"
        },
        {
            "education_level": "Postgraduate",
            "description": "Completed Master's degree"
        },
        {
            "education_level": "Integrated Degree",
            "description": "Integrated Bachelor's and Master's degree"
        },
        {
            "education_level": "Professional Degree",
            "description": "Professional degree such as MBBS, BDS, BAMS, BHMS, BUMS, BSMS, BNYS, LLB, B.Pharm, CA, CS, CMA, etc."
        },
        {
            "education_level": "Doctorate (PhD)",
            "description": "Doctoral degree"
        },
        {
            "education_level": "Post Doctorate",
            "description": "Postdoctoral qualification"
        },
        {
            "education_level": "Any Graduation",
            "description": "Any recognized Bachelor's degree"
        },
        {
            "education_level": "Any Post Graduation",
            "description": "Any recognized Master's degree"
        },
        {
            "education_level": "Any Qualification",
            "description": "No specific educational qualification required"
        },
    ]

    def handle(self, *args, **kwargs):
        created = 0
        updated = 0

        for level in self.EDUCATION_LEVELS:
            _, is_created = EducationLevel.objects.update_or_create(
                education_level=level["education_level"],
                defaults={
                    "description": level["description"]
                }
            )

            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"""
Education Levels imported successfully!

Created : {created}
Updated : {updated}
Total   : {len(self.EDUCATION_LEVELS)}
"""
            )
        )