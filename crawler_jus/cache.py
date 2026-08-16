import json
import os

from redis import asyncio as redis

CACHE_URL = os.getenv("CACHE_URL", "redis://redis:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "300"))

redis_client = redis.from_url(CACHE_URL, encoding="utf-8", decode_responses=True)


async def get_cache(key: str):
    """Busca um valor no cache Redis.
    
    Args:
        key (str): Chave usada para localizar o valor no cache.
    
    Returns:
        dict | None: Valor desserializado quando encontrado ou None quando a chave não existe.
    """
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None


async def set_cache(key: str, value: dict, ttl: int | None = None):
    """Armazena um valor no cache Redis com tempo de expiração.
    
    Args:
        key (str): Chave usada para armazenar o valor.
        value (dict): Dicionário que será serializado em JSON.
        ttl (int | None): Tempo de vida em segundos. Quando omitido, usa o TTL padrão.
    """
    ex = ttl if ttl is not None else CACHE_TTL
    await redis_client.set(key, json.dumps(value, ensure_ascii=False), ex=ex)
