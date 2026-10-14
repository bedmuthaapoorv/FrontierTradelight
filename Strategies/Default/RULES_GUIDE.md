# How to Write `rules.md`

`rules.md` is the only file you need to edit to define a strategy. It's a
plain-English spec — you never write Python. When you run
`generate_screener.py`, its full text gets pasted into a prompt sent to
Gemini, which turns it into `generated_rules.py` (a function that scores
every stock). This guide explains what to put in it and why, so the
generated code actually does what you intend.

## What data is available to reference

Every rule you write has to be computable from what the screener actually
fetches per stock. Don't invent a metric it has no way to calculate. You have:

- **Daily OHLCV price history** (~400 days) per stock: `open`, `high`, `low`,
  `close`, `volume`. You can reference relative days like `Volume[-1]`
  (yesterday), `Volume[-2]` (the day before), or ranges like `HighestHigh(252)`
  (highest high over the last 252 trading days ≈ 1 year).
- **Delivery percentage** (`delivery_pct`) — NSE's published % of traded
  volume that actually settled as delivery (vs. intraday-only churn), same
  ~400-day history as OHLCV. A high delivery % on a strong-volume day is a
  proxy for genuine buying (investors taking the stock home) rather than
  speculative intraday flow that's likely to reverse. May be `NaN` for
  cached history fetched before this field was tracked - handle missing
  values rather than assuming it's always present.
- **Standard technical indicators** computed from that price history — RSI,
  moving averages, etc. (the generator uses `pandas_ta`, so anything that
  library supports is fair game).
- **Sector info** — each stock's sector name, and a `SectorRank` (1 = best
  performing sector by recent average return, higher = weaker).
- **Market breadth** — a `MarketBreadth` value (0-100: % of the entire
  universe currently trading above its own 50-day moving average),
  computed once per day across all stocks, not specific to any one stock.
  It's a stand-in for a Nifty benchmark regime filter (no external index
  data is available) — useful for a rule like "pause entries when the
  broader market itself is weak, even if this stock's setup looks fine."
- **Momentum rank** — each stock's cross-sectional "12-1" momentum
  percentile (0-100, 100 = strongest): its return from 252 trading days ago
  to 21 trading days ago, ranked against every other stock in the universe
  that day. Use it for rules like "bottom 5% of momentum" (≤ 5) or "top 10%"
  (≥ 90). It's empty for stocks with less than ~253 days of history.
- **Company/sector metadata** — name, sector, current price.
- **Annual fundamentals** (`fundamentals`) — from Screener.in, cached by
  `fetch_fundamentals.py` (run it first; refresh quarterly). Per stock, as
  publicly known on the evaluated day (a fiscal year only counts 60 days
  after it ends, the SEBI results deadline):
  `positive_eps_years`, `eps`, `eps_cagr_3y`, `sales_cagr_3y`, `roe`,
  `de` (debt/equity, None for banks/financials), `is_financial`, `pe`
  (today's close / latest EPS) and `peg` (`pe / (eps_cagr_3y × 100)`).
  Growth rates and ROE are fractions (0.15 = 15%). Any value can be missing
  — say what a rule does then (usually: fail). Figures are annual only and
  restated, not as first reported.

These are passed into the generated function as
`evaluate_stock(symbol, df, universe, sector_ranks, market_breadth, momentum_ranks=None)`
or `evaluate_stock(symbol, df, universe, sector_ranks, market_breadth, fundamentals=None)`
— if your rules reference sector rank, market breadth, momentum rank or fundamentals, use
these parameters directly rather than trying to compute them from `df` (a
single stock's own OHLCV can't tell you about its sector's return, the whole
market's breadth, or its earnings). Momentum ranks are cross-sectional; fundamentals
are point-in-time company data.

Fundamentals change about once a year, so a fundamentals-only rule passes
on every trading day and the backtester (which opens a trade every day a
stock passes) would keep re-entering. For slow fundamental strategies, add
an entry-day rule such as "the signal day is the first trading day on or
after 15 June or 15 December" so each stock can signal only on a
rebalance day, and pair it with an exit that holds until the next one.

If a rule needs something outside this (e.g. options data, news sentiment,
quarterly results), it won't be computable — the generator will either
skip it or hallucinate a stand-in, which defeats the point.

## Required structure

Keep these five sections. The generator (see the prompt in
`generate_screener.py`) expects the whole file, so consistent headings make
it far more reliable, but the section order below is the one that's been
tested and works well.

### 1. Strategy Metadata

Free-form context: strategy name, market, timeframe, holding period. Doesn't
drive logic, but helps Gemini and future readers understand intent.

```markdown
## Strategy Metadata

Strategy Name: Trendline Support Momentum
Market: India (NSE/BSE)
Timeframe: Daily
Holding Period: Swing Trade (1-30 Days)
```

Two optional lines **do** change how the backtester treats the strategy:

- `Direction: Short` — a passing stock is a **short** signal: the backtest
  profits when price falls (P&L sign flipped), and Strategy Compare shows
  "Short signal". Default (no line): `Long`.
- `Holding: Intraday` — every trade is opened at the next day's open and
  closed the **same day** (MIS): the exit strategy only sees that one day,
  and anything still open is squared off at its close (`SquareOff`).
  Default (no line): a normal swing trade held until the exit strategy
  fires.

See `Rules_backup/momentum_loser_intraday_short_v1_rules_*.md` for a
complete short + intraday example.

### 2. Mandatory Filters

The core of the strategy: a numbered list of rules that **all** must pass for
a stock to be considered a valid pick. Each rule should have:

- **Description** — one sentence, plain English, of *why* this filter exists.
- **Condition** — the precise, computable logic. Use comparison operators
  (`>`, `<`, `<=`, `AND`, `OR`) against the data fields above. Be exact about
  numbers — "RSI between 40 and 60" is fine, "RSI is reasonable" is not.
- **Notes** (optional) — edge cases: what to do with missing data, which
  sessions to include/exclude, etc. These matter — vague edge cases produce
  inconsistent generated code.

```markdown
### Rule 1: Increasing Volume

Description:
Volume should show increasing participation over the last 3 completed trading sessions.

Condition:

Volume[-1] > Volume[-2]
AND
Volume[-2] > Volume[-3]

Notes:
- Ignore today's volume.
- Stocks with missing volume data should be rejected.
```

Repeat this pattern for each filter (RSI range, distance from 52-week high,
sector strength, trendline proximity, or whatever your strategy needs).

### 3. Rejection Rules

Usually just a one-liner stating the logical relationship between the
mandatory filters:

```markdown
## Rejection Rules

Reject stock if ANY mandatory filter fails.
```

### 4. Ranking Rules

Stocks that pass the mandatory filters still need to be ranked against each
other. Define a **weighted score out of 100%** — the weights must sum to
100, and each component needs a precise sub-formula so it's unambiguous how
to compute it:

```markdown
## Ranking Rules

### Rank Score

Score =
40% Trendline Quality
+
25% Sector Strength
+
20% Volume Growth
+
15% RSI Closeness To 50

Where:

RSI Score = 100 - abs(RSI - 50)

Higher score is better.
```

Every weighted component should have a "Where: ... Score = ..." definition
like the RSI one above, otherwise Gemini has to guess how to translate it
into a 0–100 number.

### 5. Output Columns

List exactly what you want to see in the final report, plus how to sort and
how many results to keep:

```markdown
## Output Columns

Return:

- Symbol
- Company Name
- Sector
- Current Price
- RSI(14)
- Sector Rank
- Rank Score

Sort:

Rank Score DESC

Limit:

Top 20 Stocks
```

## Router strategies (switching between strategies by market regime)

Instead of one strategy, `rules.md` can route between several saved
strategies. `generate_screener.py` switches to router mode when `rules.md`
contains a `## Referenced Strategies` section:

```markdown
## Referenced Strategies
- Trendline: ../Rules_backup/<trendline file>.md
- Breakout: ../Rules_backup/<breakout file>.md

### Default Strategy: Trendline

## Routing Rules
Use Breakout when MarketBreadth is above 60, otherwise Trendline.
```

- Each `- Key: path` entry is compiled separately into
  `generated_strategies/<Key>.py`. Paths are relative to the folder you run
  the script from, and every file must exist.
- `### Default Strategy:` is optional. If you set it, it must be one of the
  keys, and it is used as the fallback.
- `## Routing Rules` must be the last section. Gemini turns it into a
  `select_strategy(market_breadth)` function.
- The resulting `generated_rules.py` exposes the same `evaluate_stock(...)`
  interface as a single strategy, so the screener and backtester work
  unchanged.

## Tips for writing good rules

- **Be numeric, not vibes-based.** "Volume should be picking up" is
  ambiguous; "Volume[-1] > Volume[-2] AND Volume[-2] > Volume[-3]" isn't.
- **One condition per line**, joined with `AND`/`OR` — makes it trivial for
  the generator (and you) to see exactly what's being checked.
- **State the weight breakdown for scoring explicitly**, and make sure the
  percentages add up to 100%.
- **Call out missing-data behavior.** If volume or RSI can't be computed
  for a stock (too little history, delisted, etc.), say what should happen
  (usually: reject it, don't crash).
- **Change one section at a time.** After editing `rules.md`, re-run
  `generate_screener.py` and skim the diff in `generated_rules.py` before
  trusting it — treat the AI output as a draft, not gospel.
- **Keep it to what's computable from price, volume, sector and the annual
  fundamentals above.** Anything else (quarterly results, news, options
  flow) isn't available to the screener and will produce unreliable
  generated code.

## Full example

See [`rules.md`](rules.md) in this directory for the current, working
strategy that follows every convention above (currently a breakout
momentum strategy, with a Strategy Rationale section documenting how and
why it evolved through several backtested iterations). Copy its structure
when starting a new strategy — swap out the rules, weights, and output
columns, but keep the same sections and level of precision. Previous
strategy versions are kept in [`Rules_backup/`](../Rules_backup/) for
reference or restoring via the Backtest tab's dropdown.

## Common Method Library

Generated strategies share verified helper functions from
[`common_methods/`](common_methods/) (pivot detection, rising-trendline
fitting, pandas_ta column selection, liquidity and sector-rank checks, …).
When `generate_screener.py` compiles `rules.md`, Gemini is shown the
library's catalog and must call these methods instead of re-implementing
them, so the same rule compiles to the same logic every time.

- **New methods are added automatically** when Gemini proposes reusable
  logic that isn't in the library yet, but only after
  [`method_library.py`](method_library.py)'s checks pass: one documented
  function per file, allowed imports only (numpy, pandas, pandas_ta, scipy,
  math), and a smoke test of the full strategy on cached price data. If the
  checks fail twice, the method is pasted into that strategy's own code
  instead and the library is left untouched.
- **Strategy code may not contain helper functions or for/while loops.**
  Any algorithm has to live in the library. When Gemini's code works but
  keeps a loop inline, one extra focused call asks it to move that loop
  into a library method. The refactor is accepted only if the strategy
  returns identical results before and after on cached data; otherwise
  the working original is kept as-is. Broken code gets one full retry.
  The run log lists the methods reused and added.
- **Methods are immutable.** Never edit a saved method file - old
  strategies and backtests depend on its exact behaviour. To change one,
  add a new file with a new name (e.g. `find_rising_trendline_v2.py`, one
  function with the same name as the file and a docstring).
- Spell out precise algorithms in `rules.md` exactly as before - the
  library only changes how they are implemented, not what you specify.
  Give exact ranges (e.g. "positions `T-90` to `T-4` inclusive, where
  `T` is today's row") rather than phrases like "the last 90 days" -
  Gemini can read a loose phrase differently on each compile, which
  silently changes which trades the strategy takes.
- India only for now: the US side (`Strategies/US/`) still generates
  everything inline.
