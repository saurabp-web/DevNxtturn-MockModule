from rest_framework import serializers
from MockAdmin.models import Exam

class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ['exam_id', 'exam_name', 'exam_year', 'conducting_body']