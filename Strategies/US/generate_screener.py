import os
import re
import sys
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from google import genai
# pyrefly: ignore [missing-import]
from google.genai import types

load_dotenv()

EVALUATE_STOCK_PROMPT_TEMPLATE = """
You are an expert quantitative developer.

Generate production-ready Python code.

The generated file must contain:

1. All necessary imports.
2. A function:

def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):

Where market_breadth (float, 0-100) is the percentage of the entire stock
universe currently trading above its own 50-day moving average, computed
once per day across all stocks (not specific to this symbol). It is a
broad market regime signal - a stand-in for an S&P 500 benchmark index, since
no external index data is available. If the RULES below define a market
breadth filter, implement it using this parameter directly - do not attempt
to compute breadth yourself from `df` (a single stock's own data cannot
tell you about the whole market).

3. The function must return:

return {{
    "Symbol": symbol,
    "Passed": bool,
    "ClosenessScore": float,
    "FailedRules": list,
    "Details": dict
}}

Definitions:

Passed:
- True only if ALL mandatory rules pass.
- False otherwise.

FailedRules:
- Human readable list of failed rules.

Examples:
[
    "RSI outside range (63.5)",
    "Sector rank 8 not in top 5",
    "Volume not increasing for last 3 sessions"
]

Details:
Store every calculated metric used, PLUS every field listed in RULES'
"Output Columns" section (if present), using that section's exact field
names as dict keys (spaces are fine in keys, e.g. "Ideal Entry Price Low").
Compute each Output Columns field exactly as defined in that section's
"Where:" formulas - do not omit a field because it isn't otherwise used by
a mandatory filter or the ranking score.

Example:
{{
    "RSI": 54.2,
    "SectorRank": 3,
    "TrendlineDistancePct": 1.8,
    "Volume1": 1200000,
    "Volume2": 1000000,
    "Volume3": 800000
}}

ClosenessScore:

Must be between 0 and 100. Implement it EXACTLY according to the "Ranking
Rules" / "Rank Score" section in RULES below - the specific factors,
weights, and per-factor scoring formulas are defined there, not here. Do
not substitute a different scoring scheme, and do not fall back to a
generic weighting if RULES defines its own. If RULES has no Ranking Rules
section at all, use a simple heuristic based on how close the stock came
to passing every mandatory rule.

Requirements:

- Use pandas_ta as ta.
- Handle missing data safely.
- Never throw exceptions.
- Return a valid dictionary even if a stock cannot be evaluated.
- Use helper functions when needed.
- Output ONLY valid Python code.
- No markdown.
- No explanations.

Critical implementation constraints:

- Never hardcode pandas_ta output column names (e.g. "BBL_20_2.0"). Column
  suffixes vary by pandas_ta version. Instead, select columns by prefix, e.g.:
  bb = ta.bbands(df['close'], length=20, std=2)
  lower_bb_col = next(c for c in bb.columns if c.startswith('BBL_'))
  lower_bb = bb[lower_bb_col].iloc[-1]
  Apply the same prefix-matching approach for any other multi-column
  pandas_ta indicator (MACD, Stochastic, ADX, etc.).
- Some pandas_ta indicators return a single-column pandas Series instead of
  a DataFrame (e.g. ta.rsi() with a single length). Never call `.columns` on
  the result without first checking `isinstance(result, pd.DataFrame)`.
  If it is a DataFrame, select the column by prefix as above; if it is a
  Series, use it directly. Apply this check for every pandas_ta call whose
  return type (Series vs DataFrame) is not certain.
- The top-level try/except in evaluate_stock must never swallow the error
  message. On exception, append f"Calculation error: {{e}}" (the actual
  exception text) to FailedRules, not a generic "Calculation error" string.
- `universe` maps symbol -> {{"Name": str, "Sector": str}} (capitalized keys).
  `sector_ranks` maps symbol -> int directly (NOT sector name -> int). To get
  a stock's sector rank, use `sector_ranks.get(symbol, 99)` directly - do NOT
  look up the stock's sector name first and then index sector_ranks by that
  name; sector_ranks is never keyed by sector name.
- Never substitute a fixed/hardcoded placeholder for something RULES asks
  you to compute (e.g. `dist_pct = 1.5  # placeholder`). If a rule requires
  nontrivial geometry or statistics - trendline/support-resistance fitting,
  regression, pivot/extrema detection, clustering, anything beyond a simple
  arithmetic condition - implement it fully using numpy/scipy/pandas, using
  the exact algorithm RULES specifies step by step if one is given. A
  fake/approximated value that happens to make the code run is worse than
  an honest failure.
- When a rule asks you to count matches, touches, or occurrences against a
  SPECIFIC set of points (e.g. "count how many pivot lows lie near this
  line" or "count occurrences among the values listed in step N"), count
  only against that exact set - never substitute a looser, easier-to-satisfy
  superset (e.g. checking every row in a dataframe instead of only the
  specific points named), even if it's simpler to implement. This silently
  weakens the rule and produces a different, more lenient strategy than the
  one specified.
- `df` is indexed by DATE, not by a plain 0..N-1 integer range. Never index
  a column by an integer position with bracket notation (e.g. `close[i]`,
  `low[j]`) - pandas looks that up as a LABEL, not a position, and raises a
  KeyError the moment `i` isn't literally a date in the index (which is
  every single row). Whenever a rule requires walking the data by integer
  position (pivot/extrema detection, a rolling window scan, "the day at
  index i", trendline fitting, etc.), first convert to a plain positional
  array with `.values` (e.g. `close = df['close'].values`) and index that,
  or use `.iloc[i]` on the original Series - never bracket-index the
  Series/DataFrame itself by an integer meant as a position.

RULES:

{rules_content}
"""

SELECT_STRATEGY_PROMPT_TEMPLATE = """
You are an expert quantitative developer.

Generate production-ready Python code.

The generated file must contain ONLY:

1. All necessary imports (if any - usually none are needed).
2. A single function:

def select_strategy(market_breadth):

Where market_breadth (float, 0-100) is the percentage of the entire stock
universe currently trading above its own 50-day moving average, computed
once per trading day (a broad market regime signal - a stand-in for a
S&P 500 benchmark index, since no external index data is available).

The function must return one of these exact string keys: {strategy_keys}

Implement the ROUTING RULES below EXACTLY, checked in the order written -
the first matching route's key wins. If none match, return the Default
Strategy's key. Do not invent thresholds or logic not stated below, and do
not substitute a different scheme.

Requirements:

- Never throw exceptions - if market_breadth is missing/invalid, fall back
  to the Default Strategy's key.
- Output ONLY valid Python code.
- No markdown.
- No explanations.

ROUTING RULES:

{routing_rules_content}
"""


def _client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not found.")
        print("Please create a .env file and add your API key: GEMINI_API_KEY=your_key")
        sys.exit(1)
    return genai.Client(api_key=api_key)


def _strip_code_fence(text):
    code = text.strip()
    if code.startswith("```python"):
        code = code[9:]
    if code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    return code.strip()


def _generate_from_prompt(client, prompt):
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
        )
    )
    return _strip_code_fence(response.text)


def generate_evaluate_stock_code(client, rules_content):
    """Generates a module's worth of code implementing a single strategy's
    evaluate_stock(symbol, df, universe, sector_ranks, market_breadth) from
    its rules.md content. Used both for a normal single-strategy rules.md
    and, once per referenced file, when compiling a router (see
    generate_router)."""
    prompt = EVALUATE_STOCK_PROMPT_TEMPLATE.format(rules_content=rules_content)
    return _generate_from_prompt(client, prompt)


def _sanitize_key(name):
    return re.sub(r"[^a-zA-Z0-9_]+", "_", name.strip()).strip("_") or "strategy"


def _parse_referenced_strategies(rules_content):
    """Parses the "## Referenced Strategies" section into an ordered
    {sanitized_key: path} dict from lines shaped like "- Key: path/to/file.md".
    Only lines within that section (up to the next "## " heading or "---")
    are considered."""
    match = re.search(
        r"##\s*Referenced Strategies\s*\n(.*?)(?=\n##\s|\n---|\Z)",
        rules_content, re.DOTALL,
    )
    if not match:
        return {}

    section = match.group(1)
    referenced = {}
    for line in section.splitlines():
        line_match = re.match(r"\s*-\s*([^:]+):\s*(.+?)\s*$", line)
        if line_match:
            key = _sanitize_key(line_match.group(1))
            path = line_match.group(2).strip()
            referenced[key] = path
    return referenced


def _extract_default_strategy_name(rules_content):
    match = re.search(r"###\s*Default Strategy:\s*(.+)", rules_content)
    return match.group(1).strip() if match else None


def _extract_routing_rules_section(rules_content):
    match = re.search(
        r"##\s*Routing Rules\s*\n(.*?)(?=\Z)",
        rules_content, re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def generate_router(client, rules_content):
    """Compiles a "router" rules.md (one containing a "## Referenced
    Strategies" section) into generated_rules.py: a per-referenced-strategy
    module under generated_strategies/, plus a Gemini-generated
    select_strategy(market_breadth) routing function, assembled with a
    hand-written (not Gemini-generated) evaluate_stock() dispatcher so the
    file exposes the exact same interface stock_screener.py/backtest.py
    already call for a normal single strategy."""
    referenced = _parse_referenced_strategies(rules_content)
    if not referenced:
        print("Error: '## Referenced Strategies' section found but no '- Key: path' entries parsed.")
        sys.exit(1)

    default_name = _extract_default_strategy_name(rules_content)
    default_key = _sanitize_key(default_name) if default_name else None
    if default_key and default_key not in referenced:
        print(f"Error: Default Strategy '{default_name}' is not one of the Referenced Strategies: {list(referenced.keys())}.")
        sys.exit(1)

    strategies_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_strategies")
    os.makedirs(strategies_dir, exist_ok=True)
    init_path = os.path.join(strategies_dir, "__init__.py")
    if not os.path.exists(init_path):
        open(init_path, "w", encoding="utf-8").close()

    for key, path in referenced.items():
        if not os.path.exists(path):
            print(f"Error: Referenced Strategies entry '{key}' points to '{path}', which does not exist.")
            sys.exit(1)

        print(f"Generating sub-strategy '{key}' from {path}...")
        with open(path, "r", encoding="utf-8") as f:
            sub_rules_content = f.read()
        sub_code = generate_evaluate_stock_code(client, sub_rules_content)
        with open(os.path.join(strategies_dir, f"{key}.py"), "w", encoding="utf-8") as f:
            f.write(sub_code)

    print("Generating routing logic from Routing Rules...")
    routing_rules_content = _extract_routing_rules_section(rules_content)
    select_prompt = SELECT_STRATEGY_PROMPT_TEMPLATE.format(
        strategy_keys=", ".join(f'"{k}"' for k in referenced),
        routing_rules_content=routing_rules_content,
    )
    select_strategy_code = _generate_from_prompt(client, select_prompt)

    import_lines = "\n".join(f"from generated_strategies import {key} as _s_{key}" for key in referenced)
    dict_entries = ", ".join(f'"{key}": _s_{key}' for key in referenced)
    fallback_key = default_key or next(iter(referenced))

    assembled = f'''"""Auto-generated router: compiled from rules.md's "Referenced Strategies"
and "Routing Rules" sections by generate_screener.py. Do not edit by hand -
edit rules.md and regenerate instead."""

{import_lines}

{select_strategy_code}

_STRATEGIES = {{{dict_entries}}}
_FALLBACK_KEY = "{fallback_key}"


def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):
    try:
        active_key = select_strategy(market_breadth)
        if active_key not in _STRATEGIES:
            active_key = _FALLBACK_KEY
    except Exception:
        active_key = _FALLBACK_KEY

    result = _STRATEGIES[active_key].evaluate_stock(symbol, df, universe, sector_ranks, market_breadth)
    result.setdefault("Details", {{}})["Active Strategy"] = active_key
    return result
'''

    with open("generated_rules.py", "w", encoding="utf-8") as f:
        f.write(assembled)

    print(f"Successfully generated generated_rules.py (router over {list(referenced.keys())})!")


def generate_rules():
    try:
        with open("rules.md", "r", encoding="utf-8") as f:
            rules_content = f.read()
    except FileNotFoundError:
        print("Error: rules.md not found in the current directory.")
        sys.exit(1)

    client = _client()

    if "## Referenced Strategies" in rules_content:
        generate_router(client, rules_content)
    else:
        print("Generating python screening logic from rules.md...")
        code = generate_evaluate_stock_code(client, rules_content)
        with open("generated_rules.py", "w", encoding="utf-8") as f:
            f.write(code)
        print("Successfully generated generated_rules.py!")


if __name__ == "__main__":
    generate_rules()
