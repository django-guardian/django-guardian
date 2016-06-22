from django.core.urlresolvers import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from guardian.mixins import PermissionRequiredMixin, PermissionListMixin
from guardian.shortcuts import assign_perm
from .models import Article


class ArticleListView(PermissionListMixin, ListView):
    model = Article
    permission_required = ['view_article', ]


class ArticleDetailView(PermissionRequiredMixin, DetailView):
    model = Article
    permission_required = ['view_article']


class ArticleCreateView(PermissionRequiredMixin, CreateView):
    model = Article
    permission_object = None
    permission_required = ['articles.add_article']
    fields = ['title', 'slug', 'content']

    def form_valid(self, *args, **kwargs):
        resp = super(ArticleCreateView, self).form_valid(*args, **kwargs)
        assign_perm('view_article', self.request.user, self.object)
        assign_perm('change_article', self.request.user, self.object)
        assign_perm('delete_article', self.request.user, self.object)
        return resp


class ArticleUpdateView(UpdateView):
    model = Article
    permission_required = ['view_article', 'change_article']
    fields = ['title', 'slug', 'content']


class ArticleDeleteView(DeleteView):
    model = Article
    success_url = reverse_lazy('articles:list')
    permission_required = ['view_article', 'delete_article']
