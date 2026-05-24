# Progress

## Status
In Progress — Issue #165 (strategy_proposals episodic table) complete. Deployed to main.

## Tasks

### Completed (this session)
- **#165** — strategy_proposals episodic table: StrategyProposal ORM model with keccak256 content hash dedup; strategy_memory.py non-blocking write path; /api/proposals endpoint with verdict/agent/since filtering + pagination + siblings endpoint; wired into generation_pipeline (all candidates), fusion job, and architect construct. 15 new tests, 436 total green.

### Completed (prior sessions)
- **#180** — Dependabot + detect-secrets: `.github/dependabot.yml`, `.pre-commit-config.yaml`, `.secrets.baseline`
- **#162** — regime_tag field on Strategy dataclass (bull/bear/regime_neutral)
- **#175** — E2E testnet smoke test script: `verify_arc_e2e.py`
- **#179** — Rate limiting via slowapi
- **#181** — User-data minimization: encrypt email at rest
- **#150** — DepositFlow stepper modal
- **#174** — `/api/health/amm` + agent_runner VaultFactory poll
- **#172** — WelcomeProfileModal + personalized header
- **#167** — Generate page single input + backend auto-route
- **#177** — Nginx security headers
- **#178** — CORS lockdown
- **#166** — Landing sidebar parity + CTA differentiation
- **#169** — Corpus default Catalog tab + plain-English labels
- **#170** — Reasoning verify arcscan enhancement
- **#171** — Portfolio traces honesty
- **#173** — Agents subpackage refactor

## Files Changed (Issue #165)
- `backend/archimedes/models/strategy_proposal.py` — NEW: StrategyProposal ORM model (strategy_proposals table)
- `backend/archimedes/services/strategy_memory.py` — NEW: persist_proposal, query_proposals, get_siblings write/read paths
- `backend/archimedes/api/proposals_routes.py` — NEW: /api/proposals + /api/proposals/{gid}/siblings endpoints
- `backend/archimedes/agents/generation_pipeline.py` — Wired: persist all candidates to episodic memory after best selection
- `backend/archimedes/api/strategies_routes.py` — Wired: persist fusion proposals + architect proposals
- `backend/archimedes/db.py` — Added StrategyProposal import for table creation
- `backend/archimedes/main.py` — Added proposals_router
- `backend/tests/services/test_strategy_memory.py` — NEW: 15 tests (model, memory write path, API endpoint)

## Validation
- Backend tests: 436 passed, 0 failed, 2 skipped (pre-existing Redis flakes)
- 15 new strategy_memory tests: all green
- Non-blocking writes: persist_proposal returns None on DB failure, doesn't raise
- Content hash dedup: same inputs → same proposal_id
- API filtering: verdict, agent, since all work correctly
- Pagination: limit/offset verified
- Siblings: generation_id-based grouping works

## Open items
- Issues still assigned to t2o2: #176 (SSM secrets), #161 (passport spec rewrite), #159 (StrategyPassport refactor), #158 (paper-qa), #157 (StockBench), #156 (Xia protocols), #153/#152 (CorpusGraph/KG), #151 (GPU EC2 + KB pipeline), #149 (StrategyRegistry.sol), #148 (archimedes-arc.app domain), #147 (S3 + DynamoDB)
