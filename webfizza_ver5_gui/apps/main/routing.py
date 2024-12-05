#main/routing.py

from django.urls import re_path
from apps.main import consumers 

websocket_urlpatterns = [
    re_path(r'^ws/input/$', consumers.InputConsumer.as_asgi()),
]
