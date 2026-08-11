from django.core.management.base import BaseCommand
from MockAdmin.models import Stream, Field, SubField


class Command(BaseCommand):
    help = "Import SubFields — run import_streams and import_fields first"

    # Structure: { stream_name: { field_name: [subfield, ...] } }
    SUBFIELDS = {
        "Engineering": {
            "Computer Science Engineering": [
                "Data Structures & Algorithms",
                "Operating Systems",
                "Database Management Systems",
                "Computer Networks",
                "Software Engineering",
                "Compiler Design",
                "Theory of Computation",
                "Object Oriented Programming",
                "Web Technologies",
                "Mobile Application Development",
            ],
            "Information Technology": [
                "Network Security",
                "Cloud Infrastructure",
                "IT Project Management",
                "Enterprise Resource Planning",
                "Web Development",
            ],
            "Mechanical Engineering": [
                "Thermodynamics",
                "Fluid Mechanics",
                "Machine Design",
                "Manufacturing Processes",
                "Heat Transfer",
                "Industrial Engineering",
            ],
            "Civil Engineering": [
                "Structural Engineering",
                "Geotechnical Engineering",
                "Transportation Engineering",
                "Environmental Engineering",
                "Surveying",
                "Construction Management",
            ],
            "Electrical Engineering": [
                "Power Systems",
                "Control Systems",
                "Electrical Machines",
                "Power Electronics",
                "High Voltage Engineering",
            ],
            "Electronics and Communication Engineering": [
                "Digital Electronics",
                "Analog Circuits",
                "Signal Processing",
                "VLSI Design",
                "Embedded Systems",
                "Wireless Communication",
                "Microprocessors & Microcontrollers",
            ],
            "Chemical Engineering": [
                "Process Engineering",
                "Mass Transfer",
                "Reaction Engineering",
                "Petroleum Refining",
                "Polymer Technology",
            ],
            "Aerospace Engineering": [
                "Aerodynamics",
                "Aircraft Structures",
                "Propulsion",
                "Flight Mechanics",
                "Avionics",
            ],
            "Artificial Intelligence": [
                "Machine Learning",
                "Deep Learning",
                "Natural Language Processing",
                "Computer Vision",
                "Reinforcement Learning",
            ],
            "Data Science": [
                "Data Analytics",
                "Big Data",
                "Data Visualization",
                "Statistical Modeling",
                "Business Intelligence",
            ],
            "Cyber Security": [
                "Ethical Hacking",
                "Network Security",
                "Cryptography",
                "Digital Forensics",
                "Incident Response",
            ],
            "Robotics Engineering": [
                "Robot Kinematics",
                "Automation",
                "Mechatronics",
                "Sensors & Actuators",
            ],
        },

        "Medical": {
            "MBBS": [
                "Anatomy",
                "Physiology",
                "Biochemistry",
                "Pathology",
                "Pharmacology",
                "Microbiology",
                "Forensic Medicine",
                "Community Medicine",
                "Internal Medicine",
                "Surgery",
            ],
            "BDS": [
                "Oral Anatomy",
                "Oral Pathology",
                "Prosthodontics",
                "Orthodontics",
                "Periodontics",
                "Oral Surgery",
            ],
            "BAMS": [
                "Ayurvedic Samhita",
                "Dravyaguna",
                "Kayachikitsa",
                "Shalya Tantra",
                "Prasuti Tantra",
            ],
            "BHMS": [
                "Homoeopathic Materia Medica",
                "Organon of Medicine",
                "Repertory",
                "Practice of Medicine",
            ],
        },

        "Science": {
            "Physics": [
                "Mechanics",
                "Thermodynamics",
                "Electrostatics",
                "Magnetism",
                "Optics",
                "Modern Physics",
                "Waves & Oscillations",
                "Nuclear Physics",
            ],
            "Chemistry": [
                "Physical Chemistry",
                "Organic Chemistry",
                "Inorganic Chemistry",
                "Analytical Chemistry",
                "Environmental Chemistry",
            ],
            "Biology": [
                "Botany",
                "Zoology",
                "Genetics",
                "Ecology",
                "Cell Biology",
                "Human Physiology",
                "Microbiology",
            ],
            "Mathematics": [
                "Algebra",
                "Calculus",
                "Coordinate Geometry",
                "Trigonometry",
                "Statistics",
                "Probability",
                "Matrices & Determinants",
                "Vectors",
            ],
            "Biotechnology": [
                "Molecular Biology",
                "Genetic Engineering",
                "Immunology",
                "Bioprocess Technology",
            ],
        },

        "Commerce": {
            "Accountancy": [
                "Financial Accounting",
                "Cost Accounting",
                "Management Accounting",
                "Auditing",
            ],
            "Business Studies": [
                "Business Organization",
                "Marketing Management",
                "Financial Management",
                "Human Resource Management",
            ],
            "Economics": [
                "Microeconomics",
                "Macroeconomics",
                "Indian Economy",
                "International Trade",
            ],
            "Finance": [
                "Corporate Finance",
                "Investment Analysis",
                "Banking",
                "Insurance",
                "Capital Markets",
            ],
            "Taxation": [
                "Income Tax",
                "GST",
                "Corporate Tax",
                "International Taxation",
            ],
        },

        "Arts": {
            "History": [
                "Ancient History",
                "Medieval History",
                "Modern History",
                "World History",
            ],
            "Political Science": [
                "Indian Constitution",
                "Political Theory",
                "International Relations",
                "Public Administration",
            ],
            "Geography": [
                "Physical Geography",
                "Human Geography",
                "Economic Geography",
                "Cartography",
            ],
            "Sociology": [
                "Social Theory",
                "Indian Society",
                "Rural Sociology",
                "Urban Sociology",
            ],
        },

        "Management": {
            "MBA": [
                "Marketing",
                "Finance",
                "Human Resources",
                "Operations",
                "Information Systems",
                "International Business",
                "Entrepreneurship",
            ],
            "BBA": [
                "Business Communication",
                "Principles of Management",
                "Marketing Basics",
                "Financial Accounting",
            ],
            "Business Analytics": [
                "Predictive Analytics",
                "Data Mining",
                "Business Intelligence",
                "Decision Science",
            ],
        },

        "Computer Science": {
            "Computer Science": [
                "Programming Fundamentals",
                "Data Structures",
                "Algorithms",
                "Database Systems",
                "Software Development",
            ],
            "Artificial Intelligence": [
                "Machine Learning",
                "Deep Learning",
                "Natural Language Processing",
                "Expert Systems",
            ],
            "Machine Learning": [
                "Supervised Learning",
                "Unsupervised Learning",
                "Neural Networks",
                "Feature Engineering",
            ],
            "Cloud Computing": [
                "AWS",
                "Azure",
                "Google Cloud",
                "DevOps",
                "Containerization",
            ],
        },

        "Law": {
            "LLB": [
                "Constitutional Law",
                "Criminal Law",
                "Civil Law",
                "Contract Law",
                "Family Law",
                "Labour Law",
                "Corporate Law",
                "Intellectual Property Law",
            ],
            "LLM": [
                "International Law",
                "Cyber Law",
                "Human Rights Law",
                "Environmental Law",
                "Tax Law",
            ],
        },

        "Pharmacy": {
            "B.Pharm": [
                "Pharmaceutics",
                "Pharmacology",
                "Pharmaceutical Chemistry",
                "Pharmacognosy",
                "Clinical Pharmacy",
            ],
            "M.Pharm": [
                "Drug Regulatory Affairs",
                "Pharmaceutical Biotechnology",
                "Industrial Pharmacy",
                "Quality Assurance",
            ],
        },

        "Agriculture": {
            "Agriculture": [
                "Agronomy",
                "Soil Science",
                "Plant Pathology",
                "Entomology",
                "Agricultural Economics",
            ],
            "Horticulture": [
                "Fruit Science",
                "Vegetable Science",
                "Floriculture",
                "Post Harvest Technology",
            ],
            "Agricultural Engineering": [
                "Farm Machinery",
                "Irrigation Engineering",
                "Food Process Engineering",
            ],
        },

        "Education": {
            "B.Ed": [
                "Pedagogy",
                "Educational Psychology",
                "Curriculum Development",
                "Inclusive Education",
            ],
            "M.Ed": [
                "Educational Administration",
                "Research Methodology",
                "Educational Technology",
            ],
        },

        "Design": {
            "Fashion Design": [
                "Textile Design",
                "Apparel Design",
                "Fashion Merchandising",
                "Pattern Making",
            ],
            "Graphic Design": [
                "Typography",
                "Brand Identity",
                "Digital Illustration",
                "Motion Graphics",
            ],
            "UI/UX Design": [
                "User Research",
                "Wireframing",
                "Prototyping",
                "Interaction Design",
                "Usability Testing",
            ],
            "Product Design": [
                "Industrial Design",
                "Ergonomics",
                "3D Modelling",
            ],
        },

        "Mass Communication": {
            "Journalism": [
                "Print Journalism",
                "Broadcast Journalism",
                "Investigative Journalism",
                "Sports Journalism",
            ],
            "Digital Media": [
                "Social Media Marketing",
                "Content Creation",
                "SEO & SEM",
                "Podcasting",
            ],
            "Advertising": [
                "Copywriting",
                "Media Planning",
                "Brand Management",
            ],
        },

        "Biotechnology": {
            "Biotechnology": [
                "Genetic Engineering",
                "Bioinformatics",
                "Industrial Biotechnology",
                "Agricultural Biotechnology",
            ],
            "Genetics": [
                "Molecular Genetics",
                "Population Genetics",
                "Genomics",
            ],
            "Microbiology": [
                "Medical Microbiology",
                "Environmental Microbiology",
                "Industrial Microbiology",
            ],
        },

        "Vocational": {
            "ITI": [
                "Electrician",
                "Fitter",
                "Welder",
                "Plumber",
                "Turner",
                "Machinist",
                "Carpenter",
                "Draughtsman Civil",
                "Draughtsman Mechanical",
                "Motor Mechanic Vehicle",
                "Refrigeration & Air Conditioning",
                "Electronics Mechanic",
            ],
            "Polytechnic": [
                "Diploma in Civil Engineering",
                "Diploma in Mechanical Engineering",
                "Diploma in Electrical Engineering",
                "Diploma in Electronics Engineering",
                "Diploma in Computer Science",
                "Diploma in Chemical Engineering",
            ],
            "Skill Development": [
                "Beauty & Wellness",
                "Healthcare",
                "Retail",
                "Logistics",
                "Construction",
                "Agriculture",
            ],
        },

        "AYUSH": {
            "Ayurveda": [
                "Panchakarma",
                "Rasayana",
                "Kayachikitsa",
                "Shalya Chikitsa",
            ],
            "Homeopathy": [
                "Materia Medica",
                "Repertory",
                "Organon",
            ],
            "Yoga & Naturopathy": [
                "Yoga Therapy",
                "Naturopathic Medicine",
                "Hydrotherapy",
            ],
        },

        "Physical Education": {
            "Physical Education": [
                "Sports Training",
                "Exercise Physiology",
                "Sports Psychology",
                "Kinesiology",
            ],
            "Sports Science": [
                "Biomechanics",
                "Sports Nutrition",
                "Sports Medicine",
                "Strength & Conditioning",
            ],
        },

        "Statistics": {
            "Statistics": [
                "Descriptive Statistics",
                "Inferential Statistics",
                "Probability Theory",
                "Regression Analysis",
                "Time Series Analysis",
            ],
            "Applied Statistics": [
                "Biostatistics",
                "Econometrics",
                "Quality Control",
                "Actuarial Science",
            ],
        },

        "Economics": {
            "Economics": [
                "Microeconomics",
                "Macroeconomics",
                "Development Economics",
                "Public Finance",
                "Agricultural Economics",
            ],
            "Applied Economics": [
                "Econometrics",
                "Environmental Economics",
                "Health Economics",
                "Labour Economics",
            ],
        },

        "Psychology": {
            "Clinical Psychology": [
                "Psychopathology",
                "Cognitive Behavioural Therapy",
                "Neuropsychology",
                "Child Psychology",
            ],
            "Counselling Psychology": [
                "Career Counselling",
                "Family Therapy",
                "Grief Counselling",
                "School Counselling",
            ],
        },

        "Architecture": {
            "Architecture": [
                "Building Construction",
                "Architectural Design",
                "Urban Planning",
                "Landscape Architecture",
                "Sustainable Design",
            ],
            "Interior Design": [
                "Space Planning",
                "Furniture Design",
                "Lighting Design",
                "Material & Finishes",
            ],
        },

        "Nursing": {
            "B.Sc Nursing": [
                "Medical-Surgical Nursing",
                "Paediatric Nursing",
                "Obstetric Nursing",
                "Community Health Nursing",
                "Mental Health Nursing",
            ],
            "M.Sc Nursing": [
                "Nursing Administration",
                "Nursing Education",
                "Critical Care Nursing",
                "Oncology Nursing",
            ],
        },
    }

    def handle(self, *args, **kwargs):
        created = 0
        skipped = 0
        errors  = []

        for stream_name, fields in self.SUBFIELDS.items():
            # Get stream — create if missing (safety net)
            stream, stream_created = Stream.objects.get_or_create(stream_name=stream_name)
            if stream_created:
                self.stdout.write(self.style.WARNING(
                    f"  Stream '{stream_name}' did not exist — created automatically."
                ))

            for field_name, subfield_names in fields.items():
                # Get field — must belong to correct stream
                try:
                    field = Field.objects.get(stream=stream, field_name=field_name)
                except Field.DoesNotExist:
                    errors.append(
                        f"Field not found: '{field_name}' under Stream '{stream_name}' — run import_fields first."
                    )
                    continue

                for subfield_name in subfield_names:
                    try:
                        _, is_created = SubField.objects.get_or_create(
                            field=field,
                            sub_field_name=subfield_name,
                        )
                        if is_created:
                            created += 1
                        else:
                            skipped += 1
                    except Exception as e:
                        errors.append(
                            f"{stream_name} > {field_name} > {subfield_name}: {e}"
                        )

        self.stdout.write(self.style.SUCCESS(
            f"\nSubFields imported successfully.\n"
            f"Created : {created}\n"
            f"Skipped : {skipped}"
        ))

        if errors:
            self.stdout.write(self.style.ERROR(f"\nErrors ({len(errors)}):"))
            for err in errors:
                self.stdout.write(self.style.ERROR(f"  {err}"))