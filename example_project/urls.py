from guardian.compat import include, url, handler404, handler500
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import logout
from django.conf.urls import url

__all__ = ['handler404', 'handler500']


admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^logout/$', logout, {'next_page': '/'}, name='logout'),
    url(r'^', include('posts.urls')),
]

if 'grappelli' in settings.INSTALLED_APPS:
    urlpatterns += [url(r'^grappelli/', include('grappelli.urls')), ]

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += [url(r'^rosetta/', include('rosetta.urls')), ]
