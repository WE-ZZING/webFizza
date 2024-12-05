from django.urls import path
from apps.main import views


urlpatterns = [
    path('', views.index, name='home'),
    path('run-webfizza/', views.run_webfizza, name='run_webfizza'),
]
