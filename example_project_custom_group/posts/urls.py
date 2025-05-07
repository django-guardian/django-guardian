from django.urls import path

from posts import views

urlpatterns = [
    path('', views.post_list, name='posts_post_list'),
    path('<slug:slug>', views.post_detail, name='posts_post_detail'),
]
