# Pitch talking points — rigor / provenance / agent track

> **Status:** One-page handout for whoever runs the pitch deck (Dan, per
> CLAUDE.md). Supplements [`demo-script-pitch-deck-outline.md`](demo-script-pitch-deck-outline.md);
> *does not replace it*. This is ammunition for the slides that touch
> rigor, the LLM agent, and on-chain provenance — the differentiation
> arc against the "96 other AI-portfolio submissions" landscape.
>
> Print double-sided, keep next to the laptop during the pitch.

## The 3-line elevator

1. **What it is:** A non-custodial portfolio agent that turns peer-reviewed quantitative finance research into investable strategies on Arc.
2. **Why it's defensible:** Every position is paper-anchored, rigor-gated (DSR + PBO + walk-forward OOS), covariance-optimized, stress-tested, and on-chain anchored. Not "trust me" — *verify it*.
3. **Why now:** November 2025 showed that the curation layer above the on-chain asset-management stack breaks on rigor. We're the rigor.

## The four credibility moves

These are the moves that distinguish us from generic LLM-portfolio submissions. **Mention at least three of them in the pitch.**

### 1. Selection-bias correction is the wedge

> *"Every Tier-1 strategy clears four statistical bars before admission: Deflated Sharpe (Bailey & López de Prado 2014), Probability of Backtest Overfitting (Bailey, Borwein, López de Prado, Zhu 2014), walk-forward out-of-sample Sharpe with no in/out cliff, and a look-ahead static audit. The numbers are on the screen — including the ones that fail. We don't hide."*

**Why this lands:** Most AI-portfolio submissions cite a Sharpe ratio from a single backtest. We tell the judges *which* statistical tests we're passing AND surface the failures honestly. Honesty is the credential.

### 2. The agent uses real tools, not just text generation

> *"The LLM isn't picking from a menu. It calls `get_asset_stats` on candidates, `get_correlation` on its top picks, `stress_test_portfolio` on its tentative allocation. Up to 12 tool-use turns before it's forced to finalize. The trace of every call is in the response — auditable per pick."*

**Why this lands:** Distinguishes us from "I asked ChatGPT to make me a portfolio." The investigation trace is *evidence the agent reasoned*, not a black box.

### 3. The math is correct and verifiable

> *"Covariance-aware Kelly mean-variance, γ-mapped per risk profile. Identity-shrinkage covariance. Magdon-Ismail closed-form expected maximum drawdown — not a 2-sigma approximation. Parametric VaR-95 alongside. Euler variance decomposition: for every 1% of weight, we tell you which 1% of variance it contributes."*

**Why this lands:** A quant-savvy judge will spot fake math in five seconds. We pre-emptively cite the math. Our PR includes a multi-agent self-review that caught — and fixed — a Kelly-formula bug. The bar is real-research-shop hygiene.

### 4. Provenance is on-chain

> *"Every recommendation produces a keccak-256 hash of the canonical JSON — regime, picks, paper anchors, market context. The canonical JSON is deterministic (we sort the strategies list explicitly). Any auditor can re-derive the hash on their laptop and verify against `ReasoningTraceRegistry` on Arc. This is what the on-chain story actually buys you."*

**Why this lands:** Many "on-chain AI" demos are *off-chain everything + 1 NFT*. We have a real verifiability primitive. The hash is the integrity guarantee.

## The honest-frame slide (non-negotiable per master script)

When you say what we don't claim, the rest of the pitch becomes 2× more credible:

- **Arc is testnet only.** No mainnet. Faucet USDC. By design.
- **We don't claim alpha.** The strategies are paper-grounded — Faber, Moskowitz-Ooi-Pedersen, Moreira-Muir, George-Hwang. The edge is rigorous construction over an audited library, not proprietary signal.
- **AI can be wrong.** "Win more than you lose, not never lose." Whether the *generated* strategies are profitable in production is genuinely TBD.
- **The real-funds custody + RIA posture is roadmap.** Today's proof is provenance and rigor.

## The 96-other-submissions comparison

If a judge asks "how is this different from [other Arc HackMoney AI-portfolio]?" — the discriminator is:

| Them | Us |
|---|---|
| Sharpe ratio from one backtest | Deflated Sharpe + PBO + walk-forward OOS + look-ahead audit |
| "Our model picked these stocks" | LLM agent with `get_correlation` / `stress_test_portfolio` tools, full trace |
| Equal-weight or naive optimization | Constrained Markowitz/Kelly with identity-shrinkage covariance, Magdon-Ismail max-DD |
| "Verifiable on-chain" (1 NFT) | Deterministic keccak hash you can recompute offline, anchored on `ReasoningTraceRegistry` |
| "AI-powered" | Paper-anchored — every position traces to a peer-reviewed publication |

## The closer

> *"The Agora was where Athens did its thinking out loud. Archimedes the mathematician was its empiricist — π by exhaustion, levers, proofs. **Archimedes the product is an AI citizen who participates in the modern agora with proofs.** Every position has a paper. Every recommendation has a hash. The lever is academic research; the fulcrum is autonomous AI; the world is your portfolio."*

## Don't-say list

| Avoid | Why |
|---|---|
| "Our model" | Reinforces the black-box framing we're trying to escape. Say "the agent" or "the optimizer." |
| "Beats the market" | We don't claim alpha. |
| "Fully autonomous" | We're bounded by the paper-anchored library. Say "research-grounded autonomy." |
| "Production-ready" | Testnet by design. Say "Arc-stage" or "non-custodial vault on Arc testnet." |
| "Better than [X]" | Don't pick fights. Compare on dimensions (rigor, provenance, tools), not on competitors. |

## Live-demo backup if Portfolio Advisor moment breaks

See [`portfolio-advisor-demo-cues.md`](portfolio-advisor-demo-cues.md) for the verbatim
60-second cue card. Backup recording in a hidden tab. Don't fake it on stage.

---

**One last note:** Judges remember the demo *moment* more than the slides. The
moment we should engineer is the agent's tool-use trace — the line where the
agent says "I checked the correlation, saw it was too high, dropped the pick."
That's the moment that proves the agent isn't a glorified completion call. Make
sure the live demo hits that beat.
