"""CLI entry point for the scraper.

Examples::

    uv run python -m graana --limit 2          # smoke test: 2 listings/city
    uv run python -m graana                     # full all-cities scrape
    uv run python -m graana --transport html    # force HTML fallback
"""

from __future__ import annotations

import argparse

from graana.config import load_config
from graana.logging_utils import configure_logging
from graana.scrape import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Graana all-cities scraper")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max listings per city (smoke test). Default: no limit.",
    )
    parser.add_argument(
        "--transport",
        choices=["json", "html"],
        default="json",
        help="List transport to use (default: json).",
    )
    parser.add_argument(
        "--skip-details",
        action="store_true",
        help="Skip detail enrichment (list pages only).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging()
    config = load_config()
    written = run(
        config,
        transport_kind=args.transport,
        limit=args.limit,
        skip_details=args.skip_details,
    )
    print(f"Wrote {len(written)} city files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
