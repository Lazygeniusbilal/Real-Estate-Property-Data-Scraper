"""Typed configuration for the Graana scraper.

All settings live here (or in ``config/cities.yaml``) and are loaded through
Pydantic models with ``extra="forbid"`` so typos fail fast. Cities are never
discovered from the network at runtime: the committed ``config/cities.yaml`` is
the single source of truth.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CITIES_PATH = REPO_ROOT / "config" / "cities.yaml"


class City(BaseModel):
    """A single Graana city and its ``cityId``."""

    model_config = ConfigDict(extra="forbid")

    id: int
    name: str


class CitiesFile(BaseModel):
    """Schema of ``config/cities.yaml``."""

    model_config = ConfigDict(extra="forbid")

    cities: list[City]


class TransportConfig(BaseModel):
    """HTTP transport behaviour. Conservative by default; raise only if safe."""

    model_config = ConfigDict(extra="forbid")

    user_agent: str = "graana-research-bot/0.1 (contact: Email)"
    rate_limit_rps: float = Field(default=3.0, gt=0, le=50.0)
    threads: int = Field(default=6, ge=1, le=32)
    timeout: float = Field(default=30.0, gt=0)


class OutputConfig(BaseModel):
    """Raw output location. One folder per run; never overwritten."""

    model_config = ConfigDict(extra="forbid")

    root: Path = Path("data/raw")
    retain_detail_json: bool = True


class ScrapeConfig(BaseModel):
    """Top-level scrape configuration."""

    model_config = ConfigDict(extra="forbid")

    base_url: str = "https://www.graana.com"
    purposes: list[str] = Field(default_factory=lambda: ["buy", "rent"])
    types: list[str] = Field(default_factory=lambda: ["residential", "commercial"])
    transport: TransportConfig = Field(default_factory=TransportConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    cities: list[City]


def load_config(cities_path: Path | None = None) -> ScrapeConfig:
    """Load and validate the city list plus default scrape settings."""
    path = cities_path or DEFAULT_CITIES_PATH
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    cities_file = CitiesFile.model_validate(raw)
    return ScrapeConfig(cities=cities_file.cities)
