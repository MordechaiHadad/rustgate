#![allow(unsafe_op_in_unsafe_fn)]

use std::{
    pin::Pin,
    sync::Arc,
    task::{Context, Poll},
};

use axum_rate_limiter::{
    RateLimiter,
    redis::{
        AiRequestError, AiUsage, RedisAiLimiter, RedisLimiter,
        extract_ai_usage as extract_ai_usage_inner,
    },
};
use pyo3::{Bound, exceptions::PyRuntimeError, prelude::*, types::PyModule};
use tokio::runtime::Runtime;

fn to_py_runtime_error(error: impl std::fmt::Display) -> PyErr {
    PyRuntimeError::new_err(error.to_string())
}

fn ai_request_error_to_string(error: &AiRequestError) -> String {
    match error {
        AiRequestError::InvalidJson(err) => format!("invalid json: {err}"),
        AiRequestError::UnsupportedModel(model) => format!("unsupported model: {model}"),
        AiRequestError::ChargeOverflow => "charge overflow".to_string(),
        AiRequestError::Tokenizer(message) => format!("tokenizer error: {message}"),
    }
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

#[pyclass(name = "AiUsage", skip_from_py_object)]
struct PyAiUsage {
    inner: AiUsage,
}

#[pymethods]
impl PyAiUsage {
    #[getter]
    fn model(&self) -> &str {
        &self.inner.model
    }

    #[getter]
    fn query_tokens(&self) -> i64 {
        self.inner.query_tokens
    }

    #[getter]
    fn charge_units(&self) -> i64 {
        self.inner.charge_units
    }

    fn __repr__(&self) -> String {
        format!(
            "AiUsage(model={:?}, query_tokens={}, charge_units={})",
            self.inner.model, self.inner.query_tokens, self.inner.charge_units
        )
    }
}

pub struct TokioContextFuture<F> {
    pub handle: tokio::runtime::Handle,
    pub future: F,
}

impl<F: Future> Future for TokioContextFuture<F> {
    type Output = F::Output;

    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        let this = unsafe { self.get_unchecked_mut() };
        let _guard = this.handle.enter();
        let inner_future = unsafe { Pin::new_unchecked(&mut this.future) };
        inner_future.poll(cx)
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
        let runtime = tokio::runtime::Builder::new_multi_thread()
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

    async fn allow(&self, identifier: String, body: Vec<u8>) -> PyResult<bool> {
        let usage = extract_ai_usage_inner(&body)
            .map_err(|error| to_py_runtime_error(ai_request_error_to_string(&error)))?;
        let limiter = Arc::clone(&self.inner);
        let handle = self.runtime.handle().clone();

        let context_aware_fut = TokioContextFuture {
            handle,
            future: async move { limiter.allow(&identifier, &usage).await },
        };

        Ok(context_aware_fut.await)
    }

    fn __repr__(&self) -> String {
        format!("RedisAiLimiter(redis_url={:?})", self.redis_url)
    }

    #[getter]
    fn redis_url(&self) -> &str {
        &self.redis_url
    }
}

#[pyfunction]
fn extract_ai_usage(body: Vec<u8>) -> PyResult<PyAiUsage> {
    let usage = extract_ai_usage_inner(&body)
        .map_err(|error| to_py_runtime_error(ai_request_error_to_string(&error)))?;
    Ok(PyAiUsage { inner: usage })
}

#[pymodule]
#[pyo3(name = "rustgate_bindings")]
fn rustgate_bindings(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyRedisLimiter>()?;
    m.add_class::<PyRedisAiLimiter>()?;
    m.add_class::<PyAiUsage>()?;
    m.add_function(wrap_pyfunction!(extract_ai_usage, m)?)?;
    Ok(())
}
