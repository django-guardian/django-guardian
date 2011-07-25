from django.shortcuts import render_to_response, get_object_or_404
from guardian.decorators import permission_required_or_403

from posts.models import Post


@permission_required_or_403('posts.view_post', (Post, 'slug', 'slug'))
def view_post(request, slug, **kwargs):
    post = get_object_or_404(Post, slug=slug)
    return render_to_response('posts/post_detail.html', {'object': post})

