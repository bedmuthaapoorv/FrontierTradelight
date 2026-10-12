# Replacing Gemini with local models: codebase inventory and hardware

Research date: 2026-10-09. This was a read-only investigation. No project files were changed, and no secrets are printed here.

## 1. Summary

- Gemini is used for one thing only: **turning a markdown spec into Python code**. An LLM writes a Python function from `rules.md` or `exit_rules.md`, and the app then imports and runs it in-process. No other part of the app uses an LLM. The event watcher, fund documents, fund manager, Nifty and NSE utilities, and the US Alpaca market data have no Gemini or LLM calls.
- There are 2 generator modules, each copied in `Strategies/Default` (India) and `Strategies/US`. The US copies match the India ones except for the benchmark name in two prompt sentences ("Nifty" vs "S&P 500").
- There are 4 prompt types: `evaluate_stock`, router `select_strategy`, `resolve_exit` plus `describe_state`, and a reuse of the evaluate prompt by the Multi-Strategy tab and per-version exit compilation.
- Every call uses the same settings: model `gemini-3.1-flash-lite`, `temperature=0.0`, no other config. There is no system instruction, structured output, max-token limit, timeout or thinking config, and the calls do not stream.
- Typical size per call: about **4k–6.5k input tokens** and about **1k–2k output tokens** of Python. Calls are rare (one per spec edit) and results are cached, so latency matters much less than **correctness**.
- Validation of generated code: **none**. There is no `ast.parse`, smoke test or unit test. Code-fence stripping is the only post-processing. Only one call path retries on errors (Multi-Strategy).
- Hardware: **Lenovo ThinkPad 21H1 (i5-1335U, 10C/12T, 16 GB DDR4-3200 in a single DIMM, Intel UHD iGPU only, no NVIDIA GPU or CUDA, no NPU)**. No local LLM runtime is installed (no Ollama, LM Studio or llama.cpp). Free disk space: C: about 10 GB, D: about 114 GB. This machine can only run small quantized models on the CPU, about 7–14B at Q4. Expect a few tokens per second, so a 1.5k-token output takes several minutes.

## 2. Call sites

### 2.1 `generate_screener.py` (India: `Strategies/Default/generate_screener.py`, US: `Strategies/US/generate_screener.py`, same line numbers)

| Item | Detail |
|---|---|
| Imports | `from google import genai` (L7), `from google.genai import types` (L9), `load_dotenv()` (L11) |
| Client | `_client()` L192-198: reads `GEMINI_API_KEY` from the environment; if missing, prints an error and calls `sys.exit(1)` |
| Call | `_generate_from_prompt()` L212-220: `client.models.generate_content(model='gemini-3.1-flash-lite', contents=prompt, config=types.GenerateContentConfig(temperature=0.0))`, then `_strip_code_fence(response.text)` |
| Post-process | `_strip_code_fence()` L201-209: removes a leading ```` ```python ```` or ```` ``` ```` and a trailing ```` ``` ````, then strips whitespace. Nothing else. |
| Single-strategy mode | `generate_rules()` L353-370: reads `rules.md` from the CWD. If it has no `## Referenced Strategies`, makes 1 call and writes `generated_rules.py` (L367-369), overwriting it with no backup and no syntax check. |
| Router mode | `generate_router()` L273-350: parses `## Referenced Strategies` with regex (L237-257). Makes **one `evaluate_stock` call per referenced .md** and writes each to `generated_strategies/<Key>.py` (L298-308). Makes **one more call** for `select_strategy(market_breadth)` (L310-316), using the `## Routing Rules` section (L265-270). Then it fills a **hand-written** template (L322-345) with imports, the LLM's `select_strategy` code pasted in verbatim, and a dispatcher `evaluate_stock` with a fallback key. A router with N strategies costs N+1 calls. No current `rules.md` or `Rules_backup/*.md` is a router (checked: 0 matches), but `Default/generated_strategies/{Breakout,MeanReversion,Trendline}.py` (3.3–5.7 KB) are left over from an earlier router. |

**Prompt A, `EVALUATE_STOCK_PROMPT_TEMPLATE`** (L13-152, about 5.9 KB, about 1.5k tokens before the rules are inserted):
- Generate a complete module with imports and `def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth)` (L23).
- It must return `{"Symbol", "Passed": bool, "ClosenessScore": float 0-100, "FailedRules": list[str], "Details": dict}` (L36-42).
- `Details` must include every metric plus every field from the rules' "Output Columns" section (L60-66).
- `ClosenessScore` must follow the rules' "Ranking Rules" exactly (L78-86).
- Constraints:
  - Use `pandas_ta as ta`; never throw; output only code (L88-97).
  - Pick pandas_ta columns by prefix (L101-107) and check Series vs DataFrame (L108-113).
  - Include the real exception text in `FailedRules` (L114-116).
  - `universe` and `sector_ranks` have specific shapes (L117-121).
  - No hardcoded placeholders; implement trendline, pivot and regression math in full (L122-129).
  - Count only against the specified point set (L130-137).
  - Index by position with `.values` or `.iloc`, never `series[i]` on a date index (L138-147).
- Then `RULES:\n{rules_content}` (L149-151).
- Many of these constraints read like patches for earlier Gemini mistakes. Expect a local model to make the same kinds of mistakes.

**Prompt B, `SELECT_STRATEGY_PROMPT_TEMPLATE`** (L154-189, about 1.1 KB): asks for `def select_strategy(market_breadth)` that returns one of the listed string keys and follows the routing rules in order, falling back to the default. The output is tiny, so any small model can handle it.

### 2.2 `generate_exit_strategy.py` (`Strategies/Default/generate_exit_strategy.py`; the US copy is byte-identical)

| Item | Detail |
|---|---|
| Imports | L6, L8; `load_dotenv()` L10 |
| `generate_exit_code(rules_content)` | L12-122. Raises `RuntimeError` if the key is missing (L15-20). Builds an f-string prompt (L22-104, about 3.5 KB, about 0.9k tokens before the rules). Calls `genai.Client(...).models.generate_content(model='gemini-3.1-flash-lite', ..., temperature=0.0)` (L106-113). Strips code fences inline (L115-121; it does not strip whitespace again after removing the closing fence). |
| CLI `generate_exit_strategy()` | L125-143: reads `exit_rules.md` and writes `generated_exit_strategy.py` with no validation |

**Prompt C contract:** `def resolve_exit(entry_price, entry_date, signal_history_df, future_df)` (L32).
- `signal_history_df` is used only for entry-time indicators (no look-ahead).
- Walk `future_df` day by day and use closes only, unless the rules say otherwise (L36-49).
- Return `{"ExitDate", "ExitPrice", "ExitReason"}` or `None`, and never invent a fallback (L51-68).
- Wrap everything in try/except and return `None` (L75-76).
- **`describe_state(...)` is not in the prompt template.** It is requested inside the spec itself: the "State Inspection" section in `Default/exit_rules.md` L354-388 and `US/exit_rules.md` L298, and in every `ExitRules_backup/*.md`. That section asks for a dict with `TrailingStop`, `DistanceToStopPct`, `DaysHeld`, `DaysToMaxHold`, `LastClose`, `HighestClose`, `InitialStop`, `Pivot`, `HandleLow`, `ATRMultiplier`, `BigWinner`, `HoldFloorActive` and `InFailedBreakoutWindow`. So each exit generation produces **two functions that must stay in sync** and repeat the same stateful walk. Current output: `Default/generated_exit_strategy.py` has `resolve_exit` and `describe_state` at L89.

### 2.3 Indirect callers that reuse the generators as a library

| Caller | Lines | What it does | Error handling |
|---|---|---|---|
| `Default/multi_strategy_utils.py` `_load_module()` | L179-205 (US: L152-178) | Compiles any saved strategy version for the Multi-Strategy tab. Cached by sha256[:16] of the rules text in `data/multi_strategy/code/strategy_<digest>.py` (L174-176). A `_codegen_lock` serializes generation. The module is loaded with `importlib` and `exec_module`. | `_client()`'s `SystemExit` becomes a `RuntimeError` (L187-190). **The only retry loop in the repo:** 3 attempts, catches any `Exception`, sleeps 3 s then 6 s, and the comment says "Gemini 503s under load are transient" (L191-198). Router strategies are rejected here (L222-223). The UI progress label says "Compiling rules with Gemini" (L225). |
| `Default/sell_screener.py` `load_exit_module()` | L34-63 (US is the same) | For holdings pinned to an `ExitRules_backup/*.md` version, compiles it on first use, or when the .md is newer than the .py, into `generated_exit_strategies/<name>.py` (L48-58). The module is exec'd in-process. | No retry. Any exception, including 503s, ends up in the per-holding `except` (L211-218) as `Recommendation: "UNKNOWN"` with the error text as the reason. |
| `Default/api/routers/stats.py` `/stats/load-strategy` | L163-195 | Copies a backup into `rules.md`, then runs `generate_screener.py` with `subprocess.run` (L184-186) | A non-zero exit returns `{"status": "error"}` (L187-191) with no retry |

### 2.4 Triggers (UI, API and CLI)

- CLI: run `python generate_screener.py` or `python generate_exit_strategy.py` from `Strategies/Default` or `Strategies/US`. Both read `rules.md` or `exit_rules.md` from the **CWD**.
- FastAPI (`Strategies/{Default,US}/api/routers/jobs.py`):
  - `POST /jobs/generate-screener` (L36-38) and `POST /jobs/generate-exit-strategy` (L46-48) run the script in a subprocess and stream stdout, ending with `__EXIT_CODE__:<n>` (L20-33).
  - `POST /jobs/check-exit-signals` (L51-53) runs `sell_screener.py`, which may compile pinned exit versions.
  - `/multi-strategy/run` and `/run-stream` are in `api/routers/multi_strategy.py` (L30, L44).
  - `/stats/load-strategy` is listed above.
- React frontend (`Strategies/frontend/src`):
  - `pages/Run.tsx` L21 (step 1 "Generate screening logic"; its description at L62 says Gemini and `GEMINI_API_KEY`)
  - `pages/Sell.tsx` L87 (generate exit) and L132 (check exit signals)
  - `pages/Stats.tsx` L88 (`statsApi.loadStrategy`)
  - `pages/MultiStrategy.tsx` L73 (`runStream`)
  - Endpoints are declared in `api.ts` L67-70, L285, L538-551.
- Other UI text that mentions Gemini: `Default/strings.py` L16-17, README L5/18/38/54/175-184, `RULES_GUIDE.md` and `BACKTEST_GUIDE.md` (both markets).
- Consumers of the generated code (they run it in-process, which matters for trust and safety): `stock_screener.py` L106/113 (`generated_rules.evaluate_stock`), `backtest.py` L56-57, L289 (`resolve_exit`), L431 (`evaluate_stock` per symbol per day, the hot loop of the backtest).

## 3. Prompt and output sizes (chars/4 for prose, about chars/3.5 for code)

| Prompt | Template | Spec (current / range in backups) | Input total | Output (current generated files) |
|---|---|---|---|---|
| evaluate_stock | 5.9 KB, about 1.5k tokens | `Default/rules.md` 17.0 KB (544 lines); `US/rules.md` 16.4 KB; `Rules_backup/` 18 files, 10.5–19.0 KB | **about 4k–6.5k tokens** | `Default/generated_rules.py` 6.7 KB / 145 lines; US 4.5 KB; sub-strategies 3.3–5.7 KB, so **about 1k–2k tokens** |
| resolve_exit + describe_state | 3.5 KB, about 0.9k tokens | `Default/exit_rules.md` 15.0 KB (388 lines); US 14.7 KB; `ExitRules_backup/` 4 files, 10.5–15 KB | **about 3.5k–4.7k tokens** | `Default/generated_exit_strategy.py` 6.0 KB / 127 lines; US 3.9 KB, so **about 1.1k–1.7k tokens** |
| select_strategy (router) | 1.1 KB | Routing Rules section only | under 1k tokens | a few dozen lines |

A context window of **8k tokens fits all prompts with room to spare; 16k is comfortable.** Specs are growing (they went from 10 KB to 19 KB across versions), so plan for 16k–32k.

## 4. API key and dependencies

- `Strategies/Default/.env.template` L1 and `Strategies/US/.env.template` L1: `GEMINI_API_KEY=`. The US template also lists `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`, which `US/market_data.py` L66-67 uses for market data, not for an LLM.
- `Strategies/Default/.env` exists, contains only `GEMINI_API_KEY`, and is gitignored (`.gitignore:2`). **`Strategies/US/.env` does not exist.** The US generators call bare `load_dotenv()` (`US/generate_screener.py` L11), which searches up from the script directory and does not reach `Default/.env`. `GEMINI_API_KEY` is also not set in the shell environment. So US generation will likely fail with a missing-key error unless the key is provided some other way. The only US module that loads its own `.env` explicitly is `US/market_data.py` L29.
- Dependencies: the only requirements file is `Strategies/Default/requirements.txt`, which lists `google-genai` (L7) with no version pin, alongside jugaad-data, pandas, numpy, scipy, pandas_ta, python-dotenv, fastapi, uvicorn, feedparser, requests, python-multipart and pypdf. The US backend has no requirements file of its own. Installed: `google-genai 2.12.1`, pandas 3.0.0, numpy 2.2.6, pandas-ta 0.4.71b0. The launcher `Start FrontierTradeLight.ps1` L29-63 prefers `Default\.venv` (which does not exist) and otherwise uses the `py` launcher.

## 5. Validation, errors and retries

- **No validation of generated code anywhere.** Searching for `ast.parse`, `py_compile`, `pytest` or `unittest` in Default and US finds nothing; the only `compile` hit is the `on_compile` callback. There are no test files in the repo.
- Output is written straight over `generated_rules.py` and `generated_exit_strategy.py`. A bad generation destroys the last working version; only the `.md` specs are backed up.
- Problems show up only at import time or at run time. Because the prompt requires blanket try/except, logic errors (such as the off-by-one and wrong-bar bugs reported in the recent session; that session is not documented in `research_notes/`) **fail silently**: you get wrong signals instead of exceptions. Catching these needs spec-derived tests or fixtures, not just syntax checks.
- Error handling:
  - The only retry is 3 attempts with 3 s / 6 s backoff, in Multi-Strategy only (`multi_strategy_utils.py` L191-198).
  - The CLI, the jobs endpoints, `load-strategy` and `sell_screener` do not retry. A 503 there becomes an uncaught traceback, a non-zero exit, or an "UNKNOWN" holding.
  - No timeout is set on `generate_content`.
  - `response.text` can be `None`, for example when the response is blocked or empty. `.strip()` would then raise `AttributeError` (`generate_screener.py` L220 to L202; `generate_exit_strategy.py` L115).
- Fence stripping only works when the fence is the first or last thing in the response. Any text before the fence ends up in the .py file.

## 6. Interface a replacement must provide

At minimum, replace two functions:
- `generate_screener._generate_from_prompt(client, prompt) -> str` together with `_client()`. Multi-Strategy imports `_client` and `generate_evaluate_stock_code` directly.
- The inline call in `generate_exit_strategy.generate_exit_code(rules_content) -> str`.

The signature is: prompt string in, one Python source string out, deterministic (temperature 0). Calls are infrequent and cached (by hash, by mtime, and in the committed generated files), so a slow local model is workable for the CLI and API jobs. The hard requirement is correctness on dense numeric specs of 15–19 KB.

## 7. Machine hardware

| Item | Value |
|---|---|
| Model | Lenovo 21H1S0PM00 (ThinkPad E14/E16 Gen 5, Intel) |
| OS | Windows 11 Pro 10.0.26100 (build 26100), 64-bit. PowerShell runs in **Constrained Language Mode**, which suggests a managed corporate device (user profile `apoorv.bedmutha.MEDIASSISTINDIA`). Installing software may be restricted. |
| CPU | 13th Gen Intel Core i5-1335U: 10 cores (2P + 8E), 12 threads, 15 W U-series laptop chip. AVX2 and AVX-VNNI, no AVX-512. |
| RAM | 16 GB total (16.4 GB visible). One DDR4-3200 module (Samsung M471A2G43CB2-CWE, 16 GB), so probably **single-channel, about 25 GB/s**. About 6.2 GB was free at sampling time. |
| GPU | Intel UHD Graphics (integrated, shared memory; AdapterRAM reports 2 GB). **No NVIDIA GPU**: `nvidia-smi` not found, `CUDA_PATH` empty, no CUDA toolkit folder. |
| NPU | None found (Raptor Lake U has no NPU) |
| Disk | C: about **10.3 GB free** (269 GB used). D: about **113.9 GB free** (81 GB used). Store models on D:. |
| Python | 3.13.0 (AMD64) via the `py` launcher. The `python` alias points to the Microsoft Store stub. |
| Local LLM runtimes | None. `ollama` not on PATH; no `%LOCALAPPDATA%\Programs\Ollama`, `C:\Program Files\Ollama` or `~\.ollama`; no LM Studio (`%LOCALAPPDATA%\Programs\LM Studio`, `~\.lmstudio`, `~\.cache\lm-studio`); no `llama-server`, `llama-cli` or `lms` on PATH. No torch, transformers, llama-cpp-python, onnx or openvino in pip. Docker and WSL are not on PATH. `%LOCALAPPDATA%\Programs` has Antigravity, Obsidian and Python. |

### What fits on this machine (rough sizing)

CPU-only token generation is limited by memory bandwidth. At about 25 GB/s single-channel, a model's decode speed is roughly bandwidth divided by model size:
- 7–8B at Q4 (about 4.5–5 GB): about 3–6 tok/s.
- 14B at Q4 (about 9 GB): about 1.5–3 tok/s, and fits only if other apps are closed (about 6 GB was free).
- 32B at Q4 (about 19 GB): does not fit in 16 GB.

Reading a 5k-token prompt on 10 hybrid cores will also take about 1–3+ minutes.

So one `evaluate_stock` generation (5k in, 1.5k out) would take about **5–10 minutes with a 7B model and about 15–25 minutes with a 14B model**. The i5's iGPU can be used through the Vulkan or SYCL backends of llama.cpp or Ollama, but it shares the same memory bandwidth, so it helps prompt processing more than generation.

Coding quality at this size (Qwen2.5/3-Coder 7B–14B class) is clearly below hosted frontier models on long, dense specs. Gemini Flash-Lite already introduced 4 off-by-one or wrong-bar bugs, so a local model of this size will likely need a validation and repair loop: `ast.parse`, an import plus a smoke run on cached OHLCV, and spec-derived fixture tests. The alternative is a bigger model on a stronger machine or server.
