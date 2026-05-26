import os
from functools import lru_cache
from uuid import uuid4

import redis
from django.conf import settings

PRESENCE_KEY_PREFIX = "nxtturn:presence:user:"
PRESENCE_CONNECTION_PREFIX = "nxtturn:presence:conn:"
PRESENCE_TTL_SECONDS = 75


@lru_cache(maxsize=1)
def _get_redis_client():
    redis_url = getattr(settings, "REDIS_URL", None) or os.getenv("REDIS_URL", "redis://redis:6379/0")
    return redis.Redis.from_url(redis_url, decode_responses=True)


def _connections_key(user_id):
    return f"{PRESENCE_KEY_PREFIX}{int(user_id)}:connections"


def _connection_key(user_id, connection_id):
    return f"{PRESENCE_CONNECTION_PREFIX}{int(user_id)}:{connection_id}"


def new_presence_connection_id():
    return uuid4().hex


def set_user_online(user_id, connection_id, ttl_seconds=PRESENCE_TTL_SECONDS):
    try:
        client = _get_redis_client()
        conn_key = _connection_key(user_id, connection_id)
        user_key = _connections_key(user_id)
        client.setex(conn_key, int(ttl_seconds), "1")
        client.sadd(user_key, connection_id)
        client.expire(user_key, int(ttl_seconds) * 2)
    except Exception:
        return


def refresh_user_presence(user_id, connection_id, ttl_seconds=PRESENCE_TTL_SECONDS):
    try:
        client = _get_redis_client()
        conn_key = _connection_key(user_id, connection_id)
        user_key = _connections_key(user_id)
        if client.exists(conn_key):
            client.expire(conn_key, int(ttl_seconds))
        client.expire(user_key, int(ttl_seconds) * 2)
    except Exception:
        return


def set_user_offline(user_id, connection_id):
    try:
        client = _get_redis_client()
        conn_key = _connection_key(user_id, connection_id)
        user_key = _connections_key(user_id)
        client.delete(conn_key)
        client.srem(user_key, connection_id)
        if not client.scard(user_key):
            client.delete(user_key)
    except Exception:
        return


def is_user_online(user_id):
    try:
        client = _get_redis_client()
        user_key = _connections_key(user_id)
        connection_ids = client.smembers(user_key)
        if not connection_ids:
            return False

        online = False
        stale_connections = []
        for connection_id in connection_ids:
            if client.exists(_connection_key(user_id, connection_id)):
                online = True
            else:
                stale_connections.append(connection_id)

        if stale_connections:
            client.srem(user_key, *stale_connections)
        if not online and not client.scard(user_key):
            client.delete(user_key)
        return online
    except Exception:
        return False
