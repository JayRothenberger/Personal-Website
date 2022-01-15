from django.contrib import admin
from django.urls import include, path
from . import views
app_name = 'personal'
urlpatterns = [
    path('', views.index_view, name='index'),
    path('test/', views.test, name='test'),
    path('code/', views.code, name='code'),
    path('ponder/', views.test, name='ponder'),
    path('blog/', views.test, name='blog'),
    path('ide/', views.ide, name='ide'),
    path('run/', views.run, name='run'),
]
