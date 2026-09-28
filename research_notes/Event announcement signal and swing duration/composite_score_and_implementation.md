# Composite Event Signal Score and Swing Duration Estimate — Implementation Research

## What are concrete composite scoring formulas used in practice (weighted z-score combination, ML probability models, magnitude/confidence ensembles)?

### Takeaway
Practitioners combine heterogeneous factors either (1) via classical credit-scoring-style pipelines — Weight-of-Evidence (WOE) transform of each factor, logistic regression on the WOE-transformed variables, then a linear points scorecard — or (2) via a simple z-score-average across factors (used in quant multi-factor ranking, e.g. Quantpedia-style composite scores), or (3) via a supervised ML classifier (gradient-boosted trees / logistic regression) trained to output a calibrated probability-of-success, often in a "meta-labeling" architecture where a primary model sets direction and a secondary probability model gates/sizes the trade. All three are implementable in Python with mainstream libraries (scikit-learn, statsmodels) and none require exotic tooling.

### Cited Findings
- Weight of Evidence: `WOE = ln(% of non-events / % of events)` computed per bin/category of a factor, where "non-events"/"events" are the two outcome classes (e.g., successful vs. failed reaction) — [ListenData: WOE and IV Explained](https://www.listendata.com/2015/03/weight-of-evidence-woe-and-information.html)
- Information Value per factor: `IV = Σ (% non-events − % events) × WOE`, summed across bins, used to rank which factors are most predictive before inclusion in the composite — [ListenData: WOE and IV Explained](https://www.listendata.com/2015/03/weight-of-evidence-woe-and-information.html)
- After WOE-transforming each factor, a logistic regression is fit: `log(odds) = β0 + β1·WOE1 + β2·WOE2 + ...`; the fitted coefficients are then multiplied by each factor's WOE value to produce "score points" per factor, and an applicant's (or here, an event's) total score is a linear sum of those points, proportional to the log of predicted good/bad odds — [ListenData](https://www.listendata.com/2015/03/weight-of-evidence-woe-and-information.html); [Medium: Understanding Credit Risk Scorecards WOE](https://medium.com/@makhija.amit/understanding-credit-risk-scorecards-the-role-of-weight-of-evidence-woe-6362e7bc1a4b)
- When a scorecard is built from multiple weighted factors (e.g., three factors F1/F2/F3 weighted 50%/30%/20%) and one factor is inapplicable for a given case, the standard fix is to renormalize: sum the scores of applicable factors and divide by the sum of their applicable weights, rather than dropping the case — [ListenData: WOE and IV Explained](https://www.listendata.com/2015/03/weight-of-evidence-woe-and-information.html)
- Quant multi-factor composite scoring pattern (Quantpedia): individual predictors (factors) are each cross-sectionally ranked over a lookback window (e.g., 20 days); for "MIN"-type effects, values are multiplied by −1 before ranking so the desired direction always maps to the highest rank; per-item ranks across all factors are then combined into one composite score, and items are sorted into quintiles by that composite score for portfolio construction — [Quantpedia: Community Alpha of QuantConnect Part 4](https://quantpedia.com/community-alpha-of-quantconnect-part-4-composite-social-trading-multi-factor-strategy/)
- Z-score-based composite: compute a rolling mean/std for each factor over a lookback window, standardize each factor into a z-score, and average the z-scores across all selected factors to get one composite z-score representing overall strength — [Medium: Z-Score Normalized Linear Signal Quantitative Trading Strategy](https://medium.com/@redsword_23261/z-score-normalized-linear-signal-quantitative-trading-strategy-a3a3b073c0cc); [Quantra glossary: z-score](https://quantra.quantinsti.com/glossary/zscore)
- Weighted multi-indicator systems (technical-analysis composite scores): each factor across categories (trend, momentum, volatility, volume, levels) contributes a signed sub-score (bullish/bearish/neutral), and these sub-scores are combined (weighted sum) into one total composite score — [WebSearch synthesis citing z-score/composite-score trading literature](https://medium.com/@redsword_23261/z-score-normalized-linear-signal-quantitative-trading-strategy-a3a3b073c0cc)
- Meta-labeling (López de Prado, "Advances in Financial Machine Learning"): a primary model outputs the trade side/direction; a secondary ("meta") model — commonly a gradient-boosted-tree or logistic-regression classifier — predicts the probability that the primary model's call will be correct; that probability is then used to size or gate the bet (only act when probability exceeds a threshold; scale size with probability). This is a two-stage decomposition of "is there a signal" (direction) vs. "how confident/how big" (magnitude/confidence) — [Hudson & Thames: Meta-Labeling (A Toy Example)](https://hudsonthames.org/meta-labeling-a-toy-example/); [Wikipedia: Meta-Labeling](https://en.wikipedia.org/wiki/Meta-Labeling); [Mlfinpy docs: Data Labelling](https://mlfinpy.readthedocs.io/en/latest/Labelling.html)
- Practical gradient-boosting implementation pattern for trading signal filtering: fit a boosted classifier on labeled outcomes (e.g., next-N-bar percent change sign), then fire a high-confidence alert only when the model's predicted P(favorable outcome) exceeds a chosen probability threshold — used as a signal-filtering / confidence gate, structurally identical to a "confidence score" output — [Medium: ML for Algorithm Trading Part 12 — Gradient Boosting](https://medium.com/@conniezhou678/machine-learning-for-algorithm-trading-part-12-boosting-your-trading-strategy-why-gradient-2d185b57e8f0)
- Cascading architecture combining logistic regression with gradient-boosted decision trees has been studied specifically for forecasting and trading stock indices, i.e., stacking a simple probability model's output as a feature into a GBDT for a refined composite signal — [ScienceDirect: Cascading logistic regression onto GBDT for forecasting and trading stock indices](https://www.sciencedirect.com/science/article/abs/pii/S1568494619305289)

### Inferences
- A robust, explainable design for this tool would mirror the credit-scorecard pattern exactly: (1) discretize/bucket each raw factor (event-type base rate, deal-size ratio, CAR z-score, sentiment score, volume-spike z-score, sector-momentum) if using WOE, or just z-score-normalize each continuously; (2) fit either a logistic regression (if enough labeled historical events exist) or use a simple weighted-sum of z-scores (if not); (3) express the output both as a 0–100 "points" scorecard (easy for humans to read) and as a probability via the logistic link, `p = 1 / (1 + exp(-(β0 + Σβi·zi)))`.
- A two-number output ("magnitude score" + "confidence score") maps naturally onto meta-labeling: a primary/base-rate-driven magnitude estimate (expected CAR conditional on event type) and a secondary ML-derived confidence/probability that this particular instance will realize that magnitude — directly satisfying the "ensemble of magnitude score and confidence score" question.
- Where historical labeled samples are sparse per event-type (a very likely situation for niche corporate-event categories), the WOE/logistic route is safer starting point than GBDT, since GBDT needs more data to avoid overfitting; a simple weighted z-score sum with hand-set or Bayesian-updated weights (see Bayesian section below) is the most defensible baseline until sample sizes grow.

### Gaps
- No single canonical, publicly documented "composite event signal score" formula specific to *event-driven equity trading* (e.g., M&A, earnings, buybacks) was found in the literature searched; the frameworks above are adapted from adjacent domains (credit scoring, generic multi-factor quant investing, meta-labeling for technical/ML strategies) rather than a purpose-built event-driven scoring paper.
- Could not access the Springer paper "Trading Signal Survival Analysis: A Framework for Enhancing Technical Analysis Strategies in Stock Markets" (Computational Economics, 2024) — it sits behind a login wall (`idp.springer.com` redirect) — which appeared highly relevant (title suggests exactly a survival-analysis + trading-signal composite framework) but could not be retrieved as full text within this research pass.

---

## How can heterogeneous factors (event-type base rate, deal size ratio, historical CAR z-score, sentiment, volume-spike z-score, sector momentum) be combined into one normalized score robustly and explainably?

### Takeaway
The two dominant, implementable, explainable patterns are (1) **z-score normalize every factor, then take a (possibly weighted) linear combination / average** — the standard quant multi-factor approach — and (2) **WOE-transform + logistic regression + points scorecard** — the standard credit-risk approach, which additionally yields a calibrated probability and naturally handles missing/inapplicable factors via weight renormalization.

### Cited Findings
- Standard z-score normalization for factor combination: for each factor, compute rolling/window mean and standard deviation, then `z = (x − mean) / std`; combine multiple factor z-scores by (weighted) averaging into one composite z-score — [Medium: Z-Score Normalized Linear Signal Quantitative Trading Strategy](https://medium.com/@redsword_23261/z-score-normalized-linear-signal-quantitative-trading-strategy-a3a3b073c0cc)
- Z-score thresholds and factor weights for a composite screen are typically set via backtesting and correlation analysis among the candidate factors (to avoid double-counting correlated signals) rather than fixed a priori — [WebSearch synthesis, Quantra/Kotak Neo z-score trading sources](https://quantra.quantinsti.com/glossary/zscore)
- Missing/inapplicable-factor handling in a weighted scorecard: renormalize by dividing the sum of applicable-factor scores by the sum of applicable weights (e.g., if a 20%-weighted factor is missing, divide the remaining 80%-weighted sum by 0.8) — [ListenData: WOE and IV Explained](https://www.listendata.com/2015/03/weight-of-evidence-woe-and-information.html)
- Cross-sectional ranking as an alternative to z-scoring: rank each item by each factor over a lookback window (flipping sign for "lower is better" factors), and combine per-factor ranks into a single composite rank/score, avoiding sensitivity to outliers that raw z-scores have — [Quantpedia: Community Alpha Part 4](https://quantpedia.com/community-alpha-of-quantconnect-part-4-composite-social-trading-multi-factor-strategy/)
- Weight-of-Evidence transform is specifically designed to convert heterogeneous variable types (categorical event-type, continuous ratios, continuous z-scores) onto the *same log-odds scale* before combination, which directly solves the "heterogeneous factor" normalization problem described in the key question — [ListenData: WOE and IV Explained](https://www.listendata.com/2015/03/weight-of-evidence-woe-and-information.html)

### Inferences
- For the six named factors (event-type base rate, deal-size ratio, CAR z-score, sentiment score, volume-spike z-score, sector momentum), a practical hybrid is: keep already-continuous/normally-distributed factors (CAR z-score, volume-spike z-score) as raw z-scores; bucket the more categorical/skewed factors (event-type, deal-size ratio, sentiment bucket) via WOE bins; then combine everything through one logistic regression (or, absent enough data, a hand-weighted sum) so all factors sit on a common log-odds/points scale.
- Explainability is best served by keeping the point-scorecard output (integer points per factor, summed to a total, mapped to a probability) as the primary user-facing artifact, with the underlying weighted z-score or GBDT model as the engine that determines the weights, following standard scorecard-development practice.

### Gaps
- No source specifically discusses combining a "sector momentum" factor with idiosyncratic-event factors (like deal-size ratio) in one scorecard; general multi-factor equity literature (momentum, value, quality composites) was found, but not a source that treats event-driven idiosyncratic factors and market-wide momentum factors together in the same composite framework.

---

## What Python libraries are commonly used for event-study abnormal returns, survival/duration modeling, and Bayesian updating?

### Takeaway
`eventstudy` (PyPI package by Jean-Baptiste Lemaire) and the R-origin `eventstudies`/`EventStudyTools` are the standard tools for AR/CAR computation via market-model OLS regression; `lifelines` is the standard Python survival-analysis library (Kaplan-Meier, CoxPHFitter, WeibullFitter, WeibullAFTFitter) and is directly reusable for "days until reversion" duration modeling; `PyMC` is the standard library for Bayesian updating, though simple conjugate-prior (Beta-Binomial) updates don't need a library at all — they're closed-form.

### Cited Findings
- **`eventstudy` (Python, PyPI)**: install via `pip install eventstudy`; computes Abnormal Returns (AR) and Cumulative Abnormal Returns (CAR) for single events, and Average Abnormal Returns (AAR) / Cumulative Average Abnormal Returns (CAAR) across aggregates of events, with built-in significance testing — [eventstudy package docs (PDF)](https://lemairejean-baptiste.github.io/eventstudy/eventstudy.pdf); [GitHub: LemaireJean-Baptiste/eventstudy](https://github.com/LemaireJean-Baptiste/eventstudy)
- Market Model (MM) methodology underlying these AR/CAR computations assumes a linear relationship between a security's returns and a market/benchmark index's returns (estimated typically via OLS over an estimation window prior to the event); abnormal return = actual return − model-predicted ("normal") return, and CAR is the running sum of ARs across the event window — [K. Riehl: Introduction into Event Study Analysis](https://medium.com/@riehlk/a-short-introduction-into-event-study-analysis-including-python-code-example-bd56b5f4c1ac); [EventStudyTools: Event Study Methodology](https://www.eventstudytools.com/introduction-event-study-methodology)
- Alternative/related Python event-study tools found: `easy-event-study` (GitHub: Darenar/easy-event-study — automatically loads return time series per ticker, loads estimation-model factors, and estimates abnormal returns per event); a Terence Lim financial-data-science notebook implementing event study directly with pandas/statsmodels — [GitHub: Darenar/easy-event-study](https://github.com/Darenar/easy-event-study); [Terence Lim: Event Study notebook](https://terence-lim.github.io/docs/financial-data-science-notebooks/1.7_event_study.html)
- **`lifelines`** (Python survival analysis library, by Cameron Davidson-Pilon): provides `KaplanMeierFitter` (non-parametric survival curve), `CoxPHFitter` (semi-parametric proportional-hazards regression), `WeibullFitter` (univariate parametric), and `WeibullAFTFitter` (parametric accelerated-failure-time regression) — [lifelines WeibullAFTFitter docs](https://lifelines.readthedocs.io/en/latest/fitters/regression/WeibullAFTFitter.html); [lifelines WeibullFitter docs](https://lifelines.readthedocs.io/en/latest/fitters/univariate/WeibullFitter.html); [lifelines GitHub source: weibull_aft_fitter.py](https://github.com/CamDavidsonPilon/lifelines/blob/master/lifelines/fitters/weibull_aft_fitter.py)
- **`PyMC`**: used for Bayesian updating and also ships a Weibull AFT reparameterization example in its official example gallery, directly demonstrating Bayesian time-to-event modeling — [PyMC example gallery: Reparameterizing the Weibull AFT Model](https://www.pymc.io/projects/examples/en/latest/survival_analysis/weibull_aft.html); [PyMC example gallery: Updating Priors](https://www.pymc.io/projects/examples/en/latest/howto/updating_priors.html)
- Simple conjugate Bayesian updating (Beta-Binomial) needs no sampling library — it is closed-form: `Prior: p ~ Beta(α0, β0)`, `Likelihood: x | p ~ Binomial(n, p)`, `Posterior: p | x ~ Beta(α0 + x, β0 + n − x)`; posterior mean `= (α0 + x) / (α0 + β0 + n)`, i.e. a weighted average of the prior mean and the observed sample proportion, with the prior's effective weight equal to `(α0+β0)/(α0+β0+n)` — [MetricGate: Bayesian Binomial Update with Beta Prior](https://metricgate.com/docs/bayesian-binomial-beta-update/)

### Inferences
- For this tool's per-event-type historical distributions, the Beta-Binomial closed-form update (no PyMC dependency needed) is sufficient for updating a "probability of directional success" per event type incrementally as new events resolve; PyMC/MCMC is only needed if the model becomes hierarchical (e.g., partial pooling across many event sub-types) or non-conjugate.
- For duration modeling, `WeibullAFTFitter` is the most directly reusable component: it lets you regress the *scale* (median/typical duration) and optionally the *shape* (how sharply hazard changes over time) of the "time until reversion" distribution on covariates (event type, deal size, sentiment, etc.), producing both a point estimate (`predict_expectation`, `predict_median`, i.e. `predict_percentile(df, p=0.5)`) and a full decay/survival curve per event — precisely the "duration/holding-period estimate + decay curve" output requested.

### Gaps
- Could not fetch the `eventstudy` package's GitHub README/API reference directly (GitHub landing page didn't expose method-level docs in the fetch, and the linked PDF documentation returned as unparseable binary/stream content) — exact class/method names (e.g. whether it is `EventStudy.from_csv(...)`, `.market_model(...)`) should be verified directly against `https://lemairejean-baptiste.github.io/eventstudy/` or the package's readthedocs before implementation.
- `EventStudyTools` (the separate commercial/web tool referenced in search results) does not appear to have its own Python package — it is a paid web-based service; the R package `eventstudies` (on CRAN) is a distinct, R-only implementation and not directly usable from Python without `rpy2`.

---

## What would a reasonable Python data schema/class design look like for per-event-type historical distributions that update incrementally?

### Takeaway
No single public reference implements this exact schema, but combining the sourced building blocks (WOE/scorecard fields, Beta-Binomial conjugate-update parameters, lifelines' AFT-fitter outputs) yields a directly implementable dataclass design; the report-writer/implementer should treat this as a designed synthesis rather than a found artifact.

### Cited Findings
- Beta-Binomial conjugate updating gives the natural incremental-update state for a "probability of success" per event type: store only `(alpha, beta)` (or equivalently `successes, failures` plus prior pseudo-counts); each new resolved event updates `alpha += 1` (success) or `beta += 1` (failure) in O(1), and posterior mean/credible interval are closed-form at any time — [MetricGate: Bayesian Binomial Update with Beta Prior](https://metricgate.com/docs/bayesian-binomial-beta-update/)
- `WeibullAFTFitter`'s fitted state (`params_`, i.e. estimated β coefficients for the λ/scale part and optionally α coefficients for the ρ/shape part, plus `confidence_intervals_`, `standard_errors_`, `variance_matrix_`) is the natural "per-event-type duration model" artifact if fit per event-type-stratified subset, or as one pooled model with event-type as a covariate — [lifelines WeibullAFTFitter docs](https://lifelines.readthedocs.io/en/latest/fitters/regression/WeibullAFTFitter.html)
- IV (Information Value) per factor, computed from binned WOE data, is the standard metric for tracking "how much has this factor's predictive power been validated by data so far" and could serve as a per-factor confidence/sample-size proxy in an incrementally updating schema — [ListenData: WOE and IV Explained](https://www.listendata.com/2015/03/weight-of-evidence-woe-and-information.html)

### Inferences
- A concrete, implementable schema (synthesized from the above, not found verbatim in any single source) is:

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class EventTypeDistribution:
    event_type: str                    # e.g. "merger_announcement", "earnings_beat"
    n_samples: int = 0                  # count of resolved historical events

    # --- CAR / magnitude distribution (updated via running stats or refit) ---
    median_car: float = 0.0
    car_iqr: float = 0.0                # 75th - 25th percentile of CAR
    car_std: float = 0.0

    # --- Bayesian success-probability state (Beta-Binomial conjugate) ---
    alpha: float = 1.0                  # prior pseudo-successes (start uninformative: 1,1)
    beta: float = 1.0                   # prior pseudo-failures

    # --- Duration state (fit via lifelines WeibullAFTFitter per event-type slice) ---
    median_duration_days: float = None  # aft.predict_median() on a representative row
    weibull_lambda: float = None        # fitted scale param
    weibull_rho: float = None           # fitted shape param

    confidence: float = 0.0             # e.g. derived from n_samples and/or Information Value
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def update_with_new_event(self, car: float, success: bool, duration_days: float):
        # running-stats update for CAR distribution (e.g. Welford's algorithm)
        # Beta-Binomial update:
        if success:
            self.alpha += 1
        else:
            self.beta += 1
        self.n_samples += 1
        self.last_updated = datetime.utcnow()
        # duration/CAR refit is typically batched (e.g. nightly re-fit of WeibullAFTFitter
        # and recompute of median/IQR) rather than done per-event, since AFT/OLS refits
        # are not naturally incremental like the Beta-Binomial update is.

    @property
    def success_probability(self) -> float:
        return self.alpha / (self.alpha + self.beta)
```
- Because `WeibullAFTFitter` and OLS-based market-model regressions are *batch* fits (no native incremental/online update in `lifelines` or `statsmodels`), the realistic "incremental update" design is a hybrid: truly incremental O(1) updates for count-based/conjugate statistics (success probability, running mean/variance), and periodic (e.g. nightly or weekly) batch re-fits for the parametric duration and magnitude models, with the dataclass simply overwriting `weibull_lambda`, `weibull_rho`, `median_car`, etc. after each batch refit.

### Gaps
- No public repository or blog post was found that documents this exact schema for event-driven trading; this section is a design synthesis built from the sourced components above, and should be flagged to the report writer as inferred/designed rather than directly cited.

---

## Are there examples of `lifelines`' Weibull/Cox models used to model "time until a price move reverts," even from adjacent domains?

### Takeaway
No example was found of `lifelines` applied specifically to "time until a price move reverts," but a closely analogous academic application exists — modeling the time until a stock index falls 20% from its peak using Kaplan-Meier, a logit model, and Cox proportional hazards — and `lifelines`' customer-churn tutorials (an adjacent domain) provide directly transferable code patterns (Kaplan-Meier median survival time, Cox `predict_expectation` for expected time-to-event) that map cleanly onto "days until reversion."

### Cited Findings
- Academic paper (Computational and Mathematical Organization Theory / medical-style biostatistics survival methods applied to finance): "A survival analysis in the assessment of the influence of the SARS-CoV-2 pandemic on the probability and intensity of decline in the value of stock indices" defines duration `T` as the time elapsed between an index reaching its maximum value (the "initial event") and the index recording a 20% decrease from that peak (the "final event"); indices not yet down 20% by the end of the observation window (~20% of the sample) are right-censored — [PMC: Survival analysis of stock index decline (SARS-CoV-2)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7968564/)
- Kaplan-Meier estimator as used in that paper: `Ŝ(t_i) = Π_{j=1}^{i} (1 − d_j/n_j)`, where `d_j` = number of indices reaching the 20% decline threshold at time `t_j` and `n_j` = number of indices still "at risk" (not yet declined, not yet censored) at `t_j` — [PMC: Survival analysis of stock index decline](https://pmc.ncbi.nlm.nih.gov/articles/PMC7968564/)
- Logit model for probability of reaching the decline threshold, conditional on covariates: `logit(p) = ln(p/(1−p)) = β0 + Σ βi·Xi`, with odds ratios `OR = exp(βi)` — in the paper, `Xi` are region/continent dummies, but this generalizes directly to event-type/sector dummies — [PMC: Survival analysis of stock index decline](https://pmc.ncbi.nlm.nih.gov/articles/PMC7968564/)
- Cox proportional hazards model for intensity of decline: `h(t, X) = h0(t)·exp(α1·X1 + α2·X2 + ... + αn·Xn)`, with hazard ratios `HR = exp(αi)` quantifying relative speed-to-decline across covariate groups; an empirical hazard estimator `ĥj = d_j / (n_j · τ_j)` (τ_j = length of the j-th time interval) is used to visualize when decline intensity peaks over time — [PMC: Survival analysis of stock index decline](https://pmc.ncbi.nlm.nih.gov/articles/PMC7968564/)
- `lifelines` Kaplan-Meier applied to customer churn (adjacent domain, directly reusable code pattern):
```python
from lifelines import KaplanMeierFitter
kmf = KaplanMeierFitter()
kmf.fit(df['Subscription Length'], event_observed=df['Churn'], label='Customer Churn')
kmf.survival_function_at_times(34)     # survival probability at time 34
median_survival = kmf.median_survival_time_
```
— [Towards Data Science: A Survival Analysis Guide with Python](https://towardsdatascience.com/a-survival-analysis-guide-with-python-using-time-to-event-models-to-forecast-customer-lifetime/)
- `lifelines` `CoxPHFitter` applied to churn, including expected-time-to-event prediction directly analogous to "expected days until move peaks/reverts":
```python
from lifelines import CoxPHFitter
cph = CoxPHFitter(penalizer=0.1)
cph.fit(df_model, duration_col='Subscription Length', event_col='Churn')
pred_survival = cph.predict_survival_function(individual)   # full survival/decay curve
pred_churn = cph.predict_expectation(df_model.iloc[[110,111]])  # expected time to event
```
— [Towards Data Science: A Survival Analysis Guide with Python](https://towardsdatascience.com/a-survival-analysis-guide-with-python-using-time-to-event-models-to-forecast-customer-lifetime/)
- `WeibullAFTFitter` (parametric alternative to Cox, directly modeling the duration distribution rather than just its hazard shape) formula and usage:
```
λ(x) = exp(β0 + β1·x1 + ... + βn·xn)         # scale
ρ(y) = exp(α0 + α1·y1 + ... + αm·ym)         # shape (optional, defaults constant)
S(t; x, y) = exp(-(t/λ(x))^ρ(y))             # survival function
H(t; x, y) = (t/λ(x))^ρ(y)                    # cumulative hazard
```
```python
from lifelines import WeibullAFTFitter
aft = WeibullAFTFitter()
aft.fit(df, duration_col='time', event_col='status')   # covariates = other columns in df
aft.print_summary()
aft.predict_expectation(new_df)             # E[T | covariates] — "expected days to reversion"
aft.predict_percentile(new_df, p=0.5)       # median time to reversion
```
— [lifelines WeibullAFTFitter docs](https://lifelines.readthedocs.io/en/latest/fitters/regression/WeibullAFTFitter.html)
- PyMC also ships an official worked example reparameterizing the Weibull AFT model in a Bayesian framework, useful if a fully Bayesian (as opposed to frequentist/MLE) duration model with credible intervals on "days to reversion" is desired — [PyMC example gallery: Reparameterizing the Weibull AFT Model](https://www.pymc.io/projects/examples/en/latest/survival_analysis/weibull_aft.html)

### Inferences
- The stock-index-decline paper is the closest direct analog found to "time until a price move reverts": swap "20% decline from peak" for "price reverts N% from the post-event extreme," swap "continent" covariates for "event type / sector / deal size," and the Kaplan-Meier + logit + Cox pipeline transfers essentially unchanged. This is a strong, concrete template to cite and adapt.
- For this tool's "swing duration estimate" output specifically, `WeibullAFTFitter.predict_expectation()` / `.predict_percentile(p=0.5)` gives the single-number "expected/median days until move peaks or reverts," while `.predict_survival_function()` (Cox) or the Weibull `S(t;x,y)` formula gives the full decay curve the objective also asks for — both are available from the same fitted model, so one model serves both output types.
- Right-censoring handling (events where the move hasn't reverted yet by the time the model is being asked, i.e. "still open" positions) is a first-class concept in both Kaplan-Meier and Cox/Weibull AFT via the `event_col` (1 = reverted/observed, 0 = censored/still ongoing) — directly solves the practical problem of open/still-running signals in a live trading system, not just closed historical ones.

### Gaps
- No source was found describing a Python implementation specifically for equity price-swing reversion duration (as opposed to the stock-index 20%-decline paper, which is close but not identical, and not itself in Python — it appears to use standard biostatistics software, not `lifelines`, though the formulas transfer directly).
- Could not access the Springer 2024 "Trading Signal Survival Analysis" paper (login-gated) which by title appears to be the single most directly relevant academic source for this exact question; flagging for the report writer in case a different access route (e.g., library proxy, Google Scholar cached version, or arXiv preprint) is available outside this research session.
