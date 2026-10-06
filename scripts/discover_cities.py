"""One-time city discovery script.

Fetches Graana's canonical city list and writes ``config/cities.yaml``.

This script is NOT part of the runtime scrape path. It exists so the committed
``config/cities.yaml`` file can be regenerated if the source list changes. Run it
manually::

    uv run python scripts/discover_cities.py
"""

from __future__ import annotations

from pathlib import Path

import requests
import yaml

CITIES_ENDPOINT = "https://www.graana.com/data/cities"
USER_AGENT = "graana-research-bot/0.1 (contact: Email)"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "config" / "cities.yaml"


def fetch_cities() -> list[dict[str, object]]:
    """Return the canonical list of ``{id, name}`` city records."""
    response = requests.get(
        CITIES_ENDPOINT,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    records = payload.get("data") or []
    cities = [
        {"id": int(item["id"]), "name": str(item["name"]).strip()}
        for item in records
    ]
    return sorted(cities, key=lambda city: int(city["id"]))


def main() -> None:
    cities = fetch_cities()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        yaml.safe_dump({"cities": cities}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    print(f"Wrote {len(cities)} cities to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
