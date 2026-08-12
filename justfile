# https://just.systems

run-rust:
     cd backend && uv run uvicorn src.main_rust:app --host 0.0.0.0 --port 8000 --reload

run-py:
    cd backend && uv run uvicorn src.main_py:app --host 0.0.0.0 --port 8000 --reload

bench-rs:
    cd scripts && ./benchmark.sh 10.0.0.6 rust churn

bench-py:
    cd scripts && ./benchmark.sh 10.0.0.6 python churn
