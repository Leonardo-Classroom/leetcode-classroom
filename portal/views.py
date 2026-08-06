from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import student_required
from assignments.forms import SubmissionForm
from assignments.models import Assignment, Submission
from assignments.utils import get_submission_status
from problems.views import render_problem_browser


@student_required
def dashboard(request):
    student = request.user.student
    assignments = (
        Assignment.objects.filter(students=student)
        .select_related("problem")
        .prefetch_related("submissions")
        .order_by("-created_at")
    )

    rows = []
    for assignment in assignments:
        subs = sorted(
            [s for s in assignment.submissions.all() if s.student_id == student.id],
            key=lambda s: -s.version,
        )
        status = get_submission_status(assignment, student, submissions=subs)
        rows.append({"assignment": assignment, "status": status})

    return render(request, "portal/dashboard.html", {"rows": rows})


@student_required
def assignment_detail(request, pk):
    student = request.user.student
    assignment = get_object_or_404(
        Assignment.objects.select_related("problem"), pk=pk, students=student
    )
    submissions = list(
        assignment.submissions.filter(student=student).select_related().order_by("-version")
    )
    status = get_submission_status(assignment, student, submissions=submissions)

    if request.method == "POST":
        form = SubmissionForm(request.POST)
        if form.is_valid():
            Submission.objects.create(
                assignment=assignment,
                student=student,
                code=form.cleaned_data["code"],
                language=form.cleaned_data["language"] or "plaintext",
                original_filename=form.cleaned_data["original_filename"],
            )
            messages.success(request, "已上傳新版本")
            return redirect("portal:assignment_detail", pk=assignment.pk)
    else:
        form = SubmissionForm()

    return render(
        request,
        "portal/assignment_detail.html",
        {
            "assignment": assignment,
            "submissions": submissions,
            "status": status,
            "form": form,
        },
    )


@student_required
def problem_list(request):
    return render_problem_browser(request, "portal/problem_list.html", show_assign_action=False)
