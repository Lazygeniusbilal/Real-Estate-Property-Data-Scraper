"""Scrape orchestration: cities x purpose x type, pagination, detail, dedup."""

from __future__ import annotations

import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

from graana.build_id import BuildIdProvider, fetch_detail
from graana.config import City, ScrapeConfig
from graana.http import HttpClient
from graana.logging_utils import configure_logging
from graana.output import build_rows, write_city_parquet
from graana.transport import Transport, make_transport

PAGE_SIZE = 30

# Fields in the raw list payload that must never be persisted (PII).
_LIST_PII_FIELDS = frozenset({"name", "phone", "userId"})


def _strip_list_pii(listing: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in listing.items() if k not in _LIST_PII_FIELDS}


def scrape_city(
    city: City,
    config: ScrapeConfig,
    transport: Transport,
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Scrape one city across all purpose/type combos.

    Deduplicates by listing id within the run.
    """
    logger = configure_logging()
    seen: dict[int, dict[str, Any]] = {}
    for purpose in config.purposes:
        for type_ in config.types:
            page = 1
            total = None
            while True:
                listings, total = transport.fetch_page(
                    city.id, purpose, type_, page
                )
                if not listings:
                    break
                for listing in listings:
                    listing_id = listing.get("id")
                    if listing_id is None:
                        continue
                    if listing_id not in seen:
                        seen[listing_id] = _strip_list_pii(listing)
                if limit is not None and len(seen) >= limit:
                    logger.info(
                        "city=%s limit=%d reached", city.name, limit
                    )
                    return list(seen.values())[:limit]
                if total is not None and page * PAGE_SIZE >= total:
                    break
                page += 1
            logger.info(
                "city=%s purpose=%s type=%s total=%s fetched=%d",
                city.name,
                purpose,
                type_,
                total,
                len(seen),
            )
    return list(seen.values())


def enrich_details(
    listings: list[dict[str, Any]],
    config: ScrapeConfig,
    helper_client: HttpClient,
    provider: BuildIdProvider,
) -> dict[int, dict[str, Any] | None]:
    """Fetch detail JSON for each listing concurrently."""
    logger = configure_logging()
    details: dict[int, dict[str, Any] | None] = {}

    def _one(listing_id: int) -> tuple[int, dict[str, Any] | None]:
        try:
            return listing_id, fetch_detail(
                helper_client, provider, config.base_url, listing_id
            )
        except Exception as exc:  # noqa: BLE001 - keep the run alive
            logger.warning("detail failed id=%s: %s", listing_id, exc)
            return listing_id, None

    ids = [listing["id"] for listing in listings if listing.get("id") is not None]
    with ThreadPoolExecutor(max_workers=config.transport.threads) as pool:
        futures = [pool.submit(_one, listing_id) for listing_id in ids]
        for future in as_completed(futures):
            listing_id, detail = future.result()
            details[listing_id] = detail
    return details


def run(
    config: ScrapeConfig,
    *,
    transport_kind: str = "json",
    limit: int | None = None,
    skip_details: bool = False,
) -> list[str]:
    """Run the full scrape and return the written Parquet paths."""
    logger = configure_logging()
    transport = make_transport(transport_kind, config.base_url, config.transport)
    client = HttpClient(config.transport)
    provider = BuildIdProvider(config.base_url, client)
    # Fetch build id once at run start.
    logger.info("buildId=%s", provider.build_id)

    scraped_at = datetime.now(timezone.utc).isoformat()
    written: list[str] = []
    for city in config.cities:
        listings = scrape_city(city, config, transport, limit=limit)
        if not listings:
            logger.info("city=%s no listings; skipping", city.name)
            continue
        if skip_details:
            details: dict[int, dict[str, Any] | None] = {}
        else:
            details = enrich_details(listings, config, client, provider)
        rows = build_rows(
            listings, details, source=transport.source, scraped_at=scraped_at
        )
        path = write_city_parquet(rows, config.output, city.name)
        written.append(str(path))
        logger.info("wrote %s rows=%d", path, len(rows))
    return written


def estimate_pages(total: int, page_size: int = PAGE_SIZE) -> int:
    """Number of pages needed for ``total`` listings."""
    return max(1, math.ceil(total / page_size))
