"""Generate simulated benchmark logs for the hypergamy engagement collection pipeline.

NOTE FOR REVIEWERS
------------------
The raw log below is SYNTHETIC (simulated with a fixed random seed). It exists so that
the whole TASK 3 pipeline (warm-up filtering, statistics, figures) is runnable from a
clean clone. Replace data/raw/test_run.jsonl with the real Week 7-8 collection logs
before citing the numbers in a report.

Each record is one pipeline run that collects engagement metadata (views, likes,
comments) for a batch of hypergamy-discourse videos on one platform.

Fields
------
run_id      : int    - sequential run identifier
phase       : str    - "warmup" (cold start, discarded) or "eval" (measured)
method      : str    - "baseline" (sequential collector) or "proposed" (concurrent collector)
platform    : str    - TikTok | Instagram Reels | YouTube Long
latency_ms  : float  - wall-clock time of the run, milliseconds
throughput  : float  - videos processed per second
error       : bool   - did the run fail (guardrail metric)
"""

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "test_run.jsonl"

PLATFORMS = ["TikTok", "Instagram Reels", "YouTube Long"]

# method -> platform -> (mean eval latency ms, mean eval throughput videos/s)
PARAMS = {
    "baseline": {
        "TikTok": (128.0, 42.0),
        "Instagram Reels": (146.0, 38.0),
        "YouTube Long": (191.0, 30.0),
    },
    "proposed": {
        "TikTok": (96.0, 61.0),
        "Instagram Reels": (109.0, 55.0),
        "YouTube Long": (143.0, 44.0),
    },
}

N_WARMUP = 12
N_EVAL = 150


def main(seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    records = []
    run_id = 0
    for method, per_platform in PARAMS.items():
        for platform in PLATFORMS:
            mu_lat, mu_thr = per_platform[platform]
            # --- warm-up phase: cold-start spikes, discarded in analysis ---
            for _ in range(N_WARMUP):
                run_id += 1
                latency = float(np.clip(rng.normal(3.2 * mu_lat, 0.6 * mu_lat), 50, None))
                throughput = float(np.clip(rng.normal(0.45 * mu_thr, 0.12 * mu_thr), 1, None))
                error = bool(rng.random() < 0.04)
                records.append(dict(run_id=run_id, phase="warmup", method=method,
                                    platform=platform, latency_ms=round(latency, 2),
                                    throughput=round(throughput, 2), error=error))
            # --- evaluation phase: the measured benchmark ---
            for _ in range(N_EVAL):
                run_id += 1
                latency = float(np.clip(rng.normal(mu_lat, 0.18 * mu_lat), 20, None))
                throughput = float(np.clip(rng.normal(mu_thr, 0.15 * mu_thr), 1, None))
                error = bool(rng.random() < 0.008)
                records.append(dict(run_id=run_id, phase="eval", method=method,
                                    platform=platform, latency_ms=round(latency, 2),
                                    throughput=round(throughput, 2), error=error))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    print(f"[generate_data] wrote {len(records)} records -> {OUT}")



# ---------------------------------------------------------------------------
# Load sweep (feeds fig1 "latency vs load"); SYNTHETIC like the file above.
# Queueing-style model: latency = floor / (1 - rho), rho = offered load / capacity,
# with right-skewed (log-normal) noise. A separate RNG stream (seed + 1) is used so
# data/raw/test_run.jsonl stays bit-for-bit identical.
# ---------------------------------------------------------------------------
LOAD_OUT = ROOT / "data" / "raw" / "load_sweep.jsonl"
LOADS_RPS = [10, 20, 40, 80, 120, 160]            # offered load, requests per second
FLOOR_MS = {"TikTok": 77.0, "Instagram Reels": 88.0, "YouTube Long": 115.0}  # unloaded latency of baseline
FLOOR_FACTOR = {"baseline": 1.0, "proposed": 0.75}
CAPACITY_RPS = {                                    # saturation throughput of each collector
    "baseline": {"TikTok": 230.0, "Instagram Reels": 210.0, "YouTube Long": 190.0},
    "proposed": {"TikTok": 340.0, "Instagram Reels": 310.0, "YouTube Long": 280.0},
}
N_WARMUP_LOAD = 4
N_EVAL_LOAD = 80
SIGMA = 0.12                                        # log-normal noise


def generate_load_sweep(seed: int = 42) -> None:
    """Simulate latency / throughput / errors at several offered-load levels."""
    rng = np.random.default_rng(seed + 1)
    records, run_id = [], 0
    for method in ("baseline", "proposed"):
        for platform in PLATFORMS:
            cap = CAPACITY_RPS[method][platform]
            floor = FLOOR_MS[platform] * FLOOR_FACTOR[method]
            for load in LOADS_RPS:
                rho = load / cap
                expected = floor / (1.0 - rho)
                for phase, n, inflate in (("warmup", N_WARMUP_LOAD, 3.0), ("eval", N_EVAL_LOAD, 1.0)):
                    for _ in range(n):
                        run_id += 1
                        noise = rng.lognormal(-0.5 * SIGMA**2, SIGMA)
                        latency = expected * inflate * noise
                        achieved = min(load, cap) * rng.normal(1.0, 0.03)
                        p_err = (0.04 if phase == "warmup" else 0.004 + 0.03 * rho**3)
                        records.append(dict(run_id=run_id, phase=phase, method=method,
                                            platform=platform, load_rps=load,
                                            latency_ms=round(float(latency), 2),
                                            throughput_rps=round(float(achieved), 2),
                                            error=bool(rng.random() < p_err)))
    LOAD_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(LOAD_OUT, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    print(f"[generate_data] wrote {len(records)} records -> {LOAD_OUT}")


if __name__ == "__main__":
    main()
    generate_load_sweep()
