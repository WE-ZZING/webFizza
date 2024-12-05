from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('api/md-file/<str:filename>/', views.get_md_file, name='get_md_file'),
]

