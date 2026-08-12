# https://just.systems

run-rust:
     cd backend && ulimit -Sn 20000 && uv run uvicorn src.main_rust:app --host 0.0.0.0 --port 8000 --reload

run-py:
    cd backend && ulimit -Sn 20000 && uv run uvicorn src.main_py:app --host 0.0.0.0 --port 8000 --reload

bench-rs:
    cd scripts && ulimit -Sn 20000 && ./benchmark.sh 10.0.0.6 rust churn

bench-py:
    cd scripts && ulimit -Sn 20000 && ./benchmark.sh 10.0.0.6 python churn
