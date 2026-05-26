from django.db import models
from django.contrib.auth.models import User

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_following", db_column='follower_id')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_followers", db_column='following_id')

    class Meta:
        managed = False
        db_table = 'community_follow'

class Message(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ("text", "Text"),
        ("gif", "GIF"),
        ("sticker", "Sticker"),
        ("file", "File"),
    )

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_received_messages")
    reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="reply_messages",
        blank=True,
        null=True,
    )

    content = models.TextField(blank=True, default="")
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default="text")
    media_title = models.CharField(max_length=255, blank=True, default="")
    external_url = models.URLField(blank=True, default="")
    provider = models.CharField(max_length=40, blank=True, default="")
    provider_id = models.CharField(max_length=80, blank=True, default="")
    animated = models.BooleanField(default=False)
    media = models.FileField(upload_to="chat_media/", blank=True, null=True)
    media_type = models.CharField(max_length=50, blank=True, default="")

    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    edited_at = models.DateTimeField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} -> {self.receiver}"

    def save(self, *args, **kwargs):
        self.message_type = (self.message_type or "text").strip().lower()
        if self.message_type not in dict(self.MESSAGE_TYPE_CHOICES):
            self.message_type = "text"
        if self.media and not self.media_type:
            content_type = getattr(self.media.file, "content_type", "") or ""
            if content_type:
                self.media_type = content_type
        super().save(*args, **kwargs)

class MessageReaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_message_reactions")
    emoji = models.CharField(max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("message", "user", "emoji")

    def __str__(self):
        return f"{self.user} reacted {self.emoji}"
