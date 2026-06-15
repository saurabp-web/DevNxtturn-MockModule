from __future__ import annotations


def normalize_message_type(message_type: str | None) -> str:
    value = str(message_type or "text").strip().lower()
    return value if value in {"text", "gif", "sticker", "file"} else "text"


def get_message_media_url(message) -> str:
    if not message:
        return ""

    message_type = normalize_message_type(getattr(message, "message_type", None))
    if message_type == "gif":
        return str(getattr(message, "external_url", "") or "")
    if message_type == "sticker":
        return str(getattr(message, "external_url", "") or "")
    return str(getattr(message, "external_url", "") or "")


def get_message_media_kind(message) -> str:
    return normalize_message_type(getattr(message, "message_type", None))


def describe_message(message, deleted: bool = False) -> str:
    if deleted:
        return "Message deleted"

    if not message:
        return ""

    message_type = normalize_message_type(getattr(message, "message_type", None))
    if message_type == "gif":
        return "GIF"
    if message_type == "sticker":
        return "Sticker"
    if message_type == "file":
        content = str(getattr(message, "content", "") or "").strip()
        if content:
            return content

        media_type = str(getattr(message, "media_type", "") or "").lower()
        media_url = str(getattr(getattr(message, "media", None), "url", "") or "")
        if media_type.startswith("video/") or media_url.lower().split("?", 1)[0].endswith(
            (".mp4", ".webm", ".ogg", ".mov")
        ):
            return "Video"
        if media_type.startswith("image/") or media_url.lower().split("?", 1)[0].endswith(
            (".jpg", ".jpeg", ".png", ".gif", ".webp")
        ):
            return "Photo"

    return str(getattr(message, "content", "") or "")


def build_chat_id(sender_id, receiver_id) -> str:
    ordered = sorted([str(sender_id), str(receiver_id)])
    return f"chat_{ordered[0]}_{ordered[1]}"
