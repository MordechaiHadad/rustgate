import uvicorn


def server_py() -> None:
    uvicorn.run("src.main_py:app", reload=True)


def server_rust() -> None:
    uvicorn.run("src.main_rust:app", reload=True)
