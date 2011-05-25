from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseForbidden

from posts.models import Post


def view_post(request, slug, **kwargs):
    post = get_object_or_404(Post, slug=slug)
    if not request.user.has_perm('posts.view_post', post):
        return HttpResponseForbidden()
    return render_to_response('posts/post_detail.html', {'object': post})
