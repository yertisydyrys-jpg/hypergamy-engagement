# Domain Model — ML/AI Track (TASK 3, Week 9)

**Project:** Algorithmic Amplification of Gender Discourses: Cross-Platform
Comparative Analysis of Hypergamy Content
**Author:** Yertis Ydyrys · **Repository:** `hypergamy-engagement`

This document formalizes the machine-learning components of the study:
(1) the narrative-classification model (RQ1), (2) the engagement metric that
serves as the quantitative core (RQ2), and (3) the system components where
metrics are collected.

---

## 1. Narrative Classification Model (RQ1)

A fine-tuned **RoBERTa** encoder produces per-class probabilities for narrative
labels $c \in \mathcal{C}$ (e.g., *status anxiety*, *partner-market complaint*,
*neutral relationship advice*).

### 1.1 Loss function

Cross-entropy with $L_2$ weight decay:

$$
\mathcal{L}(\theta)
= \underbrace{-\frac{1}{N}\sum_{i=1}^{N}\sum_{c=1}^{C} y_{ic}\,\log p_{ic}}_{\text{cross-entropy}}
+ \underbrace{\lambda \lVert \theta \rVert_2^2}_{\text{weight decay}}
$$

### 1.2 Target metrics

$$
\text{Accuracy} = \frac{1}{N}\sum_{i=1}^{N}\mathbb{1}\big[\hat{y}_i = y_i\big],
\qquad
F_1 = \frac{2\,\text{Precision}\,\text{Recall}}{\text{Precision}+\text{Recall}}
$$

**Acceptance threshold:** Cohen's $\kappa \geq 0.70$ against human annotation
(inter-coder reliability guardrail).

---

## 2. Engagement Metric (RQ2 — quantitative core)

View-based engagement rate and its variance-stabilizing log transform:

$$
\text{ER}_{\text{view}} = \frac{\text{likes} + \text{comments}}{\text{views}},
\qquad
\log(\text{ER}) = \log\big(\text{ER}_{\text{view}} + \varepsilon\big),
\quad \varepsilon = 10^{-5}
$$

Hypothesis test (one-way ANOVA / Welch's) on $\log(\text{ER})$ across platforms
with effect size $\eta^2$; $\alpha = 0.05$.

---

## 3. Pipeline Performance Metrics (TASK 3 benchmark)

Each collection-pipeline run $r$ is logged with wall-clock latency
$\ell_r$ (ms), throughput $t_r$ (videos/s) and an error indicator $e_r \in \{0,1\}$.

**Aggregates (per method × platform group $g$):**

$$
\bar{\ell}_g = \frac{1}{|g|}\sum_{r \in g}\ell_r,
\qquad
\text{CI}_{95}(\bar{\ell}_g)\ \text{via percentile bootstrap (10{,}000 resamples, seed 42)}
$$

$$
p95_g = Q_{0.95}(\{\ell_r\}),\quad p99_g = Q_{0.99}(\{\ell_r\}),\quad
\text{error rate}_g = \frac{1}{|g|}\sum_{r \in g} e_r
$$

**Guardrail:** $\text{error rate}_g < 0.05$ for every group $g$.

---

## 4. Mathematical Notation Table

| Symbol | Type | Description |
| :--- | :--- | :--- |
| $N$ | int | Number of labeled training examples |
| $C$ | $|\mathcal{C}|$ | Number of narrative classes |
| $y_{ic} \in \{0,1\}$ | binary | One-hot label: example $i$ belongs to class $c$ |
| $p_{ic} \in [0,1]$ | probability | Model-predicted probability of class $c$ for example $i$ |
| $\theta$ | vector | All trainable model parameters |
| $\lambda$ | scalar | $L_2$ regularization coefficient |
| $\mathbb{1}[\cdot]$ | indicator | 1 if the condition holds, 0 otherwise |
| $\varepsilon$ | scalar | Log-transform smoothing constant, $10^{-5}$ |
| $\ell_r$ | ms | Wall-clock latency of pipeline run $r$ |
| $t_r$ | videos/s | Throughput of pipeline run $r$ |
| $e_r \in \{0,1\}$ | binary | Failure indicator of run $r$ (guardrail) |
| $Q_q(\cdot)$ | quantile | $q$-th quantile of the empirical distribution |
| $\eta^2$ | $[0,1]$ | Eta-squared effect size of the platform factor |
| $\alpha$ | scalar | Significance level, $0.05$ |

---

## 5. Metric Collection Points (component level)

```mermaid
flowchart LR
    subgraph Pipeline["Collection Pipeline"]
        A[API Client<br/>TikTok / Meta / YouTube] --> B[Batch Collector]
        B --> C[Engagement Aggregator<br/>ER_view, log(ER)]
        B -. "logs: latency_ms, throughput, error<br/>(run_id, phase=warmup|eval)" .-> M[(test_run.jsonl)]
    end
    M --> D[process_data.py<br/>warm-up filter + bootstrap CI]
    D --> E[(metrics_summary.csv)]
    E --> F[visualize.py → reports/figures]
    C --> G[ANOVA on log(ER)]
```

*Warm-up runs (cold start) are tagged at the API Client / Batch Collector
boundary and discarded by `filter_warmup()` before aggregation.*
