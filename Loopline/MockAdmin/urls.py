from django.urls import path
from .views import (
    MockExamStatsView, MockExamToggleStatusView, QuestionListView, SubmitAnswersView,AdminSessionUserView,
    SubjectListView, ChapterListView, ExamListView, ExamDetailView, CustomQuestionListView,
    ExamTypeListView, ExamCategoryListView, EducationLevelListView,
    StreamListView, FieldListView, SubFieldListView, BoardListView,OptionListView,
    StateListView, ExamLevelListView, JobCategoryListView,ExamFilterView,MockExamListView,MockExamDetailView,
    DashboardStatsView, RecentExamsView, ExamDistributionView, ExamTrendView,
    RecentTestActivityView,BulkUploadValidateView,BulkUploadImportView,BulkUploadTemplateView,AddQuestionView,
    QuestionBankBulkUploadValidateView,QuestionBankBulkUploadImportView,
    CheckDuplicateQuestionView, PyqPdfUploadView, PyqPaperDetailsView, PyqQuestionsListView,
    PyqQuestionDetailView, PyqCreateTestView,auto_map_questions_to_chapters,update_question_chapter,PyqAddToTestView,PyqTargetTestsView,
    PyqChaptersForSubjectView,PyqStatsView, PyqTestListView
)

urlpatterns = [
    path("admin/session-user/", AdminSessionUserView.as_view(), name="admin-session-user"),
    # ── Exams & Question bank (existing) ──
    path('exams/', ExamListView.as_view(), name='exam-list'),          # GET (list), POST (create)
    path('exams/<int:exam_id>/', ExamDetailView.as_view(), name='exam-detail'),  # GET/PUT/PATCH (single exam)
    path('mockexams/', MockExamListView.as_view(), name='mockexam-list'),
    path('mockexams/<int:mockexam_id>/', MockExamDetailView.as_view()),
    path('mockexams/stats/', MockExamStatsView.as_view(), name='mockexam-stats'),
    path('mockexams/<int:mockexam_id>/toggle-status/', MockExamToggleStatusView.as_view()),
    path('mockexams/<int:mockexam_id>/bulk-upload/validate/',BulkUploadValidateView.as_view(),name='bulk-upload-validate',),
    path('mockexams/<int:mockexam_id>/bulk-upload/import/',BulkUploadImportView.as_view(),name='bulk-upload-import'),
    path('bulk-upload/template/',BulkUploadTemplateView.as_view(),name='bulk-upload-template'),
    
    # ── Question Bank bulk upload (separate from mock-exam bulk upload above) ──
    path('exams/<int:exam_id>/question-bank/bulk-upload/validate/', QuestionBankBulkUploadValidateView.as_view(), name='qb-bulk-upload-validate'),
    path('exams/<int:exam_id>/question-bank/bulk-upload/import/', QuestionBankBulkUploadImportView.as_view(), name='qb-bulk-upload-import'),

     # ── PYQ PDF import wizard (Upload PDF → Map Paper Details → Review Questions → Create Test) ──
    path('exams/<int:exam_id>/pyq-import/upload/', PyqPdfUploadView.as_view(), name='pyq-import-upload'),
    path('pyq-import/<str:upload_id>/paper-details/', PyqPaperDetailsView.as_view(), name='pyq-import-paper-details'),
    path('pyq-import/<str:upload_id>/questions/', PyqQuestionsListView.as_view(), name='pyq-import-questions'),
    path('pyq-import/<str:upload_id>/questions/<int:index>/', PyqQuestionDetailView.as_view(), name='pyq-import-question-detail'),
    path('pyq-import/<str:upload_id>/create-test/', PyqCreateTestView.as_view(), name='pyq-import-create-test'),
    path('pyq-import/<str:upload_id>/auto-map-chapters/', auto_map_questions_to_chapters),
    path('pyq-import/<str:upload_id>/questions/<int:question_index>/chapter/', update_question_chapter),
    path('pyq-import/<str:upload_id>/add-to-test/', PyqAddToTestView.as_view(), name='pyq-import-add-to-test'),
    path('pyq-import/<str:upload_id>/target-tests/', PyqTargetTestsView.as_view(), name='pyq-import-target-tests'),
    path('pyq-import/<str:upload_id>/chapters-for-subject/', PyqChaptersForSubjectView.as_view(), name='pyq-import-chapters-for-subject'),
    path('pyq/stats/',  PyqStatsView.as_view(),    name='pyq-stats'),
    path('pyq/tests/',  PyqTestListView.as_view(),  name='pyq-tests'),

    path('subjects/', SubjectListView.as_view(), name='subject-list'),
    path('chapters/', ChapterListView.as_view(), name='chapter-list'),
    path('questions/add/', AddQuestionView.as_view(), name='question-add'),
    path('questions/check-duplicate/', CheckDuplicateQuestionView.as_view(), name='question-check-duplicate'),
    path('questions/', QuestionListView.as_view(), name='question-list'),
    path('options/', OptionListView.as_view(), name='option-list'),
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

     # ── Admin Dashboard (mirrors adminDummyData.ts shape) ──
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/recent-exams/', RecentExamsView.as_view(), name='dashboard-recent-exams'),
    path('dashboard/exam-distribution/', ExamDistributionView.as_view(), name='dashboard-exam-distribution'),
    path('dashboard/exam-trend/', ExamTrendView.as_view(), name='dashboard-exam-trend'),
    path('dashboard/recent-tests/', RecentTestActivityView.as_view(), name='dashboard-recent-tests'),
]