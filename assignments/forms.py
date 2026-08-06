from django import forms

from accounts.forms import BootstrapFormMixin
from accounts.models import Student

from .models import AIReview


class StudentMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class AssignmentCreateForm(BootstrapFormMixin, forms.Form):
    title = forms.CharField(label="任務標題", max_length=255)
    description = forms.CharField(label="說明", widget=forms.Textarea, required=False)
    due_at = forms.DateTimeField(
        label="截止時間",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    students = StudentMultipleChoiceField(
        label="指派學員",
        queryset=Student.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )


class SubmissionForm(BootstrapFormMixin, forms.Form):
    code = forms.CharField(
        label="程式碼",
        widget=forms.Textarea(attrs={"class": "form-control font-monospace", "rows": 16, "id": "id_code"}),
    )
    language = forms.CharField(
        label="語言",
        max_length=32,
        required=False,
        initial="python",
        widget=forms.Select(
            choices=[
                ("python", "Python"),
                ("java", "Java"),
                ("cpp", "C++"),
                ("c", "C"),
                ("csharp", "C#"),
                ("javascript", "JavaScript"),
                ("typescript", "TypeScript"),
                ("go", "Go"),
                ("rust", "Rust"),
                ("kotlin", "Kotlin"),
                ("swift", "Swift"),
                ("ruby", "Ruby"),
                ("php", "PHP"),
            ],
            attrs={"id": "id_language"},
        ),
    )
    original_filename = forms.CharField(max_length=255, required=False, widget=forms.HiddenInput)


class AIReviewForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = AIReview
        fields = ["content", "score"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 5}),
        }
        labels = {"content": "AI 評語", "score": "分數 (0-100)"}
