# User-supplied sources (added 2026-10-06)

Three documents the user supplied after the initial web research, which could not reach them. Text was extracted to plain text and read in full. Page numbers below are the PDF page numbers of each printout, unless marked "book p." for Bulkowski.

Status tags: **CONFIRMS**, **CONTRADICTS** or **REFINES** a figure in `reports/Cup and handle breakout rules.md`, **NEW** where the report had nothing, and **ABSENT** where the report attributed something to this source that the supplied copy does not contain.

---

## 1. TraderLion: "What Is The Cup And Handle Pattern?" (Ameet Rai)

- URL: https://traderlion.com/technical-analysis/cup-and-handle-pattern/ (printed 06/10/2026, 14 pages). Local PDF: `C:\Users\apoorv.bedmutha.MEDIASSISTINDIA\Downloads\What Is The Cup And Handle Pattern_ _ TraderLion.pdf`
- Dated "Published: December 29, 2019", but the text refers to Deepvue and a 2025 related-articles list, so it has been revised since then. The author bio claims "proprietary data-based research". **The article cites no data, sample, backtest or statistic of its own.** Every number is a restated rule.
- Grade: **practitioner**. It restates O'Neil/IBD methodology. TraderLion states on p.10 that it is not affiliated with O'Neil Capital Management, IBD or MarketSurge, so this is not an IBD primary source.
- Gaps in the printout: the "Cup and Handle Pattern Examples" section (pp.7-8) printed with no chart images, and the three FAQ answers on p.9 printed collapsed (questions only). Any rule found only in those parts is missing here. So an absence below means "not in the printed copy", not "not on the page".
- The rules list on p.3 is also an embedded infographic (extracted image checked). Its wording matches the text. The only difference: the image says the handle "should slope downwards", while the p.4 text says "should ideally slope downwards".

### Rule-relevant content

| Topic | What TraderLion says | Page | Relation to report |
|---|---|---|---|
| Cup shape | Rounded, resembling a U, "not a sharp V" | p.3 | CONFIRMS the U-shape requirement. Gives no number, so the R²/side-duration tests are still Abiroid/researcher choices |
| Pattern length | "Formed over a minimum of 7 weeks. (Including Handle)" | p.3 | **REFINES** cup length. The report's `35 ≤ bars(A→C)` applies the 7 weeks to the cup alone. TraderLion counts the handle in the 7 weeks, so the doctrine is roughly bars(A→T−1) ≥ 35, which allows the cup alone to be about 30 bars. LuxAlgo's "at least about 7 weeks with a handle" (research notes) agrees. No maximum given |
| Handle length | "Minimum of 1 week" | p.3 | CONFIRMS the 5-bar handle minimum. No maximum given |
| 200-day MA | "The pattern should form above the 200dma" | p.4 (also the p.3 infographic) | **NEW**. The report had no 200-day rule. Unquantified: it does not say whether the whole cup, the cup low or only the handle/breakout must sit above the 200-DMA |
| Base depth | "Base depth should be 12-35%" | p.4 | **CONTRADICTS (slightly)** the report's 12-33% (O'Neil via LuxAlgo). The lower bound of 12% is confirmed. The upper bound is 35% against 33% |
| Handle slope | "Should ideally slope downwards, not upwards". Under mistakes: an upward-wedging handle that drifts up "instead of downward or sideways" is a red flag | p.4 | CONFIRMS the "handle not wedging" rule in words, now from a directly read practitioner source. Sideways handles are acceptable, which fits `slope ≤ 0`. The numeric slope test is still the researchers' |
| Loose handle | A handle "too wide and loose" is a mistake. A proper handle has "a tight price range with a slight downward drift" | p.4 | Qualitative support for the handle-depth cap and the handle-tightness ranking. **No number**, so the 12% cap stays secondary-only (LuxAlgo) |
| Handle position | Handles "in the lower half of the cup or below the 10-week moving average are weak". Strong handles form "in the upper half" | p.4 | CONFIRMS the upper-half rule (already practitioner via Bulkowski) and the 10-week-MA rule. The latter was graded secondary-only (LuxAlgo snippet) and can now go up to practitioner |
| Breakout volume | Volume "should increase by at least 40% to 50% above the stock's average daily volume". Ideally surges of "200%, 500%, or even 1,000%". Without the surge "a breakout is more likely to fail" | p.4 | CONFIRMS the 1.4x floor; the row can go from secondary-only to practitioner. The averaging window is **not** stated (the report's 50-day SMA remains a convention). The claim that low-volume breakouts fail more often **CONTRADICTS** OGA's flat ~57% hit rate across volume buckets. TraderLion gives no data for its claim, and OGA's study is the rigorous one |
| Pivot / trigger | Buy when the stock "breaks out of the handle on strong volume" | pp.2, 6, 7 | Weakly CONFIRMS handle high as the pivot. No "+10 cents", and no close-versus-intraday rule |
| Buy zone (5% above pivot) | **Not present** in the printed copy | none | **ABSENT**. The report's buy-zone row cites TraderLion from a search snippet at a different URL (`/the-cup-and-handle-pattern/`). It cannot be confirmed from this document, so it stays secondary-only. It may sit in the collapsed FAQ or a different TraderLion page |
| Stop loss | O'Neil's rule "to cut losses at 7-8% below your purchase price" | p.7 | CONFIRMS the 8% cap in the initial stop. The source can now be TraderLion (practitioner), not only the LuxAlgo snippet |
| Failed-breakout signs | Watch for "unexpected drops on high volume" as a warning to exit | p.7 | Qualitative only. No numeric failed-breakout test, so the report's failed-breakout row is unaffected |
| Faulty bases | Loose handle, upward-wedging handle, handle in lower half or below the 10-week MA, breakout without volume | p.4 | CONFIRMS the faulty-base list that the report's filters already encode |
| Prior uptrend | **Not stated** | none | No change. The 30% prior-advance figure stays secondary-only |
| Handle depth number | **Not stated** | none | No change |
| Rim alignment | **Not stated** | none | No change |
| Base count / late-stage bases | **Not stated** in this copy | none | ABSENT. `pattern_geometry.md` cited TraderLion for base count via a search summary. That cannot be confirmed here. The report itself cites IBD via itiger, so the report is unaffected |
| Fundamentals | "Most reliable when the stock has good and consistent earnings growth" | p.2 | Not computable from OHLCV. Noted only |
| Effectiveness claim | "O'Neil's research proved its effectiveness" | p.2 | Unsupported assertion. No figures cited. Gives no grounds to change any evidence grade |

---

## 2. Ahlawat (2016), "Empirical evaluation of price-based technical patterns using probabilistic neural networks", *Algorithmic Finance*

- DOI page: https://journals.sagepub.com/doi/10.3233/AF-160059 (printed 06/10/2026, 66 pages). Local PDF: `C:\Users\apoorv.bedmutha.MEDIASSISTINDIA\Downloads\Empirical evaluation of price-based technical patterns using probabilistic neural networks - Samit Ahlawat, 2016.pdf`
- Grade: **peer-reviewed, but low statistical power for cup-and-handle**. Details below.

### What was tested

- **Universe:** the 30 Dow Jones Industrial Average components, plus 10 index ETFs: SPY and nine Russell ETFs (IWM, IWB, IWR, IWC, XLG, IWF, IWD, IWO, IWN) (p.1, pp.15-17 Table 1). US only.
- **Period:** 1990-2015 for the Dow stocks and SPY. 2000-2015 for the Russell ETFs (p.4, p.15). Dividend- and split-adjusted closes (p.16). The Dow list appears to be the 2015 membership, which implies survivorship bias. This is our inference; the paper does not discuss it.
- **Patterns:** 14 pattern classes, one of which is cup-and-handle, classed as bullish (p.4, Table 5 p.23).
- **Detection (relevant to automated parameters):**
  - Hand-drawn straight-line prototypes, each 20 days long. Each prototype gets 600 noisy perturbations: Gaussian noise with σ = 0.3, plus ±1-day shifts. That gives 601 training examples per class (pp.5-6).
  - Each candidate window is rescaled to 20 points and min-max normalised to [0,1]. The 20-vector is the "fingerprint" (p.11).
  - A probabilistic neural network (Specht 1990) classifies the fingerprint. A match requires the winning class's likelihood to be at least **100x** every other class's (pp.12-14). The 100 is an empirical choice.
  - Search window: the method section says 20-60 days (p.11). The application uses **20-40 trading days** only (p.15, p.54). Longer patterns are not identified.
  - Validation: LOESS smoothing (quadratic, span 0.4, Gaussian kernel; Table 3 p.21). Local extrema are found on the smoothed closes. Cup-and-handle must show the high-low order **(H,L,H,L,H)** (Table 4 p.21). Matches are **not** manually checked (p.22).
  - **Volume is not used at all** (p.5, p.54). There is no prior-uptrend, depth, handle-position or rim-alignment rule, and no breakout-above-pivot trigger.
- **Trade rule:** on detection day i, trade only if Close[i+3] has moved in the pattern's predicted direction. The holding period starts at i+4 (pp.22-23). Holding periods are 10, 20, 30, 40 and 50 trading days. The return formula is (p_{i+N} − p_i)/p_i (p.16), but the text also says "price change is recorded for one unit of asset" (p.23). The fall in the reported means after costs is roughly constant in price terms per asset (e.g. IWD cup: 0.649-0.659 at all four horizons). So the "Mean" column is **most likely a per-share price change in dollars, not a percent return**. This is our inference; the paper does not state units.
- **Statistics:** one-sided t-test at 95%, with no correction for multiple comparisons (p.23). That is 14 patterns × 40 assets × 5 horizons × 2 regimes, about 5,600 tests, so about 280 "significant" results would be expected by chance alone. The same few trades are re-tested at five overlapping horizons. Several index ETFs overlap heavily (SPY, IWB, XLG, IWD, IWR), so index results are not independent.
- **Regimes:** the sample is split ex post into bull and bear periods using media-reported dates (Table 2 p.17). The author admits this "entails some in-sample bias" (p.16). **No out-of-sample or walk-forward test.** The author says a full-period run gives "similar qualitative results" but shows no table for it (p.16).
- **Costs:** 0.5% of trade notional (p.44). Tables 10-13 are after costs.

### Cup-and-handle results

| | Before costs | After 0.5% costs |
|---|---|---|
| Dow components, bull markets | AXP at 30d (n=5, t=2.05, p=0.048) and 40d (n=5); JPM at 50d (n=5). **2 of 30 stocks** (Table 6, p.24, p.29) | AXP 40d (n=5, p=0.046); JPM 50d (n=5, p=0.038). **2 of 30** (Table 10, p.45, p.47) |
| Indices, bull markets | IWB (10/20/40d, n=7), IWC (20d, n=5), IWD (all 10-50d, n=9), IWN (all 10-50d, n=11), IWO (40/50d, n=5), IWR (all 10-50d, n=14), SPY (20d, n=5), XLG (20d, n=7). **8 of 10 indices** (Table 8, pp.36-41) | IWB (10/20d), IWD (20-50d), IWN (20-50d), IWO (40/50d). **4 of 10 indices**. IWR, SPY, XLG and IWC drop out (Table 12, pp.51-52) |
| Any asset, bear markets | **None** (Tables 7, 9) | **None** (Tables 11, 13) |

- Largest sample behind any cup-and-handle result: **14 trades** (IWR). Most are 5-11.
- Typical means: about 1-3.5 (likely dollars per share) over 10-50 days. IWD reached t = 8.8 at 50 days on 9 trades.
- Inconsistency in the paper: the text on p.43 says cup-and-handle "produces statistically significant profits for 9 tickers" among the Dow components. Table 6 lists only AXP and JPM. Counting Dow and index tables together gives 10, not 9. Treat the "9" as unreliable.
- Author's conclusions: "no pattern produces statistically and economically significant profits for a cross-section of stocks and indices" (abstract, p.1). Cup-and-handle is "a more reliable pattern for indices ... than it is for Dow Jones components" (p.44, p.54). Bullish patterns work better in bull markets (p.54). Most patterns need holding periods over 20 days (p.44).

### Relation to the report

- **CONFIRMS** the report's earlier, snippet-only statement (in `performance_statistics.md`) that cup-and-handle was significant more often for indices than for Dow stocks. The details are now verified: 8/10 vs 2/30 before costs, 4/10 vs 2/30 after costs.
- **REFINES** how much weight the study can carry. The "cup-and-handle" it tests is a 20-40-day, volume-blind, template-matched shape with a 3-day confirmation entry. That is shorter than the 7-week (35-bar) O'Neil minimum, and it has no handle-depth, upper-half, prior-uptrend or volume filters. It is evidence about a generic short cup shape, not about the spec in the report. With 5-14 trades per cell and no multiple-testing correction, even the significant cells are weak. The index-vs-stock contrast says nothing about NSE single stocks, except perhaps as a mild warning that single-stock results may be noisier.
- **CONFIRMS (directionally)** the regime point: cup-and-handle profits appeared only in bull-market partitions, never in bear. This supports the report's MarketBreadth weighting/gating experiment, with the caveat that the partition was chosen ex post.
- **Detection lessons for the spec:** (a) the paper's LOESS is applied within each window that ends on the detection day, so it does not leak future bars beyond i. A full-history centered LOESS would leak, which matches the report's warning. (b) A likelihood-ratio threshold (100x) is the template-matching analogue of the report's R² gate, and it was likewise fixed before testing. (c) Volume was deliberately left out because definitions disagree. This study therefore cannot inform the 1.4x gate.
- No contradiction of any threshold, since the paper uses none of the report's geometric thresholds.

---

## 3. Bulkowski, *Encyclopedia of Chart Patterns*, 3rd ed. (Wiley, 2021): 30-page preview

- Local PDF (most likely the file supplied): `C:\Users\apoorv.bedmutha.MEDIASSISTINDIA\Downloads\L-0016326199-pdf.pdf`. Contents: front matter, the three prefaces, the table of contents and Introduction book pp.1-4. **The Cup with Handle chapter (book p.294) is not included.** The text stops partway through the "Testing Chart Patterns" example on book p.4, so the formal definition of the ultimate high is also cut off.
- Grade: **practitioner** (author's own database).

### Content relevant to the report

| Finding | Book page (PDF page) | Relation to report |
|---|---|---|
| Database: **1,396 stocks**, most from July 1991 into 2020. Not all cover the full period. Includes stocks that later went bankrupt or merged (some survivorship control) | book p.3 (PDF p.29) | NEW context for the 913-trade cup statistics (that figure is from his website and may come from a different edition or sample) |
| Selection: stock "trades above $5 a share (usually)", daily volume preferably "over 100,000 shares", with a reasonable yearly high-low range. All market caps. **Most are American companies on NYSE or NASDAQ** | book pp.3-4 (PDF pp.29-30) | NEW caveat. His statistics describe liquid US stocks above $5. Nothing is Indian. An NSE analogue would be a price/turnover floor |
| Daily data. Split-adjusted. **Not dividend-adjusted** | book p.3 | NEW minor caveat when comparing his rise percentages with adjusted NSE data |
| "Most chart patterns were added in real time" for more than 20 years, which he says avoids look-ahead bias | book p.3 | **REFINES** the report's "hand-picked" wording. The patterns are visually (discretionarily) identified but logged in real time, not cherry-picked after the outcome. Selection is still human, not algorithmic |
| Entry convention: a close above the pattern top is the breakout; "entry is made the next day using the opening price" | book p.4 (PDF p.30) | NEW. Differs from this backtester, which enters at the signal day's close |
| He rejects testing with any exit rule (stop, MACD, MA cross) because that tests the exit, not the pattern. Instead he "invented two tools I call the ultimate high and ultimate low" | book p.4 | **REFINES / CONFIRMS** the report's caveat. His performance numbers are measured to the ultimate high (a hindsight best exit), not to any tradeable exit. The exact definition (the existing notes give "the highest peak before a 20% decline") is not in this preview |
| His average rise figures are for comparing patterns. A trader makes the average "only if you trade the chart pattern perfectly", e.g. 1,099 times for the best pattern | Preface to 3rd ed., book p.xi (PDF p.13) | **CONFIRMS** in Bulkowski's own words that his 54% average rise for cups is not achievable by a mechanical system |
| About 150,000 samples across 75 patterns in the 3rd edition. New tables include "how often stops hit" and performance over time | book p.x (PDF p.12) | Context only. Those cup tables are in the missing chapter |
| Cup with Handle chapter at book p.294; Inverted at p.311 | Contents (PDF p.23) | Confirms the location of the missing chapter |
