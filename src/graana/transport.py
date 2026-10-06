"""Swappable list-page transports.

Transport A (default) hits the structured JSON API: ``/search/listings``.
Transport B (fallback) parses the path-based HTML page's ``__NEXT_DATA__`` and
returns only a reduced subset of fields for resilience.
"""

from __future__ import annotations

import json
import re
from typing import Any, Protocol

from bs4 import BeautifulSoup

from graana.config import TransportConfig
from graana.http import HttpClient

_NEXT_DATA_RE = re.compile(
    r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL
)

# purpose token used in HTML path pages: buy -> sale, rent -> rent
_PURPOSE_TOKEN = {"buy": "sale", "rent": "rent"}

# Fields the HTML fallback can reliably provide; everything else is null.
_FALLBACK_FIELDS = ("id", "price", "area", "location", "type", "bedrooms")


class Transport(Protocol):
    """Interface every transport must satisfy."""

    source: str

    def fetch_page(
        self, city_id: int, purpose: str, type_: str, page: int
    ) -> tuple[list[dict[str, Any]], int]:
        """Return ``(listings, total_count)`` for one page."""
        ...  # pragma: no cover - protocol


class JsonApiTransport:
    """Default transport: the site's structured JSON listings API."""

    source = "json_api"

    def __init__(self, base_url: str, client: HttpClient) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client

    def fetch_page(
        self, city_id: int, purpose: str, type_: str, page: int
    ) -> tuple[list[dict[str, Any]], int]:
        response = self._client.get(
            f"{self._base_url}/search/listings",
            params={
                "cityId": city_id,
                "purpose": purpose,
                "type": type_,
                "page": page,
            },
        )
        payload = response.json()
        listings = payload.get("data") or []
        total = int(payload.get("count") or 0)
        return listings, total


class HtmlFallbackTransport:
    """Fallback transport: parse the path page's embedded ``__NEXT_DATA__``.

    Returns only :data:`_FALLBACK_FIELDS`; all other fields are ``None``. This
    exists solely to keep the scrape alive if the JSON transport breaks.
    """

    source = "html_fallback"

    def __init__(self, base_url: str, client: HttpClient) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client

    def fetch_page(
        self, city_id: int, purpose: str, type_: str, page: int
    ) -> tuple[list[dict[str, Any]], int]:
        token = _PURPOSE_TOKEN.get(purpose, purpose)
        url = f"{self._base_url}/{token}/{type_}-properties-{token}-{city_id}/"
        response = self._client.get(
            url, params={"pageSize": 30, "page": page}
        )
        soup = BeautifulSoup(response.content, "html.parser")
        tag = soup.find("script", id="__NEXT_DATA__")
        if tag is None or not tag.string:
            raise ValueError(f"no __NEXT_DATA__ found at {url}")
        data = json.loads(tag.string)
        page_props = data.get("props", {}).get("pageProps", {})
        raw_listings = page_props.get("properties") or []
        total = int(page_props.get("propertiesCount") or 0)
        listings = [self._to_core(listing) for listing in raw_listings]
        return listings, total

    @staticmethod
    def _to_core(listing: dict[str, Any]) -> dict[str, Any]:
        area = listing.get("area") or {}
        city = listing.get("city") or {}
        location = area.get("name") or city.get("name")
        core: dict[str, Any] = {
            "id": listing.get("id"),
            "price": listing.get("price"),
            "area": listing.get("size"),
            "location": location,
            "type": listing.get("subtype") or listing.get("type"),
            "bedrooms": listing.get("bed"),
        }
        # Any key outside the reduced subset is explicitly null (kept out of the
        # dict entirely so downstream column handling is consistent).
        _ = _FALLBACK_FIELDS
        return core


def make_transport(
    kind: str, base_url: str, config: TransportConfig
) -> Transport:
    """Build a transport by name. ``kind`` is ``json`` or ``html``."""
    client = HttpClient(config)
    if kind == "json":
        return JsonApiTransport(base_url, client)
    if kind == "html":
        return HtmlFallbackTransport(base_url, client)
    raise ValueError(f"unknown transport: {kind}")
