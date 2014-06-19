from __future__ import unicode_literals
# handler404 and handler500 are needed for admin tests
from guardian.compat import include, patterns, handler404, handler500 # pyflakes:ignore
from guardian.mixins import PermissionRequiredMixin
from django.contrib import admin
from django import get_version as django_get_version

if (django_get_version() >= "1.5"):
    from django.views.generic import View

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
)

if (django_get_version() >= "1.5"):

    class testClassRedirectView(PermissionRequiredMixin, View):
        permission_required = 'testapp.change_project'

    urlpatterns += patterns('',
        (r'^accounts/login/', 'django.contrib.auth.views.login', {'template_name': 'blank.html'}),
        (r'^permission_required/', testClassRedirectView.as_view()),
    )
