"""Tests for typed config loading."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from graana.config import CitiesFile, load_config


def test_load_committed_cities() -> None:
    config = load_config()
    assert len(config.cities) >= 78
    ids = {city.id for city in config.cities}
    assert {1, 2, 3, 169}.issubset(ids)


def test_extra_keys_are_forbidden(tmp_path: Path) -> None:
    bad = tmp_path / "cities.yaml"
    bad.write_text(
        yaml.safe_dump({"cities": [{"id": 1, "name": "X", "typo": 2}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_config(bad)


def test_cities_file_requires_list() -> None:
    with pytest.raises(ValidationError):
        CitiesFile.model_validate({"cities": "not-a-list"})
