from django.db import models
from django.utils.six import python_2_unicode_compatible


@python_2_unicode_compatible
class Post(models.Model):
    title = models.CharField('title', max_length=64)
    slug = models.SlugField(max_length=64)
    content = models.TextField('content')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        permissions = (
            ('view_post', 'Can view post'),
        )
        get_latest_by = 'created_at'

    def __str__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('posts_post_detail', (), {'slug': self.slug})
