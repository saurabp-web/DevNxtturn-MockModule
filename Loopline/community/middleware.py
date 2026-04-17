# community/middleware.py

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from urllib.parse import parse_qs


# --- NEW: "SECRET HANDSHAKE" MIDDLEWARE ---
class CypressTestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If Cypress sends its secret header, temporarily switch to the memory
        # backend so the test can read the `mail.outbox`.
        if "X-Cypress-Test" in request.headers:
            from django.conf import settings

            settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        response = self.get_response(request)
        return response


# --- EXISTING WEBSOCKET MIDDLEWARE (UNCHANGED) ---
@database_sync_to_async
def get_user(token_key):
    try:
        token = Token.objects.select_related("user").get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token_key = query_params.get("token", [None])[0]

        if token_key:
            scope["user"] = await get_user(token_key)
        else:
            scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)
