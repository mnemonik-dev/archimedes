"""StockBench evaluation package.

Run with: python -m archimedes.evaluation.stockbench --dry-run
"""

from .adapter import (
    ArchimedesStockBenchAdapter,
    BenchmarkResult,
    MultiSeedReport,
    PUBLISHED_BASELINES,
    run_multi_seed,
    write_results_json,
    write_results_markdown,
)

__all__ = [
    "ArchimedesStockBenchAdapter",
    "BenchmarkResult",
    "MultiSeedReport",
    "PUBLISHED_BASELINES",
    "run_multi_seed",
    "write_results_json",
    "write_results_markdown",
]
