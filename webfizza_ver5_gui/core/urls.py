# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from django.urls import path, include  # add this
from django.conf import settings
from django.conf.urls.static import static  # 추가

urlpatterns = [
    path('admin/', admin.site.urls),          # Django admin route
    path("", include("apps.authentication.urls")), # Auth routes - login / register
    path("home/", include("apps.home.urls")),             # UI Kits Html files
    path("", include("apps.main.urls")),
    path('report/', include("apps.report.urls")),
    path('patch/', include("apps.patch.urls")),
    path('validation/', include("apps.validation.urls")),
    path('loading/', include("apps.loading.urls")),
]

# md 파일 서빙을 위한 URL 패턴 추가
if hasattr(settings, 'EXTRA_FILES_DIRS') and 'md_files' in settings.EXTRA_FILES_DIRS:
    urlpatterns += static(
        '/md_files/', 
        document_root=settings.EXTRA_FILES_DIRS['md_files']
    )

