# Progress — 2026-05-25

## Completed this session

| Issue | PR | Status | Description |
|-------|-----|--------|-------------|
| #163 | #315 | ✅ Merged | Dual bull/bear strategy generation — every Generate emits both regimes |
| #303 | #317 | ✅ Merged | Arcscan links on Portfolio/Passport/VaultDetail |
| #309 | #318 | ✅ Merged | /api/health/amm endpoint (per-pool liquidity) |
| #310 | #319 | ✅ Merged | Fix source_papers always empty in generated strategies |
| #307 | #324 | ✅ Merged | Per-vault strategy scoping in agent_runner |

## Previously closed (verified)

| Issue | Status | Notes |
|-------|--------|-------|
| #148 | ✅ Closed | Route 53 + HTTPS for archimedes-arc.app |
| #151 | ✅ Closed | GPU KB pipeline on 668 papers, artifacts to S3 |
| #176 | ✅ Closed | SSM secrets migration |

## Open items remaining

| Issue | Status | Notes |
|-------|--------|-------|
| #293 | Closed but backfill pending | REBEL triples in local JSONL; Postgres kg_relations backfill needed for live KG tab |
| #306 | Draft PR | KG label revert — blocked on #293 backfill to production |

## Cost estimate delivered

`docs/cost-estimates/generate-llm-costs.md` — ~$0.15 per dual-regime Generate
