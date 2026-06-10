from __future__ import annotations

import json
import logging
import sys

import tiktoken
from fastapi import HTTPException, Request
from redis.asyncio.client import Redis

from src._common import RUSTGATE_REDIS_URL, client_identifier

logger = logging.getLogger(__name__)

AI_WINDOW_SECONDS = 120
TOTAL_AI_QUOTA_UNITS = 5000
GPT_4_COST_UNITS_PER_TOKEN = 1
GPT_5_COST_UNITS_PER_TOKEN = 25

_INCRBY_EXPIRE_SCRIPT = """
local current = redis.call('INCRBY', KEYS[1], ARGV[2])
if current == tonumber(ARGV[2]) then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""

_redis = Redis.from_url(
    RUSTGATE_REDIS_URL,
    protocol=2,
    max_connections=10000,
)


def _parse_model(model: str) -> str | None:
    if model == "gpt-4" or model.startswith("gpt-4."):
        return "cl100k_base"
    if model == "gpt-5" or model.startswith("gpt-5."):
        return "o200k_base"
    return None


def _cost_per_token(model: str) -> int:
    return (
        GPT_5_COST_UNITS_PER_TOKEN
        if model == "gpt-5" or model.startswith("gpt-5.")
        else GPT_4_COST_UNITS_PER_TOKEN
    )


def _count_tokens(query: str, encoding_name: str) -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(query))


async def _check_model(identifier: str, model: str, query: str) -> bool:
    encoding_name = _parse_model(model)
    if encoding_name is None:
        return False

    query_tokens = _count_tokens(query, encoding_name)
    charge_units = query_tokens * _cost_per_token(model)
    if charge_units == 0:
        return True

    key = f"rate_limit:ai:{identifier}"
    total = await _redis.eval(  # type: ignore[arg-type, misc]
        _INCRBY_EXPIRE_SCRIPT, 1, key, str(AI_WINDOW_SECONDS), str(charge_units)
    )
    total = int(total)

    if total > TOTAL_AI_QUOTA_UNITS:
        logger.debug(
            "rate limit exceeded for %s on %s "
            "(tokens=%d, charge_units=%d, total_units=%d, quota_units=%d)",
            identifier, model, query_tokens, charge_units, total, TOTAL_AI_QUOTA_UNITS,
        )
        return False

    return True


async def rate_limit_auto_py(request: Request) -> None:
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="body required")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid json")

    query = payload.get("query", "") if isinstance(payload, dict) else ""
    if not query:
        raise HTTPException(status_code=400, detail="query required")

    identifier = client_identifier(request)
    models = ("gpt-5", "gpt-4")

    for model in models:
        allowed = await _check_model(identifier, model, query)
        if allowed:
            request.state.allowed_model = model
            return

    raise HTTPException(status_code=429, detail="rate limited")
