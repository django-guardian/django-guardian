from __future__ import unicode_literals

from django.db import models
from django.utils.six import python_2_unicode_compatible
from guardian.compat import reverse


from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase


@python_2_unicode_compatible
class Article(models.Model):
    title = models.CharField('title', max_length=64)
    slug = models.SlugField(max_length=64)
    content = models.TextField('content')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        permissions = (
            ('view_article', 'Can view article'),
        )
        get_latest_by = 'created_at'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('articles:details', kwargs={'slug': self.slug})


class ArticleUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Article, on_delete=models.CASCADE)


class ArticleGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Article, on_delete=models.CASCADE)
