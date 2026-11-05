"""Data processing and statistical aggregation module (TASK 3).

Pipeline:
    1. load_jsonl      - read raw benchmark logs (data/raw/test_run.jsonl)
    2. filter_warmup   - discard cold-start "warmup" runs, keep "eval" runs
    3. bootstrap_ci    - percentile bootstrap 95% CI for the mean (seed-fixed)
    4. summarize       - median, p25/p75, p95, p99, MeanSD, CI, guardrail error rate
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "test_run.jsonl"
OUT_PATH = ROOT / "data" / "processed" / "metrics_summary.csv"
SEED = 42
N_BOOT = 10_000


def load_jsonl(path: Path = RAW_PATH) -> pd.DataFrame:
    """Load raw .jsonl benchmark logs into a DataFrame."""
    if not Path(path).exists():
        raise FileNotFoundError(f"Raw log not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    return pd.DataFrame(records)


def filter_warmup(df: pd.DataFrame) -> pd.DataFrame:
    """Discard cold-start warm-up runs; keep only evaluation runs."""
    if "phase" not in df.columns:
        raise ValueError("Expected a 'phase' column in the raw log.")
    return df[df["phase"] == "eval"].copy()


def bootstrap_ci(data, n_boot: int = N_BOOT, seed: int = SEED):
    """Percentile bootstrap 95% confidence interval for the mean.

    The random generator is seeded so the CI is bit-for-bit reproducible.
    """
    arr = np.asarray(data, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(arr), size=(n_boot, len(arr)))
    boot_means = arr[idx].mean(axis=1)
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    return float(lo), float(hi)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate evaluation runs per (method, platform).

    Reports latency Mean+/-SD, Median (p25-p75), tail percentiles (p95, p99),
    a bootstrap 95% CI for the mean latency, mean throughput, and the guardrail
    error rate (fraction of failed runs).
    """
    rows = []
    for (method, platform), g in df.groupby(["method", "platform"]):
        lat = g["latency_ms"].to_numpy(dtype=float)
        lo, hi = bootstrap_ci(lat)
        rows.append({
            "method": method,
            "platform": platform,
            "n_runs": len(g),
            "latency_mean_ms": lat.mean(),
            "latency_std_ms": lat.std(ddof=1),
            "latency_median_ms": np.median(lat),
            "latency_p25_ms": np.percentile(lat, 25),
            "latency_p75_ms": np.percentile(lat, 75),
            "latency_p95_ms": np.percentile(lat, 95),
            "latency_p99_ms": np.percentile(lat, 99),
            "ci95_low_ms": lo,
            "ci95_high_ms": hi,
            "throughput_mean_rps": g["throughput"].mean(),
            "error_rate": g["error"].mean(),
        })
    return pd.DataFrame(rows)


def main() -> pd.DataFrame:
    df = load_jsonl()
    eval_df = filter_warmup(df)
    summary = summarize(eval_df)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_PATH, index=False)
    print(f"[process_data] {len(df)} raw runs -> {len(eval_df)} eval runs "
          f"-> summary of {len(summary)} groups saved to {OUT_PATH}")
    return summary


if __name__ == "__main__":
    main()
