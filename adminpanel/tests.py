from datetime import timedelta
from email.header import decode_header
from email.utils import parseaddr

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Student
from assignments.models import Assignment
from problems.models import Problem

from .email_backend import get_default_from_email
from .models import EmailSettings


def decode_display_name(formatted_address):
    """把 formataddr() 可能做過 RFC 2047 MIME 編碼的顯示名稱還原成原始文字，方便測試比對。"""
    name, addr = parseaddr(formatted_address)
    decoded_parts = decode_header(name)
    text = "".join(
        part.decode(enc or "utf-8") if isinstance(part, bytes) else part
        for part, enc in decoded_parts
    )
    return text, addr


class PanelAccessTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("admin1", password="pass12345", is_staff=True)
        self.stu_user = User.objects.create_user("stu1", password="pass12345")
        self.student = Student.objects.create(user=self.stu_user, student_id="S001", name="小明")

    def test_student_cannot_access_panel(self):
        self.client.login(username="stu1", password="pass12345")
        resp = self.client.get(reverse("adminpanel:dashboard"))
        self.assertEqual(resp.status_code, 403)

    def test_anonymous_redirected_to_login(self):
        resp = self.client.get(reverse("adminpanel:dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp.url)

    def test_admin_can_access_panel_dashboard(self):
        self.client.login(username="admin1", password="pass12345")
        resp = self.client.get(reverse("adminpanel:dashboard"))
        self.assertEqual(resp.status_code, 200)

    def test_admin_can_create_student(self):
        self.client.login(username="admin1", password="pass12345")
        resp = self.client.post(
            reverse("adminpanel:student_create"),
            {"email": "stu2@example.com", "name": "小華", "class_name": "資工三甲"},
        )
        self.assertEqual(resp.status_code, 302)
        student = Student.objects.get(user__email="stu2@example.com")
        self.assertEqual(student.user.username, "stu2@example.com")
        self.assertFalse(student.user.has_usable_password())
        roc_year = timezone.now().year - 1911
        self.assertTrue(student.student_id.startswith(f"s{roc_year:03d}"))

    def test_admin_can_reset_student_password(self):
        self.client.login(username="admin1", password="pass12345")
        resp = self.client.post(
            reverse("adminpanel:student_reset_password", args=[self.student.pk]),
            {"new_password1": "newpass12345", "new_password2": "newpass12345"},
        )
        self.assertEqual(resp.status_code, 302)
        self.stu_user.refresh_from_db()
        self.assertTrue(self.stu_user.check_password("newpass12345"))

    def test_admin_can_create_assignment_via_picker(self):
        problem = Problem.objects.create(
            number=1, title="Two Sum", title_slug="two-sum", url="https://leetcode.com/problems/two-sum/",
            difficulty="Easy", ac_rate="57.95",
        )
        self.client.login(username="admin1", password="pass12345")
        due = (timezone.now() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M")
        resp = self.client.post(
            f"{reverse('adminpanel:assignment_create')}?problem_id={problem.id}",
            {
                "problem_id": problem.id,
                "title": "作業一",
                "description": "",
                "due_at": due,
                "students": [self.student.id],
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Assignment.objects.filter(title="作業一").exists())


class EmailSettingsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            "admin1", password="pass12345", is_staff=True, email="admin1@example.com"
        )
        self.stu_user = User.objects.create_user("stu1", password="pass12345")
        Student.objects.create(user=self.stu_user, student_id="S001", name="小明")

    def test_singleton_get_solo_reuses_same_row(self):
        first = EmailSettings.get_solo()
        second = EmailSettings.get_solo()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(EmailSettings.objects.count(), 1)

    def test_not_configured_by_default(self):
        config = EmailSettings.get_solo()
        self.assertFalse(config.is_configured)

    def test_student_cannot_access_email_settings(self):
        self.client.login(username="stu1", password="pass12345")
        resp = self.client.get(reverse("adminpanel:email_settings"))
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_save_email_settings(self):
        self.client.login(username="admin1", password="pass12345")
        resp = self.client.post(
            reverse("adminpanel:email_settings"),
            {
                "host": "smtp.example.com",
                "port": "587",
                "username": "sender@example.com",
                "password": "secret123",
                "use_tls": "on",
                "from_email": "LeetCode <noreply@example.com>",
            },
        )
        self.assertEqual(resp.status_code, 302)
        config = EmailSettings.get_solo()
        self.assertTrue(config.is_configured)
        self.assertEqual(config.password, "secret123")
        self.assertEqual(config.updated_by, self.admin)
        self.assertEqual(get_default_from_email(), "LeetCode <noreply@example.com>")

    def test_bare_display_name_is_combined_with_username(self):
        """from_email 只填顯示名稱時，自動用 username 組成合法寄件位址（避免 SMTP local-part 非 ASCII 錯誤）。"""
        self.client.login(username="admin1", password="pass12345")
        resp = self.client.post(
            reverse("adminpanel:email_settings"),
            {
                "host": "smtp.example.com",
                "port": "587",
                "username": "bot@example.com",
                "password": "secret123",
                "use_tls": "on",
                "from_email": "李奧納多小教室",
            },
        )
        self.assertEqual(resp.status_code, 302)
        config = EmailSettings.get_solo()
        name, addr = decode_display_name(config.from_email)
        self.assertEqual((name, addr), ("李奧納多小教室", "bot@example.com"))
        name, addr = decode_display_name(get_default_from_email())
        self.assertEqual((name, addr), ("李奧納多小教室", "bot@example.com"))

    def test_bare_display_name_without_username_rejected(self):
        self.client.login(username="admin1", password="pass12345")
        resp = self.client.post(
            reverse("adminpanel:email_settings"),
            {
                "host": "smtp.example.com",
                "port": "587",
                "username": "",
                "password": "secret123",
                "use_tls": "on",
                "from_email": "李奧納多小教室",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "帳號")

    def test_invalid_email_in_angle_brackets_rejected(self):
        self.client.login(username="admin1", password="pass12345")
        resp = self.client.post(
            reverse("adminpanel:email_settings"),
            {
                "host": "smtp.example.com",
                "port": "587",
                "username": "bot@example.com",
                "password": "secret123",
                "use_tls": "on",
                "from_email": "李奧納多小教室 <not-an-email>",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(EmailSettings.objects.filter(from_email="李奧納多小教室 <not-an-email>").exists())

    def test_get_default_from_email_repairs_pre_existing_bad_data(self):
        """模擬修 bug 前就已經存進 DB 的壞資料：from_email 只有名稱，沒有 email。"""
        config = EmailSettings.get_solo()
        config.host, config.username, config.password = "smtp.example.com", "bot@example.com", "x"
        config.from_email = "李奧納多小教室"
        config.save()
        name, addr = decode_display_name(get_default_from_email())
        self.assertEqual((name, addr), ("李奧納多小教室", "bot@example.com"))

    def test_blank_password_does_not_overwrite_existing(self):
        config = EmailSettings.get_solo()
        config.host, config.username, config.password = "smtp.example.com", "u", "keepme123"
        config.save()

        self.client.login(username="admin1", password="pass12345")
        self.client.post(
            reverse("adminpanel:email_settings"),
            {
                "host": "smtp.example.com",
                "port": "587",
                "username": "u",
                "password": "",  # 留空 -> 不應覆蓋
                "use_tls": "on",
                "from_email": "",
            },
        )
        config.refresh_from_db()
        self.assertEqual(config.password, "keepme123")

    def test_send_test_email_view_sends_to_given_address(self):
        self.client.login(username="admin1", password="pass12345")
        resp = self.client.post(
            reverse("adminpanel:email_settings_test"), {"to_email": "check@example.com"}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("check@example.com", mail.outbox[0].to)


class ConfigurableEmailBackendTests(TestCase):
    """直接測試 backend 選擇邏輯：不透過 Django 測試環境的 locmem override。"""

    def test_falls_back_to_fallback_backend_when_not_configured(self):
        from django.core.mail.backends.console import EmailBackend as ConsoleBackend

        from .email_backend import ConfigurableEmailBackend

        backend = ConfigurableEmailBackend()
        self.assertIsInstance(backend._connection, ConsoleBackend)

    def test_uses_smtp_when_db_configured(self):
        from django.core.mail.backends.smtp import EmailBackend as SMTPBackend

        from .email_backend import ConfigurableEmailBackend

        config = EmailSettings.get_solo()
        config.host, config.username, config.password = "smtp.example.com", "u", "p"
        config.port = 2525
        config.save()

        backend = ConfigurableEmailBackend()
        self.assertIsInstance(backend._connection, SMTPBackend)
        self.assertEqual(backend._connection.host, "smtp.example.com")
        self.assertEqual(backend._connection.port, 2525)
