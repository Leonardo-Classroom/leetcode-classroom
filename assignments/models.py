from django.conf import settings
from django.db import models

from accounts.models import Student
from problems.models import Problem


class Assignment(models.Model):
    title = models.CharField("任務標題", max_length=255)
    problem = models.ForeignKey(Problem, on_delete=models.PROTECT, related_name="assignments")
    description = models.TextField("說明", blank=True)
    due_at = models.DateTimeField("截止時間")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    students = models.ManyToManyField(Student, related_name="assignments")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="submissions")
    version = models.PositiveIntegerField()
    code = models.TextField()
    language = models.CharField(max_length=32, default="plaintext")
    original_filename = models.CharField(max_length=255, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        unique_together = ("assignment", "student", "version")

    def __str__(self):
        return f"{self.assignment} - {self.student} v{self.version}"

    def save(self, *args, **kwargs):
        if self.version is None:
            last = (
                Submission.objects.filter(assignment=self.assignment, student=self.student)
                .order_by("-version")
                .first()
            )
            self.version = (last.version + 1) if last else 1
        super().save(*args, **kwargs)


class AIReview(models.Model):
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name="ai_review")
    content = models.TextField("AI 評語", blank=True)
    score = models.PositiveSmallIntegerField("分數", null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI 評價 - {self.submission}"
