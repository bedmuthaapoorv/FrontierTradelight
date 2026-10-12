# Deterministic Alternatives to LLM Code Generation for Strategy Specs (and Guardrails for LLM Code)

Evidence grades used below: **[Rigorous]** = peer-reviewed / benchmarked paper or official spec documentation; **[Practitioner]** = official product docs describing practice, maintainer statements, security advisories; **[Anecdotal]** = forum posts, blogs, third-party summaries.

Context recap: plain-English `entry rules.md` / `exit_rules.md` are compiled by Gemini into Python modules (`evaluate_stock` / `resolve_exit`). Pain points: external API 503s; subtle off-by-one / wrong-bar indexing bugs; some strategies need custom algorithms (cup-and-handle anchor detection, polyfit parabola R², swing-high detection).

---

## Q1. How do existing platforms express screening/exit rules declaratively, and what would a minimal in-house DSL + interpreter look like?

### Takeaway
Every mainstream platform resolves the "which bar?" question with one explicit, uniform offset convention baked into the language (Pine `close[1]`, AFL `Ref(C,-1)`, Chartink "1 day ago", freqtrade `shift(1)`), and none of them let a free-form generator choose indexing per rule. A small expression DSL with one offset operator, a fixed indicator vocabulary, and a vectorized pandas interpreter would remove the off-by-one bug class structurally rather than test for it after the fact.

### Cited Findings
**TradingView Pine Script [Practitioner, official docs]**
- Pine runs bar by bar from the first bar to the latest, once per historical bar. Built-ins such as `close` update before each run. — [Pine execution model](https://www.tradingview.com/pine-script-docs/language/execution-model/)
- The history operator `[]` is relative to the current bar: `close[1]` is the previous bar's committed value, `close[0]` is the current bar, and a missing bar gives `na`. Expressions can be history-referenced too, e.g. `(open[n])[1]`. — [Pine execution model](https://www.tradingview.com/pine-script-docs/language/execution-model/)
- The runtime sizes each history buffer to the largest offset the script uses (most series hold up to 5000 bars). It warns that history references in local scope can give unintended results. — [Pine execution model](https://www.tradingview.com/pine-script-docs/language/execution-model/)
- On realtime bars, the script re-runs on each tick and rolls back to the last committed state, so logic that depends on tick values can "repaint". — [Pine execution model](https://www.tradingview.com/pine-script-docs/language/execution-model/)

**AmiBroker AFL [Practitioner]**
- AFL is array-based. `Ref(array, period)` reads the past with a negative period and the future with a positive one, and the period may be an array that varies per bar. — [AmiBroker Ref() reference](https://amibroker.com/guide/afl/ref.html)
- AmiBroker issues warning 1001 ("Ref may be looking into the future") when a positive offset is used. The standard user mistake is `Ref(C, n)` where `Ref(C, -n)` was meant. — [AmiBroker forum, "Code Ambiguity"](https://forum.amibroker.com/t/code-ambiguity/40205) [Anecdotal]. The look-ahead warning is static analysis of a single, explicit offset construct.

**Chartink (Indian NSE scanner) [Practitioner]**
- Every OHLCV attribute and indicator carries an explicit offset prefix, defaulting to "Latest" (the current daily candle), with alternatives such as "1 day ago" or N candles ago. Examples: `Close > 1 day ago Close by 3%` and `Close crossed above SMA20`. — [Chartink example scans/articles](https://chartink.com/articles/author/akash/page/5)
- StockCharts uses a similar bracketed form, e.g. `[21 days ago sma(200,close)]`. — [StockCharts scan forum](https://scan.stockcharts.com/discussion/comment/5606/) [Anecdotal]

**freqtrade (Python, pandas-native) [Practitioner, official docs]**
- A strategy is a class with `populate_indicators`, `populate_entry_trend` and `populate_exit_trend`, each taking a DataFrame. Signals are written in vectorized form, e.g. `dataframe.loc[cond, 'enter_long'] = 1`. A plain `if dataframe['rsi'] > 30:` fails. Stops and exits go in separate callbacks (`custom_stoploss`, `custom_exit`). — [freqtrade strategy customization](https://www.freqtrade.io/en/stable/strategy-customization/)
- The docs list look-ahead anti-patterns: `shift(-1)`; `.iloc[-1]` inside `populate_*`; whole-column aggregates such as a full-column mean (use rolling windows); resample without `label='right'`; and merging informative timeframes by hand. These match the bug class this app hit. — [freqtrade strategy customization](https://www.freqtrade.io/en/stable/strategy-customization/)

**vectorbt [Practitioner]**
- Entries and exits are boolean arrays over the whole history, e.g. `ma_crossed_above` / `ma_crossed_below` fed to `Portfolio.from_signals`. Passing an array of windows produces one column per parameter variant. — [vectorbt README](https://cdn.jsdelivr.net/gh/polakowo/vectorbt@master/README.md), [vectorbt.dev](https://vectorbt.dev/)
- Stop and trailing-stop exits are built-in generators (`generate_ohlc_stop_ex_nb`, OHLCSTX) that can trigger a trailing stop or take-profit on the entry bar. Exit state machines are library code, not user code. — [vectorbt signals nb](https://vectorbt.dev/api/signals/nb/), [vectorbt generators](https://vectorbt.dev/api/signals/generators)

**QuantConnect LEAN [Practitioner]**
- Strategies split into modules: Universe Selection (a filter function returning symbols), Alpha Model (emits Insight objects), Portfolio Construction, Execution and Risk Management. — [QC Algorithm Framework v2](https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/overview), [QC v1 overview](https://quantconnect.com/docs/v1/algorithm-framework/overview), [QC universes](https://www.quantconnect.com/docs/v2/writing-algorithms/universes/key-concepts)

**Python expression-evaluation libraries [Practitioner, docs and advisories]**
- `pandas.eval` (numexpr engine) supports only arithmetic, comparison, boolean and basic math functions (abs, sqrt, exp, log, trig). User-defined functions need `engine='python'`. The docs warn it "can run arbitrary code which can make you vulnerable to code injection". It has no documented support for shift or rolling. — [pandas.eval docs](https://pandas.pydata.org/docs/reference/api/pandas.eval.html)
- `simpleeval` had a CRITICAL (9.8) sandbox escape before 1.0.5: modules leaking through objects, and dangerous functions passed as callbacks. The latest release is around 1.0.7. — [releasealert simpleeval CVEs](https://releasealert.dev/github/danthedeckie/simpleeval/cves), [depscope simpleeval](https://depscope.dev/pkg/pypi/simpleeval) [third-party trackers]
- `asteval`'s own docs say it is only "safer than the builtin eval", not guaranteed safe. It has had CVE-2025-24359 (f-string format escape, fixed in 1.0.6), GHSA-vp47-9734-prjw (AST tampering, before 1.0.6) and CVE-2026-55244 (BaseException escape, fixed in 1.0.9). — [asteval motivation](https://millenia.cars.aps.anl.gov/software/python/asteval/_sources/motivation.rst.txt), [OSV CVE-2025-24359](https://osv.dev/vulnerability/CVE-2025-24359), [GitLab advisory CVE-2026-55244](https://advisories.gitlab.com/pypi/asteval/CVE-2026-55244/)
- `evalidate` takes a whitelist approach, allowing an expression only if every AST node is an approved type. — [evalidate on PyPI](https://pypi.python.org/pypi/evalidate/)
- Rule engines:
  - Venmo `business-rules` defines rules as JSON objects. Its last notable releases are 1.0.1 (2016) and 1.1.1, with a community fork `business-rules-enhanced` at 1.4.8. — [business-rules PKG-INFO](https://gemfury.com/doctorondemand/python:business-rules/-/content/PKG-INFO), [business-rules-enhanced](https://copr-be.cloud.fedoraproject.org/results/%40copr/PyPI/srpm-builds/09283187/python-business-rules-enhanced.conf)
  - `durable_rules` is a Rete engine in C with Python bindings. Its last GitHub push was around March 2024. — [durable_rules on PyPI](https://pypi.python.org/pypi/durable_rules/0.33.111), [ecosyste.ms](https://awesome.ecosyste.ms/projects/github.com%2Fjruizgit%2Frules)
  - `panzi-json-logic` (pure Python) is flagged as dormant. A Rust-core JSONLogic Python package was released in Aug 2026. — [openapps panzi-json-logic](https://openapps.pro/packages/panzi-json-logic), [PyPI user plasmatic](https://pypi.org/user/plasmatic/)

### Inferences
- **The platforms converge on one design.** Indicators come from a library, each operand has one explicit offset, conditions combine with AND/OR, and exits come from library generators. For this app, a minimal DSL needs:
  - **Operands:** `close`, `open`, `high`, `low`, `volume`, and registered indicators, e.g. `sma(close, 50)`, `rsi(close, 14)`, `atr(14)`, `highest(high, 20)`, `lowest(low, 20)`.
  - **One offset operator** with a single sign convention, e.g. `close[1]` meaning "1 bar ago". This follows Pine and Chartink, not Python's `[-1]`, and negative or forward offsets are rejected at parse time, like AmiBroker's warning 1001 but as a hard error.
  - **Window aggregations:** `highest`, `lowest`, `mean`, `sum`, `count_true(cond, n)`, `bars_since(cond)`.
  - **Comparisons and logic:** `> >= < <= ==`, `crosses_above`, `and`, `or`, `not`.
  - **Arithmetic** and `pct_change(x, n)`.
  - **Scoring:** a `score:` block of `weight * normalized(expr)` terms.
  - **Output columns.**
- **Rule files in YAML/JSON, expressions as strings.** Each numbered mandatory filter in `entry rules.md` maps naturally to one list entry. Parse each expression with a small Lark or pyparsing grammar into an AST. The interpreter walks the AST and emits pandas operations:
  - `x[n]` becomes `series.shift(n)`
  - `highest(x, n)` becomes `x.rolling(n).max()`
  - `and` becomes `&`
  The last row's value gives the screen decision. The same code path produces the full boolean series for backtests. (Design inference, not from a cited source. Lark and pyparsing are mature parser libraries, but their maturity was not verified with sources in this pass; see Gaps.)
- **Write a grammar instead of using a general evaluator.** `pandas.eval`, simpleeval and asteval all accept "Python-ish" expressions. Each either lacks shift/rolling (`pandas.eval`) or has a history of sandbox escapes (simpleeval, asteval). A purpose-built grammar whose function names resolve only against a whitelisted registry has no general-purpose escape surface and makes offsets explicit. The rule-engine packages (business-rules, durable_rules, json-logic) are built for event/fact matching on scalars, not time-series windows. They are a poor fit and only weakly maintained.
- **Make exit logic a parameterized state machine, not free code.** `exit_rules.md` (stop, trailing, time-stop, priority order, state variables) has a fixed structure. As in vectorbt's stop generators, it is better expressed as a declarative config fed to one hand-written, unit-tested `resolve_exit` engine. Example config: `initial_stop: low_of(entry_bar) - 0.5*atr(14)`; `trail: highest(close, since_entry) - 3*atr`; `time_stop: 20 bars if gain < 5%`; `priority: [stop, trail, time]`.

### Gaps
- I found no official documentation of Screener.in's query syntax, the full Chartink grammar, or Backtrader/Zipline Pipeline APIs in this pass. The design conclusions do not depend on them.
- No maturity or maintenance data was gathered for Lark or pyparsing. Both are widely used, but this is unverified here.
- No source quantified how often offset bugs occur in hand-written versus DSL-expressed strategies.

---

## Q2. Limits of a DSL: how to handle custom algorithmic pieces (pattern detectors)

### Takeaway
Every mature platform gives users an escape hatch for code. The robust pattern is a registry of hand-written, unit-tested Python functions ("custom indicators" or "detectors") that return a Series or a typed record. The DSL can only reference them by name with parameters. The cup-and-handle, parabola-R² and swing-high logic belongs in that registry, written and tested once by a developer, not regenerated per strategy.

### Cited Findings
- freqtrade's design puts all computation in Python methods (`populate_indicators`) that write named columns. Entry and exit logic then compares those columns. — [freqtrade strategy customization](https://www.freqtrade.io/en/stable/strategy-customization/) [Practitioner]
- LEAN's Universe Selection is a user-defined filter function, and its Alpha Model is a user class. Custom logic sits behind a fixed interface. — [QC Algorithm Framework](https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/overview) [Practitioner]
- vectorbt exposes an indicator factory and a signal-generator framework so that custom indicators become first-class, parameterizable objects. — [vectorbt generators](https://vectorbt.dev/api/signals/generators) [Practitioner]
- AmiBroker's ecosystem adds functions such as `VariablePeriodRef` through third-party plugin DLLs instead of extending the language. — [WiseTrader Toolbox](https://wisetradertoolbox.com/docs/toolbox/pages/variableperiodref.html) [Practitioner]

### Inferences
- **Registry contract.** Use `@register("cup_handle", params={...}, outputs={"found": bool, "left_rim_idx": int, "r2": float, ...})`. The function takes an OHLCV DataFrame plus parameters and must use only data up to and including the evaluation bar. A decorator can enforce this by passing a truncated frame (see Q4, look-ahead tests). The DSL then writes, for example:
  - `cup_handle(depth_max=0.35, min_len=30).found`
  - `cup_handle(...).r2 >= 0.8`
  - `close > cup_handle(...).pivot_price`
- **Detectors are where the bugs hide.** Polyfit windows, anchor search and swing pivots need golden fixtures (synthetic cups with known rim indices) and property tests (invariance to price scaling, no change when future bars are appended). These tests are written once per detector, not per strategy.
- **Budget for registry growth.** When a new spec needs a capability the registry lacks, a developer (optionally helped by an LLM, under the guardrails in Q4) adds one function plus tests. This is a slower path than "LLM writes everything", but the cost is paid once and reused.
- **Pivots and swing highs need a confirmation lag.** A swing high at bar t is only known at t + k. The registry API should return "confirmed as of bar" indices so the DSL cannot accidentally use unconfirmed pivots. This is an inference drawn from the repainting and look-ahead warnings in [Pine docs](https://www.tradingview.com/pine-script-docs/language/execution-model/) and [freqtrade docs](https://www.freqtrade.io/en/stable/strategy-customization/).

### Gaps
- I found no published case study measuring the maintenance cost of a custom-indicator registry versus per-strategy code.

---

## Q3. Hybrid designs: keep plain-English specs, have an LLM translate to a DSL, and validate deterministically

### Takeaway
Translating English into a small, grammar-constrained DSL is a much easier and more checkable task than generating free Python. Local inference stacks (llama.cpp GBNF / JSON-Schema / LLGuidance-Lark) can force syntactically valid output. Studies report that grammar masking raises correctness for DSL generation, with the caveat that constraints guarantee syntax, not meaning. Semantic validation (fixtures, round-tripping the rule back to English for user confirmation) is still needed.

### Cited Findings
- llama.cpp's GBNF grammars can describe JSON, SQL or custom formats, and constrained decoding masks invalid tokens before sampling. — [DEV Community: structured output from on-device LLMs](https://dev.to/software_mvp-factory/structured-output-streaming-from-on-device-llms-enforcing-json-schemas-with-constrained-decoding-2nfh) [Practitioner]
- llama.cpp converts JSON Schema to GBNF (basic types, enum, pattern, oneOf/anyOf/allOf). — [tensoria.fr write-up](https://tensoria.fr/blog/structured-output-json-slm-constrained-decoding) [Anecdotal/secondary]
- llama.cpp can use LLGuidance, which accepts JSON Schema and arbitrary context-free grammars in a Lark-like syntax. Masks take about 50µs per token for a 128k vocabulary. A `gbnf_to_lark.py` converter exists. — [llama.cpp llguidance.md](https://huggingface.co/OpenTransformer/llama.cpp-prismml/blob/main/docs/llguidance.md) [Practitioner]
- Netz, Reimer and Rumpe (2024) applied grammar masking to MontiCore DSLs across several LLMs. It "dramatically" improved the rate of syntactically correct models and reduced the need for prompt engineering. — [arXiv 2407.06146](https://www.arxiv.org/pdf/2407.06146) [Rigorous, preprint]
- Raspanti, Ozcelebi and Holenderski (ACL 2025 Industry) found that grammar-constrained decoding improves both syntactic correctness and semantic accuracy in logical parsing, and can substitute for in-context examples, which especially helps small models. — [ACL 2025 industry track](https://preview.aclanthology.org/setup/2025.acl-industry.34) [Rigorous]
- CRANE (2025) notes that constrained decoding guarantees well-formedness, not functional correctness. Tam et al. (2024) observed that strict output constraints can reduce reasoning accuracy for some tasks. CRANE proposes letting the model reason freely, then constraining only the final output. — [CRANE arXiv 2502.09061](https://arxiv.org/html/2502.09061v2) [Rigorous]
- An earlier no-code automation paper found that constrained decoding helped T5 and BART, with larger benefits for weaker models. — [arXiv 2207.10648](https://arxiv.org/pdf/2207.10648) [Rigorous]

### Inferences
- **Recommended hybrid pipeline:**
  1. User writes the English spec.
  2. A local model (via llama.cpp or Ollama with a GBNF/Lark grammar generated from the DSL) emits DSL YAML. Following CRANE, it may first reason in free text and then emit the constrained block.
  3. The deterministic parser and type checker validate it: known indicators, offset ≥ 0, window > 0, and registry function signatures.
  4. A deterministic "explain" pass renders the DSL back into canonical English ("Filter 3: 20-day average volume, as of yesterday, is at least 1.5x the 50-day average") for the user to confirm.
  5. Fixture tests run.
  6. The compiled rules are cached and versioned, so the LLM runs only when the spec text changes.
- **Removes the 503 problem.** Even if a cloud LLM is kept, it sits off the hot path: screening and backtests run on committed DSL, never on a live LLM call.
- **Spec editing becomes optional.** Power users could edit the DSL directly, as Chartink and AFL users do. The English layer becomes a convenience, not the source of truth.
- **Error surface.** With a small grammar, an LLM can only produce errors of meaning (wrong threshold, wrong indicator), not of indexing mechanics. The canonical-English round trip is designed to catch meaning errors.

### Gaps
- I found no benchmark specific to "trading rule English to DSL" translation accuracy, nor numbers for small local models (7–14B) on this exact task.
- I did not retrieve the Tam et al. (2024) paper directly, so its magnitude of accuracy loss is unverified here.

---

## Q4. Guardrails for generated code, and evidence that generate → test → repair loops improve correctness

### Takeaway
Execution-feedback loops reliably help, but the size of the gain depends on the quality of the tests and feedback.
- AlphaCodium's test-driven flow raised GPT-4 pass@5 from 19% to 44%.
- Reflexion reached 91% pass@1 on HumanEval, against an 80% baseline.
- LDB added up to 9.8%.
- Olausson et al. (ICLR 2024) show that self-repair is "not a silver bullet": gains are modest or absent once cost is counted, and the bottleneck is feedback quality.

For this app, that means the strongest lever is a strong, domain-specific test oracle: golden fixtures, look-ahead truncation tests, and differential tests. Whether code comes from an LLM or a human, those tests are what catch off-by-one bugs.

### Cited Findings
**Self-repair / test-driven generation evidence [Rigorous]**
- **AlphaCodium** (Ridnik et al., 2024). The flow covers problem reflection, public-test iteration and AI-generated tests. It raised GPT-4 pass@5 on the CodeContests validation set from 19% (single well-designed prompt) to 44%. Gains held for DeepSeek, and it used about four orders of magnitude fewer LLM calls than AlphaCode. Evaluation used private tests (more than 200 per problem) to minimize false positives. — [arXiv 2401.08500](https://www.arxiv.org/pdf/2401.08500), [HF paper page](https://huggingface.co/papers/2401.08500.md)
- **Reflexion** (Shinn et al., NeurIPS 2023). Verbal self-reflection stored in episodic memory reached 91% pass@1 on HumanEval, against 80% for the earlier GPT-4 state of the art. — [NeurIPS 2023 abstract](https://proceedings.neurips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract.html). A secondary summary reports a slight MBPP drop (80.1% to 77.1%). — [Beancount research log](https://beancount.io/bean-labs/research-logs/2026/04/25/reflexion-language-agents-verbal-reinforcement-learning) [Anecdotal; not verified against paper tables]. Another secondary source attributes the base model differently. — [aiwg REF-021](https://cdn.jsdelivr.net/npm/aiwg@2026.8.8/docs/references/REF-021-reflexion-verbal-reinforcement.md). Treat that detail as conflicting.
- **LDB** (Zhong, Wang and Shang, ACL Findings 2024). It segments a program into basic blocks, records intermediate variable values while running visible tests, and has the LLM verify each block. It improved baselines by up to 9.8% across HumanEval, MBPP and TransCoder; this is a maximum, not typical. — [arXiv 2402.16906](https://arxiv.org/abs/2402.16906v6), [ACL Anthology](https://preview.aclanthology.org/setup/2024.findings-acl.49)
- **"Is Self-Repair a Silver Bullet?"** (Olausson et al., ICLR 2024). On HumanEval and APPS with Code Llama, GPT-3.5 and GPT-4, once the cost of repair is counted, gains are "modest", vary across data subsets, and are sometimes absent versus plain resampling. The authors identify the model's ability to give accurate feedback on its own code as the bottleneck: stronger-model feedback gave substantially larger gains, and human feedback did better still. — [arXiv 2306.09896](https://arxiv.org/abs/2306.09896), [ICLR 2024 proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/hash/9ddc141bdbf9d1db510cefff56c586ad-Abstract-Conference.html)

**Look-ahead / determinism testing [Practitioner]**
- freqtrade's `lookahead-analysis`:
  - It runs a baseline backtest, then re-runs a separate backtest for each entry/exit signal, and compares indicator columns and signals. Any difference means the signal depended on data it should not have had.
  - Output: `has_bias`, `biased_entry_signals`, `biased_exit_signals`, `biased_indicators`.
  - Limitations: it checks only signals that actually fire (false negatives), and pair-dependent or ranking logic can give false positives.
  - The docs recommend running both lookahead and recursive analysis before any live run, and warn that a clean result is not a guarantee.
  — [freqtrade lookahead-analysis](https://www.freqtrade.io/en/stable/lookahead-analysis/), [freqtrade strategy customization](https://www.freqtrade.io/en/stable/strategy-customization/)
- AmiBroker's warning 1001 statically flags any `Ref()` with a positive (future) offset. — [AmiBroker forum](https://forum.amibroker.com/t/code-ambiguity/40205) [Anecdotal]

**Property-based testing [Practitioner]**
- Hypothesis has pandas strategies in its extras (Series and DataFrame generators) for property tests without real data. Users test invariants such as "output never has duplicate keys". — [PyData Amsterdam 2023 talk](https://amsterdam2023.pydata.org/cfp/talk/CFUCUV), [EuroSciPy 2023 talk](https://pretalx.com/euroscipy-2023/talk/WPEXXC/), [Clarity AI engineering blog](https://medium.com/clarityai-engineering/property-based-testing-a-practical-approach-in-python-with-hypothesis-and-pandas-6082d737c3ee)

**Sandboxing [Practitioner]**
- asteval's maintainers and the CVE history show that in-process Python sandboxes are not security boundaries. If generated code must run, use a separate process with OS-level isolation. — [asteval motivation](https://millenia.cars.aps.anl.gov/software/python/asteval/_sources/motivation.rst.txt), [GitLab advisory](https://advisories.gitlab.com/pypi/asteval/CVE-2026-55244/)

### Inferences
Concrete guardrail stack if LLM codegen is kept. All of it runs locally on Windows.
1. **AST gate.** Parse with `ast`. Whitelist imports (`pandas`, `numpy`, `pandas_ta`, `math`, and the registry). Ban `exec`, `eval`, `open`, `__import__`, dunder attribute access and network/OS modules. Ban the freqtrade anti-patterns: `.shift(` with a negative literal, `.iloc[-1]` outside the final selection step, unwindowed `.mean()` / `.max()` on full columns, and `center=True` in rolling.
2. **Signature/contract check.** `evaluate_stock(df) -> dict` with exact output keys and types, and `resolve_exit(df, state) -> (action, new_state)`.
3. **Golden fixtures per rule.** Generate synthetic OHLCV where each numbered filter is true at bar T and false at T-1 or T+1 by construction, e.g. close exactly at the threshold, and assert the screen output. Off-by-one bugs show up immediately as boundary failures. Fixtures come from the spec's own numbers, so they can be generated deterministically from the DSL or YAML, not by the LLM.
4. **Look-ahead truncation test.** For random bars t, evaluating on `df[:t+1]` must equal evaluating the full df's signal series at t. This is freqtrade's method and cheap to implement in pandas. Also assert that appending random future bars never changes past outputs (a Hypothesis property).
5. **Differential testing.** Run the generated module against the DSL interpreter, or against the previous hand-fixed version, across the full Nifty 500 history. Any disagreement blocks deployment.
6. **Metamorphic properties.** Scaling all prices by k should leave ratio-based filters unchanged, and scaling volume should leave volume-ratio rules unchanged.
7. **Repair loop.** Feed failing-test diffs (bar index, expected vs actual, intermediate values in the style of LDB) back to the model, capped at 2–3 iterations, then escalate to a human. Per Olausson et al., gains depend on feedback quality, so concrete fixture diffs matter more than "tests failed".
8. **Process isolation.** Run candidate modules in a subprocess with a timeout. Never run them in the Streamlit or app process before they pass the gates.

The evidence suggests the test oracle (steps 3–5) does most of the work. The benchmark gains above all come from execution feedback against tests. Without a strong oracle, self-repair gains are small.

### Gaps
- All the codegen numbers come from competitive-programming or HumanEval-style benchmarks. I found no study on LLM-generated quantitative or trading code specifically, or on time-series indexing bugs.
- No published numbers for local open-weight models (e.g. Qwen-Coder or DeepSeek-Coder at 7–32B) in repair loops on this kind of task.
- I did not retrieve the official `hypothesis.extra.pandas` API reference, so the exact signatures were not verified.

---

## Q5. Trade-offs: user flexibility vs determinism; maintenance; how comparable products handle it

### Takeaway
Commercial screeners (Chartink, StockCharts) and backtesting platforms (TradingView, AmiBroker, freqtrade, LEAN, vectorbt) all make users express rules in a formal language or API. None compiles free English into executable logic as the source of truth. A DSL plus registry trades some expressiveness and up-front engineering for reproducibility, offline operation, and the removal of a whole bug class. An LLM can sit in front as an optional, constrained authoring aid.

### Cited Findings
- Chartink and StockCharts expose structured, offset-annotated scan syntax built through a UI or text. — [Chartink articles](https://chartink.com/articles/author/akash/page/5), [StockCharts forum](https://scan.stockcharts.com/discussion/comment/5606/)
- TradingView (Pine), AmiBroker (AFL), freqtrade (Python class API), QuantConnect LEAN (framework modules) and vectorbt (array API) all require formal code against a fixed runtime. — [Pine docs](https://www.tradingview.com/pine-script-docs/language/execution-model/), [AmiBroker Ref](https://amibroker.com/guide/afl/ref.html), [freqtrade](https://www.freqtrade.io/en/stable/strategy-customization/), [QC framework](https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/overview), [vectorbt](https://vectorbt.dev/)
- Even with formal languages, platforms ship look-ahead tooling because users still misuse offsets. freqtrade has lookahead and recursive analysis; AmiBroker has warning 1001. A DSL alone is not sufficient without a look-ahead test. — [freqtrade lookahead-analysis](https://www.freqtrade.io/en/stable/lookahead-analysis/), [AmiBroker forum](https://forum.amibroker.com/t/code-ambiguity/40205)
- Constraint-based generation helps small models most, which is relevant for running locally. — [ACL 2025 industry](https://preview.aclanthology.org/setup/2025.acl-industry.34), [arXiv 2207.10648](https://arxiv.org/pdf/2207.10648)

### Inferences
| Option | Determinism / offline | User flexibility | Bug exposure | Up-front effort | Ongoing effort |
|---|---|---|---|---|---|
| A. Status quo (cloud LLM to Python, hand-fix) | Low; API dependent | Highest (any English) | High: indexing bugs per strategy | Low | High: review each regeneration |
| B. LLM to Python plus guardrail stack (Q4) | Medium: cached output, but LLM needed for changes | High | Medium: caught by fixtures and look-ahead tests | Medium (test harness) | Medium |
| C. Hand-authored DSL plus registry (no LLM) | Full | Medium: limited to grammar and registry | Low: offsets handled once in interpreter | Medium-high (grammar, interpreter, exit engine) | Low per strategy; registry grows |
| D. English to (local or cloud) LLM to DSL to deterministic validation, plus registry | Full at run time; LLM only at authoring | High (English kept, canonical English shown back) | Low: only meaning errors, surfaced in round-trip English | Highest (C plus grammar-constrained prompting) | Low-medium |

- **Recommendation shape.** Build C first; it is a prerequisite for D and gives the oracle for B. Then add D as an authoring aid.
  - Migrate custom algorithms (cup-and-handle, parabola R², swing highs) into tested registry functions regardless of option.
  - Keep option B's guardrails (fixtures, look-ahead truncation, differential tests) as a CI gate for registry functions themselves, which will still be hand-written or LLM-assisted.
- **Main risk of C/D.** Specs that need logic the grammar cannot express push work onto developers adding registry functions. The existing specs (numbered numeric filters, weighted scores, stop/trail/time-stop with priority) look well within a small grammar. The pattern detectors are the exception, and they are rare and reusable.

### Gaps
- I found no public source describing how commercial products that advertise "AI strategy builders" (e.g. natural-language scanners) validate generated logic internally. Claims about their accuracy could not be sourced.
- No quantitative data on how expressiveness limits affect user satisfaction or adoption for DSL-based screeners.
