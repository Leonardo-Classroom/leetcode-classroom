from django.conf import settings
from django.core.mail import get_connection


class ConfigurableEmailBackend:
    """
    寄信時實際使用的 backend。優先順序：
    1. 後台「Email 設定」頁面存在資料庫裡的 SMTP 設定（EmailSettings.is_configured）
    2. 部署時用環境變數設定的 FALLBACK_EMAIL_BACKEND（見 config/settings.py）
    每次寄信都會重新讀一次資料庫設定，所以在後台改完設定不用重啟服務就會生效。
    """

    def __init__(self, fail_silently=False, **kwargs):
        from .models import EmailSettings

        config = EmailSettings.get_solo()
        if config.is_configured:
            self._connection = get_connection(
                backend="django.core.mail.backends.smtp.EmailBackend",
                host=config.host,
                port=config.port,
                username=config.username,
                password=config.password,
                use_tls=config.use_tls,
                fail_silently=fail_silently,
            )
        else:
            self._connection = get_connection(
                backend=settings.FALLBACK_EMAIL_BACKEND, fail_silently=fail_silently
            )

    def open(self):
        return self._connection.open()

    def close(self):
        return self._connection.close()

    def send_messages(self, email_messages):
        return self._connection.send_messages(email_messages)


def get_default_from_email():
    from email.utils import formataddr, parseaddr

    from .models import EmailSettings

    config = EmailSettings.get_solo()
    if not config.is_configured:
        return settings.DEFAULT_FROM_EMAIL

    if config.from_email:
        _, addr = parseaddr(config.from_email)
        if addr and "@" in addr:
            return config.from_email
        # 存下來的值只有顯示名稱、沒有 email（例如舊資料或還沒套用表單驗證前存的），
        # 用 SMTP 帳號補成合法的寄件位址，避免寄信時整串非 ASCII 文字被當成 local-part。
        return formataddr((config.from_email, config.username))

    return config.username
