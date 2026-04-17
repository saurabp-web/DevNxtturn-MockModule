from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Match the cloud-ready prefix
    re_path(r"^ws/activity/$", consumers.UserActivityConsumer.as_asgi()),
]
