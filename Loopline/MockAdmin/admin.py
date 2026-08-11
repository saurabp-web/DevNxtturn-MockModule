from django.contrib import admin
from MockAdmin.models import *


class ExamAdmin(admin.ModelAdmin):
    # CHANGED: education_level / stream are now ManyToManyFields (see
    # models.py). M2M fields can't be put directly in list_display (Django
    # can't render a "column" for a to-many relation), so a small method
    # renders them as a comma-joined string instead. list_filter DOES
    # support M2M out of the box, so those just needed the new field name.
    list_display = ('exam_name', 'exam_code', 'education_level_list', 'level', 'exam_type')
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
    search_fields = ('exam__mockexam_name',)

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_id', 'exam', 'chapter', 'question_text', 'question_type')
    search_fields = ('question_text',)
    

# Register your models here.
admin.site.register(Exam, ExamAdmin)
admin.site.register(Subject)
admin.site.register(Chapter)
admin.site.register(Question,QuestionAdmin)
admin.site.register(QuestionOption)
admin.site.register(Solution)
admin.site.register(CorrectAnswer)
admin.site.register(MockExam, MockExamAdmin)