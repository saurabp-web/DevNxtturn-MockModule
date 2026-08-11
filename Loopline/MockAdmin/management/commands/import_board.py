from django.core.management.base import BaseCommand
from MockAdmin.models import State, Board


class Command(BaseCommand):
    help = "Import Boards"

    BOARDS = [
        ("AP", "Board of Secondary Education Andhra Pradesh", "BSEAP"),
        ("AR", "Directorate of School Education Arunachal Pradesh", "DSEAP"),
        ("AS", "Assam State School Education Board", "ASSEB"),
        ("BR", "Bihar School Examination Board", "BSEB"),
        ("CG", "Chhattisgarh Board of Secondary Education", "CGBSE"),
        ("GA", "Goa Board of Secondary and Higher Secondary Education", "GBSHSE"),
        ("GJ", "Gujarat Secondary and Higher Secondary Education Board", "GSEB"),
        ("HR", "Board of School Education Haryana", "BSEH"),
        ("HP", "Himachal Pradesh Board of School Education", "HPBOSE"),
        ("JH", "Jharkhand Academic Council", "JAC"),
        ("KA", "Karnataka School Examination and Assessment Board", "KSEAB"),
        ("KL", "Kerala Board of Public Examinations", "KBPE"),
        ("MP", "Madhya Pradesh Board of Secondary Education", "MPBSE"),
        ("MH", "Maharashtra State Board of Secondary and Higher Secondary Education", "MSBSHSE"),
        ("MN", "Board of Secondary Education Manipur", "BOSEM"),
        ("ML", "Meghalaya Board of School Education", "MBOSE"),
        ("MZ", "Mizoram Board of School Education", "MBSE"),
        ("NL", "Nagaland Board of School Education", "NBSE"),
        ("OD", "Board of Secondary Education Odisha", "BSEOD"),
        ("PB", "Punjab School Education Board", "PSEB"),
        ("RJ", "Board of Secondary Education Rajasthan", "RBSE"),
        ("SK", "State Institute of Education Sikkim", "SIE"),
        ("TN", "Directorate of Government Examinations Tamil Nadu", "DGE"),
        ("TS", "Board of Secondary Education Telangana", "BSET"),
        ("TR", "Tripura Board of Secondary Education", "TBSE"),
        ("UP", "Uttar Pradesh Madhyamik Shiksha Parishad", "UPMSP"),
        ("UK", "Uttarakhand Board of School Education", "UBSE"),
        ("WB", "West Bengal Board of Secondary Education", "WBBSE"),
        ("DL", "Central Board of Secondary Education", "CBSE"),
        ("DL", "Council for the Indian School Certificate Examinations", "CISCE"),
        ("DL", "National Institute of Open Schooling", "NIOS"),
    ]

    def handle(self, *args, **kwargs):
        for state_code, board_name, board_code in self.BOARDS:
            state = State.objects.get(state_code=state_code)

            Board.objects.update_or_create(
                state=state,
                board_code=board_code,
                defaults={
                    "board_name": board_name,
                }
            )

        self.stdout.write(self.style.SUCCESS("Boards imported successfully."))