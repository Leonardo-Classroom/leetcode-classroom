from django.conf import settings
from django.db import models


class EmailSettings(models.Model):
    """
    整個系統只會有一筆資料（singleton），透過後台頁面設定寄信用的 SMTP 資訊。
    如果這裡沒有設定（host/username 為空），寄信邏輯會退回使用環境變數設定，
    再不然就退回 console backend（開發模式，信件內容印在終端機）。
    """

    host = models.CharField("SMTP 主機", max_length=255, blank=True)
    port = models.PositiveIntegerField("連接埠", default=587)
    username = models.CharField("帳號", max_length=255, blank=True)
    password = models.CharField("密碼", max_length=255, blank=True)
    use_tls = models.BooleanField("使用 TLS", default=True)
    from_email = models.CharField(
        "寄件者顯示",
        max_length=255,
        blank=True,
        help_text='例如：LeetCode 教學管理系統 <noreply@example.com>',
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = "Email 設定"
        verbose_name_plural = "Email 設定"

    def __str__(self):
        return "Email 設定"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def is_configured(self):
        return bool(self.host and self.username)
