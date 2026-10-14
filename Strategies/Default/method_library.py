"""Tooling for the Common Method Library (common_methods/): builds the
catalog shown to Gemini, validates methods Gemini proposes, smoke-tests a
generated strategy against cached price data, and saves accepted methods.

Library methods are immutable: save_methods() never overwrites a file, so a
strategy compiled today keeps behaving the same after the library grows."""

import ast
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager

if os.name == "nt":
    import msvcrt

    def _lock_file(f):
        # LK_LOCK gives up after ~10 s of retries, so keep retrying until
        # the other process releases the lock, matching flock's blocking wait.
        f.seek(0)
        while True:
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                return
            except OSError:
                continue

    def _unlock_file(f):
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl

    def _lock_file(f):
        fcntl.flock(f, fcntl.LOCK_EX)

    def _unlock_file(f):
        fcntl.flock(f, fcntl.LOCK_UN)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(APP_DIR, "common_methods")
CACHE_DIR = os.path.join(APP_DIR, "data", "backtest_cache")
LOCK_PATH = os.path.join(LIB_DIR, ".lock")

ALLOWED_IMPORTS = {"numpy", "pandas", "pandas_ta", "scipy", "math", "common_methods"}
FORBIDDEN_CALLS = {"open", "exec", "eval", "compile", "__import__", "input", "globals", "setattr", "delattr"}
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")

SMOKE_SYMBOLS = 20
SMOKE_ROWS = 300
SMOKE_TIMEOUT_SECONDS = 180


def list_methods():
    return sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(LIB_DIR)
        if f.endswith(".py") and not f.startswith("_")
    )


def build_catalog():
    """Signature + docstring of every library method, for the prompt."""
    entries = []
    for name in list_methods():
        with open(os.path.join(LIB_DIR, f"{name}.py"), "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        doc = ast.get_docstring(func) or ""
        indented_doc = "\n".join(f"    {line}" for line in doc.splitlines())
        entries.append(f"{name}({ast.unparse(func.args)})\n{indented_doc}")
    return "\n\n".join(entries) if entries else "(library is empty)"


def validate_new_method(name, code, existing=None):
    """Returns an error string, or None if the method is acceptable."""
    existing = set(list_methods()) if existing is None else existing
    if not NAME_RE.match(name or ""):
        return f"'{name}': name must be snake_case"
    if name in existing:
        return f"'{name}': already exists in the library - use it, or pick a new name (e.g. {name}_v2) if behaviour must differ"
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"'{name}': syntax error: {e}"

    funcs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if len(funcs) != 1 or funcs[0].name != name:
        return f"'{name}': must define exactly one top-level function named '{name}'"
    if not ast.get_docstring(funcs[0]):
        return f"'{name}': missing docstring"
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.Import, ast.ImportFrom)):
            return f"'{name}': only imports and the single function are allowed at top level"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            roots = [(node.module or "").split(".")[0]]
        else:
            roots = []
        for root in roots:
            if root not in ALLOWED_IMPORTS:
                return f"'{name}': import of '{root}' is not allowed (allowed: {sorted(ALLOWED_IMPORTS)})"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            return f"'{name}': call to '{node.func.id}' is not allowed"
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return f"'{name}': dunder attribute access ('{node.attr}') is not allowed"
    return None


_SMOKE_RUNNER = r'''
import glob, json, sys, traceback
import pandas as pd

cache_dir, n_symbols, n_rows = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
errors = []
try:
    import strategy_under_test as s
except Exception:
    print(json.dumps({"errors": ["import failed: " + traceback.format_exc(limit=3)]}))
    sys.exit(0)

files = sorted(glob.glob(cache_dir + "/*.csv"))
step = max(1, len(files) // n_symbols)
for path in files[::step][:n_symbols]:
    symbol = path.rsplit("/", 1)[-1].split("_")[0]
    df = pd.read_csv(path, parse_dates=["date"], index_col="date").tail(n_rows)
    try:
        r = s.evaluate_stock(symbol, df, {symbol: {"Name": symbol, "Sector": "Test"}}, {symbol: 3}, 55.0)
    except Exception as e:
        errors.append(f"{symbol}: raised {type(e).__name__}: {e}")
        continue
    if not isinstance(r, dict) or not {"Symbol", "Passed", "ClosenessScore", "FailedRules", "Details"} <= set(r):
        errors.append(f"{symbol}: returned an invalid result shape")
        continue
    calc = [x for x in r["FailedRules"] if "Calculation error" in str(x)]
    if calc:
        errors.append(f"{symbol}: {calc[0]}")
print(json.dumps({"errors": errors[:5], "error_count": len(errors)}))
'''


def smoke_test(strategy_code, new_methods):
    """Runs the strategy (with candidate methods added to a temp copy of the
    library) on cached symbols in a fresh interpreter, so the live,
    already-imported common_methods package is never touched. Returns an
    error string, or None on success."""
    if not glob.glob(os.path.join(CACHE_DIR, "*.csv")):
        return None  # no cached data on this machine - static checks only

    with tempfile.TemporaryDirectory() as tmp:
        lib_copy = os.path.join(tmp, "common_methods")
        shutil.copytree(LIB_DIR, lib_copy, ignore=shutil.ignore_patterns("__pycache__", ".lock"))
        for m in new_methods:
            with open(os.path.join(lib_copy, f"{m['name']}.py"), "w", encoding="utf-8") as f:
                f.write(m["code"])
        with open(os.path.join(tmp, "strategy_under_test.py"), "w", encoding="utf-8") as f:
            f.write(strategy_code)
        runner = os.path.join(tmp, "smoke_runner.py")
        with open(runner, "w", encoding="utf-8") as f:
            f.write(_SMOKE_RUNNER)

        try:
            proc = subprocess.run(
                [sys.executable, runner, CACHE_DIR, str(SMOKE_SYMBOLS), str(SMOKE_ROWS)],
                cwd=tmp, capture_output=True, text=True, timeout=SMOKE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return f"smoke test timed out after {SMOKE_TIMEOUT_SECONDS}s"

    try:
        result = json.loads(proc.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return f"smoke test crashed: {proc.stderr.strip()[-800:]}"
    if result["errors"]:
        return f"{result.get('error_count', len(result['errors']))} smoke-test failure(s), e.g.: " + "; ".join(result["errors"])
    return None


_EQUIV_RUNNER = r'''
import glob, json, math, sys, traceback
import pandas as pd

cache_dir, n_symbols, n_rows = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
try:
    import strategy_a as a, strategy_b as b
except Exception:
    print(json.dumps({"diffs": ["import failed: " + traceback.format_exc(limit=3)], "compared": 0}))
    sys.exit(0)

def key(r):
    score = r.get("ClosenessScore")
    score = None if score is None or (isinstance(score, float) and math.isnan(score)) else round(float(score), 6)
    return (bool(r.get("Passed")), score, [str(x) for x in r.get("FailedRules", [])])

files = sorted(glob.glob(cache_dir + "/*.csv"))
step = max(1, len(files) // n_symbols)
diffs, compared = [], 0
for path in files[::step][:n_symbols]:
    symbol = path.rsplit("/", 1)[-1].split("_")[0]
    full = pd.read_csv(path, parse_dates=["date"], index_col="date")
    for end in range(len(full), max(n_rows, len(full) - 1500), -60):
        df = full.iloc[:end].tail(n_rows)
        args = (symbol, df, {symbol: {"Name": symbol, "Sector": "Test"}}, {symbol: 3}, 55.0)
        try:
            ka, kb = key(a.evaluate_stock(*args)), key(b.evaluate_stock(*args))
        except Exception as e:
            diffs.append(f"{symbol}@{df.index[-1].date()}: raised {type(e).__name__}: {e}")
            continue
        compared += 1
        if ka != kb:
            diffs.append(f"{symbol}@{df.index[-1].date()}: before={ka} after={kb}")
print(json.dumps({"diffs": diffs[:5], "diff_count": len(diffs), "compared": compared}))
'''


def equivalence_test(code_before, code_after, new_methods):
    """Runs two versions of a strategy on the same cached data (many symbols
    x many historical dates) and checks they return identical Passed,
    ClosenessScore and FailedRules. Used to prove a refactor that moves
    logic into the library didn't change behaviour. Returns an error string,
    or None if they match everywhere."""
    if not glob.glob(os.path.join(CACHE_DIR, "*.csv")):
        return "no cached price data to compare on"

    with tempfile.TemporaryDirectory() as tmp:
        lib_copy = os.path.join(tmp, "common_methods")
        shutil.copytree(LIB_DIR, lib_copy, ignore=shutil.ignore_patterns("__pycache__", ".lock"))
        for m in new_methods:
            with open(os.path.join(lib_copy, f"{m['name']}.py"), "w", encoding="utf-8") as f:
                f.write(m["code"])
        for name, code in (("strategy_a", code_before), ("strategy_b", code_after)):
            with open(os.path.join(tmp, f"{name}.py"), "w", encoding="utf-8") as f:
                f.write(code)
        runner = os.path.join(tmp, "equiv_runner.py")
        with open(runner, "w", encoding="utf-8") as f:
            f.write(_EQUIV_RUNNER)
        try:
            proc = subprocess.run(
                [sys.executable, runner, CACHE_DIR, str(SMOKE_SYMBOLS), str(SMOKE_ROWS)],
                cwd=tmp, capture_output=True, text=True, timeout=SMOKE_TIMEOUT_SECONDS * 2,
            )
        except subprocess.TimeoutExpired:
            return "equivalence test timed out"

    try:
        result = json.loads(proc.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return f"equivalence test crashed: {proc.stderr.strip()[-800:]}"
    if result["diffs"]:
        return f"behaviour changed in {result.get('diff_count')} of {result['compared']} cases, e.g.: " + "; ".join(result["diffs"])
    return None


@contextmanager
def _library_lock():
    with open(LOCK_PATH, "w") as lock:
        _lock_file(lock)
        try:
            yield
        finally:
            _unlock_file(lock)


def save_methods(new_methods):
    """Atomically adds methods to the library. Raises RuntimeError if a name
    was taken by a different method in the meantime (never overwrites)."""
    with _library_lock():
        for m in new_methods:
            path = os.path.join(LIB_DIR, f"{m['name']}.py")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    if f.read() == m["code"]:
                        continue
                raise RuntimeError(f"'{m['name']}' was added to the library by another run with different code")
        for m in new_methods:
            path = os.path.join(LIB_DIR, f"{m['name']}.py")
            if os.path.exists(path):
                continue
            fd, tmp_path = tempfile.mkstemp(dir=LIB_DIR, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(m["code"])
            os.replace(tmp_path, path)


def inline_methods(strategy_code, new_methods):
    """Fallback when new methods can't be added to the library: paste them
    into the strategy module itself and drop them from its common_methods
    imports, so the run still works without touching the library."""
    names = {m["name"] for m in new_methods}
    combined = "\n\n".join(m["code"] for m in new_methods) + "\n\n" + strategy_code
    tree = ast.parse(combined)
    lines = combined.splitlines()
    for node in sorted(
        (n for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "common_methods"),
        key=lambda n: n.lineno, reverse=True,
    ):
        kept = [a for a in node.names if a.name not in names]
        indent = lines[node.lineno - 1][: node.col_offset]
        statement = ast.unparse(ast.ImportFrom(module="common_methods", names=kept, level=0)) if kept else "pass"
        lines[node.lineno - 1: node.end_lineno] = [f"{indent}{statement}"]
    return "\n".join(lines) + "\n"
