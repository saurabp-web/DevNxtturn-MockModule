from django.core.management.base import BaseCommand
from MockAdmin.models import ExamType, JobCategory, JobExamCategory  # update 'yourapp'

# Key: job_category_id, Value: (job_category_name, [(exam_name, description), ...])
DATA = {
    1: ("UPSC", [
        ("Civil Services Examination (CSE)", "UPSC Civil Services Examination for IAS, IPS, IFS and allied Group A & B central services."),
        ("Engineering Services Examination (ESE)", "UPSC Engineering Services Examination for Civil, Mechanical, Electrical and Electronics engineering posts."),
        ("Combined Defence Services (CDS)", "UPSC Combined Defence Services Examination for Army, Navy and Air Force officer entry."),
        ("National Defence Academy (NDA)", "UPSC NDA & NA Examination for entry to Army, Navy and Air Force wings of NDA."),
        ("Combined Medical Services (CMS)", "UPSC Combined Medical Services Examination for medical officer posts under central government."),
        ("Indian Forest Service (IFoS)", "UPSC Indian Forest Service Examination for Class I forest officer posts."),
        ("Central Armed Police Forces (CAPF)", "UPSC CAPF Assistant Commandant Examination for BSF, CRPF, CISF, ITBP and SSB."),
        ("Indian Economic Service (IES)", "UPSC Indian Economic Service Examination for economic adviser posts."),
        ("Indian Statistical Service (ISS)", "UPSC Indian Statistical Service Examination for statistical officer posts."),
        ("Geo-Scientist", "UPSC Geo-Scientist and Geologist Examination for geological survey posts."),
    ]),
    2: ("State PSC", [
        ("State Civil Services", "State Public Service Commission Civil Services Examination for Group A and B gazetted posts."),
        ("State Engineering Services", "State PSC Engineering Services Examination for assistant and junior engineer posts."),
        ("State Forest Services", "State PSC Forest Services Examination for state forest officer posts."),
        ("State Judicial Services", "State PSC Judicial Services Examination for civil judge and judicial magistrate posts."),
        ("State Medical Services", "State PSC Medical Services Examination for state medical officer posts."),
        ("Assistant Professor Recruitment", "State PSC Assistant Professor recruitment for government colleges and universities."),
        ("State Police Services", "State PSC Police Services Examination for deputy superintendent of police posts."),
    ]),
    3: ("SSC", [
        ("Combined Graduate Level (CGL)", "SSC CGL Examination for Group B and C posts like Inspector, Auditor, Assistant and SO."),
        ("Combined Higher Secondary Level (CHSL)", "SSC CHSL Examination for LDC, DEO, Postal Assistant and Sorting Assistant posts."),
        ("Multi Tasking Staff (MTS)", "SSC MTS Examination for Group C non-technical multi tasking staff posts."),
        ("Junior Engineer (JE)", "SSC JE Examination for Junior Engineer Civil, Electrical and Mechanical posts."),
        ("Selection Post", "SSC Selection Post Examination for various posts from matriculation to graduation level."),
        ("Delhi Police", "SSC Delhi Police Head Constable and other recruitment examinations."),
        ("Constable GD", "SSC Constable GD Examination for General Duty Constable in CAPFs, NIA, SSF and AR."),
        ("Stenographer", "SSC Stenographer Grade C and D Examination for central government departments."),
        ("Junior Hindi Translator (JHT)", "SSC Junior Hindi Translator and Junior Translator Examination."),
        ("CPO SI", "SSC CPO Examination for Sub Inspector in Delhi Police and Central Armed Police Forces."),
    ]),
    4: ("Banking", [
        ("Probationary Officer (PO)", "Bank PO Examination including IBPS PO and SBI PO for officer cadre entry."),
        ("Clerk", "Bank Clerk Examination including IBPS Clerk and SBI Clerk for clerical cadre entry."),
        ("Specialist Officer (SO)", "Bank SO Examination for IT, Law, Agriculture, HR, Marketing and other specialist posts."),
        ("RRB Officer Scale I", "IBPS RRB Officer Scale I Examination for Regional Rural Bank officer entry."),
        ("RRB Office Assistant", "IBPS RRB Office Assistant Multipurpose Examination for clerical posts in RRBs."),
        ("Local Bank Officer (LBO)", "State and local area bank officer recruitment examinations."),
        ("Apprentice", "Bank apprenticeship recruitment under National Apprenticeship Promotion Scheme."),
    ]),
    5: ("Insurance", [
        ("Assistant Administrative Officer (AAO)", "LIC and GIC AAO Examination for assistant administrative officer posts."),
        ("Administrative Officer (AO)", "Insurance sector Administrative Officer recruitment examinations."),
        ("Assistant", "NIACL, UIIC and other insurance company assistant recruitment examinations."),
        ("Development Officer (ADO)", "LIC Apprentice Development Officer recruitment examination."),
        ("Insurance Apprentice", "Insurance sector apprenticeship recruitment under NAPS scheme."),
    ]),
    6: ("Railway", [
        ("NTPC", "RRB Non-Technical Popular Categories Examination for clerk, guard, assistant and other posts."),
        ("Group D", "RRB Group D Level 1 Examination for track maintainer, helper and other posts."),
        ("Assistant Loco Pilot (ALP)", "RRB Assistant Loco Pilot and Technician Examination."),
        ("Junior Engineer (JE)", "RRB Junior Engineer Examination for engineering posts in various railway departments."),
        ("Technician", "RRB Technician Grade I and III Examination for technical posts."),
        ("Railway Protection Force (RPF)", "RPF Constable and Sub Inspector recruitment examination."),
        ("Paramedical Staff", "RRB Paramedical Categories Examination for health and medical posts."),
        ("Ministerial & Isolated Categories", "RRB Ministerial and Isolated Categories Examination for various posts."),
    ]),
    7: ("Defence", [
        ("Agniveer", "Agniveer recruitment for Army, Navy and Air Force short service entry."),
        ("Army Officer", "Indian Army officer entry through NDA, CDS, TES, SSC Tech and other schemes."),
        ("Army Soldier", "Indian Army soldier recruitment for GD, Technical, Clerk and Tradesman categories."),
        ("Navy Officer", "Indian Navy officer entry through NDA, CDS, UES, SSC and direct entry schemes."),
        ("Navy Sailor", "Indian Navy sailor recruitment for SSR, MR and AA categories."),
        ("Air Force Officer", "Indian Air Force officer entry through NDA, CDS, AFCAT and other schemes."),
        ("Airman", "Indian Air Force Agniveer Vayu and group X and Y trades recruitment."),
        ("Territorial Army", "Territorial Army officer and soldier recruitment for part-time defence service."),
    ]),
    8: ("Police", [
        ("Constable", "State and central police constable GD recruitment examinations."),
        ("Head Constable", "State and central police head constable recruitment examinations."),
        ("Sub Inspector (SI)", "State police sub inspector recruitment examinations."),
        ("Assistant Sub Inspector (ASI)", "State and central police assistant sub inspector recruitment."),
        ("Jail Warder", "State prison and jail department warder and constable recruitment."),
        ("Driver Constable", "Police driver constable and driver operator recruitment."),
    ]),
    9: ("Paramilitary Forces", [
        ("BSF Constable", "Border Security Force Constable GD and Tradesman recruitment."),
        ("CRPF Constable", "Central Reserve Police Force Constable GD recruitment."),
        ("CISF Constable", "Central Industrial Security Force Constable Fire and GD recruitment."),
        ("ITBP Constable", "Indo-Tibetan Border Police Constable GD and Tradesman recruitment."),
        ("SSB Constable", "Sashastra Seema Bal Constable GD recruitment."),
        ("Assam Rifles Technical & Tradesman", "Assam Rifles Technical and Tradesman recruitment for various trades."),
    ]),
    10: ("Teaching", [
        ("CTET", "Central Teacher Eligibility Test for Paper I and II for central government school teachers."),
        ("State TET", "State Teacher Eligibility Test for primary and upper primary level teachers."),
        ("PRT", "Primary Teacher recruitment for classes I to V in government schools."),
        ("TGT", "Trained Graduate Teacher recruitment for classes VI to X in government schools."),
        ("PGT", "Post Graduate Teacher recruitment for classes XI and XII in government schools."),
        ("Assistant Professor", "Assistant Professor recruitment for government degree colleges and universities."),
        ("Professor", "Professor and Associate Professor recruitment for government universities."),
        ("Lecturer", "Lecturer recruitment for government polytechnic and ITI institutions."),
        ("KVS Recruitment", "Kendriya Vidyalaya Sangathan PRT, TGT, PGT and principal recruitment."),
        ("NVS Recruitment", "Navodaya Vidyalaya Samiti TGT, PGT and miscellaneous teaching staff recruitment."),
    ]),
    11: ("Judiciary", [
        ("Civil Judge", "State judicial services Civil Judge Junior Division examination."),
        ("District Judge", "Direct recruitment to District Judge posts through state high courts."),
        ("Judicial Magistrate", "Judicial First Class Magistrate recruitment examination."),
        ("High Court Recruitment", "High Court administrative, clerical and law clerk recruitment."),
        ("Supreme Court Recruitment", "Supreme Court of India junior court assistant and staff recruitment."),
    ]),
    12: ("PSU", [
        ("Graduate Engineer Trainee (GET)", "PSU Graduate Engineer Trainee recruitment through GATE and direct examination."),
        ("Management Trainee (MT)", "PSU Management Trainee recruitment for finance, HR and operations functions."),
        ("Executive Trainee (ET)", "PSU Executive Trainee recruitment for various disciplines."),
        ("Junior Executive", "PSU Junior Executive recruitment for engineering and management functions."),
        ("Technician", "PSU Technician and operator cum technician recruitment."),
    ]),
    13: ("Healthcare", [
        ("Staff Nurse", "Government hospital and health department Staff Nurse recruitment."),
        ("Nursing Officer", "Central government Nursing Officer recruitment including AIIMS and ESIC."),
        ("Medical Officer", "Government Medical Officer and MBBS doctor recruitment."),
        ("Pharmacist", "Government hospital Pharmacist and drug inspector recruitment."),
        ("Lab Technician", "Government hospital Lab Technician and MLT recruitment."),
        ("ANM", "Auxiliary Nurse Midwife recruitment for primary health centres."),
        ("GNM", "General Nursing and Midwifery qualified nurse recruitment."),
        ("Community Health Officer (CHO)", "Ayushman Bharat Community Health Officer recruitment."),
    ]),
    14: ("Engineering", [
        ("Assistant Engineer (AE)", "Government department Assistant Engineer recruitment for various disciplines."),
        ("Junior Engineer (JE)", "Government department Junior Engineer recruitment through SSC JE and state exams."),
        ("Executive Engineer", "Government department Executive Engineer and divisional engineer recruitment."),
        ("Site Engineer", "Government and PSU site engineer and project engineer recruitment."),
    ]),
    15: ("Scientific Research", [
        ("Scientist", "Research organisation Scientist B, C and D recruitment including DRDO, ISRO and CSIR."),
        ("Technical Assistant", "Research organisation Technical Assistant and Scientific Assistant recruitment."),
        ("Research Associate", "Government research organisation Research Associate recruitment."),
        ("Junior Research Fellow (JRF)", "UGC NET JRF, CSIR JRF and ICMR JRF for research fellowship."),
        ("Senior Research Fellow (SRF)", "Government funded Senior Research Fellowship in various science disciplines."),
        ("Project Associate", "Research organisation and university Project Associate and Project Scientist recruitment."),
    ]),
    16: ("Space & Aerospace", [
        ("Scientist/Engineer", "ISRO and aerospace organisation Scientist and Engineer SC and SD recruitment."),
        ("Technical Assistant", "ISRO and aerospace organisation Technical Assistant recruitment."),
        ("Technician", "ISRO Technician B and HAL Technician recruitment."),
        ("Apprenticeship", "ISRO, HAL and aerospace PSU apprenticeship recruitment."),
    ]),
    17: ("Agriculture", [
        ("Agriculture Officer", "State agriculture department Agriculture Officer recruitment."),
        ("Agriculture Field Officer (AFO)", "IBPS SO Agriculture Field Officer specialist officer recruitment."),
        ("Horticulture Officer", "State horticulture department officer recruitment."),
        ("Veterinary Officer", "State animal husbandry department Veterinary Officer recruitment."),
        ("Soil Conservation Officer", "State soil conservation and land use department officer recruitment."),
    ]),
    18: ("Forest & Wildlife", [
        ("Forest Guard", "State forest department Forest Guard and forest watcher recruitment."),
        ("Forest Ranger", "State forest department Forest Range Officer recruitment."),
        ("Wildlife Inspector", "State wildlife and environment department inspector recruitment."),
        ("Forest Officer", "Indian Forest Service and state forest service officer recruitment."),
    ]),
    19: ("Postal Services", [
        ("Gramin Dak Sevak (GDS)", "India Post Gramin Dak Sevak recruitment for Branch Post Master and assistant posts."),
        ("Postal Assistant", "India Post Postal Assistant recruitment for post office counter and back office work."),
        ("Sorting Assistant", "India Post Sorting Assistant recruitment for mail sorting centres."),
        ("Mail Guard", "India Post Mail Guard recruitment for mail motor service."),
        ("Postman", "India Post Postman and Mail Deliverer recruitment."),
    ]),
    20: ("Civil Aviation", [
        ("Airport Operations", "AAI and private airport operator ground operations staff recruitment."),
        ("Junior Executive (AAI)", "Airports Authority of India Junior Executive ATC, Electronics and Civil recruitment."),
        ("Air Traffic Controller (ATC)", "AAI Air Traffic Control Officer recruitment and training."),
        ("Ground Staff", "Airline and airport ground handling staff recruitment."),
    ]),
    21: ("Maritime & Shipping", [
        ("Merchant Navy Officer", "Merchant Navy Deck Officer and competency examination."),
        ("Deck Cadet", "Merchant Navy Deck Cadet sponsorship and training recruitment."),
        ("Marine Engineer", "Merchant Navy and port Marine Engineer and motor cadet recruitment."),
        ("Port Authority Recruitment", "Major and minor Port Authority multi-post recruitment."),
    ]),
    22: ("Power & Energy", [
        ("Junior Engineer", "State electricity board and power PSU Junior Engineer recruitment."),
        ("Assistant Engineer", "State electricity board and power PSU Assistant Engineer recruitment."),
        ("Technician", "Power sector Technician and wireman recruitment."),
        ("Executive Trainee", "Power PSU Executive Trainee through GATE recruitment."),
        ("Lineman", "State electricity board Lineman and Helper recruitment."),
    ]),
    23: ("Telecommunications", [
        ("Junior Telecom Officer (JTO)", "BSNL Junior Telecom Officer recruitment examination."),
        ("Telecom Technical Assistant (TTA)", "BSNL Telecom Technical Assistant recruitment examination."),
        ("Technician", "Telecom sector Technician and cable jointer recruitment."),
    ]),
    24: ("Food & Supply", [
        ("Assistant Grade", "FCI and CWC Assistant Grade II and III recruitment."),
        ("Manager", "FCI and CWC Manager in various disciplines recruitment."),
        ("Technical Officer", "FCI Technical Officer and CWC Technical Assistant recruitment."),
        ("Depot Manager", "State civil supplies Depot Manager and Godown Keeper recruitment."),
    ]),
    25: ("Public Administration", [
        ("Municipal Officer", "Municipal corporation and urban local body officer recruitment."),
        ("Revenue Inspector", "State revenue department Revenue Inspector and Patwari recruitment."),
        ("Secretariat Assistant", "State and central secretariat assistant and lower division clerk recruitment."),
        ("Development Officer", "State rural and urban development department officer recruitment."),
    ]),
    26: ("Disaster Management", [
        ("NDRF Recruitment", "National Disaster Response Force Constable and technical post recruitment."),
        ("SDRF Recruitment", "State Disaster Response Force constable and officer recruitment."),
        ("Disaster Response Officer", "NDMA and SDMA Disaster Response Officer and consultant recruitment."),
    ]),
    27: ("Intelligence & Investigation", [
        ("Intelligence Officer", "State and central intelligence department officer recruitment."),
        ("Assistant Central Intelligence Officer (ACIO)", "IB ACIO Grade II Executive recruitment examination."),
        ("Investigation Officer", "CBI, ED, NIA and NCB Investigation Officer and Inspector recruitment."),
    ]),
    28: ("Forensic Science", [
        ("Scientific Officer", "Central and state FSL Scientific Officer recruitment."),
        ("Forensic Expert", "Government forensic expert and examiner recruitment."),
        ("Laboratory Assistant", "Forensic Science Laboratory Assistant and technician recruitment."),
    ]),
    29: ("Tourism & Hospitality", [
        ("Tourism Officer", "Central and state tourism department Tourism Officer recruitment."),
        ("Hotel Manager", "Government hotel and ITDC Hotel Manager recruitment."),
        ("Hospitality Executive", "Government hospitality and catering establishment executive recruitment."),
    ]),
    30: ("Sports Authority", [
        ("Coach", "SAI and state sports authority Coach and Senior Coach recruitment."),
        ("Physical Training Instructor", "Government school and institution Physical Training Instructor recruitment."),
        ("Sports Officer", "State sports department and sports authority officer recruitment."),
    ]),
    31: ("Culture & Archaeology", [
        ("Archaeologist", "ASI and state archaeology department Archaeologist recruitment."),
        ("Museum Curator", "National and state Museum Curator and Keeper recruitment."),
        ("Archivist", "National and state Archives Archivist and Assistant Archivist recruitment."),
        ("Conservation Assistant", "ASI and state department Conservation Assistant recruitment."),
    ]),
    32: ("Skill Development", [
        ("Skill Instructor", "Government ITI and skill centre Skill Instructor recruitment."),
        ("Training Officer", "State skill development and vocational training department officer recruitment."),
        ("Vocational Trainer", "NSDC and PMKVY empanelled Vocational Trainer recruitment."),
    ]),
    33: ("Apprenticeship", [
        ("Graduate Apprentice", "Graduate Engineering Apprentice under Apprentices Act in government and PSU."),
        ("Technician Apprentice", "Diploma holder Technician Apprentice under Apprentices Act."),
        ("Trade Apprentice", "ITI passed Trade Apprentice in government and PSU establishments."),
    ]),
    34: ("Private Sector", [
        ("Graduate Trainee", "Private sector Graduate Engineer Trainee and Management Trainee entry."),
        ("Management Trainee", "Private company Management Trainee programme recruitment."),
        ("Business Analyst", "Private sector Business Analyst and process analyst recruitment."),
        ("HR Executive", "Private sector Human Resources executive and generalist recruitment."),
        ("Sales Executive", "Private sector Sales Executive and business development recruitment."),
    ]),
    35: ("Information Technology", [
        ("Software Engineer", "Private and government Software Engineer and developer recruitment."),
        ("Python Developer", "Python Developer and backend engineer recruitment."),
        ("Java Developer", "Java Developer and J2EE engineer recruitment."),
        ("Full Stack Developer", "Full Stack Web Developer recruitment."),
        ("DevOps Engineer", "DevOps and Site Reliability Engineer recruitment."),
        ("Cloud Engineer", "Cloud Infrastructure and Solutions Engineer recruitment."),
        ("Cyber Security Engineer", "Cyber Security Analyst and Information Security Engineer recruitment."),
        ("QA Engineer", "Quality Assurance and Software Testing Engineer recruitment."),
    ]),
    36: ("Data Science & Analytics", [
        ("Data Scientist", "Data Scientist recruitment in government and private sector."),
        ("Data Analyst", "Data Analyst and reporting analyst recruitment."),
        ("Machine Learning Engineer", "Machine Learning and AI model development engineer recruitment."),
        ("AI Engineer", "Artificial Intelligence Engineer and AI researcher recruitment."),
        ("Business Intelligence Analyst", "Business Intelligence and BI Developer recruitment."),
    ]),
    37: ("Finance & Accounting", [
        ("Accountant", "Government and private sector Accountant and accounts assistant recruitment."),
        ("Auditor", "CAG, internal audit and statutory Auditor recruitment."),
        ("Tax Officer", "Income Tax, GST and customs department officer recruitment."),
        ("Financial Analyst", "Private sector Financial Analyst and investment analyst recruitment."),
        ("Cost Accountant", "CMA qualified Cost Accountant and cost analyst recruitment."),
    ]),
    38: ("Legal Services", [
        ("Legal Officer", "Government department and PSU Legal Officer recruitment."),
        ("Law Officer", "Central and state government Law Officer and Assistant Law Officer recruitment."),
        ("Corporate Counsel", "Private sector in-house Corporate Counsel and legal advisor recruitment."),
        ("Legal Assistant", "Government department and court Legal Assistant recruitment."),
    ]),
    39: ("Media & Communication", [
        ("Public Relations Officer (PRO)", "Government department and PSU Public Relations Officer recruitment."),
        ("Journalist", "Print, broadcast and digital media Journalist recruitment."),
        ("Content Writer", "Digital media and corporate Content Writer recruitment."),
        ("Social Media Manager", "Government and private sector Social Media Manager recruitment."),
    ]),
    40: ("E-Commerce & Retail", [
        ("Store Manager", "Organised retail and e-commerce Store Manager recruitment."),
        ("Retail Executive", "Retail store floor executive and customer associate recruitment."),
        ("Supply Chain Executive", "E-commerce and retail Supply Chain and logistics executive recruitment."),
        ("Category Manager", "E-commerce platform Category Manager and merchandising executive recruitment."),
    ]),
    41: ("Manufacturing", [
        ("Production Engineer", "Manufacturing plant Production Engineer and production supervisor recruitment."),
        ("Quality Engineer", "Manufacturing Quality Engineer and QC inspector recruitment."),
        ("Plant Engineer", "Manufacturing Plant Engineer and maintenance engineer recruitment."),
        ("Maintenance Engineer", "Industrial Maintenance Engineer and reliability engineer recruitment."),
    ]),
    42: ("Startup & Innovation", [
        ("Product Manager", "Startup and tech company Product Manager and associate PM recruitment."),
        ("Innovation Associate", "Corporate innovation lab and startup Innovation Associate recruitment."),
        ("Startup Fellow", "Government and accelerator Startup Fellowship programme recruitment."),
        ("Operations Executive", "Startup Operations Executive and business operations associate recruitment."),
    ]),
}


class Command(BaseCommand):
    help = "Seed JobExamCategory data matched by job_category_id"

    def handle(self, *args, **kwargs):
        try:
            exam_type = ExamType.objects.get(type_name="Job")
        except ExamType.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'ExamType with type_name="Job" not found. Please create it first.'
            ))
            return

        created_count = 0
        skipped_count = 0
        error_count = 0

        for job_category_id, (expected_name, exams) in DATA.items():
            try:
                job_category = JobCategory.objects.get(job_category_id=job_category_id)
            except JobCategory.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f'[ID {job_category_id}] JobCategory not found in DB. Skipping.'
                ))
                error_count += 1
                continue

            # Safety check: warn if name doesn't match
            if job_category.job_category_name != expected_name:
                self.stdout.write(self.style.WARNING(
                    f'[ID {job_category_id}] Name mismatch — '
                    f'DB: "{job_category.job_category_name}" | '
                    f'Script: "{expected_name}" — using DB record.'
                ))

            for exam_name, exam_desc in exams:
                obj, created = JobExamCategory.objects.get_or_create(
                    category_name=exam_name,
                    job_category=job_category,
                    defaults={
                        "exam_type": exam_type,
                        "description": exam_desc,
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        f"  [CREATED] [{job_category_id}] {job_category.job_category_name} → {exam_name}"
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        f"  [EXISTS]  [{job_category_id}] {job_category.job_category_name} → {exam_name}"
                    )

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Created: {created_count} | Already existed: {skipped_count} | Errors: {error_count}"
        ))