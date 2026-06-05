from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from .models import Follow, Message, MessageReaction

User = get_user_model()


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower_link", "following_link", "created_at")
    list_filter = ("follower", "following")
    search_fields = ("follower__username", "following__username")
    readonly_fields = ("follower_link", "following_link", "created_at")

    def follower_link(self, obj):
        """Display follower with link to user admin"""
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.follower.id,
            obj.follower.username,
        )

    follower_link.short_description = "Follower"

    def following_link(self, obj):
        """Display following with link to user admin"""
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.following.id,
            obj.following.username,
        )

    following_link.short_description = "Following"

    def created_at(self, obj):
        """Display creation date"""
        return obj.follower.date_joined if hasattr(obj.follower, "date_joined") else "N/A"

    created_at.short_description = "Created At"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender_link", "receiver_link", "message_preview", "message_type", "is_read", "timestamp")
    list_filter = ("message_type", "is_read", "is_deleted", "timestamp")
    search_fields = ("sender__username", "receiver__username", "content")
    readonly_fields = (
        "sender_link",
        "receiver_link",
        "reply_to_link",
        "timestamp",
        "edited_at",
        "content_display",
        "media_preview",
    )
    fieldsets = (
        (
            "Message Info",
            {
                "fields": (
                    "sender_link",
                    "receiver_link",
                    "reply_to_link",
                    "timestamp",
                    "edited_at",
                )
            },
        ),
        (
            "Content",
            {
                "fields": ("content_display", "message_type"),
            },
        ),
        (
            "Media",
            {
                "fields": (
                    "media_preview",
                    "media_type",
                    "media_title",
                    "external_url",
                    "provider",
                    "provider_id",
                    "animated",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Status",
            {
                "fields": ("is_read", "is_deleted"),
            },
        ),
    )

    def sender_link(self, obj):
        """Display sender with link to user admin"""
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.sender.id,
            obj.sender.username,
        )

    sender_link.short_description = "Sender"

    def receiver_link(self, obj):
        """Display receiver with link to user admin"""
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.receiver.id,
            obj.receiver.username,
        )

    receiver_link.short_description = "Receiver"

    def reply_to_link(self, obj):
        """Display reply_to message with link"""
        if obj.reply_to:
            return format_html(
                '<a href="/admin/messaging/message/{}/change/">Message from {}</a>',
                obj.reply_to.id,
                obj.reply_to.sender.username,
            )
        return "No reply"

    reply_to_link.short_description = "Reply To"

    def message_preview(self, obj):
        """Display a preview of the message content"""
        preview = obj.content[:50] if obj.content else f"[{obj.message_type.upper()}]"
        return preview + "..." if len(obj.content) > 50 else preview

    message_preview.short_description = "Preview"

    def content_display(self, obj):
        """Display full content in readonly field"""
        return obj.content or "[Empty]"

    content_display.short_description = "Content"

    def media_preview(self, obj):
        """Display media preview if available"""
        if obj.media:
            return format_html(
                '<a href="{}" target="_blank">View Media</a>',
                obj.media.url,
            )
        return "No media"

    media_preview.short_description = "Media"


class MessageReactionInline(admin.TabularInline):
    """Inline admin for message reactions"""
    model = MessageReaction
    extra = 0
    readonly_fields = ("user_link", "emoji", "created_at")
    fields = ("user_link", "emoji", "created_at")
    can_delete = True

    def user_link(self, obj):
        """Display user with link to user admin"""
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username,
        )

    user_link.short_description = "User"


# Add inline to Message admin
MessageAdmin.inlines = [MessageReactionInline]


@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ("user_link", "emoji", "message_link", "created_at")
    list_filter = ("emoji", "created_at")
    search_fields = ("user__username", "message__content", "emoji")
    readonly_fields = ("user_link", "message_link", "created_at")

    def user_link(self, obj):
        """Display user with link to user admin"""
        return format_html(
            '<a href="/admin/auth/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username,
        )

    user_link.short_description = "User"

    def message_link(self, obj):
        """Display message with link to message admin"""
        return format_html(
            '<a href="/admin/messaging/message/{}/change/">Message from {}</a>',
            obj.message.id,
            obj.message.sender.username,
        )

    message_link.short_description = "Message"
