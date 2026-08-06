from email.utils import formataddr, parseaddr

from django import forms
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email

from accounts.forms import BootstrapFormMixin

from .models import EmailSettings


class EmailSettingsForm(BootstrapFormMixin, forms.ModelForm):
    password = forms.CharField(
        label="密碼",
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="留空表示不變更密碼",
    )

    class Meta:
        model = EmailSettings
        fields = ["host", "port", "username", "password", "use_tls", "from_email"]
        help_texts = {
            "from_email": (
                '可以只填顯示名稱，例如：李奧納多小教室（系統會自動用下面的「帳號」當作寄件信箱）；'
                '也可以完整填「顯示名稱 <email@example.com>」'
            ),
        }

    def clean(self):
        cleaned = super().clean()
        raw = (cleaned.get("from_email") or "").strip()
        username = (cleaned.get("username") or "").strip()

        if not raw:
            return cleaned

        has_brackets = "<" in raw and ">" in raw

        if has_brackets:
            # 使用者顯然是想填「顯示名稱 <email>」完整格式，就照這個格式驗證，不要偷偷改意思
            _, addr = parseaddr(raw)
            if not addr or "@" not in addr:
                self.add_error("from_email", "格式不正確，請確認 <> 裡面是有效的 email 地址")
                return cleaned
            try:
                validate_email(addr)
            except DjangoValidationError:
                self.add_error("from_email", "email 格式不正確，請確認 <> 裡面是有效的 email 地址")
            return cleaned

        if "@" in raw:
            # 沒有 <>，但看起來本身就是一個 email
            try:
                validate_email(raw)
            except DjangoValidationError:
                self.add_error("from_email", "email 格式不正確")
            return cleaned

        # 沒有 <> 也沒有 @，代表只填了顯示名稱，用「帳號」欄位補上寄件信箱
        if not username:
            self.add_error(
                "from_email",
                '這欄目前只有名稱、沒有 email 地址，請先填上面的「帳號」欄位，系統會自動組合成寄件位址，'
                '或直接改成「顯示名稱 <email@example.com>」的完整格式',
            )
        else:
            cleaned["from_email"] = formataddr((raw, username))

        return cleaned


class TestEmailForm(BootstrapFormMixin, forms.Form):
    to_email = forms.EmailField(label="收件 Email")
