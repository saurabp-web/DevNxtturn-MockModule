# ---  REAL-TIME POST DELETION SIGNAL (Corrected Model Name) ---
import logging

logger = logging.getLogger(__name__)
import re
from django.db.models import Q
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import (
    UserProfile,
    Follow,
    Like,
    StatusPost,
    Notification,
    Comment,
    GroupJoinRequest,
    ConnectionRequest,
)

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import NotificationSerializer, LivePostSerializer

User = get_user_model()

# =================================================================================
# === NEW REAL-TIME POST DELETION SIGNAL ===
# =================================================================================


@receiver(post_delete, sender=StatusPost)
def post_deleted_signal(sender, instance, **kwargs):
    """
    Handles the deletion of a StatusPost instance.

    Broadcasts a 'post_deleted' event to the author AND all of their followers,
    ensuring real-time UI consistency across all relevant clients.
    """
    author = instance.author
    if not author:
        return

    channel_layer = get_channel_layer()

    # --- FIX #1: The payload is now correctly nested ---
    # This now matches the structure your frontend EXPECTS.
    message_to_send = {"type": "post_deleted", "payload": {"post_id": instance.id}}

    # --- FIX #2: We find all relevant users (author + followers) ---
    follower_ids = Follow.objects.filter(following=author).values_list(
        "follower_id", flat=True
    )
    recipient_user_ids = list(follower_ids) + [author.id]

    # --- FIX #3: We broadcast to each user's personal group ---
    # We will use the 'send_live_post' handler type for consistency,
    # as this is a "live" update related to a post.
    for user_id in recipient_user_ids:
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            {
                "type": "send_live_post",  # Re-using the existing, correct handler type
                "message": message_to_send,
            },
        )

    logger.info(
        f"Real-time: Sent post_deleted signal for post ID {instance.id} to {len(recipient_user_ids)} users."
    )


# =================================================================================


# =================================================================================
# === CENTRALIZED REAL-TIME NOTIFICATION SIGNAL (Unchanged) ===
# =================================================================================
@receiver(post_save, sender=Notification)
def send_new_notification_signal(sender, instance, created, **kwargs):
    if created:
        serializer = NotificationSerializer(instance)
        channel_layer = get_channel_layer()
        group_name = f"user_{instance.recipient.id}"
        message_data = {
            "type": "send_notification",
            "message": {"type": "new_notification", "payload": serializer.data},
        }
        async_to_sync(channel_layer.group_send)(group_name, message_data)
        logger.info(
            f"Real-time: Sent notification type '{instance.notification_type}' to user group {group_name}."
        )


# =================================================================================


# --- SIGNAL HANDLERS WITH CORRECTED DUPLICATE CHECKING (Unchanged) ---


@receiver(post_save, sender=User, dispatch_uid="create_user_profile_signal")
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=Like, dispatch_uid="create_like_notification_signal")
def create_like_notification(sender, instance, created, **kwargs):
    if not created:
        return
    liked_object, liker, post_target = (
        instance.content_object,
        instance.user,
        instance.parent_post,
    )
    if isinstance(liked_object, StatusPost):
        recipient, verb, notification_target = (
            liked_object.author,
            "liked your post",
            liked_object,
        )
    elif isinstance(liked_object, Comment):
        recipient, verb, notification_target = (
            liked_object.author,
            "liked your reply" if liked_object.parent else "liked your comment",
            liked_object,
        )
    else:
        return
    if recipient and recipient != liker:
        action_object_content_type = ContentType.objects.get_for_model(instance)
        if not Notification.objects.filter(
            recipient=recipient,
            actor=liker,
            action_object_content_type=action_object_content_type,
            action_object_object_id=instance.id,
        ).exists():
            Notification.objects.create(
                recipient=recipient,
                actor=liker,
                verb=verb,
                notification_type=Notification.LIKE,
                action_object=instance,
                target=notification_target,
            )
            logger.info(f"DB: Created Like notification for {recipient.username}")


@receiver(post_save, sender=Follow, dispatch_uid="create_follow_notification_signal")
def create_follow_notification(sender, instance, created, **kwargs):
    """
    Notifies a user when they get a new follower.
    Silenced if the relationship is mutual (Connected), as the Connection signal handles the alert.
    """
    if not created:
        return

    followed_user, follower = instance.following, instance.follower

    if followed_user != follower:
        # --- THE FINAL SYNC FIX ---
        # Check if the person we just followed is already following us back.
        # If yes, they are "Connected." We don't want to spam them with a generic Follow alert.
        is_mutual = Follow.objects.filter(
            follower=followed_user, following=follower
        ).exists()

        if is_mutual:
            logger.info(
                f"Signal: Muting Follow alert for {followed_user.username} (Relationship is Mutual)."
            )
            return

        # Create alert only for one-way follows
        if not Notification.objects.filter(
            recipient=followed_user,
            actor=follower,
            notification_type=Notification.FOLLOW,
        ).exists():
            Notification.objects.create(
                recipient=followed_user,
                actor=follower,
                verb="started following you",
                notification_type=Notification.FOLLOW,
                target=follower,
            )
            logger.info(f"DB: Created Follow notification for {followed_user.username}")


@receiver(
    post_save,
    sender=ConnectionRequest,
    dispatch_uid="create_connection_notification_signal",
)
def create_connection_notification(sender, instance, created, **kwargs):
    """
    Handles notifications for the Connection Request lifecycle (Sent and Accepted).
    """
    # SCENARIO A: A brand new request is sent
    if created and instance.status == "pending":
        Notification.objects.create(
            recipient=instance.receiver,
            actor=instance.sender,
            verb="sent you a connection request",
            notification_type=Notification.CONNECTION_REQUEST,
            action_object=instance,
            target=instance.sender,
        )
        logger.info(
            f"DB: Created Connection Request notification for {instance.receiver.username}"
        )

    # SCENARIO B: An existing request is marked as 'accepted'
    elif not created and instance.status == "accepted":
        # We notify the person who sent the request originally (the actor becomes the receiver)
        # Note: We check if a notification already exists for this 'acceptance' to avoid double-firing
        if not Notification.objects.filter(
            recipient=instance.sender,
            actor=instance.receiver,
            notification_type=Notification.CONNECTION_ACCEPTED,
        ).exists():
            Notification.objects.create(
                recipient=instance.sender,
                actor=instance.receiver,
                verb="accepted your connection request",
                notification_type=Notification.CONNECTION_ACCEPTED,
                action_object=instance,
                target=instance.receiver,
            )
            logger.info(
                f"DB: Created Connection Accepted notification for {instance.sender.username}"
            )


@receiver(
    post_save, sender=Comment, dispatch_uid="create_comment_reply_notification_signal"
)
def create_comment_and_reply_notification(sender, instance, created, **kwargs):
    if not created:
        return
    commenter, post = instance.author, instance.content_object
    if instance.parent:
        recipient, verb, notification_type = (
            instance.parent.author,
            "replied to your comment",
            Notification.REPLY,
        )
    else:
        recipient, verb, notification_type = (
            post.author,
            "commented on your post",
            Notification.COMMENT,
        )
    mentioned_usernames = set(re.findall(r"@(\w+)", instance.content or ""))
    if recipient != commenter and recipient.username not in mentioned_usernames:
        action_object_content_type = ContentType.objects.get_for_model(instance)
        if not Notification.objects.filter(
            recipient=recipient,
            actor=commenter,
            action_object_content_type=action_object_content_type,
            action_object_object_id=instance.id,
        ).exists():
            Notification.objects.create(
                recipient=recipient,
                actor=commenter,
                verb=verb,
                notification_type=notification_type,
                action_object=instance,
                target=instance,
            )
            logger.info(
                f"DB: Created {notification_type} notification for {recipient.username}"
            )


@receiver(post_save, sender=StatusPost, dispatch_uid="mention_handler_signal_post")
@receiver(post_save, sender=Comment, dispatch_uid="mention_handler_signal_comment")
def create_mention_notifications(sender, instance, created, **kwargs):
    if not created:
        return
    actor, content_text = instance.author, instance.content or ""
    mentioned_usernames = set(re.findall(r"@(\w+)", content_text))
    if not mentioned_usernames:
        return
    if sender is StatusPost:
        verb, target = "mentioned you in a post", instance
    elif sender is Comment:
        verb, target = (
            "mentioned you in a reply"
            if instance.parent
            else "mentioned you in a comment"
        ), instance.content_object
    else:
        return
    for username in mentioned_usernames:
        try:
            recipient = User.objects.get(username=username)
            if recipient != actor:
                action_object_content_type = ContentType.objects.get_for_model(instance)
                if not Notification.objects.filter(
                    recipient=recipient,
                    actor=actor,
                    action_object_content_type=action_object_content_type,
                    action_object_object_id=instance.id,
                ).exists():
                    Notification.objects.create(
                        recipient=recipient,
                        actor=actor,
                        verb=verb,
                        notification_type=Notification.MENTION,
                        target=target,
                        action_object=instance,
                    )
                    logger.info(
                        f"DB: Created Mention notification for {recipient.username}"
                    )
        except User.DoesNotExist:
            continue


@receiver(post_save, sender=GroupJoinRequest)
def create_group_join_request_notification(sender, instance, created, **kwargs):
    update_fields = kwargs.get("update_fields") or set()
    is_new_request = created
    is_revived_request = "status" in update_fields and instance.status == "pending"
    if not (is_new_request or is_revived_request):
        return
    join_request, group, requester, group_owner = (
        instance,
        instance.group,
        instance.user,
        instance.group.creator,
    )
    if requester == group_owner:
        return
    if not Notification.objects.filter(
        recipient=group_owner,
        actor=requester,
        action_object_content_type=ContentType.objects.get_for_model(join_request),
        action_object_object_id=join_request.id,
        verb="sent a request to join",
    ).exists():
        Notification.objects.create(
            recipient=group_owner,
            actor=requester,
            verb="sent a request to join",
            notification_type=Notification.GROUP_JOIN_REQUEST,
            target=group,
            action_object=join_request,
        )
        logger.info(f"DB: Created Group Join Request for {group_owner.username}")


# --- OTHER SIGNALS ---
@receiver(post_save, sender=StatusPost, dispatch_uid="live_post_to_followers_signal")
def send_live_post_to_followers(sender, instance, created, **kwargs):
    if not created:
        return
    author = instance.author
    followers = Follow.objects.filter(following=author).select_related("follower")
    if not followers:
        return
    serializer = LivePostSerializer(instance)
    channel_layer = get_channel_layer()
    message_data = {
        "type": "send_live_post",
        "message": {"type": "new_post", "payload": serializer.data},
    }
    for follow_relation in followers:
        follower = follow_relation.follower
        group_name = f"user_{follower.id}"
        async_to_sync(channel_layer.group_send)(group_name, message_data)
        logger.info(
            f"Real-time: Dispatched new post ID {instance.id} to follower group {group_name} ({follower.username})."
        )
