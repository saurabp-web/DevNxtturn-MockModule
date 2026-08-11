import os
import re
import logging
import pdfplumber
from django.core.management.base import BaseCommand
from MockAdmin.models import Exam 

# pdfminer ke warnings ko console se hatane ke liye
logging.getLogger("pdfminer").setLevel(logging.ERROR)

class Command(BaseCommand):
    help = "Scrapes all local JEE PDFs and stores exam_name as 'JEE Main YYYY Previous Year Paper'."

    def handle(self, *args, **options):
        folder_path = r"C:\Users\hp\Desktop\nxtturn\nxtturn\jee_main_papers_folder"
        
        if not os.path.exists(folder_path):
            self.stdout.write(self.style.ERROR(f"Error: Path '{folder_path}' nahi mila!"))
            return

        pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]

        if not pdf_files:
            self.stdout.write(self.style.WARNING("Folder mein koi PDF file nahi mili."))
            return

        inserted_count = 0
        updated_count = 0
        error_count = 0

        for filename in pdf_files:
            file_path = os.path.join(folder_path, filename)
            exam_year = None
            
            # 1. & 2. Extraction Logic remains the same
            try:
                with pdfplumber.open(file_path) as pdf:
                    if pdf.pages:
                        first_page_text = pdf.pages[0].extract_text() or ""
                        year_match = re.search(r"JEE\s+Main\s+(\d{4})", first_page_text, re.IGNORECASE)
                        if year_match:
                            exam_year = int(year_match.group(1))
            except Exception:
                pass

            if not exam_year:
                filename_year_match = re.search(r"(\d{4})", filename)
                if filename_year_match:
                    exam_year = int(filename_year_match.group(1))

            if not exam_year or not (2002 <= exam_year <= 2025):
                continue

            # Format naming
            shift_match = re.search(r"\(([^)]+)\)", filename)
            if shift_match:
                raw_shift_text = shift_match.group(1).replace('_', ' ')
                clean_shift = re.sub(r"^\d{2}\s+[A-Za-z]{3}\s+", "", raw_shift_text)
                exam_name = f"JEE Main {exam_year} ({clean_shift}) Previous Year Paper"
            else:
                exam_name = f"JEE Main {exam_year} Previous Year Paper"

            # --- MODEL STORAGE ---
            try:
                obj, created = Exam.objects.update_or_create(
                    exam_name=exam_name,
                    defaults={
                        'exam_code': "JEE_MAIN",
                        'exam_year': exam_year,
                        'conducting_body': "NTA",
                        'exam_category': "Engineering Entrance",
                        'estimated_time_hours': 3
                    }
                )
                
                if created:
                    inserted_count += 1
                    status = "Inserted"
                else:
                    updated_count += 1
                    status = "Updated"
                
                self.stdout.write(self.style.SUCCESS(f"[{status}] -> {exam_name}"))

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"Error processing {filename}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(
            f"\n=== Run Completed ===\n"
            f"- Successfully Inserted: {inserted_count}\n"
            f"- Successfully Updated: {updated_count}\n"
            f"- Errors: {error_count}"
        ))