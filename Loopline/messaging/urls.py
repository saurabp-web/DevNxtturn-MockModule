from django.urls import path

from . import views

urlpatterns = [
    path("users/", views.all_users, name="all-users"),
    path("conversations/", views.conversations, name="conversations"),
    path("conversations/<int:user_id>/messages/", views.get_messages, name="get-messages"),
    path("conversations/<int:user_id>/send/", views.send_message, name="send-message"),
    path("conversations/<int:user_id>/media/", views.send_media, name="send-media"),
    path("messages/<int:message_id>/", views.message_detail, name="message-detail"),
    path("messages/react/", views.react_message, name="react-message"),
    path("messages/unread-count/", views.unread_count, name="unread-count"),
]
