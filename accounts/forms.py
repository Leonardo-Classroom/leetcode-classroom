from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User

from .models import Student, generate_next_student_id


class BootstrapFormMixin:
    """替表單每個欄位的 widget 自動加上 Bootstrap 樣式 class。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            else:
                widget.attrs.setdefault("class", "form-control")


class StyledAuthenticationForm(BootstrapFormMixin, AuthenticationForm):
    pass


class StyledPasswordResetForm(BootstrapFormMixin, PasswordResetForm):
    """
    Django 內建的 PasswordResetForm 只會找「已經有可用密碼」的帳號。
    但學員剛被邀請、還沒點連結設定密碼時是 unusable password，
    這種情況也要能用「忘記密碼」重新拿到設定密碼連結，所以拿掉這個限制。
    """

    def get_users(self, email):
        email_field_name = User.get_email_field_name()
        return User._default_manager.filter(
            **{f"{email_field_name}__iexact": email, "is_active": True}
        )


class StyledSetPasswordForm(BootstrapFormMixin, SetPasswordForm):
    pass


class StudentCreateForm(BootstrapFormMixin, forms.Form):
    email = forms.EmailField(label="Email（同時作為登入帳號，邀請信會寄到這裡）")
    name = forms.CharField(label="姓名", max_length=64)
    class_name = forms.CharField(label="班級", max_length=64, required=False)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("此 Email 已被使用")
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("此 Email 已被使用")
        return email

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data["email"],
            email=data["email"],
            is_staff=False,
        )
        user.set_unusable_password()
        user.save()
        return Student.objects.create(
            user=user,
            student_id=generate_next_student_id(),
            name=data["name"],
            class_name=data["class_name"],
        )
