from django.core.management.base import BaseCommand
from MockAdmin.models import Stream


class Command(BaseCommand):
    help = "Import Streams"

    STREAMS = [
        "General",
        "Science",
        "Commerce",
        "Arts",
        "Humanities",
        "Medical",
        "Non-Medical",
        "Engineering",
        "Agriculture",
        "Biotechnology",
        "Computer Science",
        "Information Technology",
        "Pharmacy",
        "Nursing",
        "Paramedical",
        "Dentistry",
        "Veterinary Science",
        "AYUSH",
        "Law",
        "Management",
        "Education",
        "Architecture",
        "Design",
        "Fine Arts",
        "Performing Arts",
        "Mass Communication",
        "Journalism",
        "Hotel Management",
        "Tourism",
        "Aviation",
        "Maritime Studies",
        "Fashion Technology",
        "Home Science",
        "Environmental Science",
        "Food Technology",
        "Forestry",
        "Fisheries Science",
        "Library Science",
        "Physical Education",
        "Social Work",
        "Statistics",
        "Mathematics",
        "Economics",
        "Psychology",
        "Open Schooling",
        "Vocational",
        "Any Stream",
    ]

    def handle(self, *args, **kwargs):
        created = 0
        updated = 0

        for stream in self.STREAMS:
            _, is_created = Stream.objects.update_or_create(
                stream_name=stream
            )

            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Streams imported successfully.\n"
                f"Created: {created}\n"
                f"Updated: {updated}\n"
                f"Total: {len(self.STREAMS)}"
            )
        )