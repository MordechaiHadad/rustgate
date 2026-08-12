# https://just.systems

run-rust:
     cd backend && uv run uvicorn src.main_rust:app --host 0.0.0.0 --port 8000 --reload

run-py:
    cd backend && uv run uvicorn src.main_py:app --host 0.0.0.0 --port 8000 --reload
