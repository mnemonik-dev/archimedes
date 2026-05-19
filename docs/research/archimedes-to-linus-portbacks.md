# Archimedes → Linus port-backs

Three things Archimedes has shipped in deployed / externally-verifiable form that Linus only designs softly. Pulled forward as a durable artifact so the idea isn't lost. Source: the bidirectional comparison in [`linus-archimedes-comparison.md`](linus-archimedes-comparison.md).

## The three ports

1. **Quantitative rigor gate as a hard admission primitive.** Archimedes' DSR + PBO + walk-forward-OOS + look-ahead gate is a *numeric, pass/fail* quality test. Linus's curation is a *soft* scorecard (DEC-0019) — fine for notes, **wrong for any Worker output that makes a stakeable prediction/claim.** Target: `src/linus/knowledge/rigor.py`.
2. **Externally-verifiable, hash-anchored provenance.** Linus has a great *internal* fsync'd append-only audit — but provenance you can only check *locally* doesn't enforce the Marelli accountability pillar. Archimedes anchors content hashes *externally* (on-chain) so a third party can verify/falsify. The pattern doesn't require a blockchain — a Merkle/notarized anchor works. Target: `src/linus/memory/anchor.py` — gives the accountability pillar enforcement *teeth*.
3. **Served + loud-degradation discipline.** Archimedes forced the stack into a deployed request path with `/health` reporting `llm_backend: live|canned`. Linus's richer stack is mostly offline; the lesson is the thin served surface + honest degradation signal.

Reciprocal insight: Archimedes is *pressure-testing Linus's own thesis* — that the durable asset is a compounding, citation-typed, provenance-anchored substrate — by making it externally verifiable. The parts to bring back are the **enforcement + externalization + the quantitative gate**, which Linus designed softly.

## Paste-ready prompt for Claude (run from the Linus repo)

```
Context: our sibling project Archimedes (a q-fin strategy engine) shipped, in a
deployed/externally-verifiable form, three things Linus currently only designs softly.
I want you to evaluate each against Linus's actual architecture and propose concrete
designs — do NOT implement yet; produce options + tradeoffs + the smallest first step.

1. QUANTITATIVE RIGOR GATE. Archimedes admits a strategy only if it passes a hard
   numeric battery: Deflated Sharpe Ratio, Probability of Backtest Overfitting (CSCV),
   walk-forward out-of-sample, and a look-ahead audit. Linus's quality handling is the
   soft DEC-0019 ingest scorecard. Question: for Linus Workers that emit stakeable
   predictions/claims (not just notes), should there be a hard, numeric admission gate
   analogous to this? Propose `src/linus/knowledge/rigor.py` — its interface, what
   "overfitting/look-ahead" mean for Worker outputs, and how it composes with the
   DEC-0019 scorecard (gate vs. signal). Reference the relevant ADRs/pillars.

2. EXTERNALLY-VERIFIABLE PROVENANCE. Linus's audit log (DEC-0030/31) is fsync'd,
   append-only, but locally checkable only — provenance a third party cannot
   independently verify doesn't fully enforce the Marelli accountability pillar.
   Archimedes anchors content hashes externally so any claim is verifiable/falsifiable
   after the fact. Propose `src/linus/memory/anchor.py`: an anchor adapter that makes
   the audit/episodic record externally tamper-evident WITHOUT requiring a blockchain
   (e.g. periodic Merkle-root notarization). Interface, threat model, what it adds over
   the current fsync log, and how it strengthens the accountability pillar.

3. SERVED + LOUD DEGRADATION. Archimedes wired its pipeline into a deployed request
   path with a /health endpoint reporting live-vs-degraded(canned) so silent failure
   is impossible. Evaluate: where in Linus would an analogous "honest degradation"
   signal matter most, and what's the minimal version?

For each: (a) does Linus already have something close (cite the file/ADR)? (b) is this
worth doing for Linus's own goals, or is it Archimedes-specific? (c) the smallest
high-signal first step. Be skeptical — reject any that don't serve Linus's thesis.
```

## Self-contained

The prompt above carries the facts Claude in the Linus repo needs — no Archimedes-context handoff required. Designed to *instigate evaluation*, not blindly build.
