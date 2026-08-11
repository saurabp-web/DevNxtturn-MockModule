from django.core.management.base import BaseCommand
from MockAdmin.models import JobCategory


class Command(BaseCommand):
    help = "Import Job Categories"

    JOB_CATEGORIES = [
        {
            "job_category_name": "UPSC",
            "description": "Union Public Service Commission recruitment examinations."
        },
        {
            "job_category_name": "State PSC",
            "description": "State Public Service Commission recruitment examinations."
        },
        {
            "job_category_name": "SSC",
            "description": "Staff Selection Commission recruitment examinations."
        },
        {
            "job_category_name": "Banking",
            "description": "Public and private banking recruitment examinations."
        },
        {
            "job_category_name": "Insurance",
            "description": "Insurance sector recruitment examinations."
        },
        {
            "job_category_name": "Railway",
            "description": "Indian Railways recruitment examinations."
        },
        {
            "job_category_name": "Defence",
            "description": "Indian Army, Navy, Air Force, Coast Guard and defence recruitment."
        },
        {
            "job_category_name": "Police",
            "description": "Police and law enforcement recruitment."
        },
        {
            "job_category_name": "Paramilitary Forces",
            "description": "BSF, CRPF, CISF, ITBP, SSB, Assam Rifles recruitment."
        },
        {
            "job_category_name": "Teaching",
            "description": "School, college and university teaching recruitment."
        },
        {
            "job_category_name": "Judiciary",
            "description": "Judicial services and court recruitment."
        },
        {
            "job_category_name": "PSU",
            "description": "Public Sector Undertaking recruitment."
        },
        {
            "job_category_name": "Healthcare",
            "description": "Medical, nursing and healthcare recruitment."
        },
        {
            "job_category_name": "Engineering",
            "description": "Engineering and technical recruitment."
        },
        {
            "job_category_name": "Scientific Research",
            "description": "Research organizations such as ISRO, DRDO, CSIR, BARC, ICMR, etc."
        },
        {
            "job_category_name": "Space & Aerospace",
            "description": "Space research and aerospace recruitment."
        },
        {
            "job_category_name": "Agriculture",
            "description": "Agriculture and allied department recruitment."
        },
        {
            "job_category_name": "Forest & Wildlife",
            "description": "Forest, wildlife and environmental recruitment."
        },
        {
            "job_category_name": "Postal Services",
            "description": "India Post recruitment."
        },
        {
            "job_category_name": "Civil Aviation",
            "description": "Airport Authority and aviation recruitment."
        },
        {
            "job_category_name": "Maritime & Shipping",
            "description": "Ports, shipping and merchant navy recruitment."
        },
        {
            "job_category_name": "Power & Energy",
            "description": "Electricity boards and energy sector recruitment."
        },
        {
            "job_category_name": "Telecommunications",
            "description": "Telecommunication sector recruitment."
        },
        {
            "job_category_name": "Food & Supply",
            "description": "Food Corporation, Warehousing and Civil Supplies recruitment."
        },
        {
            "job_category_name": "Public Administration",
            "description": "Municipal corporations, development authorities and administrative recruitment."
        },
        {
            "job_category_name": "Disaster Management",
            "description": "NDRF, SDRF and disaster management recruitment."
        },
        {
            "job_category_name": "Intelligence & Investigation",
            "description": "Intelligence Bureau, NIA and investigative agencies recruitment."
        },
        {
            "job_category_name": "Forensic Science",
            "description": "Forensic laboratories and forensic services recruitment."
        },
        {
            "job_category_name": "Tourism & Hospitality",
            "description": "Tourism and hospitality sector recruitment."
        },
        {
            "job_category_name": "Sports Authority",
            "description": "Sports Authority of India and sports recruitment."
        },
        {
            "job_category_name": "Culture & Archaeology",
            "description": "Museums, archives and archaeology recruitment."
        },
        {
            "job_category_name": "Skill Development",
            "description": "Skill development missions and vocational training recruitment."
        },
        {
            "job_category_name": "Apprenticeship",
            "description": "Government and PSU apprenticeship recruitment."
        },
        {
            "job_category_name": "Private Sector",
            "description": "Private company recruitment across all industries."
        },
        {
            "job_category_name": "Information Technology",
            "description": "Software, cybersecurity, AI, cloud and IT recruitment."
        },
        {
            "job_category_name": "Data Science & Analytics",
            "description": "Data Science, AI, ML and Analytics recruitment."
        },
        {
            "job_category_name": "Finance & Accounting",
            "description": "Finance, accounting, taxation and auditing recruitment."
        },
        {
            "job_category_name": "Legal Services",
            "description": "Legal officers, advocates and corporate legal recruitment."
        },
        {
            "job_category_name": "Media & Communication",
            "description": "Journalism, broadcasting and public relations recruitment."
        },
        {
            "job_category_name": "E-Commerce & Retail",
            "description": "Retail and e-commerce recruitment."
        },
        {
            "job_category_name": "Manufacturing",
            "description": "Manufacturing and industrial recruitment."
        },
        {
            "job_category_name": "Startup & Innovation",
            "description": "Startup ecosystem and innovation recruitment."
        }
    ]

    def handle(self, *args, **kwargs):
        created = 0
        updated = 0

        for item in self.JOB_CATEGORIES:
            _, is_created = JobCategory.objects.update_or_create(
                job_category_name=item["job_category_name"],
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
                f"""
Job Categories imported successfully!

Created : {created}
Updated : {updated}
Total   : {len(self.JOB_CATEGORIES)}
"""
            )
        )