from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("messaging", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="message_type",
            field=models.CharField(
                choices=[
                    ("text", "Text"),
                    ("gif", "GIF"),
                    ("sticker", "Sticker"),
                    ("file", "File"),
                ],
                default="text",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="message",
            name="media_title",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="message",
            name="external_url",
            field=models.URLField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="message",
            name="provider",
            field=models.CharField(blank=True, default="", max_length=40),
        ),
        migrations.AddField(
            model_name="message",
            name="provider_id",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="message",
            name="animated",
            field=models.BooleanField(default=False),
        ),
    ]
