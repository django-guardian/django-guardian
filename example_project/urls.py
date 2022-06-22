from guardian.compat import include,  handler404, handler500
from django.conf import settings
from django.urls import path
from django.contrib import admin
from django.contrib.auth.views import LogoutView

__all__ = ['handler404', 'handler500']

admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('article/', include('articles.urls', namespace='articles')),
    path('', include('posts.urls')),
]

if 'grappelli' in settings.INSTALLED_APPS:
    urlpatterns += [path('grappelli/', include('grappelli.urls')), ]

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += [path('rosetta/', include('rosetta.urls')), ]
