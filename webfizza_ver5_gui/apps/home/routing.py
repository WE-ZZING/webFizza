from django.urls import re_path
from apps.home import consumers

websocket_urlpatterns = [
    re_path(r'ws/logs/$', consumers.LogConsumer.as_asgi()),
    re_path(r"ws/input/", consumers.InputConsumer.as_asgi()),
]

