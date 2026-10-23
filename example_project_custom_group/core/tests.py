from articles.models import Article, ArticleGroupObjectPermission
from core.models import CustomGroup
from django.test import TestCase
from posts.models import Post

from guardian.shortcuts import assign_perm, has_perm


class GuardianGroupMixinTestCase(TestCase):
    """Tests the methods GuardianGroupMixin adds to a custom group model."""

    def setUp(self):
        self.group = CustomGroup.objects.create(name="test-group")
        self.post = Post.objects.create(title="foo-title", slug="foo-slug", content="bar-content")

    def test_add_obj_perm(self):
        self.group.add_obj_perm("view_post", self.post)
        self.assertTrue(has_perm(self.group, "view_post", self.post))

    def test_del_obj_perm(self):
        assign_perm("view_post", self.group, self.post)
        self.group.del_obj_perm("view_post", self.post)
        self.assertFalse(has_perm(self.group, "view_post", self.post))

    def test_has_perm(self):
        assign_perm("view_post", self.group, self.post)
        self.assertTrue(self.group.has_perm("view_post", self.post))
        self.assertTrue(self.group.has_perm("posts.view_post", self.post))
        self.assertFalse(self.group.has_perm("change_post", self.post))
        self.assertFalse(self.group.has_perm("no_such_perm", self.post))

    def test_has_perm_on_another_object(self):
        other_post = Post.objects.create(title="bar-title", slug="bar-slug", content="bar-content")
        assign_perm("view_post", self.group, other_post)
        self.assertFalse(self.group.has_perm("view_post", self.post))

    def test_has_perm_matches_shortcut(self):
        assign_perm("view_post", self.group, self.post)
        for perm in ("view_post", "posts.view_post", "change_post", "no_such_perm"):
            with self.subTest(perm=perm):
                self.assertEqual(self.group.has_perm(perm, self.post), has_perm(self.group, perm, self.post))

    def test_add_obj_perm_uses_the_direct_permission_model(self):
        """Article has its own group permission model, it must be used instead of the generic one."""
        article = Article.objects.create(title="foo-title", slug="foo-slug", content="bar-content")
        self.group.add_obj_perm("view_article", article)

        self.assertEqual(ArticleGroupObjectPermission.objects.count(), 1)
        self.assertTrue(self.group.has_perm("view_article", article))

    def test_del_obj_perm_uses_the_direct_permission_model(self):
        article = Article.objects.create(title="foo-title", slug="foo-slug", content="bar-content")
        assign_perm("view_article", self.group, article)

        self.group.del_obj_perm("view_article", article)

        self.assertEqual(ArticleGroupObjectPermission.objects.count(), 0)
        self.assertFalse(self.group.has_perm("view_article", article))
