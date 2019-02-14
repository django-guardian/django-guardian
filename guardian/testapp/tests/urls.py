# handler404 and handler500 are needed for admin tests
from guardian.compat import url, handler404, handler500  # pyflakes:ignore
from guardian.mixins import PermissionRequiredMixin
from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.views.generic import View

admin.autodiscover()


class TestClassRedirectView(PermissionRequiredMixin, View):
    permission_required = 'testapp.change_project'

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/login/', LoginView.as_view(template_name='blank.html')),
    url(r'^permission_required/', TestClassRedirectView.as_view()),
]
