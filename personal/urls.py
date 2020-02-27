from django.contrib import admin
from django.urls import include, path
from . import views
app_name = 'personal'
urlpatterns = [
    path('', views.index_view, name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('user/<str:profileID>/', views.profileView, name='profileView'),
    path('uploads/image', views.upload_file, name='upload_file'),
    path('images/<str:image_ID>/', views.serveImage, name='serveImage'),
    path('newUser/', views.create_user, name='create_user'),
    path('imageSearch/', views.imageSearch, name='imageSearch'),
]