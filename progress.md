# Progress

## Status
In Progress — Issue #167 (Generate single input + auto-route pipeline) complete. Deployed to main.

## Tasks

### Completed
- **#167** — Generate page: single unified form (removed mode picker). Backend `_pick_pipeline()` auto-routes fusion/architect/agent. `pipeline_selected` SSE event emitted after `brief_validated`. GenerationStream passes pipeline selection to parent via `onPipelineSelected` callback.

### Also Completed (prior sessions)
- **#177** — Nginx security headers
- **#178** — CORS lockdown
- **#166** — Landing sidebar parity + CTA differentiation
- **#169** — Corpus default Catalog tab + plain-English labels
- **#170** — Reasoning verify arcscan enhancement
- **#171** — Portfolio traces honesty
- **#173** — Agents subpackage refactor

## Files Changed (this session)
- `ui/src/components/Generate.jsx` — removed mode picker (3 toggle buttons); single unified form with intent + risk + assets + depth
- `ui/src/components/GenerationStream.jsx` — added `pipeline_selected` event label + `onPipelineSelected` callback
- `backend/archimedes/agents/generation_pipeline.py` — added `_pick_pipeline()` function; emits `pipeline_selected` event after brief_validated
- `backend/archimedes/api/generate_schemas.py` — added `pipeline_selected` to EventName union; added `mode` field (ignored, backwards-compat) to GenerateStartRequest
- `backend/tests/services/test_generation_pipeline.py` — updated event ordering assertion; fixed stale patch paths

## Validation
- `pytest -q` → 371 passed, 2 skipped, 0 failures
- `npm run build` → clean
- AC: `grep -c "Streaming agent\|setMode\|useState('agent')" Generate.jsx` → 0
- AC: `_pick_pipeline` exists in `generation_pipeline.py`
- AC: `pipeline_selected` in schemas + pipeline (3+ matches)

## Remaining (assigned to t2o2)
- #168 — Explore page real oracle prices
- #172 — WelcomeProfileModal
- #174 — /api/health/amm + agent-runner vault poll
- #175 — End-to-end testnet smoke
- #176 — Migrate secrets to AWS SSM
- #179 — Rate limiting (slowapi)
- #180 — Dependabot + secret scanning
- #181 — User-data minimization
- #152–#165 — Track C/E (KB pipeline, passport unification, etc.)
