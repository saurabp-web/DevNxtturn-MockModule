from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Count
from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes

from .models import Message, MessageReaction, Follow
from .serializers import MessageSerializer


def _serialize_chat_user(user_obj, request):
    picture_url = None
    try:
        profile = getattr(user_obj, "profile", None)
        picture = getattr(profile, "picture", None)
        if picture and hasattr(picture, "url"):
            # Return a browser-reachable path instead of the backend container host.
            picture_url = picture.url
    except Exception:
        picture_url = None

    return {
        "id": user_obj.id,
        "username": user_obj.username,
        "first_name": user_obj.first_name,
        "last_name": user_obj.last_name,
        "picture": picture_url,
    }


def broadcast_message(sender_id, receiver_id, data, event="created"):
    user_ids = sorted([sender_id, receiver_id])
    room_group_name = f"chat_{user_ids[0]}_{user_ids[1]}"
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        room_group_name,
        {"type": "chat.message", "message": data, "event": event}
    )


def resolve_reply_target(sender, receiver, reply_to_message_id):
    if not reply_to_message_id:
        return None
    try:
        reply_id = int(reply_to_message_id)
    except (TypeError, ValueError):
        return None

    try:
        reply = Message.objects.select_related("sender").get(id=reply_id)
    except Message.DoesNotExist:
        return None

    valid_pair = {
        (sender.id, receiver.id),
        (receiver.id, sender.id),
    }
    if (reply.sender_id, reply.receiver_id) not in valid_pair:
        return None
    return reply


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_message(request, user_id):
    sender = request.user
    receiver = get_object_or_404(User, id=user_id)
    reply_to_message = resolve_reply_target(
        sender,
        receiver,
        request.data.get("reply_to_message_id"),
    )

    content = request.data.get("content", "").strip()
    if not content:
        return Response({"error": "Message content is required"})

    message = Message.objects.create(
        sender=sender,
        receiver=receiver,
        content=content,
        reply_to=reply_to_message,
    )

    serializer = MessageSerializer(message, context={"request": request})
    broadcast_message(sender.id, receiver.id, serializer.data, event="created")

    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def send_media(request, user_id):
    sender = request.user
    receiver = get_object_or_404(User, id=user_id)
    reply_to_message = resolve_reply_target(
        sender,
        receiver,
        request.data.get("reply_to_message_id"),
    )

    upload = request.FILES.get("media")
    content = request.data.get("content", "").strip()
    if not upload and not content:
        return Response({"error": "Media file or message content is required"})

    media_type = getattr(upload, "content_type", "") if upload else ""
    if not media_type and upload:
        name = (getattr(upload, "name", "") or "").lower()
        if name.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
            media_type = "image/*"
        elif name.endswith((".mp4", ".webm", ".ogg", ".mov")):
            media_type = "video/*"

    message = Message.objects.create(
        sender=sender,
        receiver=receiver,
        content=content,
        media=upload,
        media_type=media_type,
        reply_to=reply_to_message,
    )

    serializer = MessageSerializer(message, context={"request": request})
    broadcast_message(sender.id, receiver.id, serializer.data, event="created")

    return Response(serializer.data)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def message_detail(request, message_id):
    try:
        message = Message.objects.select_related("sender", "receiver").get(id=message_id)
    except Message.DoesNotExist:
        return Response({"error": "Message not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.user.id not in [message.sender_id, message.receiver_id]:
        return Response({"error": "You cannot modify this message"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        if request.user.id != message.sender_id:
            return Response({"error": "You can only edit your own messages"}, status=status.HTTP_403_FORBIDDEN)
        if message.is_deleted:
            return Response({"error": "Deleted messages cannot be edited"}, status=status.HTTP_400_BAD_REQUEST)
        if timezone.now() > message.timestamp + timedelta(minutes=30):
            return Response(
                {"error": "Messages can only be edited within 30 minutes"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        content = request.data.get("content", "").strip()
        if not content:
            return Response({"error": "Message content is required"}, status=status.HTTP_400_BAD_REQUEST)

        message.content = content
        message.edited_at = timezone.now()
        message.save(update_fields=["content", "edited_at"])

        serializer = MessageSerializer(message, context={"request": request})
        broadcast_message(message.sender_id, message.receiver_id, serializer.data, event="edited")
        return Response(serializer.data)

    if request.user.id != message.sender_id:
        return Response({"error": "You can only delete your own messages"}, status=status.HTTP_403_FORBIDDEN)

    if message.media:
        message.media.delete(save=False)

    message.content = ""
    message.media = None
    message.media_type = ""
    message.is_deleted = True
    message.edited_at = timezone.now()
    message.save(update_fields=["content", "media", "media_type", "is_deleted", "edited_at"])

    serializer = MessageSerializer(message, context={"request": request})
    broadcast_message(message.sender_id, message.receiver_id, serializer.data, event="deleted")
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def react_message(request):
    user = request.user
    message_id = request.data.get("message_id")
    emoji = (request.data.get("emoji") or "").strip()

    if not message_id or not emoji:
        return Response({"error": "message_id and emoji are required"})
    if len(emoji) > 16:
        return Response({"error": "Emoji is too long"})

    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({"error": "Message not found"})

    if user.id not in [message.sender_id, message.receiver_id]:
        return Response({"error": "You cannot react to this message"})

    reaction, created = MessageReaction.objects.get_or_create(
        message=message,
        user=user,
        emoji=emoji
    )
    if not created:
        reaction.delete()

    reactions = list(
        MessageReaction.objects.filter(message=message)
        .values("emoji")
        .annotate(count=Count("id"))
        .order_by("emoji")
    )

    payload = {"message_id": message.id, "reactions": reactions}
    broadcast_message(message.sender_id, message.receiver_id, payload)

    return Response(payload)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_messages(request, user_id):
    user = request.user
    other_user = get_object_or_404(User, id=user_id)

    Message.objects.filter(
        sender=other_user,
        receiver=user,
        is_read=False
    ).update(is_read=True)

    # Load latest messages first; allow older messages as offset increases
    offset = int(request.GET.get('offset', 0))
    limit = int(request.GET.get('limit', 50))  # Default to last 50 messages

    messages = Message.objects.select_related("sender", "receiver", "reply_to", "reply_to__sender").filter(
        sender__in=[user, other_user],
        receiver__in=[user, other_user]
    ).order_by("-timestamp")[offset:offset + limit]

    messages = list(reversed(messages))

    serializer = MessageSerializer(messages, many=True, context={"request": request})

    # Get total count for pagination info
    total_count = Message.objects.filter(
        sender__in=[user, other_user],
        receiver__in=[user, other_user]
    ).count()

    return Response({
        "messages": serializer.data,
        "total_count": total_count,
        "has_more": offset + limit < total_count
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unread_count(request):
    user = request.user
    count = Message.objects.filter(receiver=user, is_read=False).count()
    return Response({"count": count})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_users(request):
    user = request.user
    users = User.objects.all()
    data = []

    for other in users:
        if other.id == user.id:
            continue
        is_following = Follow.objects.filter(follower=user, following=other).exists()
        is_followed_by = Follow.objects.filter(follower=other, following=user).exists()
        unread = Message.objects.filter(
            sender=other,
            receiver=user,
            is_read=False
        ).count()
        data.append({
            **_serialize_chat_user(other, request),
            "is_following": is_following,
            "is_followed_by": is_followed_by,
            "can_message": True,
            "unread_count": unread
        })

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversations(request):
    """
    Returns only users the current user has exchanged messages with.
    Sorted by most recent message (newest first).
    Includes the last message preview and unread count.
    """
    from django.db.models import Q

    user = request.user

    # Get all unique partner IDs who have exchanged messages with this user
    sent_to = Message.objects.filter(sender=user).values_list('receiver_id', flat=True)
    received_from = Message.objects.filter(receiver=user).values_list('sender_id', flat=True)
    partner_ids = set(list(sent_to) + list(received_from))

    data = []
    for partner_id in partner_ids:
        other = User.objects.filter(id=partner_id).first()
        if not other:
            continue

        # Get the latest message in this conversation
        last_msg = Message.objects.filter(
            Q(sender=user, receiver=other) | Q(sender=other, receiver=user)
        ).order_by('-timestamp').first()

        unread = Message.objects.filter(
            sender=other,
            receiver=user,
            is_read=False
        ).count()

        is_following = Follow.objects.filter(follower=user, following=other).exists()
        is_followed_by = Follow.objects.filter(follower=other, following=user).exists()

        data.append({
            **_serialize_chat_user(other, request),
            "is_following": is_following,
            "is_followed_by": is_followed_by,
            "can_message": True,
            "unread_count": unread,
            "last_message": (
                "Message deleted" if last_msg and last_msg.is_deleted else last_msg.content
            ) if last_msg else "",
            "last_message_time": last_msg.timestamp.isoformat() if last_msg and last_msg.timestamp else None,
            "last_message_is_mine": last_msg.sender_id == user.id if last_msg else False,
        })

    # Sort: unread conversations first, then by latest message timestamp descending
    from datetime import datetime, timezone as tz
    def sort_key(x):
        has_unread = 0 if x['unread_count'] > 0 else 1
        if x['last_message_time']:
            try:
                dt = datetime.fromisoformat(x['last_message_time'].replace('Z', '+00:00'))
                ts = -dt.timestamp()  # negate so newest sorts first
            except Exception:
                ts = 0
        else:
            ts = 0
        return (has_unread, ts)

    data.sort(key=sort_key)

    return Response(data)
