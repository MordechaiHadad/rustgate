import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from src.rustgate_bindings import RedisAiLimiter


GPT_5_MODEL = "gpt-5"
GPT_4_MODEL = "gpt-4"


def _client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


async def _allow_model(request: Request, model: str) -> bool:
    return await run_in_threadpool(limiter.allow, _client_identifier(request), model)


def _model_used_response(model: str) -> dict[str, str]:
    return {"model": model}


def _model_limited_response(message: str) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": message})


app = FastAPI()
limiter = RedisAiLimiter(os.environ.get("RUSTGATE_REDIS_URL", "redis://127.0.0.1:6379/0"))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/models/auto", response_model=None)
async def auto_model(request: Request):
    if await _allow_model(request, GPT_5_MODEL):
        return _model_used_response(GPT_5_MODEL)
    if await _allow_model(request, GPT_4_MODEL):
        return _model_used_response(GPT_4_MODEL)
    return _model_limited_response("both gpt-4 & gpt-5 were used too much")


@app.get("/models/gpt-5", response_model=None)
async def gpt_5_only(request: Request):
    if await _allow_model(request, GPT_5_MODEL):
        return _model_used_response(GPT_5_MODEL)
    return _model_limited_response("gpt-5 used too much")


@app.get("/models/gpt-4", response_model=None)
async def gpt_4_only(request: Request):
    if await _allow_model(request, GPT_4_MODEL):
        return _model_used_response(GPT_4_MODEL)
    return _model_limited_response("gpt-4 used too much")
