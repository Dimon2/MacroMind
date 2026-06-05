from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from macromind.brief.context import BriefContext
from macromind.brief.pipeline import NoSnapshotError, run_brief
from macromind.db.signal_snapshot import SignalSnapshotRow

_NOW = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
_DAY = date(2026, 6, 5)


def _minimal_context() -> BriefContext:
    row = SignalSnapshotRow(
        snapshot_date=_DAY,
        signal_name="risk_regime",
        status="computed",
        value=1.0,
        label="risk_on",
        reason=None,
        inputs={},
        metadata={"label": "risk_on"},
        as_of=_NOW,
    )
    return BriefContext(
        snapshot_date=_DAY,
        previous_snapshot_date=None,
        as_of=_NOW,
        snapshots_by_name={"risk_regime": row},
        deltas=[],
        crawl_status={"crawlers": {}, "missing": ["fred", "kalshi", "market"]},
    )


def test_run_brief_returns_markdown() -> None:
    repo = MagicMock()
    with (
        patch("macromind.brief.pipeline.utc_today", return_value=_DAY),
        patch("macromind.brief.pipeline.load_brief_context", return_value=_minimal_context()),
    ):
        text = run_brief(snapshot_repo=repo)
    assert "# MacroMind Daily Brief — 2026-06-05" in text


def test_run_brief_raises_when_no_snapshot() -> None:
    repo = MagicMock()
    with (
        patch("macromind.brief.pipeline.utc_today", return_value=_DAY),
        patch("macromind.brief.pipeline.load_brief_context", return_value=None),
        pytest.raises(NoSnapshotError) as exc,
    ):
        run_brief(snapshot_repo=repo)
    assert exc.value.snapshot_date == _DAY
