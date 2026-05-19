from django.urls import path

from . import views

app_name = "messaging"

urlpatterns = [
    path("users/", views.all_users, name="all-users"),
    path("users", views.all_users, name="all-users-no-slash"),
    path("conversations/", views.conversations, name="conversations"),
    path("conversations", views.conversations, name="conversations-no-slash"),
    path("conversations/<int:user_id>/messages/", views.get_messages, name="get-messages"),
    path("conversations/<int:user_id>/messages", views.get_messages, name="get-messages-no-slash"),
    path("conversations/<int:user_id>/send/", views.send_message, name="send-message"),
    path("conversations/<int:user_id>/send", views.send_message, name="send-message-no-slash"),
    path("conversations/<int:user_id>/media/", views.send_media, name="send-media"),
    path("conversations/<int:user_id>/media", views.send_media, name="send-media-no-slash"),
    path("messages/<int:message_id>/", views.message_detail, name="message-detail"),
    path("messages/<int:message_id>", views.message_detail, name="message-detail-no-slash"),
    path("messages/react/", views.react_message, name="react-message"),
    path("messages/react", views.react_message, name="react-message-no-slash"),
    path("messages/unread-count/", views.unread_count, name="unread-count"),
    path("messages/unread-count", views.unread_count, name="unread-count-no-slash"),
]
