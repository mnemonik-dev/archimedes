# LLM Cost Estimate: Generate Button

> **Date:** 2026-05-25  
> **Model:** `claude-sonnet-4-20250514` (configured via `LLM_MODEL` in `.env`)  
> **Pricing:** $3.00 / MTok input, $15.00 / MTok output  
> **Provider:** Anthropic-compatible endpoint (GLM via z.ai in production; pricing here assumes direct Anthropic rates as upper bound)  
> **Prompt caching:** Not currently enabled in the codebase (`max_tokens=4096` hardcoded; no `cache_control` blocks)

---

## Architecture: What Happens on Each Generate Press

The generation pipeline (`backend/archimedes/agents/generation_pipeline.py`) executes:

1. **Brief Validation** — 1 LLM call. Small system prompt validates user intent.
2. **Strategy Generation** — multi-turn agent with tool use (`portfolio_agent.py`).  
   The agent uses `propose_portfolio_with_tools()` which iterates up to `MAX_AGENT_ITERATIONS = 12` API calls, though typical runs complete in 3–5 turns.

### Current Flow (single regime)
| Step | API Calls |
|------|-----------|
| Brief validation | 1 |
| Agent run (1 regime) | 3–5 turns |
| **Total** | **4–6 API calls** |

### New Dual Bull/Bear Flow (issue #163)
| Step | API Calls |
|------|-----------|
| Brief validation | 1 |
| Bull-regime agent run | 3–5 turns |
| Bear-regime agent run | 3–5 turns |
| **Total** | **7–11 API calls** |

---

## Token Breakdown by Call Type

### 1. Brief Validation (`_BRIEF_VALIDATION_SYSTEM`)

| Component | Tokens |
|-----------|--------|
| System prompt | ~240 |
| User message (JSON: intent + risk + assets) | ~70 |
| **Total input** | **~310** |
| Output (small JSON verdict) | **~100** |

**Cost per call:** $0.0009 input + $0.0015 output = **$0.0024**

### 2. Portfolio Agent — Multi-Turn Tool Use

The agent builds a large context window that grows each turn. Key components:

**Fixed per-turn (system + tools, billed every API call):**

| Component | Tokens |
|-----------|--------|
| System prompt (`_build_system_prompt` + tool-use addendum) | ~550 |
| Tool definitions (4 tools: `get_asset_stats`, `get_correlation`, `stress_test_portfolio`, `propose_portfolio`) | ~850 |
| **Fixed overhead** | **~1,400** |

**User prompt (`_build_tool_user_prompt`):**

| Component | Tokens |
|-----------|--------|
| Context (regime, risk, budgets) | ~80 |
| Market ranking (top 20 instruments, ~50 chars each) | ~250 |
| Paper strategies (6 strategies with stats + rules) | ~300 |
| Available universe (90+ instruments by asset class) | ~750 |
| Process instructions | ~150 |
| **Total user prompt** | **~1,530** |

**Typical 4-turn agent run (2–3 tool calls per turn, final propose):**

| Turn | Input Tokens (cumulative) | Output Tokens | Description |
|------|--------------------------|---------------|-------------|
| 1 | 2,930 | ~320 | 3–4× `get_asset_stats` |
| 2 | 4,170 | ~240 | 2–3× `get_correlation` |
| 3 | 4,860 | ~100 | 1× `stress_test_portfolio` |
| 4 | 5,260 | ~800 | `propose_portfolio` (final JSON) |
| **Total** | **17,220** | **1,460** | |

**Cost per agent run:** $0.0517 input + $0.0219 output = **$0.0736**

---

## Cost Per Generate Button Press

### Current: Single Regime

| Component | Input Tokens | Output Tokens | Cost |
|-----------|-------------|---------------|------|
| Brief validation | 310 | 100 | $0.0024 |
| Agent run (1×) | 17,220 | 1,460 | $0.0736 |
| **Total** | **17,530** | **1,560** | **$0.076** |

### New: Dual Bull/Bear Regime (issue #163)

| Component | Input Tokens | Output Tokens | Cost |
|-----------|-------------|---------------|------|
| Brief validation | 310 | 100 | $0.0024 |
| Bull-regime agent run | 17,220 | 1,460 | $0.0736 |
| Bear-regime agent run | 17,220 | 1,460 | $0.0736 |
| **Total** | **34,750** | **3,020** | **$0.150** |

**Impact:** The dual-regime feature roughly doubles the per-Generate cost (~$0.076 → ~$0.150, a 97% increase).

---

## Daily Cost at Scale

| Daily Generates | Current (single regime) | New (dual regime) | Monthly (dual) |
|-----------------|------------------------|-------------------|----------------|
| 10 | $0.76 | $1.50 | $45 |
| 100 | $7.60 | $14.96 | $449 |
| 1,000 | $76 | $150 | $4,493 |
| 10,000 | $760 | $1,496 | $44,930 |

---

## Variance & Edge Cases

The estimates above assume a **typical 4-turn agent run**. In practice:

| Scenario | Turns | Input Tokens | Output Tokens | Cost/Generate (dual) |
|----------|-------|-------------|---------------|---------------------|
| Fast (agent decides quickly) | 2 | 7,060 | 1,120 | $0.060 |
| Typical | 4 | 17,220 | 1,460 | $0.150 |
| Worst-case (12 iterations) | 12 | 58,000 | 3,200 | $0.444 |

The 5-minute **response cache** (`_CACHE_TTL_SEC = 300`) in `portfolio_agent.py` deduplicates identical (regime, risk_profile, top_synths) combinations, which helps during repeated testing but not in production where each user brief is unique.

---

## Cost Optimization Opportunities

### 1. Prompt Caching (highest impact, ~75% input cost reduction on multi-turn)

Anthropic's prompt caching charges $0.30/MTok for cache hits (vs $3.00/MTok base). The agent's system prompt + tools (~1,400 tokens) are identical across all turns within a run.

| Optimization | Savings per Generate (dual) |
|---|---|
| Cache system+tools within a run (4 turns × 1,400 = 5,600 tokens saved × 2 runs) | ~$0.030 (20% of input cost) |
| Cache system+tools across runs (amortize over requests within TTL) | Up to 75% of fixed overhead |

**Implementation:** Add `cache_control: {"type": "ephemeral"}` to the system message block in `messages.create()`. Requires restructuring `LLMBackend.complete()` to pass structured messages.

### 2. Smaller Model for Brief Validation (trivial, ~$0.001 savings/call)

Brief validation is a classification task (valid/invalid + field extraction). Claude Haiku 3.5 ($0.25/MTok input, $1.25/MTok output) handles it perfectly:

| Model | Cost/validation |
|-------|----------------|
| Sonnet 4 (current) | $0.0024 |
| Haiku 3.5 | $0.0002 |
| **Savings** | **$0.0022/call** |

Low absolute impact since validation is only ~3% of total cost, but a clean separation.

### 3. Reduce Agent Iterations via Better Prompting

Currently `MAX_AGENT_ITERATIONS = 12`. The agent is instructed to:
1. get_asset_stats on 4–8 names
2. get_correlation on pairs
3. stress_test_portfolio
4. propose_portfolio

**Optimization:** Pre-compute asset stats and correlation in the prompt itself (as a table), eliminating tool calls 1–2. This converts the multi-turn agent into a 1–2 turn flow:

| Current (4 turns, 2 runs) | Optimized (2 turns, 2 runs) |
|---|---|
| ~34,750 input tokens | ~12,000 input tokens |
| Cost: $0.150 | Cost: $0.081 |
| **Savings: 46%** | |

Trade-off: Loses the "investigative agent" narrative for the demo (tool calls are streamed to the frontend as progress events).

### 4. Batch API (50% discount, latency trade-off)

Anthropic's Batch API offers 50% off ($1.50/MTok input, $7.50/MTok output) with 24-hour SLA. Not viable for interactive Generate but could work for:
- Pre-computing strategy libraries overnight
- Background portfolio rebalancing signals

### 5. GLM Backend (already partially in use)

The production endpoint routes through GLM via z.ai (`LLM_PROVIDER=anthropic_compatible`). GLM-4.7 pricing (if direct) is significantly cheaper than Claude Sonnet 4. The cost estimate above represents the **ceiling** if using direct Anthropic billing. Actual production costs may be lower depending on the z.ai agreement.

---

## Summary

| Metric | Current | Dual Bull/Bear |
|--------|---------|---------------|
| Cost per Generate | **$0.076** | **$0.150** |
| Dominant cost driver | Output tokens (62%) | Output tokens (60%) |
| At 100 generates/day | $7.60/day | $14.96/day |
| At 1,000 generates/day | $76/day | $150/day |
| Best optimization lever | Prompt caching + fewer turns | Same |
| Optimized cost (caching + fewer turns) | ~$0.040 | ~$0.075 |

The dual bull/bear feature (issue #163) is a clean 2× multiplier on the generation cost. At hackathon scale (10–100 generates/day) this is negligible ($0.15–$15/day). At production scale (1,000+ generates/day), prompt caching and pre-computed market data become essential to keep costs under $100/day.
