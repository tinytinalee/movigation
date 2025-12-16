# backend/utils/redis.py

import os

import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
)


def get_redis_client():
    """Redis 클라이언트 반환"""
    return redis_client
