from __future__ import annotations

OPERATION_TO_SYMBOL: dict[str, str] = {
    "SPY": "SPY",
    "NIKKEI": "^N225",
    "GOLD": "GC=F",
    "TREASURY": "TLT",
    "OIL": "CL=F",
    # ETF legs for relative-value / pairs strategies (Gatev et al. 2006).
    "GLD": "GLD",  # SPDR Gold Shares — tradeable gold ETF leg
    "GDX": "GDX",  # VanEck Gold Miners ETF — co-moves with GLD, the divergent leg
    "IVV": "IVV",  # iShares Core S&P 500 — near-cointegrated with SPY (sanity-check pair)
}


def resolve_operations(operations: list[str]) -> list[str]:
    normalized = [op.upper() for op in operations]
    unsupported = [op for op in normalized if op not in OPERATION_TO_SYMBOL]
    if unsupported:
        raise ValueError(f"Unsupported operation(s): {', '.join(unsupported)}")
    return normalized
