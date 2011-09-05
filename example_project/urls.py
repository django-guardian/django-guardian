from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

from django.contrib.flatpages.models import FlatPage

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'django.views.generic.list_detail.object_list',
        kwargs={'queryset': FlatPage.objects.all(),
                'template_name': 'home.html',
                'template_object_name': 'flatpage'},
        name='home'),
    (r'^admin/', include(admin.site.urls)),
    (r'^posts/', include('example_project.posts.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % settings.STATIC_URL.strip('/'),
            'django.views.static.serve',
            {'document_root': settings.STATIC_ROOT}),
)

if 'grappelli' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        (r'^grappelli/', include('grappelli.urls')),
    )

