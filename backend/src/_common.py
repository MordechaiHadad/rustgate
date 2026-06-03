import json
import os

from fastapi import Request

RUSTGATE_REDIS_URL = os.environ.get(
    "RUSTGATE_REDIS_URL", "redis://127.0.0.1:6379/0"
)


def client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


def extract_query(body: bytes) -> str:
    if not body:
        return ""
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return ""
    return payload.get("query", "") if isinstance(payload, dict) else ""
