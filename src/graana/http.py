"""HTTP layer: shared session, honest User-Agent, rate limiting, retries.

Rate limit, concurrency and User-Agent all come from
:class:`graana.config.TransportConfig` (never hardcoded).
"""

from __future__ import annotations

import threading
import time

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from graana.config import TransportConfig

_RETRYABLE_STATUS = frozenset({408, 429, 500, 502, 503, 504})


class RetryableHTTPError(Exception):
    """Raised for statuses that should trigger a tenacity retry."""


class RateLimiter:
    """A simple thread-safe token/interval limiter.

    Enforces at most ``rate_limit_rps`` requests per second across all threads
    by serialising calls to :meth:`acquire` around a minimum interval.
    """

    def __init__(self, rate_limit_rps: float) -> None:
        if rate_limit_rps <= 0:
            raise ValueError("rate_limit_rps must be positive")
        self._min_interval = 1.0 / rate_limit_rps
        self._lock = threading.Lock()
        self._next_allowed = 0.0

    def acquire(self) -> None:
        """Block until the next request is allowed."""
        with self._lock:
            now = time.monotonic()
            wait = self._next_allowed - now
            if wait > 0:
                time.sleep(wait)
                now = time.monotonic()
            self._next_allowed = now + self._min_interval


def build_session(config: TransportConfig) -> requests.Session:
    """Create a ``requests.Session`` with the configured User-Agent."""
    session = requests.Session()
    session.headers.update({"User-Agent": config.user_agent})
    return session


class HttpClient:
    """Rate-limited, retrying HTTP client shared across scraper threads."""

    def __init__(self, config: TransportConfig) -> None:
        self._config = config
        self._session = build_session(config)
        self._limiter = RateLimiter(config.rate_limit_rps)

    @property
    def session(self) -> requests.Session:
        return self._session

    @property
    def timeout(self) -> float:
        return self._config.timeout

    def get(
        self,
        url: str,
        *,
        params: dict[str, object] | None = None,
        allow_404: bool = False,
    ) -> requests.Response:
        """GET ``url`` with rate limiting and retries on transient failures.

        With ``allow_404=True`` a 404 is returned to the caller instead of
        raising, and is never retried (used for detail requests where a stale
        build id must be handled by the caller).
        """
        return self._get_with_retry(url, params, allow_404)

    @retry(
        retry=retry_if_exception_type(RetryableHTTPError),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _get_with_retry(
        self,
        url: str,
        params: dict[str, object] | None,
        allow_404: bool,
    ) -> requests.Response:
        self._limiter.acquire()
        response = self._session.get(
            url, params=params, timeout=self._config.timeout
        )
        if response.status_code in _RETRYABLE_STATUS:
            raise RetryableHTTPError(
                f"transient status {response.status_code} for {url}"
            )
        if allow_404 and response.status_code == 404:
            return response
        response.raise_for_status()
        return response
