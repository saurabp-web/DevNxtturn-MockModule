from django.urls import path
from .views import (
    QuestionListView, SubmitAnswersView,
    SubjectListView, ChapterListView, ExamListView, CustomQuestionListView,
    ExamTypeListView, ExamCategoryListView, EducationLevelListView,
    StreamListView, FieldListView, SubFieldListView, BoardListView,
    StateListView, ExamLevelListView, JobCategoryListView,ExamFilterView
)

urlpatterns = [
    # ── Exams & Question bank (existing) ──
    path('exams/', ExamListView.as_view(), name='exam-list'),
    path('subjects/', SubjectListView.as_view(), name='subject-list'),
    path('chapters/', ChapterListView.as_view(), name='chapter-list'),
    path('questions/', QuestionListView.as_view(), name='question-list'),
    path('questions/custom/', CustomQuestionListView.as_view(), name='question-custom-list'),
    path('questions/submit/', SubmitAnswersView.as_view(), name='question-submit'),

    # ── Apply Filters dropdowns (new) ──
    # path('filters/options/', FilterOptionsView.as_view(), name='filter-options'),
    path('exams/filter/', ExamFilterView.as_view(), name='exam-filter'),
    path('filters/exam-types/', ExamTypeListView.as_view(), name='filter-exam-types'),
    path('filters/exam-categories/', ExamCategoryListView.as_view(), name='filter-exam-categories'),
    path('filters/education-levels/', EducationLevelListView.as_view(), name='filter-education-levels'),
    path('filters/streams/', StreamListView.as_view(), name='filter-streams'),
    path('filters/fields/', FieldListView.as_view(), name='filter-fields'),
    path('filters/sub-fields/', SubFieldListView.as_view(), name='filter-sub-fields'),
    path('filters/boards/', BoardListView.as_view(), name='filter-boards'),
    path('filters/states/', StateListView.as_view(), name='filter-states'),
    path('filters/exam-levels/', ExamLevelListView.as_view(), name='filter-exam-levels'),
    path('filters/job-categories/', JobCategoryListView.as_view(), name='filter-job-categories'),
]