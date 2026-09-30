from django.contrib import admin
from MockAdmin.models import *
from django.utils.html import format_html, format_html_join

class ExamAdmin(admin.ModelAdmin):
    # CHANGED: education_level / stream are now ManyToManyFields (see
    # models.py). M2M fields can't be put directly in list_display (Django
    # can't render a "column" for a to-many relation), so a small method
    # renders them as a comma-joined string instead. list_filter DOES
    # support M2M out of the box, so those just needed the new field name.
    list_display = ('exam_id','exam_name', 'exam_code', 'education_level_list', 'level', 'exam_type')
    search_fields = ('exam_name', 'exam_code')
    list_filter = ('education_levels', 'streams', 'level', 'exam_type')

    # Avoids one query per row when rendering education_level_list for
    # every exam in the changelist.
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('education_levels')

    @admin.display(description='Education Level')
    def education_level_list(self, obj):
        return ", ".join(el.education_level for el in obj.education_levels.all()) or "—"
    

class MockExamAdmin(admin.ModelAdmin):
    list_display = ('mockexam_id', 'mockexam_name', 'year', 'description', 'total_marks','duration_minutes','is_active')
    search_fields = ('mockexam_name',)
    

class QuestionAdmin(admin.ModelAdmin):
    # CHANGED: 'pyq_year' -> 'pyq_years' and 'appearances' -> 'appearances_display'
    # so the columns show EVERY year / paper a question appeared in,
    # not just the first appearance.
    list_display = ('question_id', 'exam', 'chapter', 'question_text', 'question_type', 'is_previousyear',
                    'pyq_exam', 'pyq_years', 'pyq_session', 'appearances_display',
                    'is_practice', 'is_custom', 'is_mock')
    search_fields = ('question_text',)

    @admin.display(description="PYQ YEAR", ordering="pyq_year")
    def pyq_years(self, obj):
        years = []
        for a in (obj.appearances or []):
            y = a.get("year")
            if y and y not in years:
                years.append(y)
        if not years and obj.pyq_year:      # fallback for rows without appearances
            years = [obj.pyq_year]
        return ", ".join(str(y) for y in sorted(years)) or "-"

    @admin.display(description="APPEARANCES")
    def appearances_display(self, obj):
        rows = []
        for a in (obj.appearances or []):
            extra = " ".join(x for x in [(a.get("session") or "").strip(),
                                         (a.get("paper") or "").strip()] if x)
            year = f"{a.get('year')} ({extra})" if extra else a.get("year")
            qn = a.get("question_number")
            rows.append((a.get("exam_name") or "", year, f"Q{qn}" if qn not in (None, "") else ""))
        if not rows:
            return "-"
        return format_html_join("", "<div>{} | {} | {}</div>", rows)

class SchoolExamCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_id','exam_type', 'category_name', 'description')
    search_fields = ('category_name',)

class EntranceExamCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_id','exam_type', 'category_name', 'description')
    search_fields = ('category_name',)

class JobExamCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_id','exam_type', 'category_name', 'description')
    search_fields = ('category_name',)

class ChapterAdmin(admin.ModelAdmin):
    list_display = ('chapter_id','subject', 'chapter_name', 'chapter_order', 'is_active')
    search_fields = ('chapter_name',)

class QuestionChapterMappingAdmin(admin.ModelAdmin):
    list_display = ('mapping_id','question', 'chapter', 'is_primary', 'source', 'confidence')
    search_fields = ('question__question_text',)

# Register your models here.
admin.site.register(Exam, ExamAdmin)
admin.site.register(Subject)
admin.site.register(Chapter, ChapterAdmin)
admin.site.register(Question,QuestionAdmin)
admin.site.register(QuestionOption)
admin.site.register(Solution)
admin.site.register(CorrectAnswer)
admin.site.register(MockExam, MockExamAdmin)
admin.site.register(SchoolExamCategory,SchoolExamCategoryAdmin)
admin.site.register(EntranceExamCategory,EntranceExamCategoryAdmin)
admin.site.register(JobExamCategory,JobExamCategoryAdmin)
admin.site.register(QuestionChapterMapping,QuestionChapterMappingAdmin)