import ast
import json
import os
import re
import sys
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from google import genai
# pyrefly: ignore [missing-import]
from google.genai import types
from pydantic import BaseModel

import method_library

load_dotenv()

MODEL = 'gemini-3.1-flash-lite'
RETRY_TEMPERATURE = 0.4


class _NewMethod(BaseModel):
    name: str
    code: str


class _StrategyOutput(BaseModel):
    strategy_code: str
    new_methods: list[_NewMethod]

EVALUATE_STOCK_PROMPT_TEMPLATE = """
You are an expert quantitative developer.

Generate production-ready Python code.

The generated file must contain:

1. All necessary imports.
2. A function:

def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth, momentum_ranks=None, fundamentals=None):

Where market_breadth (float, 0-100) is the percentage of the entire stock
universe currently trading above its own 50-day moving average, computed
once per day across all stocks (not specific to this symbol). It is a
broad market regime signal - a stand-in for a Nifty benchmark index, since
no external index data is available. If the RULES below define a market
breadth filter, implement it using this parameter directly - do not attempt
to compute breadth yourself from `df` (a single stock's own data cannot
tell you about the whole market).

<<<<<<< Updated upstream
The generated signature is exactly
`evaluate_stock(symbol, df, universe, sector_ranks, market_breadth, momentum_ranks=None, fundamentals=None)`
- always keep BOTH optional parameters, even if the rules use neither, and
never reassign or shadow them (e.g. `momentum_ranks = None`).
=======
Always use exactly that signature, with both optional parameters, even if
RULES use only one of them (or neither).

>>>>>>> Stashed changes
`momentum_ranks` maps symbol -> this stock's cross-sectional "12-1"
momentum percentile (float in (0, 100], 100 = strongest, near 0 =
weakest): its return from 252 trading days ago to 21 trading days ago,
ranked against every other stock in the universe that day. Read it with
`(momentum_ranks or {{}}).get(symbol)`; it can be None (the dict itself, or
a symbol with too little history) - treat None as failing any rule that
uses it. If RULES refer to a momentum rank or percentile across stocks,
use this parameter - never try to compute a cross-stock ranking from `df`,
which only holds this one stock.

`fundamentals` maps symbol -> dict of annual company fundamentals as they
were publicly known on the day of the last row of `df` (point-in-time; a
fiscal year only counts once its results were due). Read this stock's entry
with `(fundamentals or {{}}).get(symbol)`. The entry is missing (None) when
no data exists - then every fundamentals rule FAILS for this stock. Keys
(any value may be None, which also means the rule fails):
  - "latest_fy": str, ISO date of the latest public fiscal year end
  - "positive_eps_years": int, consecutive fiscal years with EPS > 0,
    counting back from the latest one
  - "eps": float, latest full-year EPS in Rs
  - "eps_cagr_3y": float, 3-year EPS CAGR as a fraction (0.15 = 15%)
  - "sales_cagr_3y": float, 3-year sales CAGR as a fraction
  - "roe": float, return on equity as a fraction
  - "de": float, debt/equity; None for banks and other financials
  - "is_financial": bool, True for banks / NBFCs / insurers
  - "pe": float, today's close / latest EPS (None if EPS <= 0)
  - "peg": float, pe / (eps_cagr_3y * 100) (None if growth <= 0)
Never compute fundamentals yourself from `df` - only `fundamentals` has them.

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

Output format:

Return a JSON object with exactly two fields:
- "strategy_code": the complete Python module source as a string (valid
  Python only - no markdown fences, no explanations).
- "new_methods": a list (usually empty) of {{"name": str, "code": str}}
  objects - new reusable methods for the Common Method Library, described
  below.

Common Method Library:

Verified, reusable helper functions are importable in strategy_code with
`from common_methods import <name>`. The current library:

{common_methods_catalog}

Library rules:
- If a library method implements logic RULES needs, you MUST call it
  instead of re-implementing that logic inline - even if RULES describes
  the algorithm step by step, as long as the method's docstring matches
  it. Pass the thresholds/parameters RULES specifies as arguments.
- If RULES needs logic that is reusable across strategies (indicator math,
  pivot/pattern/trendline detection, a generic filter parameterised by
  thresholds) and no library method covers it, write it as a new method in
  "new_methods" and import it in strategy_code via
  `from common_methods import <name>`. Do not also define it inside
  strategy_code.
- strategy_code must define ONLY evaluate_stock (no other functions) and
  must contain NO `for` or `while` loops. Every helper and every iterative
  algorithm - walking bars, scanning pivots, fitting or validating lines,
  counting streaks or touches - must be a library method: call an
  existing one, or write a new one in "new_methods". Simple list/dict
  comprehensions for glue (e.g. collecting pivot values) are fine. This is
  checked automatically and answers that break it are rejected.
- Strategy-specific glue stays in strategy_code: the concrete thresholds,
  rule ordering, FailedRules wording, scoring weights and Details fields.
  Never bake a strategy's specific thresholds into a new method - make
  them parameters.
- Each new method's "code" is a standalone module: its imports plus
  exactly ONE top-level function whose name equals "name" (snake_case, not
  already in the library). It must have a docstring describing args,
  return value and edge-case behaviour, must never raise (return None /
  False / empty on bad or insufficient data), and may import only numpy,
  pandas, pandas_ta, scipy, math and common_methods. No file, network or
  OS access.
- Don't wrap a single pandas_ta call in a new method - call pandas_ta
  directly (with ta_column for column selection). New methods are for
  real algorithms.

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
  arithmetic condition - implement it fully and faithfully to the exact
  algorithm RULES specifies, but do so THROUGH THE COMMON METHOD LIBRARY:
  call the existing library method whose docstring matches that algorithm
  (passing RULES' parameters), or, if none matches, write the algorithm as
  a new method in "new_methods". Never write it out inline in
  strategy_code. A fake/approximated value that happens to make the code
  run is worse than an honest failure.
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

EXTRACT_METHODS_PROMPT_TEMPLATE = """
You are an expert quantitative developer.

Below is a WORKING Python module defining
evaluate_stock(symbol, df, universe, sector_ranks, market_breadth, momentum_ranks=None, fundamentals=None).
Keep that exact signature.
It is correct, but it breaks one structural rule:

{error}

Your only task is a pure refactor: move every helper function and every
for/while loop out of the module into the Common Method Library, WITHOUT
changing behaviour in any way. For every possible input, the refactored
evaluate_stock must return exactly the same Passed, ClosenessScore,
FailedRules (same wording) and Details as the original. This is verified
automatically on real data, and any difference rejects your answer.

How:
- For each loop/helper, reuse a library method from the catalog below ONLY
  if it computes exactly the same thing for every input. Otherwise write a
  new method in "new_methods" that does exactly what the loop/helper does,
  with the strategy's specific numbers passed in as parameters.
- In strategy_code, replace the loop/helper with a call to that method,
  imported via `from common_methods import <name>`. Keep everything else
  in the module unchanged.
- strategy_code must define only evaluate_stock and contain no for/while
  loops. Simple comprehensions are fine.
- Each new method's "code" is a standalone module: its imports plus exactly
  ONE top-level function named "name" (snake_case, not already in the
  library) with a docstring describing args, return value and edge cases.
  It must never raise (return None / False / empty on bad input) and may
  import only numpy, pandas, pandas_ta, scipy, math and common_methods.
  Give it a general, descriptive name - it will be reused by other
  strategies.

Return a JSON object with exactly two fields: "strategy_code" (the full
refactored module as a string, no markdown fences) and "new_methods" (a
list of {{"name": str, "code": str}}).

Common Method Library catalog:

{common_methods_catalog}

ORIGINAL MODULE:

{strategy_code}
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
Nifty benchmark index, since no external index data is available).

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
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
        )
    )
    return _strip_code_fence(response.text)


def _generate_strategy_output(client, prompt, temperature=0.0):
    """Returns (strategy_code, new_methods) from Gemini's structured JSON."""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=_StrategyOutput,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
    )
    data = json.loads(response.text)
    new_methods = [
        {"name": m["name"].strip(), "code": _strip_code_fence(m["code"]) + "\n"}
        for m in data.get("new_methods") or []
    ]
    return _strip_code_fence(data["strategy_code"]) + "\n", new_methods


def _library_imports(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()
    return {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "common_methods"
        for alias in node.names
    }


EVALUATE_STOCK_ARGS = ["symbol", "df", "universe", "sector_ranks", "market_breadth", "momentum_ranks", "fundamentals"]
<<<<<<< Updated upstream


def _check_signature(tree):
    """Rejects an evaluate_stock that doesn't take exactly the six expected
    parameters with momentum_ranks=None and fundamentals=None - callers pass
    them by keyword, so a missing or misnamed parameter would otherwise only
    fail at run time."""
=======
EVALUATE_STOCK_SIGNATURE = (
    "def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth, momentum_ranks=None, fundamentals=None)"
)


def _check_signature(tree):
    """Rejects an evaluate_stock that doesn't take exactly the expected
    parameters, with both optional inputs defaulting to None - callers pass
    those by keyword, so a missing or misnamed parameter would otherwise
    only fail at run time."""
>>>>>>> Stashed changes
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "evaluate_stock"]
    if not funcs:
        return "strategy_code does not define a top-level evaluate_stock function"
    args = funcs[0].args
    names = [a.arg for a in args.args]
    defaults_ok = len(args.defaults) == 2 and all(
        isinstance(d, ast.Constant) and d.value is None for d in args.defaults
    )
    if names != EVALUATE_STOCK_ARGS or not defaults_ok or args.vararg or args.kwarg or args.kwonlyargs:
<<<<<<< Updated upstream
        return (
            "evaluate_stock must have exactly this signature: "
            "def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth, momentum_ranks=None, fundamentals=None)"
        )
=======
        return f"evaluate_stock must have exactly this signature: {EVALUATE_STOCK_SIGNATURE}"
>>>>>>> Stashed changes
    return None


def _check_output(strategy_code, new_methods):
    """Checks one Gemini answer. Returns (error, methods_ok, ran_cleanly):
    - error: why the answer as a whole is rejected, or None if it passes.
    - ran_cleanly: the strategy passed the smoke test, so any error is only
      a library-structure rule (helper functions / loops), not broken code.
    - methods_ok: True when the proposed new methods are safe to keep even
      if the answer is rejected - every method passed its static checks AND
      the strategy ran cleanly with them in the smoke test. Rejections for
      strategy structure (helper functions, leftover loops) don't stop the
      smoke test, so a good method isn't lost because of an unrelated loop."""
    known = set(method_library.list_methods())
    for m in new_methods:
        error = method_library.validate_new_method(m["name"], m["code"], known)
        if error:
            return error, False, False
        known.add(m["name"])
    try:
        tree = ast.parse(strategy_code)
    except SyntaxError as e:
        return f"strategy_code has a syntax error: {e}", False, False
    missing = _library_imports(strategy_code) - known
    if missing:
        return f"strategy_code imports {sorted(missing)} from common_methods, but no such library or new method exists", False, False
    signature_error = _check_signature(tree)
    if signature_error:
        return signature_error, False, False

    smoke_error = method_library.smoke_test(strategy_code, new_methods)
    ran_cleanly = smoke_error is None
    methods_ok = bool(new_methods) and ran_cleanly

    helpers = sorted(
        n.name for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name != "evaluate_stock"
    )
    if helpers:
        return (
            f"strategy_code defines helper function(s) {helpers}. strategy_code may define only "
            "evaluate_stock - move each helper into new_methods (one method per entry, with a docstring) "
            "and import it with `from common_methods import ...`."
        ), methods_ok, ran_cleanly
    loops = sorted(n.lineno for n in ast.walk(tree) if isinstance(n, (ast.For, ast.AsyncFor, ast.While)))
    if loops:
        return (
            f"strategy_code contains for/while loops (lines {loops}). Move each iterative algorithm "
            "into a library method - reuse an existing one from the catalog or add it to new_methods."
        ), methods_ok, ran_cleanly
    return smoke_error, methods_ok, ran_cleanly


def _extract_methods(client, strategy_code, error):
    """Asks Gemini to move a working strategy's inline loops/helpers into
    library methods. Accepted only if the refactor passes every check AND
    returns identical results to the original on cached data. Returns
    (refactored_code or None, saved method names, reason it failed)."""
    prompt = EXTRACT_METHODS_PROMPT_TEMPLATE.format(
        error=error,
        common_methods_catalog=method_library.build_catalog(),
        strategy_code=strategy_code,
    )
    try:
        new_code, new_methods = _generate_strategy_output(client, prompt)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        return None, [], f"invalid JSON: {e}"
    check_error, _, _ = _check_output(new_code, new_methods)
    if check_error:
        return None, [], check_error
    same_error = method_library.equivalence_test(strategy_code, new_code, new_methods)
    if same_error:
        return None, [], same_error
    try:
        method_library.save_methods(new_methods)
    except RuntimeError as e:
        return None, [], str(e)
    return new_code, [m["name"] for m in new_methods], None


def generate_evaluate_stock_code(client, rules_content):
    """Generates a module's worth of code implementing a single strategy's
    evaluate_stock(symbol, df, universe, sector_ranks, market_breadth, momentum_ranks=None, fundamentals=None) from
    its rules.md content. Used both for a normal single-strategy rules.md
    and, once per referenced file, when compiling a router (see
    generate_router).

    The strategy may import from the Common Method Library (common_methods/).
    A proposed method is added to the library once it passes its static
    checks and the strategy runs cleanly with it. If the code works but
    keeps a loop/helper inline, one focused extraction call moves it into
    the library, accepted only if results are provably unchanged (see
    _extract_methods). Broken answers get one corrective retry; methods
    that never pass are inlined into the returned code instead, so the run
    isn't blocked and the library stays clean."""
    existing = set(method_library.list_methods())

    def build_prompt():
        return EVALUATE_STOCK_PROMPT_TEMPLATE.format(
            rules_content=rules_content,
            common_methods_catalog=method_library.build_catalog(),
        )

    base_prompt = build_prompt()
    prompt = base_prompt
    added = []
    last = None
    for attempt in range(2):
        try:
            # At temperature 0 a retry just repeats the rejected answer, so the
            # corrective retry samples a little more freely.
            temperature = 0.0 if attempt == 0 else RETRY_TEMPERATURE
            strategy_code, new_methods = _generate_strategy_output(client, prompt, temperature)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            error = f"response was not valid JSON in the required format: {e}"
            print(f"Attempt {attempt + 1}: {error}")
            prompt = base_prompt + f"\n\nYOUR PREVIOUS ANSWER WAS REJECTED: {error}\nReturn the same JSON format, corrected."
            continue

        error, methods_ok, ran_cleanly = _check_output(strategy_code, new_methods)
        saved_now = []
        if methods_ok:
            try:
                method_library.save_methods(new_methods)
                saved_now = [m["name"] for m in new_methods]
                added += saved_now
            except RuntimeError as e:
                error = error or str(e)

        reused = sorted(_library_imports(strategy_code) & existing)
        if error is None:
            print(f"Common methods reused: {', '.join(reused) or 'none'}")
            print(f"Common methods added: {', '.join(added) or 'none'}")
            return strategy_code

        if ran_cleanly and error.startswith("strategy_code "):
            # The code works and only kept a loop/helper inline. A narrow
            # "move this into the library" task succeeds far more often than
            # regenerating the whole strategy, and is proven not to change
            # behaviour before it's accepted.
            print(f"Attempt {attempt + 1} works but {error[len('strategy_code '):].split('.')[0]} - extracting into the library...")
            extracted, extracted_names, why = _extract_methods(client, strategy_code, error)
            added += extracted_names
            final_code = extracted or strategy_code
            print(f"Common methods reused: {', '.join(sorted(_library_imports(final_code) & existing)) or 'none'}")
            print(f"Common methods added: {', '.join(added) or 'none'}")
            if extracted:
                return extracted
            print(f"Note: kept that logic inline - extraction didn't pass ({why}). The strategy passed its smoke test.")
            return strategy_code

        print(f"Attempt {attempt + 1} rejected: {error}")
        if saved_now:
            print(f"Kept anyway (passed their own checks): {', '.join(saved_now)}")
            base_prompt = build_prompt()
        unsaved = [m for m in new_methods if m["name"] not in saved_now]
        # A retry can fix the rule it was told about but break the code, so
        # never let an answer that failed the smoke test replace one that ran.
        if last is None or ran_cleanly or not last[3]:
            last = (strategy_code, unsaved, reused, ran_cleanly)
        saved_note = (
            f"\nThese methods from your previous answer passed and are now in the library "
            f"(listed in the catalog above): {saved_now}. Import them with `from common_methods import ...` "
            "- do not re-propose them in new_methods."
        ) if saved_now else ""
        prompt = base_prompt + (
            f"\n\nYOUR PREVIOUS ANSWER WAS REJECTED BY AUTOMATED CHECKS:\n{error}{saved_note}\n"
            "Return a corrected answer in the same JSON format."
        )

    if last is None:
        raise RuntimeError("Gemini did not return valid JSON after 2 attempts.")

    strategy_code, new_methods, reused, ran_cleanly = last
    print(f"Common methods reused: {', '.join(reused) or 'none'}")
    print(f"Common methods added: {', '.join(added) or 'none'}")
    if not new_methods:
        if ran_cleanly:
            print("Note: some logic was kept inline instead of in the library (see above). The strategy passed its smoke test.")
        else:
            print("Warning: strategy failed its smoke test twice (see above) - writing it anyway, review it before trusting results.")
        return strategy_code
    print(f"Warning: {[m['name'] for m in new_methods]} didn't pass - inlining them into the strategy instead of the library.")
    try:
        return method_library.inline_methods(strategy_code, new_methods)
    except SyntaxError:
        print("Warning: proposed methods don't parse - writing the strategy without them, review it before trusting results.")
        return strategy_code


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

from strategy_runtime import call_evaluate as _call_evaluate

{import_lines}

{select_strategy_code}

_STRATEGIES = {{{dict_entries}}}
_FALLBACK_KEY = "{fallback_key}"


def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth, momentum_ranks=None, fundamentals=None):
    try:
        active_key = select_strategy(market_breadth)
        if active_key not in _STRATEGIES:
            active_key = _FALLBACK_KEY
    except Exception:
        active_key = _FALLBACK_KEY

<<<<<<< Updated upstream
    sub = _STRATEGIES[active_key].evaluate_stock
    result = _call_evaluate(
        sub, symbol, df, universe, sector_ranks, market_breadth,
=======
    result = _call_evaluate(
        _STRATEGIES[active_key].evaluate_stock, symbol, df, universe, sector_ranks, market_breadth,
>>>>>>> Stashed changes
        momentum_ranks=momentum_ranks, fundamentals=fundamentals,
    )
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
