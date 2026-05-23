# `docs/` — Documentation Index

Navigation aid for everything under `docs/`. Grouped by purpose so you can find the right doc without grep'ing. Last updated 2026-05-22 (Day-10).

For repo-level setup + operations, start at the **repo root**:

- [`../README.md`](../README.md) — project overview + status + documentation map
- [`../SETUP.md`](../SETUP.md) — prerequisites + 5-step install + platform notes + test suite
- [`../OPERATIONS.md`](../OPERATIONS.md) — run the stack + RPC deep-dive + LLM backends + traction + security
- [`../ARC.md`](../ARC.md) — Arc testnet reference + Circle sponsor alignment
- [`../ARC-OSS-SHOWCASE.md`](../ARC-OSS-SHOWCASE.md) — Arc OSS Showcase positioning + forkable primitives
- [`../CLAUDE.md`](../CLAUDE.md) — project context for Claude Code sessions

## Product spine (canonical — read these first)

| Doc | What it is |
|---|---|
| [`user-stories.md`](user-stories.md) | The locked product spine. Primary archetype = capable non-expert. Per-page stories. Honesty rules. **Canonical reference for what the product *is*.** |
| [`ui-simplification-proposal.md`](ui-simplification-proposal.md) | 12 pages → 5 spine pages + 1 modal. Per-page consolidation rationale. In-line tooltip strategy. Phasing. |

## Architecture (current shipped state)

| Doc | What it is |
|---|---|
| [`design.md`](design.md) | Original single-vault design document. Architecture lineage; superseded for product framing by `user-stories.md`. Component-level shipped state in `chuan-architecture-survey.md`. |
| [`architectural-principles.md`](architectural-principles.md) | The four primitives (paper-claim binding, reasoning trace, tool-call provenance, selection-bias correction) — the "why" doc. All four shipped + live. |
| [`chuan-architecture-survey.md`](chuan-architecture-survey.md) | File-by-file survey of `backend/archimedes/` (78 files). Aggregate gap clusters. Day-10 refresh. |
| [`corpus-architecture.md`](corpus-architecture.md) | The q-fin corpus end-to-end: 3-layer substrate (seed → DB → artifact), fusion path, wired-vs-not-yet table. |

## Specs

Implementation contracts. The `specs/` subdirectory:

| Doc | What it is |
|---|---|
| [`specs/strategy-passport-spec.md`](specs/strategy-passport-spec.md) | The strategy passport schema + provenance contract. **Shipped + live in the UI.** |
| [`specs/selection-bias-corrections-spec.md`](specs/selection-bias-corrections-spec.md) | DSR + PBO + walk-forward OOS + look-ahead audit math + thresholds. **Shipped; 2 Tier-1 strategies pass today.** |
| [`specs/strategy-fusion-spec.md`](specs/strategy-fusion-spec.md) | Multi-paper fusion engine spec. **Shipped** (`services/strategy_fusion.py`); SPECTER2 + RAG upgrade is the unblocked `#96` follow-on. |
| [`specs/ipfs-reasoning-traces-design-note.md`](specs/ipfs-reasoning-traces-design-note.md) | Hash → Pinata CID → on-chain anchor (Rosetta-Alpha pattern). Design note, not yet wired. |
| [`specs/commit-reveal-trace-spec.md`](specs/commit-reveal-trace-spec.md) | v1.5 trace integrity upgrade — promotes "trace existed at T" to "trace existed *before* the trade". Spec'd, not live. |
| [`specs/ecosystem-design-spec.md`](specs/ecosystem-design-spec.md) | The Day-3 marketplace pivot spec — 4-layer architecture (Synthetic Protocol + AMM + Vault Factory + Agent-as-a-Service). Substantially shipped. |
| [`specs/component-interfaces-spec.md`](specs/component-interfaces-spec.md) | The original frozen `I*` Protocol contracts for the 5-person concurrent build. Interfaces are still architecturally correct; ownership has evolved to lead+coverage. |
| [`specs/fusion-to-backtest-t2o2-issue.md`](specs/fusion-to-backtest-t2o2-issue.md) | Judge-grade issue spec for the fusion→backtest pipeline gap (constrained DSL + interpreter + rigor-gate integration). Ready to file. |
| [`specs/ecosystem-architecture.html`](specs/ecosystem-architecture.html) | Visual diagram of the ecosystem architecture (HTML render). |

## Strategy + launch + marketing

| Doc | What it is |
|---|---|
| [`launch-plan.md`](launch-plan.md) | Coordinated 3-repo reveal plan + decisions on the table for launch timing / domain / public-app posture. |
| [`competitor-landscape.md`](competitor-landscape.md) | Tiered competitive thesis grounded in real Morpho/Gauntlet numbers + the Nov-2025 curation crisis. The deck's argument lives here. |
| [`demo-script-pitch-deck-outline.md`](demo-script-pitch-deck-outline.md) | 3-min pitch + 2-min demo + Q&A structure; 9-slide deck; honesty rules baked in. |
| [`claude-design-prompts.md`](claude-design-prompts.md) | Paste-ready prompts for [Claude Design](https://claude.ai/design) — logo, slide deck, UI screens, plus explainer diagrams (corpus substrate, 3-input fusion, rigor gate, user journey, on-chain trace anchor, one-page launch). |
| [`arc-alignment.md`](arc-alignment.md) | Arc testnet posture as a strategic strength + Circle Agent Stack opportunity framing. |

## Reference / process

| Doc | What it is |
|---|---|
| [`judging-rubric-assessment.md`](judging-rubric-assessment.md) | Day-10 self-assessment against the rubric (Agentic Sophistication + Traction + Circle Tool Usage + Innovation + **Arc OSS Showcase**). |
| [`rigor-methods.md`](rigor-methods.md) | Plain-English summary of the rigor methods (DSR / PBO / Kelly / MVO) that the selection-bias spec implements. Reader-friendly companion. |
| [`anti-features.md`](anti-features.md) | What Archimedes is *not* building, with rationale. Back-pressure document for scope creep. |
| [`infra-setup.md`](infra-setup.md) | EC2 deploy + CI/CD + Terraform reference. Lead: Chuan. |
| [`architecture-diagram.html`](architecture-diagram.html) | Visual system architecture diagram (HTML render). |

## Architecture Decision Records ([`adr/`](adr/))

Durable technical decisions captured once, with alternatives + reasoning, so future contributors understand the choice without relitigating.

| ADR | Decision |
|---|---|
| [`adr/backtrader-vs-vectorbt-decision-memo.md`](adr/backtrader-vs-vectorbt-decision-memo.md) | Why backtrader over vectorbt for v1 backtest engine |

[`adr/README.md`](adr/README.md) covers the ADR convention + when to add a new one.

## Historical ([`archive/`](archive/))

Docs that were authoritative at an earlier phase and have since been superseded. Kept for traceability but **not the current shape of the product**. Always prefer the current doc that supersedes it (each archive entry names its replacement in [`archive/README.md`](archive/README.md)).

| Archived doc | Now superseded by |
|---|---|
| [`archive/mvp-scope-memo.md`](archive/mvp-scope-memo.md) | [`user-stories.md`](user-stories.md) (spine) + [`launch-plan.md`](launch-plan.md) (current scope) |
| [`archive/rfb-alignment.md`](archive/rfb-alignment.md) | [`arc-alignment.md`](arc-alignment.md) + [`demo-script-pitch-deck-outline.md`](demo-script-pitch-deck-outline.md) |
| [`archive/qfin-paper-corpus-seed.md`](archive/qfin-paper-corpus-seed.md) | [`corpus-architecture.md`](corpus-architecture.md) |
| [`archive/agora_project_analysis.md`](archive/agora_project_analysis.md) | [`architectural-principles.md`](architectural-principles.md) + [`specs/selection-bias-corrections-spec.md`](specs/selection-bias-corrections-spec.md) |

## Research ([`research/`](research/))

Research artifacts that don't fit the spine + architecture + specs hierarchy but are referenced by other docs. Currently the Linus↔Archimedes lineage comparison + the Archimedes→Linus port-backs that came out of the Day-9 cross-repo work.

## Conventions for this folder

- **Every doc has a `> Status:` line** in its second-block header naming the date + (where applicable) what's been superseded. The Day-10 audit pass added these where they were missing.
- **Cross-references use relative paths** within `docs/` (e.g. `[corpus-architecture.md](corpus-architecture.md)`); root-level docs use the `../` prefix.
- **Archived docs stay archived** — don't move them back. If something in an archived doc is still load-bearing, fold it into the current canonical doc + leave the archive in place.
- **ADRs are immutable** — capture a decision once, supersede with a new ADR if it changes; don't edit the original.

## How to add a new doc

1. Decide which group it belongs to (Product spine? Architecture? Spec? Strategy? Reference? ADR?).
2. Pick a filename (kebab-case, descriptive, no dates).
3. Add a `> Status: <date> · <one-liner>` header.
4. Link from this index (`docs/README.md`) under the right group.
5. Cross-link from related docs in the same group.

If you're unsure where it goes, default to `docs/<your-doc>.md` (top-level docs/) and ask in #standups if a subdirectory is warranted.
