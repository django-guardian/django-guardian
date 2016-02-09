from guardian.compat import url

from posts import views

urlpatterns = [
    'posts.views',
    url(r'^$', views.post_list, name='posts_post_list'),
    url(r'^(?P<slug>[-\w]+)/$', views.post_detail, name='posts_post_detail'),
]
