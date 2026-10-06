"""Tests for transports, pagination, dedup, and output writing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import responses

from graana.config import City, OutputConfig, ScrapeConfig, TransportConfig
from graana.http import HttpClient
from graana.output import write_city_parquet
from graana.scrape import estimate_pages, scrape_city
from graana.transport import HtmlFallbackTransport, JsonApiTransport

BASE = "https://www.graana.com"


def _client() -> HttpClient:
    return HttpClient(TransportConfig(rate_limit_rps=50, timeout=5))


@responses.activate
def test_json_transport_reads_data_and_count() -> None:
    responses.add(
        responses.GET,
        f"{BASE}/search/listings",
        json={"success": True, "data": [{"id": 1, "price": "10"}], "count": 1},
        status=200,
    )
    transport = JsonApiTransport(BASE, _client())
    listings, total = transport.fetch_page(1, "buy", "residential", 1)
    assert total == 1
    assert listings[0]["id"] == 1


@responses.activate
def test_scrape_city_paginates_and_dedupes() -> None:
    # count=61 -> pages 1..3 (30,30,1)
    def page(p: int, n: int, start: int) -> dict:
        return {
            "success": True,
            "count": 61,
            "data": [{"id": start + i, "name": "agent"} for i in range(n)],
        }

    responses.add(
        responses.GET,
        f"{BASE}/search/listings",
        json=page(1, 30, 0),
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE}/search/listings",
        json=page(2, 30, 0),  # duplicate ids on purpose
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE}/search/listings",
        json=page(3, 1, 100),
        status=200,
    )
    config = ScrapeConfig(cities=[City(id=1, name="Islamabad")], purposes=["buy"], types=["residential"])
    transport = JsonApiTransport(BASE, _client())
    listings = scrape_city(City(id=1, name="Islamabad"), config, transport)
    ids = {listing["id"] for listing in listings}
    assert ids == set(range(0, 30)) | {100}
    # PII stripped
    assert all("name" not in listing for listing in listings)


@responses.activate
def test_html_fallback_returns_reduced_subset() -> None:
    page_props = {
        "propertiesCount": 1,
        "properties": [
            {
                "id": 7,
                "price": "1000",
                "size": 5,
                "bed": 3,
                "subtype": "house",
                "type": "residential",
                "area": {"name": "Gulberg"},
                "city": {"name": "Lahore"},
                "phone": "123",
                "name": "agent",
            }
        ],
    }
    html = (
        '<html><script id="__NEXT_DATA__" type="application/json">'
        + json.dumps({"props": {"pageProps": page_props}})
        + "</script></html>"
    )
    responses.add(
        responses.GET, f"{BASE}/sale/residential-properties-sale-1/", body=html, status=200
    )
    transport = HtmlFallbackTransport(BASE, _client())
    listings, total = transport.fetch_page(1, "buy", "residential", 1)
    assert total == 1
    assert listings[0] == {
        "id": 7,
        "price": "1000",
        "area": 5,
        "location": "Gulberg",
        "type": "house",
        "bedrooms": 3,
    }


def test_estimate_pages() -> None:
    assert estimate_pages(0) == 1
    assert estimate_pages(30) == 1
    assert estimate_pages(31) == 2


def test_write_city_parquet_never_overwrites(tmp_path: Path) -> None:
    output = OutputConfig(root=tmp_path)
    rows = [{"id": 1, "scraped_at": "now", "source": "json_api", "detail_json": None}]
    path = write_city_parquet(rows, output, "Islamabad", run_date="2026-10-06")
    assert path.exists()
    assert path.name == "islamabad.parquet"
    with pytest.raises(FileExistsError):
        write_city_parquet(rows, output, "Islamabad", run_date="2026-10-06")
