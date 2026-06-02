Rustgate Backend
=================

Small FastAPI backend that uses a Rust pyo3 extension for AI token-aware rate
limiting backed by Redis.

Summary
-------
This repository contains two parts:
- `bindings/` -- a Rust crate that exposes Python bindings via pyo3/maturin
- `backend/` -- a small FastAPI app that loads the compiled extension and serves
  a few endpoints

The Rust extension uses the axum-rate-limiter crate and OpenAI's tiktoken-rs to
count query tokens. Rate limits are applied per model and per sliding window,
using the query's estimated token count multiplied by a model-specific cost
factor.

Prerequisites
-------------
- Rust toolchain (rustc/cargo)
- Python 3.10+
- uv (the uv dependency manager)
- Redis (running on default port 6379, or configure with RUSTGATE_REDIS_URL)

Quick Start
-----------
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
- RUSTGATE_REDIS_URL -- redis connection string used by the rate limiter
  (default: redis://127.0.0.1:6379/0)

API Endpoints
-------------
All POST endpoints accept a JSON body with a `query` field, parsed by the Rust
layer for token counting.

- `GET /health` -- basic health check, returns `{"status": "ok"}`

- `POST /models/auto` -- tries gpt-5 first, falls back to gpt-4 if rate limited.
  Returns `{"model": "<model_name>"}`.

- `POST /models/gpt-5` -- attempts to use gpt-5. Returns 429 if rate limited.

- `POST /models/gpt-4` -- attempts to use gpt-4. Returns 429 if rate limited.

Rate Limiting
-------------
Rate limits are enforced in Rust via the `RedisAiLimiter` (axum-rate-limiter
crate) with the following rules:

- **Sliding window**: 10 minutes (600 seconds).
- **Total budget**: 5000 charge units per window per client, identified by IP
  (X-Forwarded-For or remote address).
- **Per-token cost**:
  - gpt-4 family: 1 charge unit per token
  - gpt-5 family: 25 charge units per token
- **Token counting**: uses tiktoken-rs with the appropriate tokenizer
  (Cl100kBase for gpt-4, O200kBase for gpt-5).
- **Zero-token queries**: bypass rate limiting entirely.

Example: a 200-token gpt-5 query costs 5000 charge units (200 x 25), consuming
the entire budget. The same 200-token query against gpt-4 costs only 200 charge
units (200 x 1).

Supported models
----------------
The Rust layer supports two model families:
- `gpt-4` and `gpt-4.*` (e.g. gpt-4, gpt-4.1)
- `gpt-5` and `gpt-5.*` (e.g. gpt-5, gpt-5.4)

Models like `gpt-4o`, `gpt-4o-mini`, `gpt-5-mini`, or `o3` are not currently
supported and will return a 400 error.

Benchmark (sample load test)
----------------------------
Load test with oha against the POST /models/auto endpoint:

    oha -z 30s -c 100 -m POST -d '{"query": "This is my grand query"}' \
      http://localhost:8001/models/auto

Results:

| Metric                  | Value         |
|-------------------------|---------------|
| Duration                | 30.01 s       |
| Requests/sec            | 1128.10       |
| Fastest latency         | 15.34 ms      |
| Average latency         | 88.76 ms      |
| Slowest latency         | 774.95 ms     |
| p50                     | 75.0 ms       |
| p90                     | 152.1 ms      |
| p95                     | 168.36 ms     |
| p99                     | 183.6 ms      |
| Rate-limited (429)      | 33713         |
| Successful (200)        | 40            |

Comparison with the lightweight `GET /health` endpoint (no rate limiting, no
token counting, no model rerouting, just a fast return):

    oha -z 30s -c 100 -m GET http://localhost:8001/health

| Metric                  | Value         |
|-------------------------|---------------|
| Duration                | 30.00 s       |
| Requests/sec            | 1496.39       |
| Fastest latency         | 13.70 ms      |
| Average latency         | 66.90 ms      |
| Slowest latency         | 1.89 s        |
| p50                     | 51.10 ms      |
| p90                     | 58.80 ms      |
| p95                     | 73.40 ms      |
| p99                     | 656.30 ms     |
| Successful (200)        | 44796         |
