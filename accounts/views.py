from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def post_login_redirect(request):
    if request.user.is_staff:
        return redirect("adminpanel:dashboard")
    return redirect("portal:dashboard")
