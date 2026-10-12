# Algorithmic Amplification of Gender Discourses: Hypergamy Engagement Benchmark

![Python Version](https://img.shields.io/badge/python-3.11.9-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Docker Ready](https://img.shields.io/badge/Docker-Ready-brightgreen.svg)

## Title & Project Overview
* **Repository Name:** `hypergamy-engagement`
* **Author:** Yertis Ydyrys
* **GitHub Link:** [https://github.com/yertisydyrys-jpg/hypergamy-engagement.git](https://github.com/yertisydyrys-jpg/hypergamy-engagement.git)

This research project presents an automated empirical pipeline designed to evaluate algorithmic amplification and user engagement dynamics ($\text{ER}$) across major social media platforms (**TikTok**, **Instagram Reels**, and **YouTube Long-form**). Focusing on gender and relationship discourses in 2026, the pipeline measures statistically significant differences in user engagement using standardized log-transformed metrics.

---

## Research Question (RQ)
* **RQ1 (Qualitative/NLP):** What dominant narrative triggers and sentiment patterns characterize viral hypergamy content?
* **RQ2 (Quantitative Core):** How do recommendation feed architectures (short-form algorithmic feeds vs. long-form content) influence user engagement rate ($\log(\text{ER})$) for hypergamy discourse?

---

## Planned Benchmark Metrics

| Metric | Type | Target Threshold / Target Range | Purpose |
| :--- | :--- | :--- | :--- |
| $\log(\text{ER}_{\text{view}})$ | Primary | Continuous $[-\infty, 0]$ | Core statistical metric for cross-platform comparison |
| Welch's $F$-Statistic | Statistical | $p < 0.05$ ($\alpha = 0.05$) | Test hypothesis $H_1$ vs. $H_0$ |
| Eta-squared ($\eta^2$) | Effect Size | $> 0.06$ (Medium effect) | Quantify practical significance |
| Data Completeness | Guardrail | $\ge 95\%$ valid records | Prevent data distortion |
| Cohen's $\kappa$ | Guardrail | $\ge 0.70$ inter-rater reliability | Human annotation validity |

---

## Repository Structure

```text
hypergamy-engagement/
├── README.md              # Project overview and quickstart
├── LICENSE                # MIT License
├── .gitignore             # Git exclusion rules
├── Dockerfile             # Reproducible Docker container config
├── requirements.txt       # Strictly pinned dependencies
├── configs/
│   └── config.yaml        # Experiment parameters
├── data/
│   └── sample/
│       └── sample.csv     # Micro test dataset (10 rows)
├── src/
│   └── main.py            # Executable benchmark script
├── docs/
│   └── METHODOLOGY_PASSPORT.md # Methodology card
└── results/
    └── log.txt            # Generated output log