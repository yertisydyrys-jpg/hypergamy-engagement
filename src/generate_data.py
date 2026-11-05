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


if __name__ == "__main__":
    main()
