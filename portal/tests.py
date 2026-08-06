from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Student
from assignments.models import Assignment, Submission
from problems.models import Problem


class PortalTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin1", password="pass12345", is_staff=True)
        self.stu_user = User.objects.create_user("stu1", password="pass12345")
        self.student = Student.objects.create(user=self.stu_user, student_id="S001", name="小明")
        self.other_user = User.objects.create_user("stu2", password="pass12345")
        self.other_student = Student.objects.create(user=self.other_user, student_id="S002", name="小華")

        self.problem = Problem.objects.create(
            number=1, title="Two Sum", title_slug="two-sum", url="https://leetcode.com/problems/two-sum/",
            difficulty="Easy", ac_rate="57.95",
        )
        self.problem2 = Problem.objects.create(
            number=2, title="Add Two Numbers", title_slug="add-two-numbers",
            url="https://leetcode.com/problems/add-two-numbers/", difficulty="Medium", ac_rate="49.05",
        )
        self.assignment = Assignment.objects.create(
            title="作業一", problem=self.problem, due_at=timezone.now() + timedelta(days=1)
        )
        self.assignment.students.add(self.student)

    def test_admin_cannot_access_portal(self):
        self.client.login(username="admin1", password="pass12345")
        resp = self.client.get(reverse("portal:dashboard"))
        self.assertEqual(resp.status_code, 403)

    def test_student_sees_own_assignment(self):
        self.client.login(username="stu1", password="pass12345")
        resp = self.client.get(reverse("portal:dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "作業一")

    def test_student_cannot_view_assignment_not_assigned_to_them(self):
        self.client.login(username="stu2", password="pass12345")
        resp = self.client.get(reverse("portal:assignment_detail", args=[self.assignment.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_student_can_upload_multiple_versions(self):
        self.client.login(username="stu1", password="pass12345")
        url = reverse("portal:assignment_detail", args=[self.assignment.pk])
        self.client.post(url, {"code": "print(1)", "language": "python", "original_filename": "a.py"})
        self.client.post(url, {"code": "print(2)", "language": "python", "original_filename": "a.py"})
        submissions = Submission.objects.filter(assignment=self.assignment, student=self.student)
        self.assertEqual(submissions.count(), 2)
        self.assertEqual(set(submissions.values_list("version", flat=True)), {1, 2})

    def test_admin_cannot_access_portal_problem_list(self):
        self.client.login(username="admin1", password="pass12345")
        resp = self.client.get(reverse("portal:problem_list"))
        self.assertEqual(resp.status_code, 403)

    def test_student_can_browse_problem_list(self):
        self.client.login(username="stu1", password="pass12345")
        resp = self.client.get(reverse("portal:problem_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Two Sum")
        self.assertContains(resp, "Add Two Numbers")
        self.assertNotContains(resp, "派任務")

    def test_student_can_filter_problem_list(self):
        self.client.login(username="stu1", password="pass12345")
        resp = self.client.get(reverse("portal:problem_list"), {"difficulty": "Medium"})
        self.assertContains(resp, "Add Two Numbers")
        self.assertNotContains(resp, "Two Sum")
