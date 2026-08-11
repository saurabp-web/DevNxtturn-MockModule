from django.core.management.base import BaseCommand
from MockAdmin.models import State


class Command(BaseCommand):
    help = "Import Indian States and Union Territories"

    INDIAN_STATES = [
        {"state_name": "Andhra Pradesh", "state_code": "AP"},
        {"state_name": "Arunachal Pradesh", "state_code": "AR"},
        {"state_name": "Assam", "state_code": "AS"},
        {"state_name": "Bihar", "state_code": "BR"},
        {"state_name": "Chhattisgarh", "state_code": "CG"},
        {"state_name": "Goa", "state_code": "GA"},
        {"state_name": "Gujarat", "state_code": "GJ"},
        {"state_name": "Haryana", "state_code": "HR"},
        {"state_name": "Himachal Pradesh", "state_code": "HP"},
        {"state_name": "Jharkhand", "state_code": "JH"},
        {"state_name": "Karnataka", "state_code": "KA"},
        {"state_name": "Kerala", "state_code": "KL"},
        {"state_name": "Madhya Pradesh", "state_code": "MP"},
        {"state_name": "Maharashtra", "state_code": "MH"},
        {"state_name": "Manipur", "state_code": "MN"},
        {"state_name": "Meghalaya", "state_code": "ML"},
        {"state_name": "Mizoram", "state_code": "MZ"},
        {"state_name": "Nagaland", "state_code": "NL"},
        {"state_name": "Odisha", "state_code": "OD"},
        {"state_name": "Punjab", "state_code": "PB"},
        {"state_name": "Rajasthan", "state_code": "RJ"},
        {"state_name": "Sikkim", "state_code": "SK"},
        {"state_name": "Tamil Nadu", "state_code": "TN"},
        {"state_name": "Telangana", "state_code": "TS"},
        {"state_name": "Tripura", "state_code": "TR"},
        {"state_name": "Uttar Pradesh", "state_code": "UP"},
        {"state_name": "Uttarakhand", "state_code": "UK"},
        {"state_name": "West Bengal", "state_code": "WB"},
        {"state_name": "Andaman and Nicobar Islands", "state_code": "AN"},
        {"state_name": "Chandigarh", "state_code": "CH"},
        {"state_name": "Dadra and Nagar Haveli and Daman and Diu", "state_code": "DH"},
        {"state_name": "Delhi", "state_code": "DL"},
        {"state_name": "Jammu and Kashmir", "state_code": "JK"},
        {"state_name": "Ladakh", "state_code": "LA"},
        {"state_name": "Lakshadweep", "state_code": "LD"},
        {"state_name": "Puducherry", "state_code": "PY"},
    ]

    def handle(self, *args, **kwargs):
        created = 0
        updated = 0

        for state in self.INDIAN_STATES:
            _, is_created = State.objects.update_or_create(
                state_name=state["state_name"],
                defaults={
                    "state_code": state["state_code"],
                },
            )

            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed successfully.\n"
                f"Created: {created}\n"
                f"Updated: {updated}"
            )
        )