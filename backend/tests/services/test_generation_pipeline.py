"""Tests for the streaming Generate pipeline.

Forces the fixture path (no LLM credentials needed) and asserts that the
event sequence matches the spec ordering and that a strategy is persisted
at the end.
"""

from __future__ import annotations

import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest

from archimedes.api.generate_schemas import GenerateBrief
from archimedes.services.generation_pipeline import run_generation


@pytest.fixture(autouse=True)
def force_fixture_path(monkeypatch):
    monkeypatch.setenv("GENERATION_PIPELINE_FIXTURE", "1")


class _FakeStore:
    """In-memory JobStore stand-in. Captures the event sequence."""

    def __init__(self) -> None:
        self.events: list[dict] = []
        self.status: list[tuple[str, dict | None, str]] = []

    async def push_event(self, job_id, payload):
        self.events.append(payload)
        return len(self.events)

    async def update_status(self, job_id, status, *, result=None, error=""):
        self.status.append((status, result, error))


@pytest.mark.asyncio
async def test_fixture_pipeline_emits_full_event_sequence():
    store = _FakeStore()
    brief = GenerateBrief(intent="13-week treasury alternative", risk_appetite="conservative")

    with patch(
        "archimedes.services.generation_pipeline._persist_candidate",
        new=AsyncMock(return_value=("strat_fixture_001", "0xdeadbeef")),
    ):
        await run_generation(job_id="job_fixture_001", brief=brief, n_candidates=1, store=store)

    names = [e["event"] for e in store.events]
    # Spec ordering — terminal `done` must be last
    assert names[0] == "job_queued"
    assert names[1] == "brief_validated"
    assert names[2] == "candidates_selected"
    assert "agent_iteration" in names
    assert "tool_called" in names
    assert "candidate_drafted" in names
    assert "candidate_evaluated" in names
    assert "best_selected" in names
    assert "trace_hashed" in names
    assert "persisted" in names
    assert names[-1] == "done"


@pytest.mark.asyncio
async def test_pipeline_terminates_with_done_status():
    store = _FakeStore()
    brief = GenerateBrief(intent="balanced macro", risk_appetite="moderate")

    with patch(
        "archimedes.services.generation_pipeline._persist_candidate",
        new=AsyncMock(return_value=("strat_test_002", "0xabc")),
    ):
        await run_generation(job_id="job_002", brief=brief, n_candidates=1, store=store)

    # Status sequence: running → done
    statuses = [s[0] for s in store.status]
    assert statuses == ["running", "done"]
    last_result = store.status[-1][1]
    assert last_result is not None
    assert last_result["best_strategy_id"] == "strat_test_002"
    assert len(last_result["candidates"]) == 1


@pytest.mark.asyncio
async def test_pipeline_multi_candidate_picks_best():
    store = _FakeStore()
    brief = GenerateBrief(intent="aggressive crypto", risk_appetite="aggressive")

    with patch(
        "archimedes.services.generation_pipeline._persist_candidate",
        new=AsyncMock(return_value=("strat_multi_001", "0xfeed")),
    ):
        await run_generation(job_id="job_multi", brief=brief, n_candidates=3, store=store)

    # 3 candidates should produce 3 candidate_drafted events
    drafted = [e for e in store.events if e["event"] == "candidate_drafted"]
    assert len(drafted) == 3
    best = next((e for e in store.events if e["event"] == "best_selected"), None)
    assert best is not None
    assert best["data"]["considered_count"] == 3
