from django.core.management.base import BaseCommand
from MockAdmin.models import Stream, Field


class Command(BaseCommand):
    help = "Import Fields"

    FIELDS = {
        "General": [
            "Any Discipline",
            "Any Graduation",
            "Any Post Graduation",
        ],

        "Science": [
            "Physics",
            "Chemistry",
            "Biology",
            "Mathematics",
            "Biotechnology",
        ],

        "Commerce": [
            "Accountancy",
            "Business Studies",
            "Economics",
            "Finance",
            "Taxation",
        ],

        "Arts": [
            "History",
            "Political Science",
            "Geography",
            "Sociology",
            "Philosophy",
        ],

        "Humanities": [
            "Psychology",
            "Public Administration",
            "Anthropology",
            "Linguistics",
        ],

        "Engineering": [
            "Computer Science Engineering",
            "Information Technology",
            "Mechanical Engineering",
            "Civil Engineering",
            "Electrical Engineering",
            "Electronics and Communication Engineering",
            "Electronics Engineering",
            "Chemical Engineering",
            "Automobile Engineering",
            "Aerospace Engineering",
            "Aeronautical Engineering",
            "Mining Engineering",
            "Petroleum Engineering",
            "Metallurgical Engineering",
            "Production Engineering",
            "Industrial Engineering",
            "Textile Engineering",
            "Marine Engineering",
            "Robotics Engineering",
            "Artificial Intelligence",
            "Data Science",
            "Cyber Security",
        ],

        "Medical": [
            "MBBS",
            "BDS",
            "BAMS",
            "BHMS",
            "BUMS",
            "BSMS",
            "BNYS",
        ],

        "Pharmacy": [
            "D.Pharm",
            "B.Pharm",
            "M.Pharm",
            "Pharm.D",
        ],

        "Nursing": [
            "GNM",
            "B.Sc Nursing",
            "M.Sc Nursing",
        ],

        "Paramedical": [
            "Medical Laboratory Technology",
            "Radiology",
            "Operation Theatre Technology",
            "Dialysis Technology",
            "Optometry",
        ],

        "Agriculture": [
            "Agriculture",
            "Horticulture",
            "Agricultural Engineering",
            "Agricultural Science",
        ],

        "Veterinary Science": [
            "Veterinary Science",
            "Animal Husbandry",
        ],

        "Law": [
            "LLB",
            "BA LLB",
            "BBA LLB",
            "LLM",
        ],

        "Management": [
            "MBA",
            "BBA",
            "Finance",
            "Marketing",
            "Human Resource",
            "Operations",
            "Business Analytics",
        ],

        "Computer Science": [
            "Computer Science",
            "Software Engineering",
            "Artificial Intelligence",
            "Machine Learning",
            "Cloud Computing",
        ],

        "Information Technology": [
            "Information Technology",
            "Network Administration",
            "Information Systems",
        ],

        "Architecture": [
            "Architecture",
            "Interior Design",
        ],

        "Design": [
            "Fashion Design",
            "Graphic Design",
            "Product Design",
            "UI/UX Design",
        ],

        "Education": [
            "B.Ed",
            "M.Ed",
            "Special Education",
        ],

        "Mass Communication": [
            "Journalism",
            "Digital Media",
            "Advertising",
            "Public Relations",
        ],

        "Hotel Management": [
            "Hospitality Management",
            "Catering Technology",
        ],

        "Fine Arts": [
            "Painting",
            "Sculpture",
            "Applied Arts",
        ],

        "Performing Arts": [
            "Music",
            "Dance",
            "Drama",
        ],

        "Dentistry": [
            "Dental Surgery",
        ],

        "AYUSH": [
            "Ayurveda",
            "Homeopathy",
            "Unani",
            "Siddha",
            "Yoga & Naturopathy",
        ],

        "Biotechnology": [
            "Biotechnology",
            "Genetics",
            "Microbiology",
        ],

        "Environmental Science": [
            "Environmental Engineering",
            "Environmental Studies",
        ],

        "Food Technology": [
            "Food Science",
            "Food Engineering",
        ],

        "Forestry": [
            "Forestry",
        ],

        "Fisheries Science": [
            "Aquaculture",
            "Fisheries",
        ],

        "Library Science": [
            "Library and Information Science",
        ],

        "Physical Education": [
            "Physical Education",
            "Sports Science",
        ],

        "Social Work": [
            "Social Work",
        ],

        "Statistics": [
            "Statistics",
            "Applied Statistics",
        ],

        "Mathematics": [
            "Pure Mathematics",
            "Applied Mathematics",
        ],

        "Economics": [
            "Economics",
            "Applied Economics",
        ],

        "Psychology": [
            "Clinical Psychology",
            "Counselling Psychology",
        ],

        "Open Schooling": [
            "Secondary",
            "Senior Secondary",
        ],

        "Vocational": [
            "ITI",
            "Polytechnic",
            "Skill Development",
        ],

        "Any Stream": [
            "Open to All Streams",
        ],
    }

    def handle(self, *args, **kwargs):
        created = 0
        updated = 0

        for stream_name, fields in self.FIELDS.items():
            stream = Stream.objects.get(stream_name=stream_name)

            for field_name in fields:
                _, is_created = Field.objects.update_or_create(
                    stream=stream,
                    field_name=field_name
                )

                if is_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Fields imported successfully.\n"
                f"Created: {created}\n"
                f"Updated: {updated}"
            )
        )