from guardian.compat import url, include, patterns, handler404, handler500


urlpatterns = patterns('posts.views',
    url(r'^(?P<slug>[-\w]+)/$',
        view='view_post',
        name='posts_post_detail'),
)

