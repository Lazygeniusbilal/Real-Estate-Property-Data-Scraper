"""Recursively redact PII from raw payloads before they are persisted.

PII (agent names, phones, emails, user/agent identifiers) must never be written
to disk. Agency *business* name is retained for aggregate stats; agency phone and
email are removed.
"""

from __future__ import annotations

from typing import Any

# Keys removed anywhere in the payload.
PII_KEYS: frozenset[str] = frozenset(
    {
        "phone",
        "phone_number",
        "email",
        "agentDetails",
        "agentId",
        "userId",
        "systemUserId",
        "riderId",
        "Username",
        "whatsapp",
    }
)

# Agent display name is a top-level key on the listing/detail object; area and
# city also use "name", so only the top-level one is dropped.
TOP_LEVEL_PII_KEYS: frozenset[str] = frozenset({"name"})


def redact(value: Any, *, top_level: bool = True) -> Any:
    """Return ``value`` with PII keys removed at every depth."""
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if key in PII_KEYS:
                continue
            if top_level and key in TOP_LEVEL_PII_KEYS:
                continue
            cleaned[key] = redact(item, top_level=False)
        return cleaned
    if isinstance(value, list):
        return [redact(item, top_level=False) for item in value]
    return value
