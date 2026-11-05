"""Final visualization module (TASK 3).

Scientific-visualization rules implemented here:
  * explicit axis titles with physical units (Latency (ms), Throughput (videos/s))
  * uncertainty quantification: 95% bootstrap CI shown as error bars (fig 1)
  * accessibility: colorblind-safe palette + distinct markers/linestyles per series
  * every figure exported as vector .pdf AND .png at >= 300 DPI
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "data" / "processed" / "metrics_summary.csv"
FIG_DIR = ROOT / "reports" / "figures"

PALETTE = sns.color_palette("colorblind")  # colorblind-safe
STYLE = {  # distinct markers + linestyles so series survive grayscale printing
    "baseline": dict(marker="s", linestyle="--", label="Baseline (sequential)"),
    "proposed": dict(marker="o", linestyle="-", label="Proposed (concurrent)"),
}


def load_summary(path: Path = SUMMARY_PATH) -> pd.DataFrame:
    if not Path(path).exists():
        raise FileNotFoundError(f"Run src/process_data.py first. Missing: {path}")
    return pd.read_csv(path)


def fig1_latency_vs_platform(summary: pd.DataFrame) -> None:
    """Mean pipeline latency per platform with 95% bootstrap CI error bars."""
    platforms = ["TikTok", "Instagram Reels", "YouTube Long"]
    x = range(len(platforms))
    width = 0.36

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for i, (method, st) in enumerate(STYLE.items()):
        sub = summary[summary["method"] == method].set_index("platform").loc[platforms]
        means = sub["latency_mean_ms"].to_numpy()
        # CI half-width around the mean
        lo = means - sub["ci95_low_ms"].to_numpy()
        hi = sub["ci95_high_ms"].to_numpy() - means
        ax.errorbar([p + (i - 0.5) * width for p in x], means,
                    yerr=[lo, hi], fmt=st["marker"] + st["linestyle"],
                    color=PALETTE[i], capsize=4, linewidth=1.8,
                    markersize=7, label=st["label"])

    ax.set_xticks(list(x))
    ax.set_xticklabels(platforms)
    ax.set_xlabel("Platform")
    ax.set_ylabel("Pipeline latency (ms)")
    ax.set_title("Collection-pipeline latency per platform (mean with 95% bootstrap CI)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False)
    fig.tight_layout()
    _save(fig, "fig1_latency_vs_load")


def fig2_distribution_boxplot(summary_path: Path = SUMMARY_PATH) -> None:
    """Boxplot of per-run evaluation latency per platform and method."""
    import json
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from process_data import load_jsonl, filter_warmup

    df = filter_warmup(load_jsonl())
    order = ["TikTok", "Instagram Reels", "YouTube Long"]

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    sns.boxplot(data=df, x="platform", y="latency_ms", hue="method", order=order,
                hue_order=["baseline", "proposed"], palette=PALETTE,
                showfliers=False, ax=ax)
    ax.set_xlabel("Platform")
    ax.set_ylabel("Pipeline latency (ms)")
    ax.set_title("Per-run latency distribution (evaluation phase, warm-up filtered)")
    ax.grid(axis="y", alpha=0.3)
    handles, labels = ax.get_legend_handles_labels()
    labels = ["Baseline (sequential)", "Proposed (concurrent)"]
    ax.legend(handles, labels, frameon=False)
    fig.tight_layout()
    _save(fig, "fig2_distribution_boxplot")


def _save(fig: plt.Figure, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / f"{name}.pdf")                 # vector, for LaTeX
    fig.savefig(FIG_DIR / f"{name}.png", dpi=300)        # raster, for README
    plt.close(fig)
    print(f"[visualize] saved {name}.pdf / {name}.png")


def main() -> None:
    summary = load_summary()
    fig1_latency_vs_platform(summary)
    fig2_distribution_boxplot()


if __name__ == "__main__":
    main()
