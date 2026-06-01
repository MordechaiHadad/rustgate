Rustgate Backend
=================

Small FastAPI backend that uses a Rust pyo3 extension for rate-limiting logic.

Summary
-------
This repository contains two parts:
- bindings: a Rust crate that exposes Python bindings via pyo3/maturin
- backend: a small FastAPI app that loads the compiled extension and serves a few endpoints

The Rust extension is built with maturin and the Python package metadata is in
pyproject.toml (maturin is the build-backend).

Prerequisites
-------------
- Rust toolchain (rustc/cargo)
- Python 3.10+
- uv (the uv dependency manager)

Quick Start
----------------------
1. Ensure uv is installed and available on PATH.

2. Install dependencies and build everything via uv:

   `uv sync`

   "uv sync" installs pinned dependencies from uv.lock and runs the build steps
   for this repository, including building the Rust pyo3 extension and
   installing the local Python package into the environment uv manages.


Run the server
--------------
After `uv sync` completes you can start the FastAPI server with uv:

    uv run uvicorn main:app --app-dir src --host 127.0.0.1 --port 8001

This uses the environment and commands declared in the repo's uv configuration.

Environment
-----------
- RUSTGATE_REDIS_URL: redis connection string used by the rate limiter
  (default: redis://127.0.0.1:6379/0)

API Endpoints
-------------
- GET /health: basic health check
- GET /models/auto: choose a model (gpt-5 preferred, fallback gpt-4)
- GET /models/gpt-5: attempt to use gpt-5 (429 if limited)
- GET /models/gpt-4: attempt to use gpt-4 (429 if limited)

Benchmark (sample load test)
----------------------------
Key results

- Duration: 30.00 s
- Requests/sec: 824.34
- Fastest latency: 41.05 ms
- Average latency: 121.56 ms
- 95th percentile (p95): 249.92 ms
- Slowest latency: 811.82 ms
- Rate-limited responses (HTTP 429): 24633
