from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

# Import your existing models - adjust the app name if needed
from MockAdmin.models import Question, QuestionOption, Solution, CorrectAnswer

# Adjust these imports to match your actual app name for Exam/Subject/Chapter
try:
    from MockAdmin.models import Exam, Subject, Chapter
except ImportError:
    # Try other common app names
    try:
        from MockAdmin.models import Exam, Subject, Chapter
    except ImportError:
        from MockAdmin.models import Exam, Subject, Chapter

User = get_user_model()


# QUESTIONS_DATA = [
#     {
#         "question_text": "The SI unit of electric current is:",
#         "option_A": "Volt", "option_B": "Ampere",
#         "option_C": "Ohm",  "option_D": "Watt",
#         "correct_answer": "B",
#         "explanation": "Ampere (A) is the SI base unit of electric current, defined as the flow of one coulomb per second.",
#         "hints": "Think about the base SI units defined by the International System.",
#         "difficulty_level": "easy",
#     },
#     {
#         "question_text": "Which of the following is a derived unit?",
#         "option_A": "Kilogram", "option_B": "Metre",
#         "option_C": "Newton",   "option_D": "Second",
#         "correct_answer": "C",
#         "explanation": "Newton (N) is a derived unit: 1 N = 1 kg·m/s². Kilogram, Metre and Second are SI base units.",
#         "hints": "Derived units are combinations of base units.",
#         "difficulty_level": "easy",
#     },
#     {
#         "question_text": "The dimensional formula for pressure is:",
#         "option_A": "MLT⁻²",  "option_B": "ML⁻¹T⁻²",
#         "option_C": "ML²T⁻²", "option_D": "M⁰L⁰T⁰",
#         "correct_answer": "B",
#         "explanation": "Pressure = Force/Area = [MLT⁻²]/[L²] = [ML⁻¹T⁻²].",
#         "hints": "Pressure = Force ÷ Area. Find dimensions of both.",
#         "difficulty_level": "medium",
#     },
#     {
#         "question_text": "1 light year is equal to approximately:",
#         "option_A": "9.46 × 10¹² km", "option_B": "9.46 × 10¹⁵ km",
#         "option_C": "9.46 × 10⁹ km",  "option_D": "9.46 × 10¹⁸ km",
#         "correct_answer": "A",
#         "explanation": "1 light year ≈ 9.46 × 10¹² km — the distance light travels in one year.",
#         "hints": "Speed of light × seconds in a year.",
#         "difficulty_level": "medium",
#     },
#     {
#         "question_text": "The number of significant figures in 0.006700 is:",
#         "option_A": "2", "option_B": "4",
#         "option_C": "6", "option_D": "7",
#         "correct_answer": "B",
#         "explanation": "Leading zeros are not significant; trailing zeros after decimal are. 6, 7, 0, 0 → 4 significant figures.",
#         "hints": "Leading zeros before the first non-zero digit are never significant.",
#         "difficulty_level": "medium",
#     },
#     {
#         "question_text": "Which method is used to measure very large distances like the distance to stars?",
#         "option_A": "Parallax method",    "option_B": "Vernier caliper",
#         "option_C": "Screw gauge method", "option_D": "Laser rangefinder",
#         "correct_answer": "A",
#         "explanation": "The parallax method uses the apparent shift in position of a nearby star to calculate its distance.",
#         "hints": "This method uses two observation points and trigonometry.",
#         "difficulty_level": "easy",
#     },
#     {
#         "question_text": "Dimensions of Planck's constant (h) are:",
#         "option_A": "ML²T⁻¹", "option_B": "MLT⁻¹",
#         "option_C": "ML²T⁻²", "option_D": "M⁰LT⁻¹",
#         "correct_answer": "A",
#         "explanation": "E = hν → h = E/ν = [ML²T⁻²]/[T⁻¹] = [ML²T⁻¹].",
#         "hints": "Use E = hν and find dimensions of frequency.",
#         "difficulty_level": "hard",
#     },
#     {
#         "question_text": "The least count of a Vernier caliper with 50 Vernier divisions equal to 49 main scale divisions (1 MSD = 1 mm) is:",
#         "option_A": "0.01 mm", "option_B": "0.02 mm",
#         "option_C": "0.05 mm", "option_D": "0.1 mm",
#         "correct_answer": "B",
#         "explanation": "Least count = 1 MSD – 1 VSD = 1 – (49/50) = 1/50 mm = 0.02 mm.",
#         "hints": "Least count = 1 MSD – 1 VSD.",
#         "difficulty_level": "hard",
#     },
#     {
#         "question_text": "If velocity v = at + bt², the dimensions of 'a' are:",
#         "option_A": "LT⁻¹",  "option_B": "LT⁻²",
#         "option_C": "L²T⁻¹", "option_D": "LT⁻³",
#         "correct_answer": "B",
#         "explanation": "v = at → [LT⁻¹] = [a][T] → [a] = [LT⁻²], same as acceleration.",
#         "hints": "Both sides of the equation must have the same dimensions.",
#         "difficulty_level": "medium",
#     },
#     {
#         "question_text": "The percentage error in mass and speed are 2% and 3%. The maximum percentage error in KE (½mv²) is:",
#         "option_A": "5%", "option_B": "7%",
#         "option_C": "8%", "option_D": "11%",
#         "correct_answer": "C",
#         "explanation": "ΔKE/KE = Δm/m + 2·Δv/v = 2% + 2×3% = 8%.",
#         "hints": "For powers, multiply the percentage error by the exponent.",
#         "difficulty_level": "hard",
#     },
# ]


# class Command(BaseCommand):
#     help = 'Seed 10 Physics > Units & Measurements questions using existing models'

#     def handle(self, *args, **options):

#         exam, _ = Exam.objects.get_or_create(
#             exam_name='JEE Mains',
#             defaults={
#                 'exam_code': 'JEE2024',
#                 'exam_category': 'JEE',
#                 'exam_year': 2024,
#                 'conducting_body': 'NTA',
#                 'estimated_time_hours': 3,
#             }
#         )
#         self.stdout.write(f'Exam: {exam}  (id={exam.exam_id})')

#         # ── Step 2: Get or create Subject ─────────────────────────
#         subject, _ = Subject.objects.get_or_create(
#             subject_name='Physics',
#             exam=exam,
#             defaults={'teacher': None}
#         )
#         self.stdout.write(f'Subject: {subject}  (id={subject.subject_id})')

#         # ── Step 3: Get or create Chapter ─────────────────────────
#         chapter, _ = Chapter.objects.get_or_create(
#             chapter_name='Units & Measurements',
#             subject=subject,
#         )
#         self.stdout.write(f'Chapter: {chapter}  (id={chapter.chapter_id})')

#         # ── Step 4: Seed Questions ────────────────────────────────
#         created = 0
#         for q_data in QUESTIONS_DATA:
#             # Create Question (skip if exact text already exists for this subject)
#             question, was_created = Question.objects.get_or_create(
#                 subject=subject,
#                 chapter=chapter,
#                 exam=exam,
#                 question_text=q_data['question_text'],
#                 defaults={
#                     'question_type':   'MCQ',
#                     'difficulty_level': q_data['difficulty_level'],
#                     'language':        'English',
#                     'status':          'active',
#                 }
#             )

#             if was_created:
#                 # Create Options
#                 QuestionOption.objects.create(
#                     question=question,
#                     option_A=q_data['option_A'],
#                     option_B=q_data['option_B'],
#                     option_C=q_data['option_C'],
#                     option_D=q_data['option_D'],
#                 )

#                 # Create Correct Answer
#                 CorrectAnswer.objects.create(
#                     question=question,
#                     answer_value=q_data['correct_answer'],
#                     answer_type='MCQ',
#                 )

#                 # Create Solution
#                 Solution.objects.create(
#                     question=question,
#                     explaination_text=q_data['explanation'],
#                     hints=q_data['hints'],
#                     user=None,
#                 )

#                 created += 1

#         self.stdout.write(
#             self.style.SUCCESS(
#                 f'\n✓ Done! {created} new questions added '
#                 f'({len(QUESTIONS_DATA) - created} already existed).\n'
#                 f'  chapter_id to use in API: {chapter.chapter_id}'
#             )
#         )


# from django.core.management.base import BaseCommand
# # Assuming your models are imported correctly here
# # from your_app.models import Exam, Subject, Chapter, Question, QuestionOption, CorrectAnswer, Solution

# CHEMISTRY_QUESTIONS_DATA = [
#     {
#         "question_text": "Which of the following elements has the highest electronegativity?",
#         "option_A": "Oxygen", "option_B": "Fluorine",
#         "option_C": "Chlorine", "option_D": "Nitrogen",
#         "correct_answer": "B",
#         "explanation": "Fluorine is the most electronegative element in the periodic table due to its small atomic radius and high effective nuclear charge.",
#         "hints": "Look at the top-right corner of the periodic table (excluding noble gases).",
#         "difficulty_level": "easy",
#     },
#     {
#         "question_text": "What is the molarity of a solution containing 0.5 moles of solute in 250 mL of solvent?",
#         "option_A": "0.5 M", "option_B": "1.0 M",
#         "option_C": "2.0 M", "option_D": "4.0 M",
#         "correct_answer": "C",
#         "explanation": "Molarity (M) = moles of solute / volume of solution in liters. M = 0.5 mol / 0.25 L = 2.0 M.",
#         "hints": "Ensure the volume is converted to liters first.",
#         "difficulty_level": "medium",
#     },
#     {
#         "question_text": "According to the Arrhenius theory, an acid is a substance that produces:",
#         "option_A": "H⁺ ions in water", "option_B": "OH⁻ ions in water",
#         "option_C": "Electron pairs", "option_D": "Proton acceptors",
#         "correct_answer": "A",
#         "explanation": "Arrhenius defined acids as substances that dissociate in water to increase the concentration of hydrogen ions (H⁺).",
#         "hints": "Focus on what increases in an acidic aqueous solution.",
#         "difficulty_level": "easy",
#     },
#     {
#         "question_text": "What is the hybridisation of the central carbon atom in CH₄?",
#         "option_A": "sp", "option_B": "sp²",
#         "option_C": "sp³", "option_D": "dsp²",
#         "correct_answer": "C",
#         "explanation": "Carbon in methane has 4 sigma bonds and no lone pairs, leading to a tetrahedral geometry and sp³ hybridisation.",
#         "hints": "Count the number of sigma bonds and lone pairs around the carbon.",
#         "difficulty_level": "medium",
#     },
#     {
#         "question_text": "Which law states that the partial pressure of a gas in a mixture is equal to the mole fraction of the gas times the total pressure?",
#         "option_A": "Boyle's Law", "option_B": "Charles's Law",
#         "option_C": "Dalton's Law of Partial Pressures", "option_D": "Graham's Law",
#         "correct_answer": "C",
#         "explanation": "Dalton's Law states: P_i = x_i * P_total, where x_i is the mole fraction of component i.",
#         "hints": "This relates to gas mixtures, not individual gas properties like temperature or volume.",
#         "difficulty_level": "medium",
#     },
#     {
#         "question_text": "The number of electrons present in one mole of H₂O molecules is:",
#         "option_A": "6.022 × 10²³", "option_B": "1.204 × 10²⁴",
#         "option_C": "6.022 × 10²⁴", "option_D": "None of these",
#         "correct_answer": "C",
#         "explanation": "One H₂O molecule has 10 electrons (1 from each H, 8 from O). One mole contains 10 * N_A electrons = 10 * 6.022 × 10²³ = 6.022 × 10²⁴.",
#         "hints": "Determine the total number of electrons in one molecule first.",
#         "difficulty_level": "hard",
#     },
#     {
#         "question_text": "Which quantum number describes the orientation of an orbital in space?",
#         "option_A": "Principal quantum number (n)", "option_B": "Azimuthal quantum number (l)",
#         "option_C": "Magnetic quantum number (m_l)", "option_D": "Spin quantum number (m_s)",
#         "correct_answer": "C",
#         "explanation": "The magnetic quantum number (m_l) determines the orientation of the orbital in three-dimensional space.",
#         "hints": "It distinguishes the different p-orbitals (px, py, pz).",
#         "difficulty_level": "medium",
#     },
#     {
#         "question_text": "The pH of a 0.001 M HCl solution is:",
#         "option_A": "1", "option_B": "2",
#         "option_C": "3", "option_D": "4",
#         "correct_answer": "C",
#         "explanation": "pH = -log[H⁺]. Since HCl is a strong acid, [H⁺] = 0.001 M = 10⁻³. pH = -log(10⁻³) = 3.",
#         "hints": "pH is the negative log of the hydrogen ion concentration.",
#         "difficulty_level": "medium",
#     },
#     {
#         "question_text": "For a reaction to be spontaneous at all temperatures, the values of ΔH and ΔS must be:",
#         "option_A": "ΔH > 0, ΔS > 0", "option_B": "ΔH < 0, ΔS < 0",
#         "option_C": "ΔH < 0, ΔS > 0", "option_D": "ΔH > 0, ΔS < 0",
#         "correct_answer": "C",
#         "explanation": "Gibbs Free Energy ΔG = ΔH - TΔS. For ΔG < 0 (spontaneous) at all T, ΔH must be negative (exothermic) and ΔS must be positive (increasing entropy).",
#         "hints": "Consider the equation ΔG = ΔH - TΔS.",
#         "difficulty_level": "hard",
#     },
#     {
#         "question_text": "What is the shape of the NH₃ molecule?",
#         "option_A": "Linear", "option_B": "Tetrahedral",
#         "option_C": "Trigonal planar", "option_D": "Trigonal pyramidal",
#         "correct_answer": "D",
#         "explanation": "NH₃ has 3 bonding pairs and 1 lone pair, resulting in a trigonal pyramidal geometry due to VSEPR theory.",
#         "hints": "VSEPR theory: lone pairs occupy more space and push bonds down.",
#         "difficulty_level": "medium",
#     },
# ]

# class Command(BaseCommand):
#     help = 'Seed 10 Chemistry > Basic Concepts questions'

#     def handle(self, *args, **options):
#         exam, _ = Exam.objects.get_or_create(
#             exam_name='JEE Mains',
#             defaults={
#                 'exam_code': 'JEE2024',
#                 'exam_category': 'JEE',
#                 'exam_year': 2024,
#                 'conducting_body': 'NTA',
#                 'estimated_time_hours': 3,
#             }
#         )
        
#         subject, _ = Subject.objects.get_or_create(
#             subject_name='Chemistry',
#             exam=exam,
#             defaults={'teacher': None}
#         )
        
#         chapter, _ = Chapter.objects.get_or_create(
#             chapter_name='Basic Concepts',
#             subject=subject,
#         )

#         created = 0
#         for q_data in CHEMISTRY_QUESTIONS_DATA:
#             question, was_created = Question.objects.get_or_create(
#                 subject=subject,
#                 chapter=chapter,
#                 exam=exam,
#                 question_text=q_data['question_text'],
#                 defaults={
#                     'question_type':   'MCQ',
#                     'difficulty_level': q_data['difficulty_level'],
#                     'language':        'English',
#                     'status':          'active',
#                 }
#             )

#             if was_created:
#                 QuestionOption.objects.create(
#                     question=question,
#                     option_A=q_data['option_A'],
#                     option_B=q_data['option_B'],
#                     option_C=q_data['option_C'],
#                     option_D=q_data['option_D'],
#                 )
#                 CorrectAnswer.objects.create(
#                     question=question,
#                     answer_value=q_data['correct_answer'],
#                     answer_type='MCQ',
#                 )
#                 Solution.objects.create(
#                     question=question,
#                     explaination_text=q_data['explanation'],
#                     hints=q_data['hints'],
#                     user=None,
#                 )
#                 created += 1

#         self.stdout.write(self.style.SUCCESS(f'Successfully added {created} chemistry questions.'))


from django.core.management.base import BaseCommand

CHEMISTRY_QUESTIONS_DATA = [
   {
    "question_text": "What do metal carbonates and hydrogen carbonates produce when reacting with acids, and what happens to the resulting gas in lime water?",
    "option_A": "Carbon dioxide, water, milky",
    "option_B": "Hydrogen, water, blue",
    "option_C": "Carbon dioxide, oxygen, colorless",
    "option_D": "Water, chlorine, yellow",
    "correct_answer": "A",
    "explanation": "Metal carbonates/hydrogen carbonates react with acid to form salt, CO2, and water. CO2 turns lime water milky due to the formation of calcium carbonate (CaCO3).",
    "hints": "Think about the standard reaction of carbonates with acids and the test for carbon dioxide.",
    "difficulty_level": "easy"
  },
  {
    "question_text": "Which category contains the following structural descriptions: 1. A rigid, 3D tetrahedral network; 2. Hexagonal arrays in sliding layers; 3. Geodesic dome-like C60 structure?",
    "option_A": "Isotopes of Carbon",
    "option_B": "Allotropes of Carbon",
    "option_C": "Homologous Series of Carbon",
    "option_D": "Functional Groups of Carbon",
    "correct_answer": "B",
    "explanation": "These are descriptions of Diamond, Graphite, and Fullerenes, which are allotropes of carbon.",
    "hints": "These are different physical forms of the same element.",
    "difficulty_level": "medium"
  },
  {
    "question_text": "In which case is the order of acidic strength incorrect?",
    "option_A": "HI > HBr > HCl",
    "option_B": "HIO4 > HBrO4 > HClO4",
    "option_C": "HClO4 > HClO3 > HClO2",
    "option_D": "More than one of the above",
    "correct_answer": "B",
    "explanation": "For oxyacids with the same number of oxygens, acidity increases with the electronegativity of the central atom. The correct order is HClO4 > HBrO4 > HIO4.",
    "hints": "Acidity of oxyacids increases as the electronegativity of the central atom increases.",
    "difficulty_level": "hard"
  },
  {
    "question_text": "Which factor is most important in making fluorine the strongest oxidizing agent?",
    "option_A": "Electron affinity",
    "option_B": "Ionization enthalpy",
    "option_C": "Bond dissociation energy",
    "option_D": "Hydration enthalpy",
    "correct_answer": "D",
    "explanation": "The extremely high hydration enthalpy of the small fluoride ion compensates for other energy factors, making fluorine the strongest oxidizer.",
    "hints": "Consider the energy released when the small F- ion is surrounded by water molecules.",
    "difficulty_level": "hard"
  },
  {
    "question_text": "Which is the weakest acid among HI, HBr, HF, and HCl?",
    "option_A": "HI",
    "option_B": "HBr",
    "option_C": "HF",
    "option_D": "HCl",
    "correct_answer": "C",
    "explanation": "HF has the highest bond dissociation enthalpy due to the small size of fluorine, making it the least acidic.",
    "hints": "Consider the H-X bond strength across the halogen group.",
    "difficulty_level": "medium"
  },
  {
    "question_text": "Halogens have ______ electrons in their outermost shells.",
    "option_A": "Five",
    "option_B": "Six",
    "option_C": "Eight",
    "option_D": "Seven",
    "correct_answer": "D",
    "explanation": "Halogens belong to Group 17 and have seven valence electrons.",
    "hints": "They need one more electron to achieve a stable octet.",
    "difficulty_level": "easy"
  },
  {
    "question_text": "What is the decreasing order of oxidizing power of halogens?",
    "option_A": "I > Br > Cl > F",
    "option_B": "I > Cl > Br > F",
    "option_C": "Cl > F > Br > I",
    "option_D": "F > Cl > Br > I",
    "correct_answer": "D",
    "explanation": "Oxidizing power correlates with standard electrode potential, which follows the order F2 > Cl2 > Br2 > I2.",
    "hints": "Recall which halogen is the most reactive oxidizing agent.",
    "difficulty_level": "medium"
  },
  {
    "question_text": "What is the shape of a p-orbital?",
    "option_A": "Spherical",
    "option_B": "Linear",
    "option_C": "Planar",
    "option_D": "Dumbbell",
    "correct_answer": "D",
    "explanation": "Atomic orbitals have characteristic shapes: s is spherical, p is dumbbell, d is double-dumbbell.",
    "hints": "Visualize the shape of the p-orbital.",
    "difficulty_level": "easy"
  }
]

class Command(BaseCommand):
    help = 'Seed 10 Chemistry > p- BLOCK ELEMENTS'

    def handle(self, *args, **options):
        exam, _ = Exam.objects.get_or_create(
            exam_name='JEE Mains',
            defaults={
                'exam_code': 'JEE2024',
                'exam_category': 'JEE',
                'exam_year': 2024,
                'conducting_body': 'NTA',
                'estimated_time_hours': 3,
            }
        )
        
        subject, _ = Subject.objects.get_or_create(
            subject_name='Chemistry',
            exam=exam,
            defaults={'teacher': None}
        )
        
        chapter, _ = Chapter.objects.get_or_create(
            chapter_name='p- BLOCK ELEMENTS',
            subject=subject,
        )

        created = 0
        for q_data in CHEMISTRY_QUESTIONS_DATA:
            question, was_created = Question.objects.get_or_create(
                subject=subject,
                chapter=chapter,
                exam=exam,
                question_text=q_data['question_text'],
                defaults={
                    'question_type':   'MCQ',
                    'difficulty_level': q_data['difficulty_level'],
                    'language':        'English',
                    'status':          'active',
                }
            )

            if was_created:
                QuestionOption.objects.create(
                    question=question,
                    option_A=q_data['option_A'],
                    option_B=q_data['option_B'],
                    option_C=q_data['option_C'],
                    option_D=q_data['option_D'],
                )
                CorrectAnswer.objects.create(
                    question=question,
                    answer_value=q_data['correct_answer'],
                    answer_type='MCQ',
                )
                Solution.objects.create(
                    question=question,
                    explaination_text=q_data['explanation'],
                    hints=q_data['hints'],
                    user=None,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully added {created} Chemistry questions.'))