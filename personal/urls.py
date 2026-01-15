from django.contrib import admin
from django.urls import include, path
from . import views
app_name = 'personal'
urlpatterns = [
    path('', views.index_view, name='index'),
    path('ponder/', views.test, name='ponder'),
    path('blog/', views.blog, name='blog'),
    path('run/', views.run, name='run'),
    path('rendezvous/', views.rendezvous, name='rendezvous'),
    path('cv/', views.cv, name='cv'),
    path('resume/', views.resume, name='resume'),
    path('links/', views.publications, name='links'),
]
