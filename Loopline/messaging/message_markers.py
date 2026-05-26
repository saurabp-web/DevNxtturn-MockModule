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
        title = getattr(message, "media_title", "") or getattr(message, "provider_id", "") or "GIF"
        return f"GIF: {str(title).replace('-', ' ').title()}"
    if message_type == "sticker":
        title = getattr(message, "media_title", "") or getattr(message, "provider_id", "") or "Sticker"
        return f"Sticker: {str(title).replace('-', ' ').title()}"

    return str(getattr(message, "content", "") or "")


def build_chat_id(sender_id, receiver_id) -> str:
    ordered = sorted([str(sender_id), str(receiver_id)])
    return f"chat_{ordered[0]}_{ordered[1]}"
