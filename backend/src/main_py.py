from fastapi import Depends, FastAPI, Request
from src.auto_py import rate_limit_auto_py

app = FastAPI()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/models/auto",
    dependencies=[Depends(rate_limit_auto_py)],
)
async def auto_py_model(request: Request) -> dict[str, str]:
    return {"model": request.state.allowed_model}
