from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from adminpanel.email_backend import get_default_from_email


def build_password_set_link(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})
    return request.build_absolute_uri(path)


def send_invitation_email(request, student):
    """新增學員時寄出邀請信，學員點連結後自行設定密碼（沿用忘記密碼的 token 機制）。"""
    link = build_password_set_link(request, student.user)
    context = {"student": student, "link": link}
    subject = render_to_string("accounts/emails/invitation_subject.txt", context).strip()
    body = render_to_string("accounts/emails/invitation_email.txt", context)
    send_mail(subject, body, get_default_from_email(), [student.user.email])
