from django.db.models import Count
from datetime import timedelta
from urllib.parse import urlparse
from rest_framework import serializers
from django.utils import timezone
from .models import Message
from .message_markers import build_chat_id, describe_message, get_message_media_url, normalize_message_type


def _normalize_media_url(url):
    if not url:
        return ""

    # Keep already-browser-safe URLs as-is.
    if url.startswith("/") or url.startswith("blob:") or url.startswith("data:"):
        return url

    try:
        parsed = urlparse(url)
    except Exception:
        return url

    # The backend container hostname is not reachable from the browser.
    if parsed.hostname == "backend":
        relative = parsed.path or ""
        if parsed.params:
            relative += f";{parsed.params}"
        if parsed.query:
            relative += f"?{parsed.query}"
        if parsed.fragment:
            relative += f"#{parsed.fragment}"
        return relative or "/media/"

    return url


class MessageSerializer(serializers.ModelSerializer):
    media = serializers.SerializerMethodField()
    media_url = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()
    my_reaction = serializers.SerializerMethodField()
    sender_username = serializers.SerializerMethodField()
    sender_display_name = serializers.SerializerMethodField()
    reply_to_message = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    gif_url = serializers.SerializerMethodField()
    sticker_url = serializers.SerializerMethodField()
    chat_id = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = "__all__"

    def get_media(self, obj):
        if not obj.media:
            return ""
        return _normalize_media_url(obj.media.url)

    def get_media_url(self, obj):
        if not obj.media:
            return ""
        return _normalize_media_url(obj.media.url)

    def get_type(self, obj):
        return normalize_message_type(getattr(obj, "message_type", None))

    def get_gif_url(self, obj):
        return get_message_media_url(obj) if self.get_type(obj) == "gif" else ""

    def get_sticker_url(self, obj):
        return get_message_media_url(obj) if self.get_type(obj) == "sticker" else ""

    def get_chat_id(self, obj):
        return build_chat_id(obj.sender_id, obj.receiver_id)

    def get_reactions(self, obj):
        qs = obj.reactions.values("emoji").annotate(count=Count("id")).order_by("emoji")
        return list(qs)

    def get_my_reaction(self, obj):
        request = self.context.get("request") if self.context else None
        context_user = self.context.get("user") if self.context else None
        user = request.user if request and request.user.is_authenticated else context_user
        if not user or not getattr(user, "is_authenticated", False):
            return ""
        reaction = obj.reactions.filter(user=user).order_by("-id").first()
        return reaction.emoji if reaction else ""

    def get_sender_username(self, obj):
        return obj.sender.username if getattr(obj, "sender", None) else ""

    def get_sender_display_name(self, obj):
        if not getattr(obj, "sender", None):
            return ""
        return obj.sender.get_full_name() or obj.sender.username

    def get_reply_to_message(self, obj):
        reply = getattr(obj, "reply_to", None)
        if not reply:
            return None
        reply_type = normalize_message_type(getattr(reply, "message_type", None))
        media_url = self.get_media_url(reply)
        media_preview = None
        if reply_type in {"gif", "sticker"}:
            preview_url = self.get_gif_url(reply) if reply_type == "gif" else self.get_sticker_url(reply)
            if preview_url:
                media_preview = {"kind": reply_type, "url": preview_url}
        elif reply_type == "file" and media_url:
            media_type = str(getattr(reply, "media_type", "") or "").lower()
            is_video = media_type.startswith("video/") or media_url.lower().split("?", 1)[0].endswith(
                (".mp4", ".webm", ".ogg", ".mov")
            )
            media_preview = {
                "kind": "video" if is_video else "image",
                "url": media_url,
                "media_type": getattr(reply, "media_type", "") or "",
            }

        return {
            "id": reply.id,
            "sender_id": reply.sender_id,
            "sender_username": reply.sender.username,
            "sender_display_name": reply.sender.get_full_name() or reply.sender.username,
            "content": describe_message(reply, reply.is_deleted),
            "type": reply_type,
            "message_type": reply_type,
            "media_url": media_url,
            "media": self.get_media(reply),
            "media_type": getattr(reply, "media_type", "") or "",
            "media_preview": media_preview,
            "gif_url": self.get_gif_url(reply),
            "sticker_url": self.get_sticker_url(reply),
            "external_url": getattr(reply, "external_url", "") or "",
            "animated": bool(getattr(reply, "animated", False)),
            "chat_id": build_chat_id(reply.sender_id, reply.receiver_id),
            "is_deleted": reply.is_deleted,
            "timestamp": reply.timestamp.isoformat() if reply.timestamp else None,
        }

    def _is_owner(self, obj):
        request = self.context.get("request") if self.context else None
        context_user = self.context.get("user") if self.context else None

        if request and request.user.is_authenticated:
            return obj.sender_id == request.user.id
        if context_user and getattr(context_user, "is_authenticated", False):
            return obj.sender_id == context_user.id
        return False

    def _is_within_edit_window(self, obj):
        if not obj.timestamp:
            return False
        return timezone.now() <= obj.timestamp + timedelta(minutes=30)

    def get_can_edit(self, obj):
        return self._is_owner(obj) and not obj.is_deleted and self._is_within_edit_window(obj)

    def get_can_delete(self, obj):
        return self._is_owner(obj) and not obj.is_deleted
