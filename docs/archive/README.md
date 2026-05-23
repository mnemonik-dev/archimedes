# Archived design documents

> **Status:** Day-10 (2026-05-22). Curation: docs in this folder were authoritative
> at an earlier phase of the project and have since been superseded by a current
> document or by shipped code. They're kept for traceability — judges, reviewers,
> and future readers can see what we considered and what we settled on — but they
> should not be read as the current shape of the product.
> **Rule:** if you're trying to understand Archimedes *today*, read the current
> docs listed under each entry below. The archived doc is the history, not the
> contract.

## What's in here, and what supersedes each

| Archived doc | Was the canonical… | Now superseded by |
|---|---|---|
| [`mvp-scope-memo.md`](mvp-scope-memo.md) | Day-3 MVP scope memo (single-vault → marketplace pivot framing) | [`docs/user-stories.md`](../user-stories.md) for the product spine; [`docs/launch-plan.md`](../launch-plan.md) for current submission scope |
| [`rfb-alignment.md`](rfb-alignment.md) | Day-1/2 RFB (Request-for-Build) mapping for the hackathon brief | The current Arc-Circle alignment doc [`docs/arc-alignment.md`](../arc-alignment.md) + the deck framing in [`docs/demo-script-pitch-deck-outline.md`](../demo-script-pitch-deck-outline.md) |
| [`qfin-paper-corpus-seed.md`](qfin-paper-corpus-seed.md) | Original 200-paper q-fin corpus seed-curation spec | [`docs/corpus-architecture.md`](../corpus-architecture.md) — covers the current 10,000-paper DB-backed substrate end-to-end |
| [`agora_project_analysis.md`](agora_project_analysis.md) | Day-2 red-team synthesis that drove the Day-3 rigor-as-wedge pivot | The pivot is now codified in [`docs/architectural-principles.md`](../architectural-principles.md) + [`docs/specs/selection-bias-corrections-spec.md`](../specs/selection-bias-corrections-spec.md); the rigor wedge is shipped — the analysis that argued for it lives here as historical reasoning |

## Why these specifically

The four archived docs share a pattern: each was *load-bearing during its phase* but has been **(a)** displaced by a current doc that's tighter and more accurate, **(b)** rendered partly obsolete by shipped code, or **(c)** both. Reading them alongside current docs would create noise — they argue for things we now treat as settled, in vocabulary that's drifted.

The current docs (listed in the right column above) are the canonical references going forward. If something looks wrong or missing in a current doc, fix the current doc — don't reach for the archived one.

## Architecture decision records

`docs/specs/backtrader-vs-vectorbt-decision-memo.md` was moved to [`docs/adr/`](../adr/)
rather than here. ADRs are durable decisions that future contributors need to understand
even though they're "settled" — they're not stale, they're load-bearing context.
