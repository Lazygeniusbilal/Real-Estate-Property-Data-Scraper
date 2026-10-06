"""Smoke test: run a tiny real scrape against the live site.

Marked ``network`` so it can be skipped offline::

    uv run pytest -m "not network"
    uv run pytest tests/test_smoke.py -m network
"""

from __future__ import annotations

from pathlib import Path

import pytest

from graana.config import City, OutputConfig, ScrapeConfig
from graana.scrape import run

pytestmark = pytest.mark.network


@pytest.mark.network
def test_smoke_single_city_two_listings(tmp_path: Path) -> None:
    config = ScrapeConfig(
        cities=[City(id=1, name="Islamabad")],
        purposes=["buy"],
        types=["residential"],
        output=OutputConfig(root=tmp_path),
    )
    written = run(config, limit=2, skip_details=False)
    assert written, "expected at least one parquet file"
    path = Path(written[0])
    assert path.exists()
    assert path.suffix == ".parquet"
