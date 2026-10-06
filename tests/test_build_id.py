"""Tests for build-id discovery and 404-refresh-then-retry behaviour."""

from __future__ import annotations

import responses

from graana.build_id import BuildIdProvider, detail_url, fetch_detail
from graana.config import TransportConfig
from graana.http import HttpClient

BASE = "https://www.graana.com"


def _provider_and_client() -> tuple[BuildIdProvider, HttpClient]:
    client = HttpClient(TransportConfig(rate_limit_rps=50, timeout=5))
    return BuildIdProvider(BASE, client), client


@responses.activate
def test_fetch_build_id_from_html() -> None:
    responses.add(
        responses.GET,
        f"{BASE}/",
        body='<script>{"buildId":"abc123"}</script>',
        status=200,
    )
    provider, _ = _provider_and_client()
    assert provider.build_id == "abc123"


@responses.activate
def test_fetch_detail_refreshes_build_id_once_on_404() -> None:
    responses.add(
        responses.GET, f"{BASE}/", body='{"buildId":"v1"}', status=200
    )
    responses.add(
        responses.GET, f"{BASE}/", body='{"buildId":"v2"}', status=200
    )
    # stale build id -> 404, then fresh build id -> 200
    responses.add(
        responses.GET, detail_url(BASE, "v1", 1558011), status=404
    )
    responses.add(
        responses.GET,
        detail_url(BASE, "v2", 1558011),
        json={"pageProps": {"data": {"id": 1558011, "price": "1"}}},
        status=200,
    )
    provider, client = _provider_and_client()
    detail = fetch_detail(client, provider, BASE, 1558011)
    assert detail == {"id": 1558011, "price": "1"}
    # homepage hit once at start + once for refresh
    assert provider.build_id == "v2"


@responses.activate
def test_fetch_detail_returns_none_when_still_missing() -> None:
    responses.add(responses.GET, f"{BASE}/", body='{"buildId":"v1"}', status=200)
    responses.add(responses.GET, f"{BASE}/", body='{"buildId":"v1"}', status=200)
    responses.add(responses.GET, detail_url(BASE, "v1", 42), status=404)
    responses.add(responses.GET, detail_url(BASE, "v1", 42), status=404)
    provider, client = _provider_and_client()
    assert fetch_detail(client, provider, BASE, 42) is None
