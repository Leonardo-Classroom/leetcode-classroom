from django.urls import path

from . import views

app_name = "adminpanel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("students/", views.student_list, name="student_list"),
    path("students/new/", views.student_create, name="student_create"),
    path("students/<int:pk>/reset-password/", views.student_reset_password, name="student_reset_password"),
    path("problems/", views.problem_picker, name="problem_picker"),
    path("assignments/new/", views.assignment_create, name="assignment_create"),
    path("assignments/<int:pk>/", views.assignment_detail, name="assignment_detail"),
    path("submissions/<int:pk>/", views.submission_detail, name="submission_detail"),
    path("settings/email/", views.email_settings, name="email_settings"),
    path("settings/email/test/", views.email_settings_test, name="email_settings_test"),
]
