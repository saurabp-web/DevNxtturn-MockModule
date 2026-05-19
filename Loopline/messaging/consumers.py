from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User, AnonymousUser

from .models import Message
from .serializers import MessageSerializer


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or isinstance(self.user, AnonymousUser):
            await self.close()
            return

        self.other_user_id = int(self.scope["url_route"]["kwargs"]["user_id"])
        self.other_user = await self.get_user(self.other_user_id)
        if not self.other_user:
            await self.close()
            return

        user_ids = sorted([self.user.id, self.other_user_id])
        self.room_group_name = f"chat_{user_ids[0]}_{user_ids[1]}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content):
        text = content.get("content")
        if not text:
            return

        reply_to_message_id = content.get("reply_to_message_id")
        message = await self.create_message(text, reply_to_message_id)
        if not message:
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": message
            }
        )

    async def chat_message(self, event):
        await self.send_json({
            "event": event.get("event", "created"),
            "message": event["message"],
        })

    async def chat_reaction(self, event):
        await self.send_json({"reaction": event["reaction"]})

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def create_message(self, text, reply_to_message_id=None):
        reply_to = None
        if reply_to_message_id:
            try:
                reply_id = int(reply_to_message_id)
                reply_to = Message.objects.filter(
                    id=reply_id,
                    sender__in=[self.user, self.other_user],
                    receiver__in=[self.user, self.other_user],
                ).select_related("sender").first()
            except (TypeError, ValueError):
                reply_to = None

        msg = Message.objects.create(
            sender=self.user,
            receiver=self.other_user,
            content=text,
            reply_to=reply_to,
        )
        return MessageSerializer(msg, context={"user": self.user}).data