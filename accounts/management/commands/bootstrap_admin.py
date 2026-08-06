from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "非互動建立第一個管理員帳號（若帳號已存在則只重設密碼）"

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin")
        parser.add_argument("--password", default="admin12345")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        user, created = User.objects.get_or_create(
            username=username, defaults={"is_staff": True, "is_superuser": True}
        )
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        action = "建立" if created else "更新"
        self.stdout.write(self.style.SUCCESS(f"已{action}管理員帳號：{username} / {password}"))
