"""Raw output writer.

Layout (per the spec):

    data/raw/YYYY-MM-DD/<city>.parquet

One folder per scrape run, never overwritten. Each Parquet file holds the
as-scraped listing fields plus ``scraped_at`` and ``source``. The full detail
JSON is retained in a separate ``detail_json`` column.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl

from graana.config import OutputConfig
from graana.redact import redact


def run_date_dir(output: OutputConfig, run_date: str | None = None) -> Path:
    """Return (and create) ``<root>/YYYY-MM-DD`` for this run."""
    day = run_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    directory = output.root / day
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _slugify_city(name: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in name.strip())
    return "-".join(part for part in cleaned.split("-") if part)


def build_rows(
    listings: list[dict[str, Any]],
    details: dict[int, dict[str, Any] | None],
    *,
    source: str,
    scraped_at: str,
) -> list[dict[str, Any]]:
    """Merge list rows with their (redacted) detail JSON.

    The list row is the base; the detail JSON is redacted of PII and stored as a
    JSON string in ``detail_json``.
    """
    rows: list[dict[str, Any]] = []
    for listing in listings:
        listing_id = listing.get("id")
        detail = details.get(listing_id) if listing_id is not None else None
        row = dict(listing)
        row["scraped_at"] = scraped_at
        row["source"] = source
        row["detail_json"] = (
            json.dumps(redact(detail), ensure_ascii=False) if detail else None
        )
        rows.append(row)
    return rows


def write_city_parquet(
    rows: list[dict[str, Any]],
    output: OutputConfig,
    city_name: str,
    run_date: str | None = None,
) -> Path:
    """Write one city's rows to ``<root>/YYYY-MM-DD/<city>.parquet``."""
    directory = run_date_dir(output, run_date)
    path = directory / f"{_slugify_city(city_name)}.parquet"
    if path.exists():
        # Never overwrite a prior snapshot file.
        raise FileExistsError(f"refusing to overwrite existing snapshot: {path}")
    frame = pl.DataFrame(rows, infer_schema_length=None)
    frame.write_parquet(path)
    return path
