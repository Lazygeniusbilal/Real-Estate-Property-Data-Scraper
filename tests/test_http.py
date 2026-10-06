"""Tests for the rate limiter and retry behaviour."""

from __future__ import annotations

import time

import pytest

from graana.http import RateLimiter


def test_rate_limiter_rejects_non_positive() -> None:
    with pytest.raises(ValueError):
        RateLimiter(0)


def test_rate_limiter_enforces_interval() -> None:
    limiter = RateLimiter(20.0)  # 50ms between calls
    start = time.monotonic()
    for _ in range(3):
        limiter.acquire()
    elapsed = time.monotonic() - start
    # 3 calls -> at least 2 intervals of 50ms after the first (which is free).
    assert elapsed >= 0.09
