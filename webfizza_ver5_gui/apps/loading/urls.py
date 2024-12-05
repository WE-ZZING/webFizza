# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.loading import views

urlpatterns = [
    # The loading page
    path('', views.index, name='loading'),
    path('check_status/', views.check_status, name='check_status'),

]
