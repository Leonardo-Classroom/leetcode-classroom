from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("panel/", include("adminpanel.urls")),
    path("portal/", include("portal.urls")),
]
