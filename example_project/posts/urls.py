from django.conf.urls.defaults import *


urlpatterns = patterns('example_project.posts.views',
    url(r'^(?P<post_slug>[-\w]+)/$',
        view='post_detail',
        name='posts_post_detail'),
)

