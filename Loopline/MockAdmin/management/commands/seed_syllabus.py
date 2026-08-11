from django.core.management.base import BaseCommand
from MockAdmin.models import Exam, Subject, Chapter
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Seed JEE Syllabus structure into the database'

    def handle(self, *args, **options):
        # 1. Define the data structure based on the PDF syllabus
        syllabus_data = {
            'JEE Mains': {
                'Mathematics': [
                    'SETS, RELATIONS AND FUNCTIONS', 'COMPLEX NUMBERS AND QUADRATIC EQUATIONS',
                    'MATRICES AND DETERMINANTS', 'PERMUTATIONS AND COMBINATIONS',
                    'BINOMIAL THEOREM AND ITS SIMPLE APPLICATIONS', 'SEQUENCE AND SERIES',
                    'LIMIT, CONTINUITY AND DIFFERENTIABILITY', 'INTEGRAL CALCULAS',
                    'DIFFRENTIAL EQUATIONS', 'CO-ORDINATE GEOMETRY', 'THREE DIMENSIONAL GEOMETRY',
                    'VECTOR ALGEBRA', 'STATISTICS AND PROBABILITY', 'TRIGONOMETRY'
                ],
                'Physics': [
                    'Units and Measurements', 'Kinematics', 'Laws of Motion',
                    'Work, Energy and Power', 'Rotational Motion', 'Gravitation',
                    'Properties of Solids and Liquids', 'Thermodynamics', 'Kinetic Theory of Gases',
                    'Oscillations and Waves', 'Electrostatics', 'Current Electricity',
                    'Magnetic Effects of Current and Magnetism', 'Electromagnetic Induction and Alternating Currents',
                    'Electromagnetic Waves', 'Optics', 'Dual Nature of Matter and Radiation',
                    'Atoms and Nuclei', 'Electronic Devices', 'Experimental Skills'
                ],
                'Chemistry': [
                    'SOME BASIC CONCEPTS IN CHEMISTRY', 'ATOMIC STRUCTURE',
                    'CHEMICAL BONDING AND MOLECULAR STRUCTURE', 'CHEMICAL THERMODYNAMICS',
                    'SOLUTIONS', 'EQUILIBRIUM', 'REDOX REACTIONS AND ELECTROCHEMISTRY',
                    'CHEMICAL KINETICS', 'CLASSIFICATION OF ELEMENTS AND PERIODICITY IN PROPERTIES',
                    'p- BLOCK ELEMENTS', 'd and f- BLOCK ELEMENTS', 'COORDINATION COMPOUNDS',
                    'PURIFICATION AND CHARACTERISATION OF ORGANIC COMPOUNDS',
                    'SOME BASIC PRINCIPLES OF ORGANIC CHEMISTRY', 'HYDROCARBONS',
                    'ORGANIC COMPOUNDS CONTAINING HALOGENS', 'ORGANIC COMPOUNDS CONTAINING OXYGEN',
                    'ORGANIC COMPOUNDS CONTAINING NITROGEN', 'BIOMOLECULES',
                    'PRINCIPLES RELATED TO PRACTICAL CHEMISTRY'
                ]
            }
        }

        # 2. Iterate and Save
        for exam_name, subjects in syllabus_data.items():
            exam, _ = Exam.objects.get_or_create(
                exam_name=exam_name,
                defaults={
                    'exam_code': 'JEE2025',
                    'exam_year': 2025,
                    'conducting_body': 'NTA',
                    'exam_category': 'JEE',
                    'estimated_time_hours': 3
                }
            )

            for subject_name, chapters in subjects.items():
                subject, _ = Subject.objects.get_or_create(
                    subject_name=subject_name,
                    exam=exam
                )

                for ch_name in chapters:
                    # get_or_create prevents duplicates automatically
                    chapter, created = Chapter.objects.get_or_create(
                        subject=subject,
                        chapter_name=ch_name
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created Chapter: {ch_name}'))
                    else:
                        self.stdout.write(f'Chapter already exists: {ch_name}')

        self.stdout.write(self.style.SUCCESS('Successfully seeded syllabus!'))