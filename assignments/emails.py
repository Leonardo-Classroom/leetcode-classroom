from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse

from adminpanel.email_backend import get_default_from_email


def send_assignment_notifications(request, assignment):
    """
    任務建立並指派給學員後，一次寄出一封信通知所有人（同時寄送，不逐一寄）。
    收件人放在 bcc，彼此還是看不到對方的 Email，只是寄送本身是同一封信、同時送出。
    """
    link = request.build_absolute_uri(reverse("portal:assignment_detail", args=[assignment.pk]))

    students = assignment.students.select_related("user").all()
    recipients = [s.user.email for s in students if s.user.email]
    missing = len(students) - len(recipients)

    if not recipients:
        return 0, missing

    context = {"assignment": assignment, "link": link}
    subject = render_to_string("assignments/emails/notify_subject.txt", context).strip()
    body = render_to_string("assignments/emails/notify_email.txt", context)

    try:
        message = EmailMessage(
            subject=subject,
            body=body,
            from_email=get_default_from_email(),
            to=[get_default_from_email()],
            bcc=recipients,
        )
        message.send()
        return len(recipients), missing
    except Exception:
        return 0, len(students)
