from django.db import models
from django.urls import reverse


from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase


class Article(models.Model):
    title = models.CharField('title', max_length=64)
    slug = models.SlugField(max_length=64)
    content = models.TextField('content')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        default_permissions = ('add', 'change', 'delete')
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


from guardian.models import UserObjectPermissionAbstract, GroupObjectPermissionAbstract

class BigUserObjectPermission(UserObjectPermissionAbstract):
    id = models.BigAutoField(editable=False, unique=True, primary_key=True)
    class Meta(UserObjectPermissionAbstract.Meta):
        abstract = False
        indexes = [
            *UserObjectPermissionAbstract.Meta.indexes,
            models.Index(fields=['content_type', 'object_pk', 'user']),
        ]


class BigGroupObjectPermission(GroupObjectPermissionAbstract):
    id = models.BigAutoField(editable=False, unique=True, primary_key=True)
    class Meta(GroupObjectPermissionAbstract.Meta):
        abstract = False
        indexes = [
            *GroupObjectPermissionAbstract.Meta.indexes,
            models.Index(fields=['content_type', 'object_pk', 'group']),
        ]

