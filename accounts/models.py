from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_next_student_id(year=None):
    """
    格式：s + 民國註冊年(3碼) + 該年度流水號(5碼)，例如 s11500001。
    民國年 = 西元年 - 1911。流水號每年從 00001 重新開始算。
    """
    roc_year = (year or timezone.now().year) - 1911
    prefix = f"s{roc_year:03d}"

    last = Student.objects.filter(student_id__startswith=prefix).order_by("-student_id").first()
    next_seq = int(last.student_id[len(prefix):]) + 1 if last else 1
    return f"{prefix}{next_seq:05d}"


class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student")
    student_id = models.CharField("學號", max_length=32, unique=True)
    name = models.CharField("姓名", max_length=64)
    class_name = models.CharField("班級", max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["student_id"]

    def __str__(self):
        return f"{self.student_id} {self.name}"
