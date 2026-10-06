"""Tests for PII redaction."""

from __future__ import annotations

from graana.redact import redact


def test_redact_removes_top_level_name_and_pii_keys() -> None:
    detail = {
        "id": 1,
        "name": "Aamir Hayat",
        "phone": "3339857363",
        "agentDetails": {"email": "x@example.com", "Username": "u"},
        "agency": {"name": "Aamir Estate", "phone": "0333", "email": "a@b.c"},
        "area": {"id": 9, "name": "CBR Town"},
    }
    out = redact(detail)
    assert "name" not in out  # top-level agent name dropped
    assert "phone" not in out
    assert "agentDetails" not in out
    assert out["area"]["name"] == "CBR Town"  # nested area name retained
    assert out["agency"]["name"] == "Aamir Estate"  # agency business name kept
    assert "phone" not in out["agency"]
    assert "email" not in out["agency"]


def test_redact_handles_lists() -> None:
    out = redact([{"phone": "1", "id": 2}, {"email": "e", "id": 3}])
    assert out == [{"id": 2}, {"id": 3}]
