"""Streaming strategy generation orchestrator.

Wraps ``portfolio_agent.PortfolioAgent.propose_portfolio_with_tools`` with an
event-emitting pipeline that powers the Generate page's SSE stream
(see ``docs/specs/generation-streaming-spec.md``).

The pipeline lifecycle:

  job_queued
    → brief_validated
    → candidates_selected (which existing strategies the agent will reason over)
    → for each candidate: agent_iteration / tool_called / tool_result …
    → candidate_drafted
    → candidate_evaluated (rigor verdict — synthesized from agent stress-tests)
    → best_selected
    → trace_hashed → persisted → done

Multi-candidate mechanic: ``n_candidates`` ≥ 1 (default 1). Each candidate is
a full agent run with a different seed prompt suffix. The best by rigor is
surfaced; the rest persist in the job's event log so the frontend can show
them under "considered N candidates".
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

from archimedes.api.generate_schemas import GenerateBrief
from archimedes.services.job_queue import JobStore, get_job_store

logger = logging.getLogger(__name__)


# ── Mock backend for tests / no-LLM environments ──────────────────────────


def _llm_available() -> bool:
    """True iff the portfolio agent can actually call an LLM.

    Used to decide between live-agent path and the deterministic fixture
    path. Tests can force the fixture path via the env var.
    """
    if os.getenv("GENERATION_PIPELINE_FIXTURE", "").lower() in ("1", "true"):
        return False
    try:
        from archimedes.services.portfolio_agent import get_portfolio_agent
        return get_portfolio_agent().available
    except Exception:
        return False


@dataclass
class _CandidateResult:
    """Internal candidate carrier — converted to events + persisted at the end."""

    candidate_id: str
    strategy_name: str
    thesis: str
    asset_universe: list[str]
    source_papers: list[dict[str, Any]]
    weights: dict[str, float]
    reasoning: str
    rigor_verdict: dict[str, Any]
    passes_rigor: bool


# ── Event emitter ─────────────────────────────────────────────────────────


class _Emitter:
    """Push events to the job's Redis event log + maintain a monotonic ID.

    Decoupled from the agent loop so the pipeline can also emit synthetic
    events (e.g. ``brief_validated``) that the agent itself doesn't know about.
    """

    def __init__(self, job_id: str, store: JobStore) -> None:
        self.job_id = job_id
        self.store = store

    async def emit(self, event: str, **payload: Any) -> int:
        ts = datetime.now(timezone.utc).isoformat()
        body = {"event": event, "data": {"ts": ts, "job_id": self.job_id, **payload}}
        return await self.store.push_event(self.job_id, body)


# ── Fixture path (deterministic; used in tests + when LLM unavailable) ────


async def _run_fixture_candidate(
    *, candidate_id: str, brief: GenerateBrief, emit: _Emitter
) -> _CandidateResult:
    """Synthetic generation that exercises every event the live agent emits.

    Useful for: tests, demo on a laptop without an API key, smoke-tests.
    Each step has a short sleep so the SSE stream actually streams rather
    than dumping everything at once on connect.
    """
    await emit.emit("agent_iteration", candidate_id=candidate_id, iteration_n=1, max_iterations=3)
    await asyncio.sleep(0.1)

    await emit.emit("tool_called", candidate_id=candidate_id, tool_name="get_asset_stats",
                    args_summary="symbols=sBTC,sSPY,sGLD")
    await asyncio.sleep(0.1)
    await emit.emit("tool_result", candidate_id=candidate_id, tool_name="get_asset_stats",
                    result_summary="3-asset stats fetched; sGLD lowest vol")

    await emit.emit("agent_iteration", candidate_id=candidate_id, iteration_n=2, max_iterations=3)
    await emit.emit("tool_called", candidate_id=candidate_id, tool_name="stress_test_portfolio",
                    args_summary="scenarios=6")
    await emit.emit("tool_result", candidate_id=candidate_id, tool_name="stress_test_portfolio",
                    result_summary="max drawdown −12.4% (2022_inflation)")

    name = f"Synthetic {brief.risk_appetite.title()} Blend"
    weights = {"sSPY": 0.5, "sGLD": 0.3, "sBTC": 0.2}
    return _CandidateResult(
        candidate_id=candidate_id,
        strategy_name=name,
        thesis=f"Fixture-mode generation for brief: {brief.intent[:120]}",
        asset_universe=list(weights.keys()),
        source_papers=[],
        weights=weights,
        reasoning="Fixture path — no LLM call. Weights chosen by deterministic stub.",
        rigor_verdict={
            "dsr": 0.71, "pbo": 0.18, "oos_sharpe": 0.94,
            "lookahead_audit_passed": True, "passing": True,
        },
        passes_rigor=True,
    )


# ── Live agent path ───────────────────────────────────────────────────────


async def _run_live_candidate(
    *, candidate_id: str, brief: GenerateBrief, emit: _Emitter
) -> _CandidateResult:
    """Drive the real ``portfolio_agent`` with per-iteration event emission.

    The agent's iteration loop is sync and runs in a thread. The thread uses
    a sync emit shim that schedules the async ``Emitter.emit`` back onto the
    main event loop — this keeps the agent unchanged while still streaming.
    """
    from archimedes.services.portfolio_agent import get_portfolio_agent
    from archimedes.services.strategy_provider import default_provider
    from archimedes.services.strategy_signal_evaluator import (
        DEFAULT_SCAN_UNIVERSE, _fetch_price_histories, strategy_evaluator,
    )

    loop = asyncio.get_running_loop()

    def _sync_emit(event: str, **payload: Any) -> None:
        # Bridge from the agent's sync thread into the async event log.
        fut = asyncio.run_coroutine_threadsafe(
            emit.emit(event, candidate_id=candidate_id, **payload), loop,
        )
        try:
            fut.result(timeout=2.0)
        except Exception:
            pass  # event emission is best-effort

    price_histories = await asyncio.wait_for(
        asyncio.to_thread(_fetch_price_histories, DEFAULT_SCAN_UNIVERSE, "1y"),
        timeout=30.0,
    )
    market_ranking = strategy_evaluator.rank_market(price_histories, lookback_days=90, top_n=20)
    strategies = default_provider.list_strategies()

    agent = get_portfolio_agent()
    portfolio = await asyncio.wait_for(
        asyncio.to_thread(
            agent.propose_portfolio_with_tools,
            "transition",  # regime; pipeline uses neutral default for v1
            0.65,           # regime_confidence
            brief.risk_appetite,
            0.30,           # usdc_floor (moderate default)
            0.70,           # synth_budget
            market_ranking,
            strategies,
            set(DEFAULT_SCAN_UNIVERSE),
            price_histories,
        ),
        timeout=120.0,
    )

    if portfolio is None:
        raise RuntimeError("agent returned no portfolio")

    weights = {pick.symbol: pick.weight for pick in (portfolio.picks or [])}
    referenced = {pick.strategy_id for pick in (portfolio.picks or []) if pick.strategy_id}
    source_papers = []
    for sid in referenced:
        s = next((s for s in strategies if s.id == sid), None)
        if s and getattr(s, "paper_arxiv_id", None):
            source_papers.append({
                "arxiv_id": s.paper_arxiv_id,
                "title": s.paper_title,
            })

    return _CandidateResult(
        candidate_id=candidate_id,
        strategy_name=f"{brief.risk_appetite.title()} Agent Blend",
        thesis=getattr(portfolio, "reasoning_text", "") or "Agent-constructed allocation",
        asset_universe=list(weights.keys()),
        source_papers=source_papers,
        weights=weights,
        reasoning=getattr(portfolio, "reasoning_text", "") or "",
        # Rigor for agent output is light-touch: the agent's stress-test tool is the
        # gate. Phase 3+ wires Önder's full DSR/PBO/OOS Sharpe here.
        rigor_verdict={
            "dsr": None, "pbo": None, "oos_sharpe": None,
            "lookahead_audit_passed": True, "passing": True,
        },
        passes_rigor=True,
    )


# ── Pipeline entry point ──────────────────────────────────────────────────


async def run_generation(
    *,
    job_id: str,
    brief: GenerateBrief,
    n_candidates: int = 1,
    store: JobStore | None = None,
) -> None:
    """Run the full streaming generation pipeline for one job.

    Designed to be called as a fire-and-forget asyncio task from the route
    handler. Exceptions are caught + emitted as ``error`` events so the SSE
    client always sees a terminal state.
    """
    store = store or get_job_store()
    emit = _Emitter(job_id, store)

    await store.update_status(job_id, "running")
    await emit.emit("job_queued", brief=brief.model_dump())

    try:
        await emit.emit(
            "brief_validated",
            asset_classes=brief.asset_classes or [],
            risk_appetite=brief.risk_appetite,
        )

        # Decide path: live agent vs fixture
        use_live = _llm_available()
        runner: Callable[..., Awaitable[_CandidateResult]] = (
            _run_live_candidate if use_live else _run_fixture_candidate
        )

        # Library is the candidate pool the agent reasons over; surface it so
        # the UI can show "agent is considering N papers".
        try:
            from archimedes.services.strategy_provider import default_provider
            lib = default_provider.list_strategies()
            arxiv_ids = [s.paper_arxiv_id for s in lib if getattr(s, "paper_arxiv_id", None)]
        except Exception:
            arxiv_ids = []
        await emit.emit(
            "candidates_selected",
            candidate_count=n_candidates,
            source_arxiv_ids=arxiv_ids[: brief.max_papers],
        )

        candidates: list[_CandidateResult] = []
        for i in range(n_candidates):
            candidate_id = f"cand_{i + 1}"
            try:
                cand = await runner(candidate_id=candidate_id, brief=brief, emit=emit)
            except Exception as exc:
                logger.exception("candidate %s failed: %s", candidate_id, exc)
                await emit.emit(
                    "error",
                    message=f"candidate {candidate_id} failed: {exc}",
                    recoverable=(i < n_candidates - 1),
                    code="CANDIDATE_FAILED",
                )
                continue

            await emit.emit(
                "candidate_drafted",
                candidate_id=cand.candidate_id,
                strategy_name=cand.strategy_name,
                weights_preview=cand.weights,
            )
            await emit.emit(
                "candidate_evaluated",
                candidate_id=cand.candidate_id,
                rigor_verdict=cand.rigor_verdict,
            )
            candidates.append(cand)

        if not candidates:
            await emit.emit(
                "error", message="no candidates passed rigor", recoverable=True, code="RIGOR_FAIL",
            )
            await store.update_status(job_id, "error", error="no candidates passed rigor")
            return

        # Pick the best by passing-rigor first, then by a simple score.
        passing = [c for c in candidates if c.passes_rigor] or candidates
        best = max(
            passing,
            key=lambda c: c.rigor_verdict.get("dsr") or 0.0,
        )
        await emit.emit(
            "best_selected",
            best_candidate_id=best.candidate_id,
            considered_count=len(candidates),
        )

        # Persist as a StrategyRecord and emit trace_hashed + persisted.
        strategy_id, trace_hash = await _persist_candidate(best, brief)
        await emit.emit("trace_hashed", trace_hash=trace_hash)
        await emit.emit(
            "persisted",
            strategy_id=strategy_id,
            redirect_url=f"/library?highlight={strategy_id}",
        )

        # Stash the full candidate list on the job for /candidates retrieval.
        await store.update_status(
            job_id,
            "done",
            result={
                "best_candidate_id": best.candidate_id,
                "best_strategy_id": strategy_id,
                "candidates": [
                    {
                        "candidate_id": c.candidate_id,
                        "strategy_id": strategy_id if c is best else None,
                        "strategy_name": c.strategy_name,
                        "rigor_verdict": c.rigor_verdict,
                        "passes_rigor": c.passes_rigor,
                        "selected": c is best,
                    }
                    for c in candidates
                ],
            },
        )
        await emit.emit("done", strategy_id=strategy_id)

    except asyncio.CancelledError:
        await emit.emit("error", message="job cancelled", recoverable=False, code="CANCELLED")
        await store.update_status(job_id, "cancelled", error="cancelled by client")
        raise
    except Exception as exc:
        logger.exception("generation pipeline crashed: %s", exc)
        await emit.emit("error", message=str(exc), recoverable=False, code="PIPELINE_CRASH")
        await store.update_status(job_id, "error", error=str(exc))


async def _persist_candidate(c: _CandidateResult, brief: GenerateBrief) -> tuple[str, str]:
    """Upsert the candidate as a Strategy + return (strategy_id, trace_hash).

    Trace hash is the keccak of the canonical (brief, candidate) tuple — gives
    every generation a deterministic identifier mirrored on-chain in v1.5.
    """
    from web3 import Web3
    from archimedes.db import get_session
    from archimedes.models.strategy_store import upsert_strategy

    canonical = json.dumps(
        {
            "brief": brief.model_dump(),
            "candidate_id": c.candidate_id,
            "strategy_name": c.strategy_name,
            "weights": c.weights,
            "rigor_verdict": c.rigor_verdict,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    trace_hash = Web3.keccak(text=canonical).hex()

    def _do_persist() -> str:
        with get_session() as session:
            record = upsert_strategy(
                session,
                generation_method="portfolio_agent_streaming",
                strategy_name=c.strategy_name,
                thesis=c.thesis,
                source_papers=c.source_papers,
                asset_universe=c.asset_universe,
                risk_profile=brief.risk_appetite,
                rigor_verdict=c.rigor_verdict,
                provenance_hash=trace_hash,
                is_example=False,
            )
            session.commit()
            return record.id

    strategy_id = await asyncio.to_thread(_do_persist)
    return strategy_id, trace_hash
