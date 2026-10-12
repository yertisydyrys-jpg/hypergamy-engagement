import os
import sys
import yaml
import numpy as np
import pandas as pd
from scipy import stats

def load_config(config_path="configs/config.yaml"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def calculate_metrics(df, epsilon=1e-5):
    # Calculate View-based Engagement Rate
    df["er_view"] = (df["likes"] + df["comments"]) / df["views"]
    # Apply Log Transformation to handle skewness
    df["log_er_view"] = np.log(df["er_view"] + epsilon)
    return df

def run_hypothesis_test(df, alpha=0.05):
    groups = [group["log_er_view"].values for _, group in df.groupby("platform")]
    platform_names = list(df["platform"].unique())

    # One-way ANOVA test (or Kruskal-Wallis)
    f_stat, p_val = stats.f_oneway(*groups)

    # Calculate Eta-squared effect size
    all_data = df["log_er_view"].values
    grand_mean = np.mean(all_data)
    ss_total = np.sum((all_data - grand_mean) ** 2)
    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups)
    eta_sq = ss_between / ss_total if ss_total > 0 else 0.0

    result_summary = {
        "platforms": platform_names,
        "f_statistic": float(f_stat),
        "p_value": float(p_val),
        "eta_squared": float(eta_sq),
        "hypothesis_rejected": bool(p_val < alpha)
    }
    return result_summary

def main():
    print("=" * 60)
    print("HYPERGAMY ENGAGEMENT BENCHMARK PIPELINE EXECUTION")
    print("=" * 60)

    config = load_config()
    sample_path = config["paths"]["sample_data"]
    log_path = config["paths"]["log_output"]
    alpha = config["experiment"]["alpha"]
    epsilon = config["data_processing"]["epsilon"]

    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    print(f"[*] Loading sample data from: {sample_path}")
    df = pd.read_csv(sample_path)
    print(f"[+] Loaded {len(df)} sample rows across platforms: {df['platform'].unique().tolist()}")

    print("[*] Computing Engagement Rates and Log Transformations...")
    df = calculate_metrics(df, epsilon=epsilon)

    print("[*] Running Welch's / One-Way ANOVA Statistical Hypothesis Test...")
    res = run_hypothesis_test(df, alpha=alpha)

    # Prepare Log Output
    log_lines = []
    log_lines.append("=== BENCHMARK EXPERIMENT LOG ===")
    log_lines.append(f"Experiment Name: {config['experiment']['name']}")
    log_lines.append(f"Sample Records Processed: {len(df)}")
    log_lines.append(f"Alpha Significance Threshold: {alpha}")
    log_lines.append("-" * 40)
    log_lines.append("PLATFORM MEAN LOG(ER_VIEW):")
    for platform, group in df.groupby("platform"):
        mean_val = group["log_er_view"].mean()
        log_lines.append(f"  - {platform}: {mean_val:.4f}")
    log_lines.append("-" * 40)
    log_lines.append(f"F-Statistic: {res['f_statistic']:.4f}")
    log_lines.append(f"p-Value: {res['p_value']:.4f}")
    log_lines.append(f"Eta-Squared (Effect Size): {res['eta_squared']:.4f}")
    log_lines.append(f"H0 Rejected (p < alpha): {res['hypothesis_rejected']}")
    log_lines.append("================================")

    log_content = "\n".join(log_lines)
    print(log_content)

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(log_content + "\n")

    print(f"[+] Results successfully recorded to: {log_path}")
    print("[✓] Pipeline execution finished successfully.")

if __name__ == "__main__":
    main()