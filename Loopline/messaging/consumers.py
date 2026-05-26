from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User, AnonymousUser

from .models import Message
from .serializers import MessageSerializer
from .message_markers import normalize_message_type


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or isinstance(self.user, AnonymousUser):
            await self.close()
            return

        try:
            self.other_user_id = int(self.scope["url_route"]["kwargs"]["user_id"])
        except (TypeError, ValueError, KeyError):
            await self.close()
            return

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
        event = content.get("event")
        if event == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.typing",
                    "typing": {
                        "user_id": self.user.id,
                        "username": self.user.username,
                        "is_typing": bool(content.get("is_typing")),
                    },
                },
            )
            return

        reply_to_message_id = content.get("reply_to_message_id")
        message = await self.create_message(content, reply_to_message_id)
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

    async def chat_typing(self, event):
        await self.send_json(
            {
                "typing": event["typing"],
            }
        )

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def create_message(self, payload, reply_to_message_id=None):
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

        message_type = normalize_message_type(payload.get("message_type") or payload.get("type"))
        content = str(payload.get("content") or "").strip()
        external_url = str(payload.get("gif_url") or payload.get("sticker_url") or payload.get("external_url") or "").strip()
        provider = str(payload.get("provider") or "").strip()
        provider_id = str(payload.get("provider_id") or payload.get("id") or "").strip()
        media_title = str(payload.get("title") or payload.get("media_title") or "").strip()
        animated = bool(payload.get("animated", False))

        if message_type in {"gif", "sticker"} and not external_url:
            return None
        if message_type == "text" and not content:
            return None

        msg = Message.objects.create(
            sender=self.user,
            receiver=self.other_user,
            content=content if message_type == "text" else "",
            message_type=message_type,
            media_title=media_title,
            external_url=external_url,
            provider=provider or ("giphy" if message_type in {"gif", "sticker"} else ""),
            provider_id=provider_id,
            animated=animated if message_type in {"gif", "sticker"} else False,
            reply_to=reply_to,
        )
        return MessageSerializer(msg, context={"user": self.user}).data
