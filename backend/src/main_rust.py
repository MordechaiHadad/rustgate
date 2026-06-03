import json

from fastapi import Depends, FastAPI, HTTPException, Request
from src._common import RUSTGATE_REDIS_URL, client_identifier, extract_query
from src.rustgate_bindings import RedisAiLimiter

limiter = RedisAiLimiter(RUSTGATE_REDIS_URL)

app = FastAPI()


def rate_limit(*models: str):
    async def dependency(request: Request) -> None:
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="body required")

        query = extract_query(body)
        if not query:
            raise HTTPException(status_code=400, detail="query required")

        identifier = client_identifier(request)

        for model in models:
            payload = json.dumps({"model": model, "query": query}).encode()
            allowed = await limiter.allow(identifier, payload)
            if allowed:
                request.state.allowed_model = model
                return

        raise HTTPException(status_code=429, detail="rate limited")

    return dependency


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/models/auto",
    dependencies=[Depends(rate_limit("gpt-5", "gpt-4"))],
)
async def auto_model(request: Request) -> dict[str, str]:
    return {"model": request.state.allowed_model}


@app.post("/models/gpt-5", dependencies=[Depends(rate_limit("gpt-5"))])
async def gpt_5(request: Request) -> dict[str, str]:
    return {"model": request.state.allowed_model}


@app.post("/models/gpt-4", dependencies=[Depends(rate_limit("gpt-4"))])
async def gpt_4(request: Request) -> dict[str, str]:
    return {"model": request.state.allowed_model}
