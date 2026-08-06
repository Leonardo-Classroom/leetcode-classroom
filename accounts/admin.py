from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "name", "class_name", "user")
    search_fields = ("student_id", "name", "user__username")
