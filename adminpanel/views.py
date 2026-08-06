from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import staff_required
from accounts.emails import send_invitation_email
from accounts.forms import StudentCreateForm, StyledSetPasswordForm
from accounts.models import Student
from assignments.emails import send_assignment_notifications
from assignments.forms import AIReviewForm, AssignmentCreateForm
from assignments.models import Assignment, Submission
from assignments.utils import get_submission_status
from problems.models import Problem
from problems.views import render_problem_browser

from .email_backend import get_default_from_email
from .forms import EmailSettingsForm, TestEmailForm
from .models import EmailSettings


@staff_required
def dashboard(request):
    assignments = (
        Assignment.objects.select_related("problem")
        .prefetch_related("students", "submissions")
        .order_by("-created_at")
    )

    rows = []
    total_not_submitted = 0
    total_late = 0
    for assignment in assignments:
        subs_by_student = {}
        for sub in assignment.submissions.all():
            subs_by_student.setdefault(sub.student_id, []).append(sub)

        counts = {"not_submitted": 0, "on_time": 0, "late": 0}
        students = list(assignment.students.all())
        for student in students:
            subs = sorted(subs_by_student.get(student.id, []), key=lambda s: -s.version)
            status = get_submission_status(assignment, student, submissions=subs)
            counts[status.state] += 1

        total = len(students)
        total_not_submitted += counts["not_submitted"]
        total_late += counts["late"]

        pct = {}
        for key in ("on_time", "late", "not_submitted"):
            pct[key] = round(counts[key] / total * 100, 1) if total else 0

        rows.append({"assignment": assignment, "total": total, "counts": counts, "pct": pct})

    context = {
        "student_count": Student.objects.count(),
        "assignment_count": assignments.count(),
        "total_not_submitted": total_not_submitted,
        "total_late": total_late,
        "rows": rows,
    }
    return render(request, "adminpanel/dashboard.html", context)


@staff_required
def student_list(request):
    students = Student.objects.select_related("user").all()
    return render(request, "adminpanel/student_list.html", {"students": students})


@staff_required
def student_create(request):
    if request.method == "POST":
        form = StudentCreateForm(request.POST)
        if form.is_valid():
            student = form.save()
            try:
                send_invitation_email(request, student)
                messages.success(request, "學員已建立，邀請信已寄出")
            except Exception:
                messages.warning(request, "學員已建立，但邀請信寄送失敗，請確認 Email 設定或改用「重設密碼」手動設定")
            return redirect("adminpanel:student_list")
    else:
        form = StudentCreateForm()
    return render(request, "adminpanel/student_form.html", {"form": form})


@staff_required
def student_reset_password(request, pk):
    student = get_object_or_404(Student.objects.select_related("user"), pk=pk)
    if request.method == "POST":
        form = StyledSetPasswordForm(student.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"已重設 {student.name} 的密碼")
            return redirect("adminpanel:student_list")
    else:
        form = StyledSetPasswordForm(student.user)
    return render(
        request, "adminpanel/student_reset_password.html", {"form": form, "student": student}
    )


@staff_required
def problem_picker(request):
    return render_problem_browser(request, "adminpanel/problem_picker.html", show_assign_action=True)


@staff_required
def assignment_create(request):
    problem_id = request.GET.get("problem_id") or request.POST.get("problem_id")
    if not problem_id:
        return redirect("adminpanel:problem_picker")
    problem = get_object_or_404(Problem, pk=problem_id)

    if request.method == "POST":
        form = AssignmentCreateForm(request.POST)
        if form.is_valid():
            assignment = Assignment.objects.create(
                title=form.cleaned_data["title"],
                problem=problem,
                description=form.cleaned_data["description"],
                due_at=form.cleaned_data["due_at"],
                created_by=request.user,
            )
            assignment.students.set(form.cleaned_data["students"])

            sent, failed = send_assignment_notifications(request, assignment)
            if failed and sent:
                messages.warning(request, f"任務已建立並指派，通知信已合併寄出給 {sent} 位學員，另有 {failed} 位因缺少 Email 或寄送異常未收到")
            elif failed and not sent:
                messages.warning(request, f"任務已建立並指派，但通知信寄送失敗或所有學員都缺少 Email（{failed} 位）")
            else:
                messages.success(request, f"任務已建立並指派，通知信已合併寄出給 {sent} 位學員")
            return redirect("adminpanel:assignment_detail", pk=assignment.pk)
    else:
        form = AssignmentCreateForm(initial={"title": f"{problem.title} 練習"})

    return render(
        request,
        "adminpanel/assignment_create.html",
        {"form": form, "problem": problem},
    )


@staff_required
def assignment_detail(request, pk):
    assignment = get_object_or_404(Assignment.objects.select_related("problem"), pk=pk)
    rows = []
    for student in assignment.students.all().order_by("student_id"):
        subs = list(assignment.submissions.filter(student=student).order_by("-version"))
        status = get_submission_status(assignment, student, submissions=subs)
        rows.append({"student": student, "status": status})
    return render(
        request,
        "adminpanel/assignment_detail.html",
        {"assignment": assignment, "rows": rows},
    )


@staff_required
def submission_detail(request, pk):
    submission = get_object_or_404(
        Submission.objects.select_related("assignment", "assignment__problem", "student"),
        pk=pk,
    )
    ai_review = getattr(submission, "ai_review", None)

    if request.method == "POST":
        form = AIReviewForm(request.POST, instance=ai_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.submission = submission
            review.updated_by = request.user
            review.save()
            messages.success(request, "AI 評價已更新")
            return redirect("adminpanel:submission_detail", pk=submission.pk)
    else:
        form = AIReviewForm(instance=ai_review)

    other_versions = submission.assignment.submissions.filter(student=submission.student).order_by("-version")

    return render(
        request,
        "adminpanel/submission_detail.html",
        {
            "submission": submission,
            "form": form,
            "other_versions": other_versions,
        },
    )


@staff_required
def email_settings(request):
    config = EmailSettings.get_solo()
    existing_password = config.password
    if request.method == "POST":
        form = EmailSettingsForm(request.POST, instance=config)
        if form.is_valid():
            obj = form.save(commit=False)
            new_password = form.cleaned_data.get("password")
            if not new_password:
                obj.password = existing_password
            obj.updated_by = request.user
            obj.save()
            messages.success(request, "Email 設定已更新")
            return redirect("adminpanel:email_settings")
    else:
        form = EmailSettingsForm(instance=config, initial={"password": ""})

    return render(
        request,
        "adminpanel/email_settings.html",
        {
            "form": form,
            "config": config,
            "test_form": TestEmailForm(initial={"to_email": request.user.email}),
            "fallback_backend": settings.FALLBACK_EMAIL_BACKEND,
        },
    )


@staff_required
def email_settings_test(request):
    if request.method == "POST":
        form = TestEmailForm(request.POST)
        if form.is_valid():
            try:
                send_mail(
                    "LeetCode 教學管理系統 － 測試信件",
                    "如果你收到這封信，代表 Email 設定正確可以正常寄信。",
                    get_default_from_email(),
                    [form.cleaned_data["to_email"]],
                )
                messages.success(request, f"測試信已寄出到 {form.cleaned_data['to_email']}")
            except Exception as exc:
                messages.error(request, f"寄送失敗：{exc}")
    return redirect("adminpanel:email_settings")
