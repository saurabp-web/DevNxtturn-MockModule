from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User, AnonymousUser

from community.presence import (
    is_user_online,
    new_presence_connection_id,
    refresh_user_presence,
    set_user_offline,
    set_user_online,
)
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
        self.presence_connection_id = new_presence_connection_id()
        await self.set_online()

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.send_other_user_presence()
        await self.broadcast_presence(True)

    async def disconnect(self, close_code):
        is_online = False
        if hasattr(self, "presence_connection_id"):
            is_online = await self.set_offline()
            await self.broadcast_presence(is_online)
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content):
        event = content.get("event")
        if event == "typing":
            await self.refresh_presence()
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
        if event == "read":
            read_state = await self.mark_read()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.read",
                    "read": read_state,
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

    async def chat_read(self, event):
        await self.send_json({"read": event["read"]})

    async def chat_presence(self, event):
        await self.send_json({"presence": event["presence"]})

    async def send_other_user_presence(self):
        await self.send_json(
            {
                "presence": {
                    "user_id": self.other_user.id,
                    "username": self.other_user.username,
                    "is_online": await self.is_other_user_online(),
                },
            }
        )

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def set_online(self):
        set_user_online(self.user.id, self.presence_connection_id)

    @database_sync_to_async
    def set_offline(self):
        set_user_offline(self.user.id, self.presence_connection_id)
        return is_user_online(self.user.id)

    @database_sync_to_async
    def refresh_presence(self):
        if hasattr(self, "presence_connection_id"):
            refresh_user_presence(self.user.id, self.presence_connection_id)

    @database_sync_to_async
    def is_other_user_online(self):
        return is_user_online(self.other_user.id)

    async def broadcast_presence(self, is_online):
        if not hasattr(self, "room_group_name"):
            return
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.presence",
                "presence": {
                    "user_id": self.user.id,
                    "username": self.user.username,
                    "is_online": bool(is_online),
                },
            },
        )

    @database_sync_to_async
    def mark_read(self):
        updated_count = Message.objects.filter(
            sender=self.other_user,
            receiver=self.user,
            is_read=False,
        ).update(is_read=True)
        unread_count = Message.objects.filter(receiver=self.user, is_read=False).count()
        return {
            "reader_id": self.user.id,
            "sender_id": self.other_user_id,
            "chat_id": f"chat_{min(self.user.id, self.other_user_id)}_{max(self.user.id, self.other_user_id)}",
            "updated_count": updated_count,
            "unread_count": unread_count,
        }

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
