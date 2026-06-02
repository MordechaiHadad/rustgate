from fastapi import Depends, FastAPI, Request
from src.funcs import rate_limit

app = FastAPI()


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
