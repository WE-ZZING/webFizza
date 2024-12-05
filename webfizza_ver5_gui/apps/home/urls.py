# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.home import views


urlpatterns = [

    # The home page
    path('', views.index, name='home'),
    path('check_validation_status/', views.check_validation_status, name='check_validation_status'),
    path('report_status/', views.check_validation_status, name='report_status'),

    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),
    

]

