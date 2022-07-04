from django.urls import path
from . import views


app_name = 'articles'
urlpatterns = [
    path('', views.ArticleListView.as_view(),
        name="list"),
    path('~create', views.ArticleCreateView.as_view(),
        name="create"),
    path('<slug:slug>', views.ArticleDetailView.as_view(),
        name="details"),
    path('<slug:slug>/~update', views.ArticleUpdateView.as_view(),
        name="update"),
    path('<slug:slug>/~delete', views.ArticleDeleteView.as_view(),
        name="delete"),
]
