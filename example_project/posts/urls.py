try:
    from django.conf.urls import patterns, url
except ImportError:
    from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('posts.views',
    url(r'^(?P<slug>[-\w]+)/$',
        view='view_post',
        name='posts_post_detail'),
)

