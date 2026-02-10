"""WebSocket URL routing for novels app."""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/generate/(?P<task_id>[^/]+)/$', consumers.GenerationConsumer.as_asgi()),
    re_path(r'ws/project/(?P<project_id>[0-9a-f-]+)/$', consumers.ProjectConsumer.as_asgi()),
]
