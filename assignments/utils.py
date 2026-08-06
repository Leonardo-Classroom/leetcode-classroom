from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone


@dataclass
class SubmissionStatus:
    state: str  # "not_submitted" | "on_time" | "late"
    latest_submission: object | None
    version_count: int
    late_by: timedelta | None

    @property
    def late_by_display(self) -> str:
        return format_timedelta(self.late_by) if self.late_by else ""


def format_timedelta(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60

    parts = []
    if days:
        parts.append(f"{days}天")
    if hours or (days and minutes):
        parts.append(f"{hours}小時")
    if not days and not hours:
        parts.append(f"{minutes}分鐘")
    return "".join(parts) or "不到1分鐘"


def get_submission_status(assignment, student, submissions=None):
    """
    依「最新一筆 Submission」的繳交時間與 assignment.due_at 比較判斷狀態。
    submissions 可傳入已排序(依 version 遞減)的 list，避免重複查詢。
    """
    if submissions is None:
        submissions = list(
            assignment.submissions.filter(student=student).order_by("-version")
        )

    if not submissions:
        return SubmissionStatus(state="not_submitted", latest_submission=None, version_count=0, late_by=None)

    latest = submissions[0]
    if latest.submitted_at <= assignment.due_at:
        return SubmissionStatus(
            state="on_time", latest_submission=latest, version_count=len(submissions), late_by=None
        )

    late_by = latest.submitted_at - assignment.due_at
    return SubmissionStatus(
        state="late", latest_submission=latest, version_count=len(submissions), late_by=late_by
    )


def is_overdue_no_submission(assignment):
    return timezone.now() > assignment.due_at
