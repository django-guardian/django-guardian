from django.conf.urls.defaults import *


urlpatterns = patterns('posts.views',
    url(r'^(?P<slug>[-\w]+)/$',
        view='view_post',
        name='posts_post_detail'),
)

