"""Unit tests: per-source rate limiter (FR-016)."""

from __future__ import annotations

from app.security.ratelimit import RateLimiter


def test_allows_within_limit():
    limiter = RateLimiter(per_minute=3)
    assert all(limiter.allow("skybot", now=t) for t in (0.0, 1.0, 2.0))


def test_rejects_over_limit():
    limiter = RateLimiter(per_minute=2)
    assert limiter.allow("skybot", now=0.0)
    assert limiter.allow("skybot", now=0.1)
    assert not limiter.allow("skybot", now=0.2)


def test_window_slides():
    limiter = RateLimiter(per_minute=1, window_s=60.0)
    assert limiter.allow("skybot", now=0.0)
    assert not limiter.allow("skybot", now=30.0)
    assert limiter.allow("skybot", now=61.0)  # outside the window


def test_sources_are_isolated():
    limiter = RateLimiter(per_minute=1)
    assert limiter.allow("skybot", now=0.0)
    assert limiter.allow("jira", now=0.0)
