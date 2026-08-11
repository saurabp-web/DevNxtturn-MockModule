from django.db import models
from django.contrib.auth.models import User
from MockAdmin.models import Question,TestSession
from django.conf import settings
from datetime import timezone
from django.utils import timezone

# Create your models here.
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=150)
    avatar_url = models.URLField(blank=True)

    class Meta:
        db_table = 'mockups_student'
 
    def __str__(self):
        return self.name
    

class StudentSubmission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    student_answer = models.TextField()
    is_correct = models.BooleanField(default=False)
    teacher_feedback = models.TextField(blank=True, null=True)
    reviewed = models.BooleanField(default=False)

    class Meta:
        db_table = 'mockups_studentsubmission'


class UserQuestionAttempt(models.Model):
    attempt_id = models.AutoField(primary_key=True)
    session = models.ForeignKey(
        TestSession,
        on_delete=models.CASCADE,
        db_column='session_id',
        null=True,      # ← add this
        blank=True,     # ← add this
        related_name='student_attempts'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        db_column='question_id',
        related_name='student_attempts'
    )
    selected_option_id = models.CharField(max_length=10, null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    time_taken_seconds = models.IntegerField(null=True, blank=True)
    attempted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'user_question_attempts'
        indexes = [
            models.Index(fields=['session']),
            models.Index(fields=['session', 'question']),
        ]


