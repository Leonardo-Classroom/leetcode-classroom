from django.contrib import admin

from .models import AIReview, Assignment, Submission


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "problem", "due_at", "created_by", "created_at")
    filter_horizontal = ("students",)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "version", "language", "submitted_at")
    list_filter = ("language",)


@admin.register(AIReview)
class AIReviewAdmin(admin.ModelAdmin):
    list_display = ("submission", "score", "updated_at")
