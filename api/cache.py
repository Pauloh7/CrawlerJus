import os
import json
from redis import asyncio as redis

CACHE_URL = os.getenv("CACHE_URL", "redis://redis:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "300"))

redis_client = redis.from_url(
    CACHE_URL,
    encoding="utf-8",
    decode_responses=True
)

async def get_cache(key: str):
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None

async def set_cache(key: str, value: dict):
    await redis_client.set(key, json.dumps(value, ensure_ascii=False), ex=CACHE_TTL)