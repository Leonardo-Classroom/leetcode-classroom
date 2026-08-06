from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .forms import StudentCreateForm
from .models import Student, generate_next_student_id


class StudentCreateFormTests(TestCase):
    def test_creates_user_and_student_with_unusable_password(self):
        form = StudentCreateForm(
            data={"email": "stu1@example.com", "name": "小明", "class_name": "資工三甲"}
        )
        self.assertTrue(form.is_valid(), form.errors)
        student = form.save()
        user = User.objects.get(username="stu1@example.com")
        self.assertEqual(user.email, "stu1@example.com")
        self.assertEqual(user.username, "stu1@example.com")
        self.assertFalse(user.has_usable_password())

        roc_year = timezone.now().year - 1911
        self.assertEqual(student.student_id, f"s{roc_year:03d}00001")

    def test_duplicate_email_rejected(self):
        User.objects.create_user("dup@example.com", password="x", email="dup@example.com")
        form = StudentCreateForm(data={"email": "dup@example.com", "name": "小新"})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_student_id_sequence_increments_within_same_year(self):
        f1 = StudentCreateForm(data={"email": "a@example.com", "name": "甲"})
        self.assertTrue(f1.is_valid(), f1.errors)
        s1 = f1.save()

        f2 = StudentCreateForm(data={"email": "b@example.com", "name": "乙"})
        self.assertTrue(f2.is_valid(), f2.errors)
        s2 = f2.save()

        roc_year = timezone.now().year - 1911
        self.assertEqual(s1.student_id, f"s{roc_year:03d}00001")
        self.assertEqual(s2.student_id, f"s{roc_year:03d}00002")


class GenerateNextStudentIdTests(TestCase):
    def test_format(self):
        sid = generate_next_student_id(year=2026)
        self.assertEqual(sid, "s11500001")

    def test_increments(self):
        user = User.objects.create_user("u1", password="x")
        Student.objects.create(user=user, student_id="s11500001", name="舊生")
        self.assertEqual(generate_next_student_id(year=2026), "s11500002")

    def test_resets_for_a_different_year(self):
        user = User.objects.create_user("u1", password="x")
        Student.objects.create(user=user, student_id="s11500007", name="舊生")
        self.assertEqual(generate_next_student_id(year=2027), "s11600001")
