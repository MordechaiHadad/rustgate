import json
import os
from fastapi import Request, HTTPException
from src.rustgate_bindings import RedisAiLimiter

limiter = RedisAiLimiter(
    os.environ.get("RUSTGATE_REDIS_URL", "redis://127.0.0.1:6379/0")
)

def _client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


def _extract_query(body: bytes) -> str:
    if not body:
        return ""
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return ""
    return payload.get("query", "") if isinstance(payload, dict) else ""


def rate_limit(*models: str):
    async def dependency(request: Request) -> None:
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="body required")

        query = _extract_query(body)
        if not query:
            raise HTTPException(status_code=400, detail="query required")

        identifier = _client_identifier(request)

        for model in models:
            payload = json.dumps({"model": model, "query": query}).encode()
            allowed = await limiter.allow(identifier, payload) 
            if allowed:
                request.state.allowed_model = model
                return

        raise HTTPException(status_code=429, detail="rate limited")

    return dependency
