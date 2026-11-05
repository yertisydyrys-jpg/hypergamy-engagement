"""Final visualization module (TASK 3).

Scientific-visualization rules implemented here:
  1. explicit axis titles with physical units (Latency (ms), Offered load (requests/s));
     logarithmic axes where values span an order of magnitude (fig 1)
  2. uncertainty quantification: shaded 95% bootstrap-CI bands + error bars (fig 1) and
     95% bootstrap-CI error bars on every median (fig 2)
  3. accessibility: colorblind-safe palette; series differ by marker, line style and
     hatch pattern in addition to colour, so they survive monochrome printing
  4. every figure exported as vector .pdf AND .png at 300 DPI
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator, NullFormatter, ScalarFormatter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from process_data import filter_warmup, load_jsonl  # noqa: E402

SUMMARY_PATH = ROOT / "data" / "processed" / "metrics_summary.csv"
LOAD_SUMMARY_PATH = ROOT / "data" / "processed" / "load_sweep_summary.csv"
FIG_DIR = ROOT / "reports" / "figures"

PLATFORMS = ["TikTok", "Instagram Reels", "YouTube Long"]
PALETTE = sns.color_palette("colorblind")  # colorblind-safe
STYLE = {  # colour + marker + linestyle + hatch: readable in grayscale
    "baseline": dict(color=PALETTE[0], marker="s", linestyle="--", hatch="//",
                     label="Baseline (sequential)"),
    "proposed": dict(color=PALETTE[1], marker="o", linestyle="-", hatch="..",
                     label="Proposed (concurrent)"),
}

plt.rcParams.update({
    "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10,
    "legend.fontsize": 9, "pdf.fonttype": 42, "ps.fonttype": 42,
})


def _require(path: Path) -> Path:
    if not Path(path).exists():
        raise FileNotFoundError(f"Run src/process_data.py first. Missing: {path}")
    return Path(path)


def load_summary(path: Path = SUMMARY_PATH) -> pd.DataFrame:
    return pd.read_csv(_require(path))


def fig1_latency_vs_load(load_summary_df: pd.DataFrame) -> None:
    """Mean latency vs offered load, one panel per platform (log-log), 95% bootstrap CI."""
    loads = sorted(load_summary_df["load_rps"].unique())
    fig, axes = plt.subplots(1, 3, figsize=(11.0, 4.0), sharey=True)
    for ax, platform in zip(axes, PLATFORMS):
        for method, st in STYLE.items():
            sub = (load_summary_df[(load_summary_df["platform"] == platform)
                                   & (load_summary_df["method"] == method)]
                   .sort_values("load_rps"))
            x = sub["load_rps"].to_numpy()
            y = sub["latency_mean_ms"].to_numpy()
            lo, hi = sub["ci95_low_ms"].to_numpy(), sub["ci95_high_ms"].to_numpy()
            ax.fill_between(x, lo, hi, color=st["color"], alpha=0.25, linewidth=0)  # CI band
            ax.errorbar(x, y, yerr=[y - lo, hi - y], color=st["color"], marker=st["marker"],
                        linestyle=st["linestyle"], capsize=3, linewidth=1.6, markersize=6,
                        label=st["label"])
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.xaxis.set_major_locator(FixedLocator(loads))
        ax.xaxis.set_major_formatter(ScalarFormatter())
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_yticks([60, 100, 200, 400, 800])
        ax.set_ylim(50, 950)  # explicit limits: identical layout across matplotlib versions
        ax.yaxis.set_major_formatter(ScalarFormatter())
        ax.yaxis.set_minor_formatter(NullFormatter())
        ax.set_title(platform)
        ax.set_xlabel("Offered load (requests/s)")
        ax.set_ylabel("Mean latency (ms, log scale)")
        ax.grid(True, which="major", alpha=0.3)
    axes[0].legend(frameon=False, loc="upper left")
    fig.suptitle("Pipeline latency vs offered load (mean with 95% bootstrap CI; "
                 "synthetic benchmark data)", y=1.02)
    fig.tight_layout()
    _save(fig, "fig1_latency_vs_load")


def fig2_distribution_boxplot(summary: pd.DataFrame) -> None:
    """Per-run latency distributions (evaluation phase) with 95% bootstrap CI of each median."""
    df = filter_warmup(load_jsonl())
    width = 0.34
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    for j, (method, st) in enumerate(STYLE.items()):
        offset = (j - 0.5) * (width + 0.04)
        data, pos, cis, meds = [], [], [], []
        for i, platform in enumerate(PLATFORMS):
            data.append(df[(df["method"] == method) & (df["platform"] == platform)]["latency_ms"])
            pos.append(i + offset)
            row = summary[(summary["method"] == method) & (summary["platform"] == platform)].iloc[0]
            meds.append(row["latency_median_ms"])
            cis.append((row["median_ci95_low_ms"], row["median_ci95_high_ms"]))
        bp = ax.boxplot(data, positions=pos, widths=width, patch_artist=True, showfliers=False,
                        medianprops=dict(color="black", linewidth=1.4),
                        whiskerprops=dict(color="black"), capprops=dict(color="black"),
                        boxprops=dict(edgecolor="black"))
        for patch in bp["boxes"]:
            patch.set_facecolor(st["color"])
            patch.set_alpha(0.75)
            patch.set_hatch(st["hatch"])
        lo = np.array(meds) - np.array([c[0] for c in cis])
        hi = np.array([c[1] for c in cis]) - np.array(meds)
        ax.errorbar(pos, meds, yerr=[lo, hi], fmt="none", ecolor="black", elinewidth=2.0,
                    capsize=5, capthick=2.0, zorder=5)  # 95% CI of the median
    ax.set_xticks(range(len(PLATFORMS)))
    ax.set_xticklabels(PLATFORMS)
    ax.set_xlabel("Platform")
    ax.set_ylabel("Pipeline latency (ms)")
    ax.set_title("Per-run latency distribution (evaluation phase, warm-up filtered)")
    ax.grid(axis="y", alpha=0.3)
    handles = [Patch(facecolor=s["color"], edgecolor="black", hatch=s["hatch"], alpha=0.75,
                     label=s["label"]) for s in STYLE.values()]
    handles.append(plt.Line2D([0], [0], color="black", linewidth=2.0, marker="_", markersize=9,
                              label="95% bootstrap CI of median"))
    ax.legend(handles=handles, frameon=False, loc="upper left")
    fig.tight_layout()
    _save(fig, "fig2_distribution_boxplot")


def _save(fig: plt.Figure, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    # CreationDate=None keeps the PDF byte-for-byte reproducible between runs
    fig.savefig(FIG_DIR / f"{name}.pdf", bbox_inches="tight", metadata={"CreationDate": None})  # vector
    fig.savefig(FIG_DIR / f"{name}.png", dpi=300, bbox_inches="tight")    # raster, for README
    plt.close(fig)
    print(f"[visualize] saved {name}.pdf / {name}.png")


def main() -> None:
    fig1_latency_vs_load(pd.read_csv(_require(LOAD_SUMMARY_PATH)))
    fig2_distribution_boxplot(load_summary())


if __name__ == "__main__":
    main()
