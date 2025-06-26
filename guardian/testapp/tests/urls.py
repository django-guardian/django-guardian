from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import path
from django.views.generic import View

from guardian.mixins import PermissionRequiredMixin

admin.autodiscover()


class TestClassRedirectView(PermissionRequiredMixin, View):
    permission_required = "testapp.change_project"


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", LoginView.as_view(template_name="blank.html")),
    path("permission_required/", TestClassRedirectView.as_view()),
]
