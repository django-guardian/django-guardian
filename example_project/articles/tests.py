from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import RequestFactory
from guardian.shortcuts import assign_perm
from articles.models import Article
from articles.views import (ArticleCreateView, ArticleDeleteView, ArticleDetailView,
                            ArticleListView, ArticleUpdateView)


class ViewTestCase(TestCase):
    def setUp(self):
        self.article = Article.objects.create(title='foo-title',
                                              slug='foo-slug',
                                              content='bar-content')
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            'joe', 'joe@doe.com', 'doe')
        self.client.login(username='joe', password='doe')

    def test_list_permitted(self):
        request = self.factory.get('/')
        request.user = self.user
        assign_perm('articles.view_article', self.user, self.article)
        assign_perm('articles.delete_article', self.user, self.article)
        view = ArticleListView.as_view()
        response = view(request)
        response.render()
        self.assertContains(response, 'foo-title')

    def test_list_denied(self):
        request = self.factory.get('/')
        request.user = self.user
        view = ArticleListView.as_view()
        response = view(request)
        response.render()
        self.assertNotContains(response, 'foo-title')

    def test_create_permitted(self):
        request = self.factory.get('/~create')
        request.user = self.user
        assign_perm('articles.add_article', self.user)
        view = ArticleCreateView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_create_denied(self):
        request = self.factory.get('/~create')
        request.user = self.user
        view = ArticleCreateView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_detail_permitted(self):
        request = self.factory.get('/foo/')
        request.user = self.user
        assign_perm('articles.view_article', self.user, self.article)
        view = ArticleDetailView.as_view()
        response = view(request, slug='foo-slug')
        self.assertEqual(response.status_code, 200)

    def test_detail_denied(self):
        request = self.factory.get('/foo/')
        request.user = self.user
        view = ArticleDetailView.as_view()
        response = view(request, slug='foo-slug')
        self.assertEqual(response.status_code, 302)

    def test_update_permitted(self):
        request = self.factory.get('/')
        request.user = self.user
        assign_perm('articles.view_article', self.user, self.article)
        assign_perm('articles.change_article', self.user, self.article)
        view = ArticleUpdateView.as_view()
        response = view(request, slug='foo-slug')
        self.assertEqual(response.status_code, 200)

    def test_update_denied(self):
        request = self.factory.get('/')
        request.user = self.user
        view = ArticleUpdateView.as_view()
        response = view(request, slug='foo-slug')
        self.assertEqual(response.status_code, 302)

    def test_delete_permitted(self):
        request = self.factory.get('/foo-slug/~delete')
        request.user = self.user
        assign_perm('articles.view_article', self.user, self.article)
        assign_perm('articles.delete_article', self.user, self.article)
        view = ArticleDeleteView.as_view()
        response = view(request, slug='foo-slug')
        self.assertEqual(response.status_code, 200)

    def test_delete_denied(self):
        request = self.factory.get('/foo/~delete')
        request.user = self.user
        view = ArticleDeleteView.as_view()
        response = view(request, slug='foo-slug')
        self.assertEqual(response.status_code, 302)
