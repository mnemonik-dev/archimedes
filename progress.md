# Progress

## Status
In Progress

## Tasks
### Completed
- [x] #153 CorpusGraph + CorpusKG frontend components
- [x] #158 Wire paper-qa as defense-in-depth ranker behind strategy_fusion.select_candidates()

## Files Changed

### Issue #158
- `backend/archimedes/services/paper_rag.py` (NEW — 280 lines) — TF-IDF + sentence-transformer semantic reranker for fusion candidate selection
- `backend/archimedes/agents/strategy_fusion.py` — `select_candidates()` now chains `paper_rag.augment_candidate_scores()` after keyword ranking
- `backend/archimedes/main.py` — `/health` includes `paper_rag` status; new `/health/paper-rag` dedicated endpoint
- `backend/tests/services/test_paper_rag.py` (NEW — 31 tests) — full coverage: tokenizer, TF-IDF, feature flag, health, rerank, integration, anti-hallucination, fallback
- `backend/requirements.txt` — added `paper-qa` and `sentence-transformers` as optional commented deps
- `.env.example` — added `FUSION_SEMANTIC_RETRIEVAL=true`

### Issue #153
- `ui/src/components/CorpusGraph.jsx` (NEW) — Force-directed SPECTER2 similarity graph using react-force-graph-2d
- `ui/src/components/CorpusKG.jsx` (NEW) — Knowledge graph SVG viewer with entity search
- `ui/src/components/CorpusExplorer.jsx` — Replaced inline canvas graph + KGViewer with new components
- `ui/package.json` + `ui/package-lock.json` — Added react-force-graph-2d dependency

## Notes
- paper_rag uses TF-IDF as zero-dep baseline; sentence-transformers and paper-qa as optional upgrades
- Feature flag `FUSION_SEMANTIC_RETRIEVAL=true` (default ON); graceful fallback when disabled or deps missing
- Anti-hallucination: semantic rerank only reorders keyword-filtered candidates, never introduces phantom papers
- 554 backend tests passing (1 pre-existing unrelated failure in test_run_backtests_script)
- Frontend build clean
