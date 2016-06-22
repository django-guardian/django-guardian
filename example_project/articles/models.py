from __future__ import unicode_literals

from django.db import models
from django.core.urlresolvers import reverse

from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase


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

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('articles:details', kwargs={'slug': self.slug})


class ArticleUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Article)


class ArticleGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Article)
