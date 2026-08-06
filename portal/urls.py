from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("assignments/<int:pk>/", views.assignment_detail, name="assignment_detail"),
    path("problems/", views.problem_list, name="problem_list"),
]
