# Linus ↔ Archimedes — Bidirectional Architecture Comparison

**For:** strategist writing build-specs. **Bias:** skeptical; distinguishes *implemented & wired*
from *claimed/aspirational*.

**Project A — Linus:** `submodules/Linus`. A personal AI-orchestration backend ("personal LLM
Wiki at scale"). Its paper-intelligence stack is mostly **design + reference-note + ADR**, with a
thin Phase 2a runtime landed (FastAPI OpenAI-compat server, read-only KB SQLite adapter, SQLite
episodic memory + JSONL audit). The deep retrieval/synthesis engine (paper-qa) is a *resolved
decision (DEC-0044) not yet integrated*. KG/embeddings/hybrid-retrieval live in the
`modules/KnowledgeBase` submodule it consumes, not in `src/linus/`.

**Project B — Archimedes:** the parent repo. A live q-fin strategy engine. Has a working
corpus scraper, a Claude/GLM extraction pipeline, an architect that is route-wired, and a
genuinely-wired four-control selection-bias rigor gate. Multi-paper fusion exists but is
near-dead in the live path.

---

## Verified wiring facts (checked against source, not docs)

- **`strategy_fusion` is effectively dead code in the product path.** It is imported by
  *nothing in `api/`*. The *only* non-test importer is `main.py`'s `/health` handler, which
  calls `fusion_enabled()` + `load_corpus()` + `default_backend()` purely to print a
  diagnostic status line. There is **no fusion route, no fusion in the architect path**. It is
  flag-gated OFF (`ARCHIMEDES_FUSION_ENABLED` default false) and revertible by deleting the file.
- **`strategy_architect` IS wired** — `api/routes.py:42,80` `default_architect()`, exposed as
  the "design me a portfolio" route (line ~441), feeding the guardrail + construction-trace
  (the on-chain reasoning-trace path).
- **`selection_bias` IS wired** — via a dedicated `api/selection_bias_routes.py`
  (`/api/selection-bias/gate`, `/gate/{id}`, `/pbo`), included in `main.py`. The four controls
  (DSR, PBO-CSCV, walk-forward OOS, AST look-ahead) are real math and run over persisted
  backtest returns, with synthetic-from-stub fallback when a strategy has no backtest. This is
  the strongest single piece in either repo.
- **`arxiv_corpus` is a CLI, not a service in the request path.** It is *not* imported by
  `api/`. But its output IS in the tree: `data/corpus/manifest.jsonl` = 200 rows,
  metadata-complete. **Caveat:** the manifest records `pdf_sha256` for all 200, but
  `data/corpus/pdfs/` and `data/corpus/text/` are absent from the tree — so the corpus is
  **metadata/abstract-only in-repo; no cached full text**. ("Prod has no corpus" is broadly
  true for *full-text*; metadata manifest does exist.)
- **`arxiv_pipeline.extract_strategy` is reachable only via
  `IStrategyProvider.extract_from_paper`** — which has **no API route** in `api/`. It is a
  library method, demo-only, not user-reachable over HTTP.
- **Served library = 4 hand-curated strategy files** (`analytics-engine/strategies/`): Faber
  2007, Moreira-Muir 2017, Moskowitz-Ooi-Pedersen 2012, buy-hold. Provider reads them via AST
  `literal_eval` (never imports backtrader). That is the entire live "corpus → product" path.

---

## 1. Capability matrix

| Capability | Linus — implemented? maturity | Archimedes — implemented? wired? | Honest verdict (who's ahead & why) |
|---|---|---|---|
| **Corpus ingestion** | Design + `KnowledgeBaseAdapter` read-only over submodule's `metadata.db` (PR #34). Linus itself does not ingest; KB submodule does. | `arxiv_corpus.py`: working recency-biased multi-category scraper, sha256 content-addressed PDF+text cache, idempotent, injectable seams. 200-row manifest in-tree. **CLI only, not in request path; full text not cached in-tree.** | **Archimedes** has a more concrete, domain-tuned, runnable ingester. Linus's is an adapter over an external submodule it doesn't own. |
| **Full-text extraction** | Delegated to KB submodule (PyMuPDF/SPECTER2 per Archimedes' own CLAUDE notes on KnowledgeBase). Not in `src/linus/`. | `arxiv_pipeline.extract_text` + `arxiv_corpus._extract_text`: defensive page-by-page pypdf (BSD-3, deliberately not AGPL PyMuPDF), sha256-cached. Implemented, demo-only. | **Tie / Archimedes** for in-repo working code. Linus has the better *upstream* (SPECTER2-grade) but it's out-of-package. |
| **Embeddings** | KB submodule has SPECTER2 (per ARCHITECTURE.md/CLAUDE.md); paper-qa would add `st-` sentence-transformers. **Not implemented in `src/linus`.** | **None.** No embeddings anywhere in the served path. Fusion candidate-selection is explicitly keyword/substring, "SPECTER2 ranker is a post-hackathon swap." | **Linus** (via its KB submodule + planned paper-qa). Archimedes has zero semantic retrieval. |
| **Knowledge graph** | KB submodule: dual RDF + property graph (DEC-0015), REBEL/SciSpacy KG per Archimedes' own notes. Designed, ADR-ratified; **not in `src/linus`**. | **None.** No KG, no entity layer, no edges. | **Linus** — it has a real KG substrate (in the submodule) and a typed `model_prediction` edge ADR. Archimedes has nothing. |
| **Hybrid retrieval / RAG-gateway** | "RAG gateway" is an ARCHITECTURE.md component (fuse SPECTER2+TF-IDF+KG via RRF) — **designed, Phase 3, not built**. paper-qa (RCS: keyword tantivy + top-k vector + per-chunk LLM rescoring) is the resolved engine, **integration pending (DEC-0044, not done)**. | **None.** Fusion does deterministic keyword/synonym filtering then hands raw abstracts to one LLM call. No vector, no RRF, no rerank. | **Linus on paper (design + chosen engine); neither has it wired.** Archimedes has keyword-only and it's the dead path anyway. |
| **Multi-doc synthesis / fusion** | paper-qa does grounded multi-paper QA + contradiction detection (its headline). Not integrated; reference-note Integrate verdict only. | `strategy_fusion.py`: a genuinely thoughtful >=2-paper novelty-seeking synthesizer with anti-hallucination id-filtering + honest provenance (`response.model`). **But dead: no route, only `/health` touches it, flag OFF.** | **Tie — both have it as non-running code.** Archimedes' is more *built* (full service, tests) but unwired; Linus's is a third-party tool not yet adopted. |
| **Provenance / citation** | Strong *as discipline*: claim-typing (`[!source]`/`[!analysis]`), SHA-256 content hashing, audit JSONL, paper-qa grounded in-text citations. Implemented: episodic SHA chain + audit log (PR #35). Citation *surfacing in answers* = via paper-qa, not yet wired. | **Strongest here.** Strategy passport: paper id/title/authors/DOI, methodology hash, `EXTRACTION_LLM`, true served-model honesty (`response.model` vs requested), paper-claim deltas surfaced un-aggregated, **hashed + anchored on-chain via `ReasoningTraceRegistry`**. | **Archimedes** — on-chain, tamper-evident, user-surfaced provenance is live and is its actual moat. Linus has the better internal discipline but no external verifiability. |
| **Curation / quality gate** | "Quality gate as a *surface*, not a hard gate — Dan is the filter" (resolved Tier 1 #6). KB per-paper scorecard (DEC-0019) designed, not in `src/linus`. Soft by philosophy. | **Hard, quantitative, wired:** DSR (Bailey-LdP), PBO-CSCV, walk-forward OOS, AST look-ahead, `passes_all` gate, CANDIDATE→VALIDATED. Real math behind a live router. | **Archimedes, decisively.** This is rigor as a *mechanism*, not a posture. Linus deliberately chose soft. |
| **Memory layers** | **Architectural pillar.** 5 layers (A–E) ADR-ratified (DEC-0028–0052); Layer C SQLite episodic + JSONL audit + content-hash **implemented (PR #35)**; B facade; D/E designed; `memory_mode`/`cot_budget` router primitives. | **None.** No episodic/session/investigation memory. Redis holds live regime state only — operational cache, not a memory architecture. | **Linus, decisively.** A genuine multi-layer memory architecture with running v0 substrate. Archimedes has no concept of it. |
| **Model-backend abstraction** | OpenAI-compat `/v1/chat/completions` shipped (PR #32/#40); Anthropic `/v1/messages` designed (DEC-0056), not shipped; Ollama-first, local-first; provider router. | `LLMBackend` Protocol + `ClaudeBackend` (Anthropic SDK, also GLM via `ANTHROPIC_BASE_URL`/`AUTH_TOKEN`) + `CannedBackend` deterministic fallback. Clean seam, honest served-model capture. | **Tie, different axes.** Linus = served HTTP surface + local-first + multi-protocol design. Archimedes = clean injectable client seam + true-served-model honesty. Each has what the other lacks. |
| **Served product path** | OpenAI-compat endpoint + KB read tool wrappers (`search_papers`/`get_paper`) + sandbox. A backend with thin tools; **no domain product**; single-user, local. | Full FastAPI product: architect route → guardrail → construction-trace → on-chain registry; selection-bias router; vaults; AMM; 10 deployed contracts; live EC2. **An actual shipped product.** | **Archimedes, decisively.** It is a deployed, end-to-end product. Linus is infrastructure-in-progress. |

---

## 2. "Have we replicated the full paper-intelligence stack in Archimedes?"

**No — not even close, and the gap is structural, not cosmetic.** Archimedes has a corpus
*scraper* and a single-paper *extractor*, then it stops. The middle of the stack — the part
that makes literature *intelligence* rather than literature *fetching* — is absent:

Specifically missing in Archimedes (each is a hard gap, not a polish item):

1. **No embeddings.** Zero semantic representation of any paper. Everything downstream of the
   manifest is keyword/substring matching (`_ASSET_SYNONYMS`, regex direction keywords).
2. **No knowledge graph.** No entities, no relations, no `model_prediction`-style typed edges,
   no cross-paper structure. Papers are independent JSONL rows.
3. **No hybrid retrieval / RAG-gateway.** No BM25+vector+graph fusion, no RRF, no rerank, no
   contextual-summary loop. The "retrieval" is a sorted list slice.
4. **Multi-paper fusion is unwired (dead code).** The one component that *would* be
   cross-document synthesis is reachable by `/health` only — no route, flag OFF. In the live
   path Archimedes never combines two papers.
5. **Single-paper extraction is not user-reachable.** `extract_from_paper` has no HTTP route;
   it's a demo library call. The live product serves 4 hand-written strategy files.
6. **No corpus full-text in the served system.** The 200-row manifest is abstract-only in-tree
   (no cached PDFs/text); the architect prompt is built from passport metadata, never paper
   bodies, in the live path.
7. **No memory layer.** No episodic/semantic substrate; the corpus does not compound or get
   re-queried — it is re-scraped or static.
8. **Provenance is surfaced (the one thing it does have)** — but it is provenance of a
   *4-strategy hand-curated library*, not of an intelligence pipeline.

What Archimedes *did* replicate well: the *engineering taste* Linus's notes prize — sha256
content-addressed caches, defensive page-by-page extraction, injectable seams, honest
labelled fallbacks, license hygiene (pypdf not PyMuPDF). The patterns transferred; the
*pipeline* did not.

Conversely, Linus has not "replicated" the stack as running code either — its KG/embeddings
live in a submodule and its retrieval engine (paper-qa) is a chosen-but-unintegrated decision.
**The honest summary: neither repo runs a full paper-intelligence stack today; Linus has the
complete *design + chosen components + a memory architecture*; Archimedes has the *deployed
product surface, the rigor gate, and on-chain provenance* but a hollow middle.**

---

## 3. Port FROM Linus → Archimedes (ranked, concrete)

1. **Adopt paper-qa as the retrieval/synthesis engine behind a RAG gateway.**
   Target: new `backend/archimedes/services/paper_rag.py`; wire into `strategy_architect.py`
   (`_build_user_prompt`) and resurrect `strategy_fusion.py` behind it. *Payoff:* replaces
   keyword/substring candidate selection with grounded, citation-precise multi-paper retrieval
   over the 200-paper corpus — turns the dead fusion module into the product's actual
   intelligence and makes the architect reason from paper *bodies*, not just passports.
   Apache-2.0, single-tool integration, `st-` embeddings (no API key).

2. **SPECTER2 (or `st-`) embeddings + a minimal KG over the corpus manifest.**
   Target: extend `arxiv_corpus.py` to emit an embedding column; new
   `services/corpus_index.py`. *Payoff:* the fusion module's own docstring admits "a SPECTER2
   ranker is a clean post-hackathon swap behind this same seam." This is the single
   highest-leverage swap: novelty-seeking fusion is only credible with semantic
   neighbor-distance, not synonym lists. Directly upgrades the q-fin "find the un-decayed
   combination" thesis.

3. **The five-layer memory architecture, scoped to Layer C (episodic).**
   Target: `backend/archimedes/services/strategy_memory.py` (SQLite + content-hash + audit
   JSONL, lifting `memory-architecture.md`'s DEC-0029 substrate). *Payoff:* makes the strategy
   library *compound* — past architect proposals, rejected fusions, regime-shift decisions
   become recallable provenance instead of being recomputed. Pairs naturally with the existing
   on-chain trace (Layer C SHA chain ↔ `ReasoningTraceRegistry` hash). This is the missing
   substrate that would let the strategy library behave like a knowledge base.

(Honorable mention, not top-3: the constitution-as-prompt + lint-as-verifier pattern from
`memex` as a CI integrity check over the strategy-passport directory; the
reject-and-explain SQLite critique loop from `obsidian-llm-wiki-local` for human curator
feedback without retraining.)

---

## 4. Port FROM Archimedes → Linus (ranked)

1. **The selection-bias rigor gate as a quantitative quality primitive.**
   Target: `src/linus/knowledge/rigor.py` (analogue of `selection_bias.py`); expose as a Linus
   tool. *Payoff:* Linus deliberately chose "quality gate = soft surface, Dan is the filter."
   That is fine for prose syntheses but **wrong for any quantitative or predictive Worker
   output** — exactly the BioReason-Pro "typed structured prediction" cases Linus's own docs
   flag. DSR/PBO/walk-forward generalize to any "is this measured effect real or
   multiple-testing noise?" check (biology screens, benchmark deltas). Linus has nothing like
   it; it is the single most reusable hard-engineering asset in Archimedes.

2. **On-chain (or hash-anchored, tamper-evident) provenance surfaced in outputs.**
   Target: `src/linus/memory/anchor.py` + audit-log integration. *Payoff:* Linus's audit log
   is internal and self-attested; Marelli-accountability (a stated Linus design pillar) wants
   *externally verifiable* attribution. Archimedes' pattern — hash the reasoning trace,
   anchor the hash, store the full trace off-chain, let anyone recompute — is the concrete
   mechanism Linus's "claim provenance" discipline currently lacks an enforcement teeth for.
   (Even without a chain: a Merkle-anchored, signed audit log is the liftable shape.)

(Also strong, below the top-2: the `LLMBackend` true-served-model honesty pattern
(`response.model` vs requested) for Linus's provider router; the Anthropic-compat GLM-via-
base-url backend config, which Linus has only as DEC-0056 design.)

---

## 5. The entrepreneurial-architecture insight Archimedes is NOT exploiting

**From Linus's own docs (entrepreneurship-synthesis, total-/synthesis-landscape, the
ARCHITECTURE.md "harness vs orchestration" thesis, and the Canteen Agent/Identity/Venue
decomposition):**

> *"Commercial surface only crystallizes when the underlying schemas, citation discipline,
> and Maestro/Worker context-management patterns are right. Productization is downstream of
> structure, not upstream of it... the orchestration layer is where domain intelligence
> accrues; harnesses (front-ends) are thin and swappable."*

And the sharper, more specific one Linus repeatedly lands on: **the durable asset is the
compounding, citation-typed knowledge substrate — not the model and not the UI.** Linus is
explicitly *memory-first*: a substrate that "compounds across every interaction, every paper
read, every synthesis written," with claim-typing + content-hashing + write-back as the
structural moat. Plus the Venue-layer idea: a deployment/jurisdiction surface *above*
orchestration that turns accrued skills into addressable, monetizable services.

**What Archimedes is doing instead:** treating the strategy library as a static, hand-curated
set of 4 files plus an LLM that re-derives a portfolio from scratch on every request. Nothing
compounds. The corpus is scraped-then-frozen; the architect's reasoning is not stored as
recallable, citation-typed knowledge; the fusion engine that *would* generate accruing novel
combinations is dead-coded off. Each user request starts from zero. Archimedes' real moat (on-
chain provenance) is being applied to a *non-compounding* asset.

**How this changes the Archimedes strategy engine if exploited:**

- **Make the strategy library a memory-first compounding substrate, not a file directory.**
  Every architect proposal, every fusion hypothesis, every rigor-gate verdict, every
  regime-shift decision becomes a claim-typed, content-hashed, on-chain-anchored record that
  *future* requests retrieve and build on. The library *grows and self-curates* — exactly the
  "compounding strategy library" the North Star promises but the implementation doesn't
  deliver.
- **Reframe the moat from "this 4-strategy library is verified" to "our verified-knowledge
  substrate compounds and every increment is provenance-anchored."** That is defensible in a
  way a static list is not — and it is the same insight (structure/substrate > model/UI) that
  Linus's entrepreneurship synthesis derives from the g10-finance quant-agent prior art.
- **Turn the dead fusion engine on, behind embeddings + the rigor gate + the memory
  substrate.** Novelty-seeking multi-paper synthesis that (a) is semantically grounded, (b)
  must pass DSR/PBO before admission, and (c) accrues into the compounding substrate is the
  product the architecture is *one wiring pass* away from — and is precisely the
  "structure-first, then productize" sequencing Linus's docs argue for.
- **Adopt the Venue-layer framing:** the rigor-gated, provenance-anchored, compounding library
  is the addressable service; the chat UI / vault UI are swappable harnesses. Archimedes
  currently conflates the two and ties its identity to the front-end demo.
