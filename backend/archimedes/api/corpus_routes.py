"""/api/corpus/* — Knowledge-Graph + similarity-graph surface.

Replaces the metadata-derived stubs that were previously embedded in
routes.py with endpoints that read from the KB pipeline's artifacts
(named volume) + ORM tables (kg_entities, kg_relations).

Per cross-cutting principle #2 — no new endpoints in routes.py.

Phase 3c contract:
  GET /api/corpus/runner-state    — pipeline phase + last-run manifest
  GET /api/corpus/overview        — aggregate (paper count, top topics)
  GET /api/corpus/graph           — SPECTER2-similarity 2D scatter (Phase 3c full)
  GET /api/corpus/kg/entities     — search KG entities by name
  GET /api/corpus/kg/entity/{id}  — single entity + adjacent relations
  GET /api/corpus/kg/paper/{id}   — all triples for one paper

This skeleton implements the runner-state + overview endpoints (read from
the artifact volume + DB) and returns explicit "pipeline not yet run" 503s
for graph/kg endpoints until the KB pipeline lands its first artifact.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

corpus_router = APIRouter(prefix="/api/corpus", tags=["corpus"])

ARTIFACT_DIR = Path(os.getenv("KB_ARTIFACT_DIR", "/srv/corpus-artifact"))


def _load_manifest() -> dict | None:
    """Manifest written by run_kb_pipeline.py. None if the pipeline never ran."""
    path = ARTIFACT_DIR / "manifest.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("corpus_routes: manifest unreadable: %s", exc)
        return None


def _load_state() -> dict | None:
    """In-progress state written during a running pipeline."""
    path = ARTIFACT_DIR / "state.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


@corpus_router.get("/runner-state")
async def runner_state() -> dict[str, Any]:
    """Surface the KB pipeline phase + progress for the UI banner.

    During a run, ``state.json`` carries ``{phase, progress, started_at}``.
    When idle, the response reflects the last completed run from ``manifest.json``.
    """
    state = _load_state()
    manifest = _load_manifest()
    if state:
        return {"running": True, **state, "last_manifest": manifest}
    if manifest:
        return {
            "running": False,
            "last_run_ts": manifest.get("run_ts"),
            "duration_s": manifest.get("duration_s"),
            "paper_count": manifest.get("paper_count"),
            "status": manifest.get("status", "ok"),
        }
    return {
        "running": False,
        "status": "pipeline never run — see docs/specs/kb-integration-spec.md to enable",
    }


@corpus_router.get("/overview")
async def corpus_overview() -> dict[str, Any]:
    """KB-aware corpus overview. Falls back to DB-only counts if no manifest."""
    manifest = _load_manifest()
    try:
        from sqlalchemy import func
        from archimedes.db import get_session
        from archimedes.models.corpus_store import PaperRecord
        with get_session() as session:
            paper_count = session.query(func.count(PaperRecord.arxiv_id)).scalar() or 0
            cluster_rows = session.query(
                PaperRecord.cluster_id, func.count(PaperRecord.arxiv_id),
            ).group_by(PaperRecord.cluster_id).all()
    except Exception as exc:
        logger.warning("corpus_routes: overview DB read failed: %s", exc)
        paper_count = 0
        cluster_rows = []

    return {
        "paper_count": paper_count,
        "cluster_count": len([c for c, _ in cluster_rows if c is not None]),
        "last_run_ts": (manifest or {}).get("run_ts"),
        "pipeline_status": (manifest or {}).get("status", "never run"),
    }


@corpus_router.get("/graph")
async def corpus_graph() -> dict[str, Any]:
    """SPECTER2-similarity 2D scatter. Requires a completed KB run."""
    manifest = _load_manifest()
    if manifest is None or not (ARTIFACT_DIR / "embeddings.npy").exists():
        raise HTTPException(
            status_code=503,
            detail=(
                "Corpus graph requires a completed KB pipeline run. "
                "Run `docker compose run --rm kb-runner python -m archimedes.scripts.run_kb_pipeline` "
                "(or set KB_PIPELINE_ENABLED=1 in the kb-runner container) to produce embeddings.npy. "
                "See docs/specs/kb-integration-spec.md."
            ),
        )
    # Skeleton: when the pipeline lands, this loads embeddings.npy + ids.json,
    # runs UMAP to 2D, returns {points: [{arxiv_id, x, y, cluster_id}], topics: {...}}.
    raise HTTPException(status_code=501, detail="UMAP projection not yet wired; see Phase 3c.")


@corpus_router.get("/kg/entities")
async def kg_search_entities(q: str = Query(..., min_length=2, max_length=120)) -> dict[str, Any]:
    """Search KG entities by canonical name."""
    try:
        from archimedes.db import get_session
        from archimedes.models.kg import KGEntity
        with get_session() as session:
            rows = session.query(KGEntity) \
                .filter(KGEntity.canonical_name.ilike(f"%{q}%")) \
                .order_by(KGEntity.paper_count.desc()) \
                .limit(50).all()
    except Exception as exc:
        logger.warning("kg search failed: %s", exc)
        rows = []
    return {
        "query": q,
        "entities": [
            {"id": r.id, "canonical_name": r.canonical_name, "entity_type": r.entity_type,
             "paper_count": r.paper_count}
            for r in rows
        ],
    }


@corpus_router.get("/kg/entity/{entity_id}")
async def kg_entity_detail(entity_id: int) -> dict[str, Any]:
    """Single entity + its outgoing relations."""
    try:
        from archimedes.db import get_session
        from archimedes.models.kg import KGEntity, KGRelation
        with get_session() as session:
            entity = session.query(KGEntity).filter(KGEntity.id == entity_id).first()
            if not entity:
                raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
            relations = session.query(KGRelation).filter(KGRelation.subject_id == entity_id).limit(200).all()
            obj_ids = {r.object_id for r in relations if r.object_id}
            objects = {
                e.id: e for e in session.query(KGEntity).filter(KGEntity.id.in_(obj_ids)).all()
            }
            return {
                "id": entity.id,
                "canonical_name": entity.canonical_name,
                "entity_type": entity.entity_type,
                "paper_count": entity.paper_count,
                "relations": [
                    {
                        "relation": r.relation,
                        "object": objects.get(r.object_id).canonical_name if r.object_id in objects else None,
                        "paper_arxiv_id": r.paper_arxiv_id,
                        "confidence": r.confidence,
                    }
                    for r in relations
                ],
            }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("kg entity detail failed: %s", exc)
        raise HTTPException(status_code=503, detail="KG store unavailable") from exc


@corpus_router.get("/kg/paper/{arxiv_id}")
async def kg_paper_triples(arxiv_id: str) -> dict[str, Any]:
    """All KG triples extracted from a single paper."""
    try:
        from archimedes.db import get_session
        from archimedes.models.kg import KGEntity, KGRelation
        with get_session() as session:
            rows = session.query(KGRelation).filter(KGRelation.paper_arxiv_id == arxiv_id).all()
            if not rows:
                return {"arxiv_id": arxiv_id, "triples": []}
            entity_ids = {r.subject_id for r in rows} | {r.object_id for r in rows if r.object_id}
            entities = {
                e.id: e.canonical_name
                for e in session.query(KGEntity).filter(KGEntity.id.in_(entity_ids)).all()
            }
            return {
                "arxiv_id": arxiv_id,
                "triples": [
                    {
                        "subject": entities.get(r.subject_id),
                        "relation": r.relation,
                        "object": entities.get(r.object_id),
                        "confidence": r.confidence,
                    }
                    for r in rows
                ],
            }
    except Exception as exc:
        logger.exception("kg paper triples failed: %s", exc)
        raise HTTPException(status_code=503, detail="KG store unavailable") from exc
