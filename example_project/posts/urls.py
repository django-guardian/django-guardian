from guardian.compat import url, patterns


urlpatterns = patterns('posts.views',
    url(r'^$', view='post_list', name='posts_post_list'),
    url(r'^(?P<slug>[-\w]+)/$', view='post_detail', name='posts_post_detail'),
)

