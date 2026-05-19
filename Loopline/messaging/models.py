from django.db import models
from django.contrib.auth.models import User

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_following", db_column='follower_id')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_followers", db_column='following_id')

    class Meta:
        managed = False
        db_table = 'community_follow'

class Message(models.Model):
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
    media = models.FileField(upload_to="chat_media/", blank=True, null=True)
    media_type = models.CharField(max_length=50, blank=True, default="")

    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    edited_at = models.DateTimeField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} -> {self.receiver}"

    def save(self, *args, **kwargs):
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
