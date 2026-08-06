from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from accounts.models import Student
from problems.models import Problem

from .models import AIReview, Assignment, Submission
from .utils import format_timedelta, get_submission_status


class SubmissionVersioningTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("stu1", password="pass12345")
        self.student = Student.objects.create(user=self.user, student_id="S001", name="小明")
        self.problem = Problem.objects.create(
            number=1, title="Two Sum", title_slug="two-sum", url="https://leetcode.com/problems/two-sum/",
            difficulty="Easy", ac_rate="57.95",
        )
        self.assignment = Assignment.objects.create(
            title="作業一", problem=self.problem, due_at=timezone.now() + timedelta(days=1)
        )
        self.assignment.students.add(self.student)

    def test_version_auto_increments(self):
        s1 = Submission.objects.create(assignment=self.assignment, student=self.student, code="a")
        s2 = Submission.objects.create(assignment=self.assignment, student=self.student, code="b")
        self.assertEqual(s1.version, 1)
        self.assertEqual(s2.version, 2)

    def test_status_not_submitted(self):
        status = get_submission_status(self.assignment, self.student)
        self.assertEqual(status.state, "not_submitted")

    def test_status_on_time(self):
        Submission.objects.create(assignment=self.assignment, student=self.student, code="a")
        status = get_submission_status(self.assignment, self.student)
        self.assertEqual(status.state, "on_time")

    def test_status_late(self):
        past_assignment = Assignment.objects.create(
            title="遲交測試", problem=self.problem, due_at=timezone.now() - timedelta(days=2)
        )
        past_assignment.students.add(self.student)
        Submission.objects.create(assignment=past_assignment, student=self.student, code="a")
        status = get_submission_status(past_assignment, self.student)
        self.assertEqual(status.state, "late")
        self.assertIsNotNone(status.late_by)
        self.assertIn("天", status.late_by_display)

    def test_ai_review_optional(self):
        submission = Submission.objects.create(assignment=self.assignment, student=self.student, code="a")
        self.assertFalse(hasattr(submission, "ai_review"))
        AIReview.objects.create(submission=submission, content="寫得不錯", score=90)
        submission.refresh_from_db()
        self.assertEqual(submission.ai_review.score, 90)


class FormatTimedeltaTests(TestCase):
    def test_days_and_hours(self):
        self.assertEqual(format_timedelta(timedelta(days=2, hours=3)), "2天3小時")

    def test_minutes_only(self):
        self.assertEqual(format_timedelta(timedelta(minutes=30)), "30分鐘")
