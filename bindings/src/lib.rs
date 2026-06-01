#![allow(unsafe_op_in_unsafe_fn)]

use std::sync::Arc;

use axum_rate_limiter::{RateLimiter, redis::{RedisAiLimiter, RedisLimiter}};
use pyo3::{Bound, exceptions::PyRuntimeError, prelude::*, types::PyModule};
use tokio::runtime::Runtime;

fn to_py_runtime_error(error: impl std::fmt::Display) -> PyErr {
    PyRuntimeError::new_err(error.to_string())
}

#[pyclass(name = "RedisLimiter")]
struct PyRedisLimiter {
    inner: Arc<RedisLimiter>,
    runtime: Arc<Runtime>,
    redis_url: String,
}

#[pymethods]
impl PyRedisLimiter {
    #[new]
    fn new(redis_url: String) -> PyResult<Self> {
        let runtime = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .map_err(to_py_runtime_error)?;
        let client = redis::Client::open(redis_url.as_str()).map_err(to_py_runtime_error)?;
        let connection = runtime
            .block_on(client.get_multiplexed_async_connection())
            .map_err(to_py_runtime_error)?;

        Ok(Self {
            inner: Arc::new(RedisLimiter::new(connection)),
            runtime: Arc::new(runtime),
            redis_url,
        })
    }

    fn allow(&self, identifier: String) -> bool {
        let limiter = Arc::clone(&self.inner);
        let runtime = Arc::clone(&self.runtime);

        runtime.block_on(async move { limiter.allow(&identifier).await })
    }

    fn __repr__(&self) -> String {
        format!("RedisLimiter(redis_url={:?})", self.redis_url)
    }

    #[getter]
    fn redis_url(&self) -> &str {
        &self.redis_url
    }
}

#[pyclass(name = "RedisAiLimiter")]
struct PyRedisAiLimiter {
    inner: Arc<RedisAiLimiter>,
    runtime: Arc<Runtime>,
    redis_url: String,
}

#[pymethods]
impl PyRedisAiLimiter {
    #[new]
    fn new(redis_url: String) -> PyResult<Self> {
        let runtime = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .map_err(to_py_runtime_error)?;
        let client = redis::Client::open(redis_url.as_str()).map_err(to_py_runtime_error)?;
        let connection = runtime
            .block_on(client.get_multiplexed_async_connection())
            .map_err(to_py_runtime_error)?;

        Ok(Self {
            inner: Arc::new(RedisAiLimiter::new(connection)),
            runtime: Arc::new(runtime),
            redis_url,
        })
    }

    fn allow(&self, identifier: String, model: String) -> bool {
        let limiter = Arc::clone(&self.inner);
        let runtime = Arc::clone(&self.runtime);

        runtime.block_on(async move { limiter.allow(&identifier, &model).await })
    }

    fn __repr__(&self) -> String {
        format!("RedisAiLimiter(redis_url={:?})", self.redis_url)
    }

    #[getter]
    fn redis_url(&self) -> &str {
        &self.redis_url
    }
}

#[pymodule]
#[pyo3(name = "rustgate_bindings")]
fn rustgate_bindings(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyRedisLimiter>()?;
    m.add_class::<PyRedisAiLimiter>()?;
    Ok(())
}
