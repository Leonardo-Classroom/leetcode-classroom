from django.contrib import admin

from .models import Problem, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("number", "title", "difficulty", "ac_rate")
    list_filter = ("difficulty",)
    search_fields = ("title", "number")
    autocomplete_fields = ("tags",)
