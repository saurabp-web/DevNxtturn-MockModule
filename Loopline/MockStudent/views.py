from rest_framework import viewsets
from MockAdmin.models import Exam
from .serializers import ExamSerializer

class StudentExamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    # Add django-filter support here for the Sidebar filters
    filterset_fields = ['exam_category', 'exam_year']