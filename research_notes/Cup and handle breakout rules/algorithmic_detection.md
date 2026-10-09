# Algorithmic Detection of Cup-and-Handle Patterns from Daily OHLCV

Scope: concrete, deterministic, rule-based detection methods (steps + parameters), roundness metrics, boundary definition, breakout detection, look-ahead handling, open-source references, and pitfalls. Target: a plain-English spec an LLM can translate into pandas/numpy/scipy, for a day-by-day backtester with ~400 daily bars per stock, which already has 7-bar fractal swing lows and `argrelextrema(order=4)`.

## 1. Published / open-source step-by-step algorithms and their parameters

### Takeaway
Nearly every published or open-source detector follows the same skeleton: (a) smooth or pivot-filter the price, (b) find alternating local extrema, (c) label a sequence of extrema as K (start of the prior advance) → A (left rim) → B (cup low) → C (right rim) → D (handle low), and (d) accept the sequence only if price ratios, segment lengths and volume conditions pass. The best-documented smoothing method is Lo, Mamaysky & Wang's (2000) kernel regression with bandwidth 0.3 × the cross-validated bandwidth, though LMW did not define a cup-and-handle themselves. The K-A-B-C-D rule sets (TASC 1998/99 lineage, the canslimTechnical repo) supply concrete numbers.

### Cited Findings

**A. Lo, Mamaysky & Wang (2000), "Foundations of Technical Analysis" (J. Finance 55(4)): the general framework**
- Three-step algorithm: (1) define each pattern by its geometry (sequence of local max/min); (2) build a kernel estimator of the price series so its extrema can be found numerically; (3) scan the kernel estimator's extrema for each pattern — [MIT summary page](https://web.mit.edu/Alo/www/Papers/techanal.html); [UPenn copy of paper](https://www.cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf)
- Smoother: Nadaraya–Watson kernel regression. Bandwidth h* is first chosen by leave-one-out cross-validation. LMW found CV bandwidths "too smooth" when they showed the fits to professional technical analysts, so they use **0.3 × h***. They call this ad hoc, and say it was fixed before the statistical analysis and never revised — [paper text, Sec. I.C and fn. 5](https://www.cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf)
- Rolling windows: a separate kernel regression is fit to each window of **l + d = 38 trading days (l = 35, d = 3)**. The window focuses detection on patterns completed within it. LMW say fitting one regression to the whole series makes signal and noise "virtually impossible" to tell apart — [paper, Sec. I.D](https://www.cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf)
- Extrema: a local extremum of the smoothed curve m̂ is a time t where sign(m̂′(t)) ≠ sign(m̂′(t+1)) (+ to − = max, − to + = min). The actual extremum is then taken from the **original price series within [t−1, t+1]**, and the original prices are used for the pattern tests. Flat stretches (m̂′ = 0) are handled by comparing against the next nonzero-derivative date. Extrema found this way always alternate max/min — [paper](https://www.cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf)
- Why smooth: raw 3-bar extrema (P[t−1] < P[t] > P[t+1]) "identifies too many extrema" and yields patterns "not visually consistent" with what technicians find compelling — [paper](https://www.cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf)
- Numeric tolerances in LMW pattern definitions: matching extrema must be within **1.5% of their average** (HS/IHS shoulders and troughs; double-top tops). Double tops/bottoms must be **at least 22 trading days apart** (following Edwards & Magee) — [paper, Sec. II.A](https://www.cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf)
- LMW detect patterns from the last five extrema E1..E5 of the smoothed series in a 38-day window — [MPRA paper 60825 (secondary description)](https://mpra.ub.uni-muenchen.de/60825/1/MPRA_paper_60825.pdf)

**B. K-A-B-C-D rule set: canslimTechnical (R, GitHub, ~61 stars, 12 commits)**
- Uses kernel regression with **bandwidth = 3** (in bars) to smooth, then labels extrema K, A, B, C, D — [README](https://github.com/kanwalpreet18/canslimTechnical/blob/master/README.md)
- K→A (prior advance): A ≥ 1.15 × K (the README also says "≥30", apparently a 30% gain in O'Neil's sense; ambiguous). Up-reversal/down-reversal count ratio > 1 — [README](https://github.com/kanwalpreet18/canslimTechnical/blob/master/README.md)
- A→B (left side of cup): B between **0.65 × A and 0.85 × A** (a 15–35% depth). Volume below its moving average. Duration **20–60 days** — [README](https://github.com/kanwalpreet18/canslimTechnical/blob/master/README.md)
- B→C (right side): **C > 0.6·A + 0.4·B** (i.e. recovers above 60% of the cup's height) **and C ≤ A**. Up/down reversals > 1. Duration **3–30 days** — [README](https://github.com/kanwalpreet18/canslimTechnical/blob/master/README.md)
- C→D (handle): D ≤ C. Up/down reversals > 1. Duration **3–20 days** — [README](https://github.com/kanwalpreet18/canslimTechnical/blob/master/README.md)
- Two code variants: `kernelPattern_brute.R` (brute-force search over point combinations) and `kernelPattern_minMax.R` (uses the min/max extrema of the smoothed curve) — [repo](https://github.com/kanwalpreet18/canslimTechnical)

**C. TASC Traders' Tips, Jan 1999 (cup-with-handle implementations in several platforms)**
- TechniFilter Plus version uses the same five points K, A, B, C, D, with constraints: **D > 0.8·C + 0.2·B** (handle low stays in the top 20% of the C–B range); A at least **20 bars** before B; B at least **3 bars** before C; C at least **2 bars** before D — [Traders.com Jan 1999](https://www.traders.com/Documentation/FEEDbk_docs/1999/01/TradersTips/Tips9901.html)
- TradeStation version searches **25 to 145 bars back** for swing highs with volume confirmation, draws a horizontal line at the right rim, and marks a breakout dot when price crosses it — [Traders.com Jan 1999](https://www.traders.com/Documentation/FEEDbk_docs/1999/01/TradersTips/Tips9901.html)
- The authors themselves warn the program "may not recognize some legitimate cup-and-handle formations or may display a pattern where one does not truly exist" — [Traders.com Jan 1999](https://www.traders.com/Documentation/FEEDbk_docs/1999/01/TradersTips/Tips9901.html)

**D. Pivot + parabola-fit approach: Abiroid "Cup & Handle" MT4 indicator (commercial, documented parameters)**
- P1 (left rim), P2 (bottom), P3 (right rim), P4 (handle low). Rims confirmed as local extrema within a **±5-bar** anchor search window — [MQL5 blog](https://www.mql5.com/en/blogs/post/771350)
- Quadratic regression over the cup: **minimum R² = 0.75** (suggested 0.70–0.85). Concavity coefficient a ≥ 0 for a bullish cup. Vertex ("peak shift") within **±0.50** of normalized cup width. Each side **≥ 25%** of cup width — [MQL5 blog](https://www.mql5.com/en/blogs/post/771350)
- Rim prices differ by **≤ 20% of cup height**. Depth/width ATR ratio minimum **0.06** (0.06–0.12). Cup width **15–200 bars** — [MQL5 blog](https://www.mql5.com/en/blogs/post/771350)
- Handle: **5–30 bars**, max retracement **61.8%** of the P3→P2 depth, plus a slope limit — [MQL5 blog](https://www.mql5.com/en/blogs/post/771350)

**E. Template / PIP / DTW approaches (academic)**
- Fu, Chung, Luk & Ng (2007), "Stock time series pattern matching: template-based vs. rule-based approaches" (Eng. Appl. of AI 20(3):347–364). Reduces the series to **perceptually important points (PIPs)**, using Euclidean, perpendicular or vertical distance, then matches either templates or rules on the PIPs. Both approaches work but in different ways — [VTC repository abstract](https://repository.vtc.edu.hk/ive-it-sp/4)
- A Columbia student project (2016) used modified Dynamic Time Warping to scan many stocks for "cup with handle" among other patterns — [GitHub Sapphirine](https://github.com/Sapphirine/Identifying-Patterns-in-Stock-Price-Movements-and-Predicting-Future-Price)

**F. Practitioner pattern specs (what the rules encode)**
- O'Neil/IBD: prior advance of about 30%+; cup depth typically **12–33%** (deeper in bear markets); at least about **7 weeks** with a handle; handle of a week or more, in the upper half of the base, drifting down on contracting volume; handle depth beyond the low teens % is a flaw; buy point = handle high plus a small margin; breakout volume about **40–50% above average** — [LuxAlgo summary of O'Neil rules](https://www.luxalgo.com/library/concept/cup-with-handle-base.md)
- MarketSmith's Pattern Recognition defines cup-with-handle bases as **6–65 weeks** long and **8–50%** deep — [Levelup/gitconnected article](https://levelup.gitconnected.com/trading-cup-and-handles-with-marketsmith-pattern-recognition-3b869d0cfe2a)
- Bulkowski: cup 7–65 weeks, U-shaped not V, rims near the same price "but be flexible", handle ≥ 1 week forming in the upper half of the cup, no cup-depth requirement — [thepatternsite.com](https://thepatternsite.com/cup.html)

### Inferences
- With ~400 daily bars, O'Neil's 7–65 week range (35–325 trading days) fits, but a practical daily-bar range is about **cup 30–250 bars, handle 5–25 bars**. This is consistent with Abiroid (15–200), canslimTechnical (A→C 23–90 days) and TASC (25–145 bars back).
- LMW's 38-day window is far too short for a cup. Borrow their *mechanics* (smooth → sign-change extrema → snap to raw high/low within ±1 bar → ratio tests) rather than their window length.
- Existing 7-bar fractal pivots (3 bars each side) and argrelextrema(order=4) behave like LMW's "raw extrema" alternative, so they will generate many candidate rims and lows. A cup detector should use a **coarser pivot order for rims/cup low (e.g. order 10–20, or a % zig-zag filter)** and the fine 7-bar rule only for the handle low.

### Gaps
- Could not fetch the full text of Fu et al. (2007) (server error). Exact PIP template weights and thresholds are not captured here.
- Did not retrieve the source of Kerry Lovvorn's original TASC cup-with-handle article (the probable origin of K-A-B-C-D). Only the Jan 1999 Traders' Tips implementations were read.
- No peer-reviewed paper was found that defines cup-and-handle specifically within the LMW kernel framework.

## 2. Quantifying "U-shaped vs V-shaped" (roundness)

### Takeaway
The only roundness metric with documented defaults is a **quadratic (parabola) fit over the cup, with R² ≥ 0.75, positive curvature, vertex near the middle and each side ≥ 25% of width** (Abiroid MT4). Rule-based K-A-B-C-D systems add **minimum segment durations** (left side ≥ 20 bars, right side ≥ 3) to rule out V-shapes. Time-near-bottom and slope-symmetry metrics are mentioned qualitatively by TradingView scripts, with no published defaults.

### Cited Findings
- Quadratic fit with R² ≥ 0.75 default (0.70–0.85 range), concavity a > 0, vertex within ±0.5 normalized width, both sides ≥ 25% of width — [MQL5 blog (Abiroid)](https://www.mql5.com/en/blogs/post/771350)
- Some engines rank candidate cups by the quadratic-regression R² ("U-shape correlation") — [search summary citing MQL5/Abiroid](https://www.mql5.com/en/blogs/post/771350)
- AGPro "Cup and Handle Quality" (TradingView, open source) scores "cup symmetry" (balance between the left and right rim areas), handle depth relative to cup depth, and breakout quality. It uses a "Maximum Rim Variance %" and a "Minimum Cup Depth ATR" filter — [TradingView AGPro](https://www.tradingview.com/script/Kg8nENSG-Cup-and-Handle-Quality-AGPro-Series/)
- RAMO Cup Family Pro (TradingView, open source) evaluates "symmetry and rounded-bottom properties" separately from handle validity. Numeric values were not disclosed on the description page — [TradingView RAMO](https://ru.tradingview.com/script/IANRXGv8/)
- Bulkowski explicitly allows variation: U-shaped not V-shaped, "allow variations" — [thepatternsite.com](https://thepatternsite.com/cup.html)

### Inferences (proposed deterministic metrics, not sourced defaults)
- **Parabola R²**: fit `np.polyfit(x, close[A:C+1], 2)`, with x normalized to [0,1]. Require a > 0, R² ≥ 0.6–0.75 and vertex x* = −b/(2a) in [0.25, 0.75].
- **Time-near-bottom (U-ness)**: the fraction of cup bars whose close is within the bottom 25% of cup depth, i.e. close ≤ B + 0.25·(min(A,C) − B). A V-cup spends only a few bars there. A plausible threshold is ≥ 15–20% of cup bars. This is a heuristic to calibrate; no published default was found.
- **Side-duration symmetry**: left bars (A→B) and right bars (B→C) each ≥ 25–30% of the cup's bars (matching Abiroid's ≥ 25%). Optionally, the ratio of the shorter side to the longer side ≥ 0.33.
- **Bottom-flatness alternative**: the smoothed curve's derivative near B stays small for several bars. In a V, |slope| stays large right up to the low.
- Use closes, or the kernel-smoothed series, for R², not highs/lows. A single wick strongly distorts quadratic fits.

### Gaps
- No academic validation found that any roundness metric (R² or otherwise) improves post-breakout returns. Thresholds are practitioner choices.

## 3. Defining rims, bottom and handle deterministically; one candidate per stock per day

### Takeaway
Implementations either (a) search backward from "today" for the most recent qualifying extrema sequence (TASC TradeStation: swing highs 25–145 bars back), or (b) brute-force over extrema combinations and keep those passing all rules (canslimTechnical "brute"). Picking exactly one candidate needs an explicit tie-break rule. None of the sources publishes a canonical tie-break, so the spec must define one.

### Cited Findings
- Point ordering and spacing constraints: A ≥ 20 bars before B; B ≥ 3 bars before C; C ≥ 2 bars before D; handle low D > 0.8·C + 0.2·B — [Traders.com Jan 1999](https://www.traders.com/Documentation/FEEDbk_docs/1999/01/TradersTips/Tips9901.html)
- Right rim must recover above 0.6·A + 0.4·B and not exceed A. Handle D ≤ C. Segment durations 20–60 / 3–30 / 3–20 days — [canslimTechnical README](https://github.com/kanwalpreet18/canslimTechnical/blob/master/README.md)
- TradeStation implementation scans 25–145 bars back for swing highs with volume confirmation — [Traders.com Jan 1999](https://www.traders.com/Documentation/FEEDbk_docs/1999/01/TradersTips/Tips9901.html)
- Rim alignment tolerances in use: ≤ 20% of cup height (Abiroid, [MQL5](https://www.mql5.com/en/blogs/post/771350)); "Maximum Rim Variance %" input (AGPro, [TradingView](https://www.tradingview.com/script/Kg8nENSG-Cup-and-Handle-Quality-AGPro-Series/)); LMW used 1.5% of the average for equal-height extrema in other patterns ([paper](https://www.cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf))
- Handle in the upper half of the cup — [thepatternsite.com](https://thepatternsite.com/cup.html); [LuxAlgo/O'Neil](https://www.luxalgo.com/library/concept/cup-with-handle-base.md). Handle max retrace 61.8% of cup depth in Abiroid — [MQL5](https://www.mql5.com/en/blogs/post/771350)
- MarketSmith's API returns explicit fields per pattern (pivot price, handle low date, patternType where 1 = cup with handle), so each pattern is a discrete object with dated anchors — [Levelup article](https://levelup.gitconnected.com/trading-cup-and-handles-with-marketsmith-pattern-recognition-3b869d0cfe2a)

### Inferences (a deterministic anchor procedure synthesized from the above)
Evaluated on day T using only bars ≤ T:
1. **Handle high H / right rim C**: the highest high in the last `handle_max` (e.g. 25) bars that is a *confirmed* pivot high, i.e. at least k bars exist after it, with k = pivot half-width. If several bars tie, take the most recent. (The C anchor is fixed first because the breakout level depends on it.)
2. **Handle low D**: the lowest low strictly after C up to T−1. Require 5 ≤ bars(C→D…T) ≤ 25, D ≥ C − 0.5·(C − B) (upper half; the stricter TASC rule is D > 0.8·C + 0.2·B) and handle depth (C − D)/C ≤ 12–15%.
3. **Left rim A**: among confirmed pivot highs from C − cup_max to C − cup_min bars (e.g. 250 to 30), pick the **most recent** one whose high is ≥ C × (1 − rim_tol) and is the highest high between itself and C. That last condition guarantees no higher peak sits inside the cup, which removes most overlapping candidates.
4. **Cup low B**: argmin of low over (A, C). This is deterministic and needs no pivot. Ties go to the later bar.
5. Validate depth (A − B)/A in [12%, 35–50%], the recovery C ≥ B + 0.6·(A − B) (canslim) or ≥ 0.9·A for O'Neil-style rims, side durations and roundness (Section 2).
6. **Prior uptrend K**: the lowest low in the N (e.g. 60–120) bars before A. Require A/K ≥ 1.15–1.30.
7. If several A candidates pass, the tie-break is "most recent A that passes all tests". An alternative is "highest parabola R²". Both are deterministic, but the first is simpler and more stable day-to-day.
- This yields at most one candidate per day. Most of the time it is the same pattern carried forward day after day until a breakout, an invalidation (close < D) or expiry.

### Gaps
- No source documents how commercial engines (MarketSmith, TradingView) resolve overlapping/nested cups. The tie-break above is a design choice, not a cited standard.

## 4. Breakout detection and look-ahead bias

### Takeaway
Breakout is usually defined as a **daily close above the right rim / handle high (pivot)**. Some versions add a buffer (MarketSmith backtest: > 1% above the pivot) or a volume rule (+40–50% vs average). The major look-ahead risk is that **pivots and centered smoothers need future bars**. LMW solve this by fitting only within the window ending on the detection day and requiring the last extremum to be d = 3 days before detection. Practitioners warn that pivot labels "shift with incoming data" and must be delayed by their confirmation length.

### Cited Findings
- Bulkowski: buy when price **closes above the right cup rim** — [thepatternsite.com](https://thepatternsite.com/cup.html)
- O'Neil: buy point = handle high plus a small margin. Breakout volume about 40–50% above average — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base.md)
- MarketSmith-based backtest entry: current price > pivot × 1.01, date after handleLowDate but within 30 days, and SMA50 > SMA200. Exits at +15%, −5% or 21 days — [Levelup article](https://levelup.gitconnected.com/trading-cup-and-handles-with-marketsmith-pattern-recognition-3b869d0cfe2a)
- Abiroid offers a horizontal trigger (P3 rim price) or a slanted trigger (line through P1 and P3). With "require breakout to show pattern" = true (the default), the pattern appears only after a close beyond the entry level and is "fully non-repainting". Otherwise the pattern can disappear if the handle later fails validation — [MQL5](https://www.mql5.com/en/blogs/post/771350)
- AGPro: episodes "open and resolve on confirmed bars only", so statistics never change after the fact. After a breakout the target (rim + cup depth) and invalidation (close below the handle low) are frozen — [TradingView AGPro](https://www.tradingview.com/script/Kg8nENSG-Cup-and-Handle-Quality-AGPro-Series/)
- LMW's look-ahead control: window from t to t+l+d−1, with the final extremum required on day t+l−1, so d = 3 days pass before detection. Returns are measured from the end of day t+l+d, so "the lag d ensures … without any 'look-ahead' bias" — [paper](https://www.cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf)
- Optuma forum (vendor staff): pivot labels shift with new data, so pivots "shouldn't be used for backtesting" without code that ignores a pivot until x bars after it — [Optuma forum](https://forum.optuma.com/t/optuma-pivot-script-not-working-correctly/3761)
- With argrelextrema, swings are registered 1–2+ periods after they occur ("just how argrelextrema works"), so signals must be dated at confirmation, not at the extremum bar — [MarketCalls](https://www.marketcalls.in/?p=63874)
- PatternPulse (argrelextrema-based, includes cup & handle) uses walk-forward, expanding-window backtesting to avoid look-ahead — [GitHub PatternPulse](https://github.com/GZ30eee/PatternPulse)

### Inferences
- **Rule for the spec:** on day T, compute everything from `df.iloc[:T+1]`. A pivot at bar i (7-bar fractal) is usable only when i + 3 ≤ T. For argrelextrema(order=n) it is usable only when i + n ≤ T, and argrelextrema must be run on the truncated array, because at the array end it silently ignores missing neighbours (its default mode='clip').
- **Never apply a centered kernel/rolling smoother to the full history.** A Gaussian/NW smoother at bar i uses bars after i. Either refit the smoother on data ≤ T each day (LMW style), or use a one-sided filter (EMA). Note that the right edge of a refit NW smoother is biased and moves as new bars arrive (edge effect). Treat extrema within the last ~h bars as unconfirmed.
- The handle low D is by definition still forming until breakout. Use "lowest low since C", not a confirmed pivot, and re-evaluate daily.
- **Breakout:** Close[T] > handle high H (the max high from C to T−1, i.e. the pivot), optionally × (1 + 0.5–1%), with Volume[T] ≥ 1.4 × SMA50(volume)[T−1]. Enter at Open[T+1] (or Close[T] if the backtester assumes MOC fills). Using High[T] > pivot (an intraday cross) gives earlier but noisier signals, and an intraday stop-entry fill needs the high only for the touch test. Using the close is the deterministic, non-repainting choice.
- Require that no close above H occurred between C and T−1 (first breakout only). Expire the pattern if no breakout within N bars (MarketSmith-style 30 days after the handle low).

### Gaps
- No source quantified how much backtest performance is inflated when using unconfirmed pivots for cup-and-handle specifically. The direction (inflation) is well established, the magnitude is not.

## 5. Open-source references and their quality

### Takeaway
Open-source cup-and-handle code is sparse, small and mostly unmaintained. The most-cited Python/R one is canslimTechnical (R, ~61 stars). Major TA libraries (TA-Lib's candlestick functions, pandas_ta) have **no cup-and-handle detector**. Python chart-pattern libraries such as zeta-zetra/chart_patterns cover triangles, H&S, doubles, flags and pennants but not cups.

### Cited Findings
| Reference | Type | What it offers | Quality |
|---|---|---|---|
| [kanwalpreet18/canslimTechnical](https://github.com/kanwalpreet18/canslimTechnical) | R | Kernel regression (bw=3) + K-A-B-C-D ratio/duration/volume rules; brute and minMax variants | ~61 stars, 36 forks, 12 commits; academic-style, unmaintained ([repo](https://github.com/kanwalpreet18/canslimTechnical)) |
| [HumanRupert/marketsmith_pattern_recognition](https://github.com/HumanRupert/marketsmith_pattern_recognition) | Python (Zipline-style) | Consumes MarketSmith's paid Pattern Recognition API; breakout = >1% above pivot within 30 days of handle low, SMA50>SMA200 | Detection is a black box (paid API) ([article](https://levelup.gitconnected.com/trading-cup-and-handles-with-marketsmith-pattern-recognition-3b869d0cfe2a)) |
| [dragonAscent009/Cup-and-handle](https://github.com/dragonAscent009/Cup-and-handle) | C++/Qt | Long-period scan for the formation | 2 stars, 4 commits; parameters not documented ([repo](https://github.com/dragonAscent009/Cup-and-handle)) |
| [myalim/Cup-and-Handle-Pattern](https://github.com/myalim/Cup-and-Handle-Pattern), [carlamHS/vcp_screener](https://github.com/carlamHS/vcp_screener) | Python | Screener-style detectors | Not inspected in detail (surfaced in search only) |
| [GZ30eee/PatternPulse](https://github.com/GZ30eee/PatternPulse) | Python | argrelextrema + geometric constraints, includes cup & handle, optional LSTM confidence filter, walk-forward backtest | 1 star, 10 commits; parameters undocumented in README ([repo](https://github.com/GZ30eee/PatternPulse)) |
| [zeta-zetra/chart_patterns](https://github.com/zeta-zetra/chart_patterns) | Python | Doubles, flags, H&S, triangles, pennants: **no cup** | ([repo](https://github.com/zeta-zetra/chart_patterns)) |
| [Sapphirine DTW project](https://github.com/Sapphirine/Identifying-Patterns-in-Stock-Price-Movements-and-Predicting-Future-Price) | Python (2016 course project) | Modified DTW template scan incl. cup with handle | Student project |
| [AGPro Cup and Handle Quality](https://www.tradingview.com/script/Kg8nENSG-Cup-and-Handle-Quality-AGPro-Series/) | Pine (open source) | Pivot span, min/max cup bars, max rim variance %, min cup depth in ATR, handle depth range, breakout volume baseline, quality score, confirmed-bar-only episodes | Active TradingView script |
| [RAMO Cup Family Pro](https://ru.tradingview.com/script/IANRXGv8/) | Pine (open source) | Structural cup/handle analysis with confidence score, developing-cup detection | Numeric defaults not in description |
| [Abiroid Cup & Handle](https://www.mql5.com/en/blogs/post/771350) | MT4 (commercial) | Fully documented defaults (R² 0.75, width 15–200, rim ≤20% of height, handle 5–30 bars, ≤61.8% retrace) | Closed source; useful parameter reference |
| [TASC Traders' Tips Jan 1999](https://www.traders.com/Documentation/FEEDbk_docs/1999/01/TradersTips/Tips9901.html) | TradeStation / TechniFilter / SmarTrader code | K-A-B-C-D constraints, 25–145-bar search | Historical; explicit caveats |

### Inferences
- There is no maintained, de-facto-standard Python implementation to copy. The spec has to be self-contained. canslimTechnical + TASC + Abiroid together give a coherent, cross-checked parameter set.
- An Amibroker AFL library entry was not located in this search, so no AFL parameters are reported.

### Gaps
- Did not inspect source code (only READMEs/descriptions) for the Python repos. Parameter values for myalim, carlamHS and PatternPulse are unknown.
- Pine source code for AGPro/RAMO was not read, so their default numbers are not captured.
- No Amibroker AFL cup-and-handle source was found.

## 6. Known pitfalls

### Takeaway
The main documented pitfalls are: too many raw extrema (noise), bandwidth/pivot-order sensitivity with only ad hoc tuning, pivot repainting / look-ahead, detector output that chartists reject, and weak post-breakout reliability in some samples.

### Cited Findings
- **Noise / too many extrema:** raw local extrema give too many patterns that do not look right to technicians — [LMW](https://www.cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf)
- **Smoothing sensitivity:** LMW's CV bandwidth was judged "too smooth" by analysts. The 0.3 factor came from trial and error and analyst polling, and the authors call it "ad hoc" — [LMW](https://www.cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf). Practitioner defaults also vary widely: canslimTechnical bw = 3 bars ([README](https://github.com/kanwalpreet18/canslimTechnical/blob/master/README.md)) vs LMW's CV-relative bandwidth.
- **Over-fitting guard (LMW):** bandwidth was fixed *before* the statistical tests and never revised — [LMW fn. 5](https://www.cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf)
- **Detector vs chartist disagreement:** the TASC authors warn of both missed and false patterns — [Traders.com](https://www.traders.com/Documentation/FEEDbk_docs/1999/01/TradersTips/Tips9901.html). O'Neil notes that "proportions are the pattern" and recommends judging on weekly charts first — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base.md)
- **Repainting pivots / look-ahead:** pivot labels change with new data — [Optuma forum](https://forum.optuma.com/t/optuma-pivot-script-not-working-correctly/3761). argrelextrema swings are known only after their order — [MarketCalls](https://www.marketcalls.in/?p=63874). Abiroid's "show before breakout" mode can make patterns disappear later — [MQL5](https://www.mql5.com/en/blogs/post/771350)
- **Handle flaws chartists reject:** handles that slope upward or form deep in the base. Handle depth beyond the low teens % — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base.md)
- **Performance caveat:** Bulkowski reports a 5% failure rate and a 54% average gain on "913 perfect trades" (hand-selected). He also found that 47% of 300 historical cup-with-handle patterns "dropped substantially within two months of the breakout" — [thepatternsite.com](https://thepatternsite.com/cup.html). Hand-curated statistics are not directly transferable to an automated detector.
- **Survivorship:** relevant whenever the stock universe is the current constituents list. (The target system already uses point-in-time Nifty 500 membership per the repo's recent commit history; no external source was needed for this point.)

### Inferences
- Expect many more candidates from an automated detector than from Bulkowski's hand-picked sample. Statistics such as a 5% failure rate should not be used as benchmarks.
- Main sensitivity knobs to fix up front, without later tuning on backtest results: pivot order for rims, rim tolerance, depth range, R²/near-bottom thresholds, handle depth/length, breakout buffer, volume multiple. Run a small sensitivity grid only to check robustness, not to pick the best.
- "Looks right algorithmically but a chartist would reject it" cases to guard against explicitly: a cup that is really a downtrend with a dead-cat bounce (no prior uptrend → require A/K ≥ 1.2–1.3); a V-bottom (fails R² / time-near-bottom / side-duration); a right rim far below the left (rim tolerance); a "handle" that is a new leg down below the cup midpoint; a cup with a higher peak inside it (step 3 rule); gaps in illiquid stocks distorting extrema (snap to raw high/low, as LMW do, and consider minimum liquidity).
- Window edges: on a ~400-bar history, cups longer than about 250 bars plus the prior-uptrend lookback (60–120 bars) cannot be evaluated early in the series. The first valid evaluation date should be documented.

### Gaps
- No rigorous out-of-sample study was found that compares automated cup-and-handle detection parameter sets on Indian or US equities. Performance evidence comes from hand-picked samples (Bulkowski) or short backtests (the MarketSmith 2016–2018 example).
