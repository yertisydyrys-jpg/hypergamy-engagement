"""Data processing and statistical aggregation module (TASK 3).

Pipeline:
    1. load_jsonl      - read raw benchmark logs (data/raw/test_run.jsonl)
    2. validate_raw    - schema + data-completeness guardrail (>= 95% valid records)
    3. filter_warmup   - discard cold-start "warmup" runs, keep "eval" runs
    4. summarize       - median, p25/p75, p95, p99, Mean+/-SD, bootstrap 95% CIs
                         (mean, median, p95, p99), error rate + Wilson 95% CI
    5. compare_methods - Baseline vs Proposed: relative median-latency reduction
                         with a bootstrap 95% CI per platform
    6. warmup_report   - quantifies the cold-start effect that is filtered out

Reproducibility: every bootstrap uses numpy's Generator seeded with SEED (42).
Note: failed runs (error == True) stay in the latency statistics (conservative
choice); the error rate is tracked separately as a guardrail metric.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "test_run.jsonl"
OUT_PATH = ROOT / "data" / "processed" / "metrics_summary.csv"
COMPARE_PATH = ROOT / "data" / "processed" / "method_comparison.csv"
WARMUP_PATH = ROOT / "data" / "processed" / "warmup_report.csv"
SEED = 42
N_BOOT = 10_000
ERROR_GUARDRAIL = 0.05          # error rate must stay below 5% in every group
COMPLETENESS_GUARDRAIL = 0.95   # >= 95% valid records
REQUIRED_COLS = ["run_id", "phase", "method", "platform", "latency_ms", "throughput", "error"]


def load_jsonl(path: Path = RAW_PATH) -> pd.DataFrame:
    """Load raw .jsonl benchmark logs into a DataFrame."""
    if not Path(path).exists():
        raise FileNotFoundError(f"Raw log not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    return pd.DataFrame(records)


def validate_raw(df: pd.DataFrame) -> float:
    """Check schema and data completeness; return the share of valid records.

    Guardrail from the methodology passport: completeness must be >= 95%.
    """
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Raw log is missing required columns: {missing}")
    valid = df[REQUIRED_COLS].notna().all(axis=1) & (df["latency_ms"] > 0)
    completeness = float(valid.mean())
    if completeness < COMPLETENESS_GUARDRAIL:
        raise ValueError(f"Data completeness {completeness:.1%} < {COMPLETENESS_GUARDRAIL:.0%}")
    return completeness


def filter_warmup(df: pd.DataFrame) -> pd.DataFrame:
    """Discard cold-start warm-up runs; keep only evaluation runs."""
    if "phase" not in df.columns:
        raise ValueError("Expected a 'phase' column in the raw log.")
    return df[df["phase"] == "eval"].copy()


def _resample_idx(n: int, n_boot: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, n, size=(n_boot, n))


def bootstrap_ci(data, n_boot: int = N_BOOT, seed: int = SEED):
    """Percentile bootstrap 95% confidence interval for the mean.

    The random generator is seeded so the CI is bit-for-bit reproducible.
    """
    arr = np.asarray(data, dtype=float)
    idx = _resample_idx(len(arr), n_boot, seed)
    boot_means = arr[idx].mean(axis=1)
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    return float(lo), float(hi)


def bootstrap_stat_ci(data, stat: str = "median", n_boot: int = N_BOOT, seed: int = SEED):
    """Percentile bootstrap 95% CI for the median, p95 or p99 of ``data``."""
    arr = np.asarray(data, dtype=float)
    samples = arr[_resample_idx(len(arr), n_boot, seed)]
    if stat == "median":
        boot = np.median(samples, axis=1)
    elif stat in ("p95", "p99"):
        boot = np.percentile(samples, float(stat[1:]), axis=1)
    else:
        raise ValueError(f"Unsupported statistic: {stat}")
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(lo), float(hi)


def wilson_ci(k: int, n: int, z: float = 1.96):
    """Wilson score 95% interval for a proportion (robust for rates near 0)."""
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return float(max(0.0, centre - half)), float(min(1.0, centre + half))


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate evaluation runs per (method, platform).

    Reports latency Mean+/-SD, Median (p25-p75), tail percentiles (p95, p99),
    bootstrap 95% CIs (mean, median, p95, p99), mean throughput and the guardrail
    error rate (fraction of failed runs) with a Wilson 95% CI.
    """
    rows = []
    for (method, platform), g in df.groupby(["method", "platform"]):
        lat = g["latency_ms"].to_numpy(dtype=float)
        lo, hi = bootstrap_ci(lat)
        med_lo, med_hi = bootstrap_stat_ci(lat, "median")
        p95_lo, p95_hi = bootstrap_stat_ci(lat, "p95")
        p99_lo, p99_hi = bootstrap_stat_ci(lat, "p99")
        n_err = int(g["error"].sum())
        err_lo, err_hi = wilson_ci(n_err, len(g))
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
            "median_ci95_low_ms": med_lo,
            "median_ci95_high_ms": med_hi,
            "p95_ci95_low_ms": p95_lo,
            "p95_ci95_high_ms": p95_hi,
            "p99_ci95_low_ms": p99_lo,
            "p99_ci95_high_ms": p99_hi,
            "n_errors": n_err,
            "error_rate_ci95_low": err_lo,
            "error_rate_ci95_high": err_hi,
            "guardrail_ok": bool(g["error"].mean() < ERROR_GUARDRAIL),
        })
    return pd.DataFrame(rows)


def compare_methods(df: pd.DataFrame, n_boot: int = N_BOOT, seed: int = SEED) -> pd.DataFrame:
    """Baseline vs Proposed per platform.

    Effect = relative reduction of the median latency, (med_base - med_prop) / med_base,
    with a percentile bootstrap 95% CI (the two groups are resampled independently).
    """
    rows = []
    for platform, g in df.groupby("platform"):
        base = g.loc[g["method"] == "baseline", "latency_ms"].to_numpy(dtype=float)
        prop = g.loc[g["method"] == "proposed", "latency_ms"].to_numpy(dtype=float)
        mb = np.median(base[_resample_idx(len(base), n_boot, seed)], axis=1)
        mp = np.median(prop[_resample_idx(len(prop), n_boot, seed + 1)], axis=1)
        red = (mb - mp) / mb
        lo, hi = np.percentile(red, [2.5, 97.5])
        rows.append({
            "platform": platform,
            "median_baseline_ms": float(np.median(base)),
            "median_proposed_ms": float(np.median(prop)),
            "median_reduction_pct": float((np.median(base) - np.median(prop)) / np.median(base) * 100),
            "reduction_ci95_low_pct": float(lo * 100),
            "reduction_ci95_high_pct": float(hi * 100),
            "ci_excludes_zero": bool(lo > 0),
        })
    return pd.DataFrame(rows)


def warmup_report(raw: pd.DataFrame) -> pd.DataFrame:
    """Quantify the cold-start spike that the warm-up filter removes."""
    rows = []
    for (method, platform), g in raw.groupby(["method", "platform"]):
        w = g.loc[g["phase"] == "warmup", "latency_ms"]
        e = g.loc[g["phase"] == "eval", "latency_ms"]
        rows.append({
            "method": method,
            "platform": platform,
            "n_warmup": len(w),
            "n_eval": len(e),
            "warmup_mean_ms": float(w.mean()),
            "eval_mean_ms": float(e.mean()),
            "cold_start_inflation_x": float(w.mean() / e.mean()),
        })
    return pd.DataFrame(rows)


def main() -> pd.DataFrame:
    df = load_jsonl()
    completeness = validate_raw(df)
    eval_df = filter_warmup(df)
    summary = summarize(eval_df)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_PATH, index=False)
    compare_methods(eval_df).to_csv(COMPARE_PATH, index=False)
    warmup_report(df).to_csv(WARMUP_PATH, index=False)
    print(f"[process_data] completeness={completeness:.1%} | {len(df)} raw runs -> "
          f"{len(eval_df)} eval runs -> summary of {len(summary)} groups saved to {OUT_PATH}")
    return summary


if __name__ == "__main__":
    main()
