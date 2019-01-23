from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from django.template import RequestContext
from guardian.decorators import permission_required_or_403

from .models import Post

User = get_user_model()


class PostList(ListView):
    model = Post
    context_object_name = 'posts'

post_list = PostList.as_view()


@permission_required_or_403('posts.view_post', (Post, 'slug', 'slug'))
def post_detail(request, slug, **kwargs):
    data = {
        'post': get_object_or_404(Post, slug=slug),
        'users': User.objects.all(),
        'groups': Group.objects.all(),
    }
    return render(
        request, 'posts/post_detail.html', data,
        RequestContext(request))
