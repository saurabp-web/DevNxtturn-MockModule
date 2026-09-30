from django.core.management.base import BaseCommand
from MockAdmin.models import ExamType, EducationLevel


# Curated mapping using the actual education_level_id values from your
# database. NOTE: "Entrance" is currently set to the same list as Job as
# a placeholder — confirm/update this list before relying on it.
EXAM_TYPE_EDUCATION_LEVELS = {
    'School': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    # Class 1–12

    'Job': [10, 12, 13, 15, 16, 18, 20, 22, 25, 26, 27],
    # Class 10, Class 12, ITI, Diploma, Polytechnic Diploma, Graduate,
    # Postgraduate, Professional Degree, Any Graduation,
    # Any Post Graduation, Any Qualification

    'Entrance': [10, 12, 13, 15, 16, 18, 20, 22, 25, 26, 27],
    # PLACEHOLDER — same as Job for now; update with the real list.
}


class Command(BaseCommand):
    help = 'Seeds ExamType.education_levels (School/Entrance/Job -> EducationLevel mapping).'

    def handle(self, *args, **options):
        for type_name, level_ids in EXAM_TYPE_EDUCATION_LEVELS.items():
            try:
                exam_type = ExamType.objects.get(type_name=type_name)
            except ExamType.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f'Skipped "{type_name}" — no ExamType row with that type_name exists.'
                ))
                continue

            levels = EducationLevel.objects.filter(education_level_id__in=level_ids)
            found_ids = set(levels.values_list('education_level_id', flat=True))
            missing_ids = set(level_ids) - found_ids
            if missing_ids:
                self.stdout.write(self.style.WARNING(
                    f'"{type_name}": education_level_id(s) not found and skipped: {sorted(missing_ids)}'
                ))

            exam_type.education_levels.set(levels)
            self.stdout.write(self.style.SUCCESS(
                f'"{type_name}" -> linked {levels.count()} education level(s): '
                + ', '.join(levels.values_list('education_level', flat=True))
            ))

        self.stdout.write(self.style.SUCCESS('Done.'))