"""Runs one stock through several saved strategies at once (Multi-Strategy
tab). Each strategy is a rules.md backup group (see backup_utils) - its
newest version is compiled to its own evaluate_stock() module under
data/multi_strategy/code/, keyed by a hash of the rules text, so this never
touches the live generated_rules.py / rules.md the screener and backtester
use. Code generation goes through generate_screener's own prompt, so a
strategy behaves here exactly as it does once loaded on the Rules tab.

Sector rank and market breadth are universe-wide inputs every strategy's
evaluate_stock() takes. They are built once from the cached stock universe
and reused for the rest of the day (see get_market_context), not refetched
per stock.
"""

import datetime
import hashlib
import importlib.util
import json
import os
import random
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from backup_utils import declared_strategy_name, group_backups, list_backups
from constants import BACKUP_DIR, DATA_DIR, RULES_PATH, UNIVERSE_CACHE_PATH
from nse_utils import calculate_market_breadth, calculate_sector_strength, fetch_stock_history

MULTI_DIR = os.path.join(DATA_DIR, "multi_strategy")
CODE_DIR = os.path.join(MULTI_DIR, "code")
CONTEXT_PATH = os.path.join(MULTI_DIR, "market_context.json")
LIVE_KEY = "__live__"
HISTORY_DAYS = 400
MIN_ROWS = 60
# Where each shared/per-strategy phase puts a strategy's progress bar.
PCT_HISTORY = 8
PCT_CONTEXT_END = 65
PCT_COMPILE = 68
PCT_EVALUATE = 90
FETCH_WORKERS = 5
STAGGER_SECONDS = (0.1, 0.5)

_context_lock = threading.Lock()
_codegen_lock = threading.Lock()


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _prepare_df(raw):
    """Same column shaping stock_screener._fetch_one applies."""
    df = raw.sort_values(by="DATE").set_index("DATE")
    df = df.rename(columns={
        "OPEN": "open", "HIGH": "high", "LOW": "low", "CLOSE": "close",
        "VOLUME": "volume", "DELIVERY %": "delivery_pct",
    })
    if "delivery_pct" not in df.columns:
        df["delivery_pct"] = float("nan")
    return df


def fetch_history(symbol):
    to_date = datetime.date.today()
    from_date = to_date - datetime.timedelta(days=HISTORY_DAYS)
    raw = fetch_stock_history(symbol=symbol, from_date=from_date, to_date=to_date, series="EQ")
    if raw is None or raw.empty:
        return None
    return _prepare_df(raw)


def load_universe():
    if not os.path.exists(UNIVERSE_CACHE_PATH):
        return {}
    return json.loads(_read(UNIVERSE_CACHE_PATH)).get("universe", {})


def _fetch_for_context(symbol):
    time.sleep(random.uniform(*STAGGER_SECONDS))
    try:
        df = fetch_history(symbol)
    except Exception:
        return symbol, None
    return symbol, df if df is not None and len(df) > 100 else None


def build_market_context(universe, on_progress=None):
    data = {}
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as executor:
        futures = [executor.submit(_fetch_for_context, s) for s in universe]
        for done, future in enumerate(as_completed(futures), start=1):
            symbol, df = future.result()
            if on_progress:
                on_progress(done, len(futures))
            if df is not None:
                data[symbol] = df
    context = {
        "date": datetime.date.today().isoformat(),
        "stocks_used": len(data),
        "universe_size": len(universe),
        "sector_ranks": calculate_sector_strength(data, universe),
        "market_breadth": calculate_market_breadth(data),
    }
    os.makedirs(MULTI_DIR, exist_ok=True)
    with open(CONTEXT_PATH, "w", encoding="utf-8") as f:
        json.dump(context, f)
    return context


def read_market_context():
    """Today's cached context, or None if missing/stale."""
    if not os.path.exists(CONTEXT_PATH):
        return None
    try:
        context = json.loads(_read(CONTEXT_PATH))
    except (OSError, ValueError):
        return None
    return context if context.get("date") == datetime.date.today().isoformat() else None


def get_market_context(universe, refresh=False, on_progress=None):
    with _context_lock:
        if not refresh:
            context = read_market_context()
            if context is not None:
                return context
        return build_market_context(universe, on_progress=on_progress)


def list_strategies():
    """One entry per rules.md backup group (newest version each), plus the
    live rules.md. The live file usually duplicates a group's newest backup
    - it is only listed if its content is not identical to one."""
    groups = group_backups(list_backups(BACKUP_DIR))
    strategies = []
    newest_contents = set()
    for key, versions in groups.items():
        content = _read(os.path.join(BACKUP_DIR, versions[0]))
        newest_contents.add(content.strip())
        is_router = "## Referenced Strategies" in content
        strategies.append({
            "key": key,
            "name": declared_strategy_name(content) or key,
            "file": versions[0],
            "versions": len(versions),
            "supported": not is_router,
            "unsupported_reason": "Router strategies (Referenced Strategies) are not supported here yet." if is_router else None,
        })
    if os.path.exists(RULES_PATH):
        live = _read(RULES_PATH)
        if live.strip() and live.strip() not in newest_contents:
            strategies.insert(0, {
                "key": LIVE_KEY,
                "name": (declared_strategy_name(live) or "Live rules.md") + " (unsaved live)",
                "file": "rules.md",
                "versions": 1,
                "supported": "## Referenced Strategies" not in live,
                "unsupported_reason": None,
            })
    return strategies


def _rules_for_key(key):
    if key == LIVE_KEY:
        return _read(RULES_PATH)
    groups = group_backups(list_backups(BACKUP_DIR))
    if key not in groups:
        raise ValueError(f"Unknown strategy: {key}")
    return _read(os.path.join(BACKUP_DIR, groups[key][0]))


def _code_path(rules_content):
    digest = hashlib.sha256(rules_content.encode("utf-8")).hexdigest()[:16]
    return digest, os.path.join(CODE_DIR, f"strategy_{digest}.py")


def _load_module(rules_content, on_compile=None):
    digest, path = _code_path(rules_content)
    with _codegen_lock:
        if not os.path.exists(path):
            if on_compile:
                on_compile()
            import generate_screener  # deferred: pulls in the Gemini client

            try:
                client = generate_screener._client()
            except SystemExit:
                raise RuntimeError("GEMINI_API_KEY is not set - needed to compile a strategy not yet cached.")
            for attempt in range(3):  # Gemini 503s under load are transient
                try:
                    code = generate_screener.generate_evaluate_stock_code(client, rules_content)
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(3 * (attempt + 1))
            os.makedirs(CODE_DIR, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
    spec = importlib.util.spec_from_file_location(f"multi_strategy_{digest}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _json_safe(value):
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and value != value:
        return None
    if isinstance(value, (int, float, str, bool)) or value is None:
        return value
    return str(value)


def _run_one(key, symbol, df, universe, sector_ranks, breadth, emit=lambda pct, stage: None):
    try:
        rules = _rules_for_key(key)
        if "## Referenced Strategies" in rules:
            return {"key": key, "status": "error", "error": "Router strategies are not supported here yet."}
        if not os.path.exists(_code_path(rules)[1]):
            emit(PCT_COMPILE, "Waiting to compile rules")
        module = _load_module(rules, on_compile=lambda: emit(PCT_COMPILE + 3, "Compiling rules with Gemini"))
        emit(PCT_EVALUATE, "Evaluating rules")
        result = module.evaluate_stock(symbol, df, universe, sector_ranks, breadth)
    except Exception as e:
        return {"key": key, "status": "error", "error": str(e)}

    failed = [str(r) for r in result.get("FailedRules", [])]
    passed = bool(result.get("Passed"))
    # Same near-miss definition backtest.py uses: exactly one rule failed.
    status = "buy" if passed else "near" if len(failed) == 1 else "none"
    return {
        "key": key,
        "status": status,
        "closeness_score": _json_safe(result.get("ClosenessScore")),
        "failed_rules": failed,
        "details": {k: _json_safe(v) for k, v in (result.get("Details") or {}).items()},
    }


def run_stock_events(symbol, keys, refresh_context=False):
    """Generator of progress events for one run, ending with a "result"
    (or "error") event. Phases shared by every strategy (price history,
    market context) report the same percentage for all of them; compiling
    and evaluating are reported per strategy as each one reaches them."""
    events = queue.Queue()

    def emit_all(pct, stage):
        for k in keys:
            events.put({"type": "progress", "key": k, "pct": pct, "stage": stage})

    def work():
        try:
            clean = symbol.strip().upper()
            emit_all(2, "Fetching price history")
            df = fetch_history(clean)
            if df is None or len(df) < MIN_ROWS:
                raise ValueError(f"Not enough price history for {clean} (need {MIN_ROWS}+ trading days).")
            emit_all(PCT_HISTORY, "Loading market context")

            universe = load_universe()

            def on_context(done, total):
                pct = PCT_HISTORY + (PCT_CONTEXT_END - PCT_HISTORY) * done / total
                emit_all(round(pct, 1), f"Building market context ({done}/{total} stocks)")

            context = get_market_context(universe, refresh=refresh_context, on_progress=on_context)
            emit_all(PCT_CONTEXT_END, "Market context ready")

            def run_key(k):
                def emit(pct, stage):
                    events.put({"type": "progress", "key": k, "pct": pct, "stage": stage})
                result = _run_one(k, clean, df, universe, context["sector_ranks"], context["market_breadth"], emit)
                events.put({"type": "progress", "key": k, "pct": 100, "stage": "Done" if result["status"] != "error" else "Failed"})
                return result

            with ThreadPoolExecutor(max_workers=max(1, min(len(keys), 4))) as executor:
                results = list(executor.map(run_key, keys))

            events.put({"type": "result", "run": {
                "symbol": clean,
                "last_close": float(df["close"].iloc[-1]),
                "last_date": df.index[-1].date().isoformat(),
                "in_universe": clean in universe,
                "market_breadth": context["market_breadth"],
                "context_date": context["date"],
                "results": results,
            }})
        except ValueError as e:
            events.put({"type": "error", "status": 404, "message": str(e)})
        except Exception as e:
            events.put({"type": "error", "status": 502, "message": f"Could not fetch data for {symbol.strip().upper()}: {e}"})

    threading.Thread(target=work, daemon=True).start()
    while True:
        event = events.get()
        yield event
        if event["type"] in ("result", "error"):
            return


def run_stock(symbol, keys, refresh_context=False):
    """Blocking form of run_stock_events - returns the final run payload."""
    for event in run_stock_events(symbol, keys, refresh_context):
        if event["type"] == "result":
            return event["run"]
        if event["type"] == "error":
            if event["status"] == 404:
                raise ValueError(event["message"])
            raise RuntimeError(event["message"])
