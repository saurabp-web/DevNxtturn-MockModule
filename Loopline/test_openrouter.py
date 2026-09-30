import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import requests
from django.conf import settings

resp = requests.post(
    settings.OPENROUTER_API_URL,
    headers={
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": settings.OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
        "max_tokens": 10,
    },
    timeout=30,
)
print(resp.status_code)
print(resp.json())