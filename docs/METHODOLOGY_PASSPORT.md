# Methodology Passport Card

## 1. Project Information
* **Project Title:** Algorithmic Amplification of Gender and Relationship Discourses: A Cross-Platform Comparative Analysis of Hypergamy Content on TikTok, Instagram Reels, and YouTube
* **Author:** Yertis Ydyrys
* **Repository Link:** [https://github.com/yertisydyrys-jpg/hypergamy-engagement.git](https://github.com/yertisydyrys-jpg/hypergamy-engagement.git)
* **Academic Context:** Data Science / Computational Social Science (Year 2026)

---

## 2. Study Type
**Mixed-Methods Design with a Quantitative Core**
* **Rationale:**
    * **Quantitative Core (RQ2):** Evaluating cross-platform engagement rate differences ($\text{ER}$) across recommendation architectures (TikTok vs. Instagram Reels vs. YouTube) requires rigorous statistical testing (Welch's ANOVA / Kruskal-Wallis with Dunn-Bonferroni post-hoc tests and regression modeling).
    * **Qualitative/NLP Module (RQ1):** Identifying narrative patterns, status anxiety cues, and audio-visual triggers requires qualitative thematic coding and fine-tuned Transformer-based classification (RoBERTa), the outputs of which serve as qualitative covariates in the quantitative model.

---

## 3. Hypotheses and Operationalization

### Null Hypothesis ($H_0$)
The mean log-transformed engagement rate ($\log(\text{ER})$) for hypergamy-related content is equal across TikTok, Instagram Reels, and YouTube Long-form formats.
$$\mu_{\log(\text{ER}_{\text{TikTok}})} = \mu_{\log(\text{ER}_{\text{Reels}})} = \mu_{\log(\text{ER}_{\text{YouTube\_Long}})}$$

### Alternative Hypothesis ($H_1$)
Short-form algorithmic feeds featuring high recommendation density (TikTok and Instagram Reels) exhibit a statistically significantly higher mean log-transformed engagement rate ($\log(\text{ER})$) for hypergamy discourse compared to YouTube Long-form content.
$$\mu_{\log(\text{ER}_{\text{Short\_Form}})} > \mu_{\log(\text{ER}_{\text{YouTube\_Long}})}$$

* **Statistical Parameters:** Significance level $\alpha = 0.05$; Effect size reported as Eta-squared ($\eta^2$) or Cohen’s $d$.
* **Transformation:** Due to severe positive skewness in raw social media engagement metrics, dependent variables are log-transformed: $\log(\text{ER} + 10^{-5})$.
* **Operationalization of "Polarizing Content":** Posts exceeding a comment-to-like threshold ratio $> 0.15$ or scoring $> 0.70$ toxicity/controversy on fine-tuned sentiment classifiers.

---

## 4. Variable Matrix

| Variable Group | Variable Name | Description & Scale | Operational Formula / Source |
| :--- | :--- | :--- | :--- |
| **Independent Variable** | Platform Format | Categorical (TikTok, Instagram Reels, YouTube Long-form) | Metadata tags from API extraction |
| **Dependent Variable** | View-based Engagement Rate ($\text{ER}_{\text{view}}$) | Continuous ratio, log-transformed ($\log(\text{ER})$) | $\text{ER}_{\text{view}} = \frac{\text{Likes} + \text{Comments}}{\text{Views}}$ |
| **Controlled Variables** | Search Keywords / Hashtags | Filtered set (#hypergamy, #relationshipadvice) | NARROW keywords excluding broad terms like #levelup |
| | Sampling Period | Fixed temporal window (Jan–Sep 2026) | Uniform temporal normalization |
| | Language | English language posts only | NLP language identification filter |
| | Video Duration | Continuous (seconds) | Meta covariate in regression models |
| | Author Follower Count | Continuous integer | Log-transformed covariate ($\log(\text{Followers})$) |
| | Content Category | Binary (Hypergamy Discourse vs. Neutral Relationship Control) | Topic classification model |

---

## 5. Metrics, Baselines, and Guardrails

### Primary Metric
* **Log-Transformed View-Based Engagement Rate ($\log(\text{ER}_{\text{view}})$):** Standardized metric ensuring cross-platform comparability despite varying public metadata availability.

### Guardrail Metrics (Safety & Data Quality)
1. **Missing Data Threshold:** Data completeness must exceed $95\%$ across required fields ($\text{Views}$, $\text{Likes}$, $\text{Comments}$).
2. **Bot & Spam Comment Ratio:** Automated filtering discarding samples where $>10\%$ of comments are duplicate spam or bot-generated.
3. **Inter-Coder Reliability:** Qualitative narrative annotation must achieve Cohen’s $\kappa \ge 0.70$.
4. **Platform ToS & Rate Limit Compliance:** Strict execution via Official/Research APIs (YouTube Data API v3, Meta Content Library, TikTok Research API) adhering to query rate limits and zero web-scraping policy violations.

### Baseline & Control Groups
* **Platform Baseline:** YouTube Long-form content serves as the benchmark reference category ($0$-level baseline) in comparative regression models.
* **Topic Baseline (Neutral Control):** A matched sample of non-hypergamy, neutral relationship advice content from the same creator pool to isolate the platform architecture effect from topic-specific virality.
* **NLP Classification Baseline:** Rule-based keyword matching and Majority Class Classifier as baselines against fine-tuned RoBERTa models.

---

## 6. Real Peer-Reviewed Literature (Related Work)
1. **Ging, D. (2019).** *Alphas, Betas, and Incels: Theorizing the Male Red Pill Online.* **Feminist Media Studies**, 19(5), 638-657.
2. **Ribeiro, M. H., et al. (2020).** *From Far-Right to Red Pill: Algorithmic Pathways in YouTube.* **ACM Conference on Fairness, Accountability, and Transparency (FAT\*)**, 131-141.
3. **Mountford, J., et al. (2023).** *Algorithmic amplification of gender discourse on short-form video platforms.* **New Media & Society**, 25(8), 2100–2122.
4. **Bandy, N. (2021).** *Problematic Machine Behavior: A Review of Algorithmic Amplification Research.* **Information, Communication & Society**, 24(6), 785-802.