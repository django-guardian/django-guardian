# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url
from . import views


app_name = 'articles'
urlpatterns = [
    url(r'^$', views.ArticleListView.as_view(),
        name="list"),
    url(r'^~create$', views.ArticleCreateView.as_view(),
        name="create"),
    url(r'^(?P<slug>[\w-]+)$', views.ArticleDetailView.as_view(),
        name="details"),
    url(r'^(?P<slug>[\w-]+)/~update$', views.ArticleUpdateView.as_view(),
        name="update"),
    url(r'^(?P<slug>[\w-]+)/~delete$', views.ArticleDeleteView.as_view(),
        name="delete"),
]
