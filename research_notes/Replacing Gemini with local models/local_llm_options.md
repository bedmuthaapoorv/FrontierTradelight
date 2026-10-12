# Local / Self-Hosted LLM Options for Spec-to-Python Codegen (Windows, as of Oct 2026)

Research date: 2026-10-09. Evidence grades used below: **[Official]** = vendor model card / official docs (self-reported); **[Independent]** = third-party leaderboard that runs the eval itself (e.g. Aider); **[Aggregator]** = third-party guide or site relaying others' numbers; **[Anecdotal]** = single-user reports (Reddit, Medium, forum posts).

## Which open-weight code-capable models are strongest in 2026, at what sizes, with benchmarks and licenses?

### Takeaway
As of mid/late 2026 the strongest locally runnable picks for Python codegen are the **Qwen3.6 family** (dense 27B and MoE 35B-A3B, both Apache-2.0, April 2026), followed by **Qwen3-Coder-30B-A3B** (Apache-2.0, 2025), **Devstral Small 2 24B** (Apache-2.0, Dec 2025) and **gpt-oss-20b** (Apache-2.0, Aug 2025) for 16 GB machines. Most 2026 headline numbers are vendor self-reported SWE-bench/LiveCodeBench figures; the independent Aider polyglot leaderboard has not been updated with these 2026 models, so independent verification is thin.

### Cited Findings
**Qwen3.6-27B (dense, released April 2026)** [Official]
- 27B params (28B listed in BF16 safetensors), hybrid Gated DeltaNet + Gated Attention, 64 layers; has a vision encoder; 262,144-token native context (YaRN up to ~1.01M); **Apache-2.0** — [Qwen/Qwen3.6-27B model card](https://huggingface.co/Qwen/Qwen3.6-27B)
- Vendor-reported: LiveCodeBench v6 **83.9**, SWE-bench Verified **77.2**, SWE-bench Pro 53.5, Terminal-Bench 2.0 59.3. Same table lists Qwen3.6-35B-A3B LCB v6 80.4 / SWE-V 73.4, Qwen3.5-27B LCB 80.7 / SWE-V 75.0, Gemma4-31B LCB 80.0 / SWE-V 52.0, Claude 4.5 Opus LCB 84.8 / SWE-V 80.9. Card notes harnesses/settings differ across benchmarks — [Qwen/Qwen3.6-27B model card](https://huggingface.co/Qwen/Qwen3.6-27B)
- Thinking mode is default (emits `<think>` blocks); non-thinking via `chat_template_kwargs: {enable_thinking: False}`; recommended thinking/precise-coding sampling temp 0.6, top_p 0.95, top_k 20; suggested output budget 32,768 tokens (81,920 for hardest coding) — [Qwen/Qwen3.6-27B model card](https://huggingface.co/Qwen/Qwen3.6-27B)
- Ollama tag `qwen3.6:27b`, ~17 GB download; recommended for 32 GB tier — [ModelFit guide, 2026-06-12](https://modelfit.io/guides/best-local-llm-for-coding/) [Aggregator]

**Qwen3.6-35B-A3B (MoE, 35B total / ~3B active, April 2026)**
- SWE-bench Verified 73.4, LiveCodeBench v6 80.4 (vendor) — [Qwen3.6-27B card comparison table](https://huggingface.co/Qwen/Qwen3.6-27B) [Official]; Apache-2.0, 262K context, multimodal; release date reported as 2026-04-16 vs 2026-04-27 by different aggregators — [LLM Reference](https://www.llmreference.com/model/qwen3.6-35b-a3b); [pricepertoken](https://pricepertoken.com/pricing-page/model/qwen-qwen3.6-35b-a3b) [Aggregator, conflicting dates]

**Qwen3-Coder-30B-A3B-Instruct (MoE, 2025)** [Official]
- 30.5B total / 3.3B active, 128 experts (8 active), 48 layers, GQA 32Q/4KV; 262,144 native context (1M with YaRN); **Apache-2.0**; non-thinking only; recommended temp 0.7, top_p 0.8, top_k 20, rep. penalty 1.05; model card itself lists no benchmark numbers (points to blog) — [Qwen/Qwen3-Coder-30B-A3B-Instruct](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct)
- ~19 GB Ollama download, 32 GB tier; described as "noticeably faster per token" than dense 27B — [ModelFit](https://modelfit.io/guides/best-local-llm-for-coding/) [Aggregator]

**Larger Qwen coder (Qwen3-Coder-Next)**
- One guide calls it the overall best local coding model of 2026 at 70.6% SWE-bench Verified, needing ~48 GB+ VRAM (64 GB+ preferred) — via search summary of [layer3labs guide (Aug 2026)](https://www.layer3labs.io/guides/best-local-llm-for-coding) / [morphllm](https://www.morphllm.com/best-ollama-models) [Aggregator; not verified against model card]

**gpt-oss-20b (OpenAI, Aug 2025)** [Official]
- 21B total / 3.6B active MoE, MXFP4-quantized MoE weights, "runs within 16GB of memory"; **Apache-2.0**; reasoning effort low/medium/high set via system prompt — [openai/gpt-oss-20b card](https://huggingface.co/openai/gpt-oss-20b)
- ~14 GB download, 128K context, 16–24 GB tier — [ModelFit](https://modelfit.io/guides/best-local-llm-for-coding/) [Aggregator]
- gpt-oss-120b (high) scored **41.8%** on Aider polyglot (run 2025-08-06), well-formed edits only 79.1% — [Aider leaderboard](https://aider.chat/docs/leaderboards/) [Independent]. No Aider entry for gpt-oss-20b.

**Devstral Small 2 (Mistral, 24B dense, Dec 2025)**
- **Apache-2.0** (the larger Devstral 2 123B uses a modified MIT license that bars companies with >$20M monthly revenue) — [Simon Willison, 2025-12-09](https://simonwillison.net/2025/Dec/9/devstral-2/); [OpenSourceForU](https://www.opensourceforu.com/2025/12/mistral-makes-coding-ai-portable-with-open-source-devstral-small-2/)
- 68.0% SWE-bench Verified (vendor card, relayed), ~15 GB download, 384K context; Devstral 2 123B 72.2% — [ModelFit](https://modelfit.io/guides/best-local-llm-for-coding/) [Aggregator]. Another guide cites 46.8% for an older Devstral, illustrating version confusion — [search summary of 2026 guides](https://www.morphllm.com/best-ollama-models) [Aggregator]
- One third-party catalog lists it as deprecated — unverified — [DataLearner](https://www.datalearner.com/ai-models/pretrained-models/devstral-small-2)

**Older/smaller models (independent Aider polyglot numbers, all 2024–2025)** [Independent] — [Aider leaderboard](https://aider.chat/docs/leaderboards/)
- Qwen3 32B: 40.0% (2025-05-08); Qwen3 235B-A22B no-think: 59.6%; Qwen2.5-Coder-32B-Instruct: 16.4%; gemma-3-27b-it: 4.9%; Llama 4 Maverick: 15.6%; DeepSeek-V3.2-Exp (Reasoner): 74.2%; DeepSeek R1-0528: 71.4%; Kimi K2: 59.1%.
- For reference: gemini-2.5-flash (no think) 44.0%, (24k think) 55.1%; GPT-5 (high) 88.0%. No Flash-Lite, GLM, Devstral, or Qwen3.6 entries on the board.
- Qwen2.5-Coder 7B (~4.7 GB, 32K ctx) and 1.5B remain listed as budget options — [ModelFit](https://modelfit.io/guides/best-local-llm-for-coding/) [Aggregator]

### Inferences
- For this task (single 100–200 line Python module from a precise spec, no agentic loop), LiveCodeBench-style "write a correct function" ability is the most relevant signal; on that, Qwen3.6-27B (83.9) and 35B-A3B (80.4) are reported in the same range as frontier closed models — but these are vendor numbers and LCB problems are competitive-programming style, not pandas/index-arithmetic specs.
- All primary candidates (Qwen3.6, Qwen3-Coder, Devstral Small 2, gpt-oss-20b) are Apache-2.0 and permit commercial use. Avoid Devstral 2 123B if license terms matter (revenue cap) — it is impractical on a laptop anyway.
- Thinking/reasoning modes (Qwen3.6 thinking, gpt-oss "Reasoning: high") likely help with index arithmetic (cf. Aider: gemini-2.5-flash 44% no-think vs 55% think), at the cost of many more output tokens — acceptable since minutes of latency are fine.

### Gaps
- No independent (Aider/EvalPlus/BigCodeBench) results found for Qwen3.6, Qwen3-Coder-30B-A3B, Devstral Small 2 or gpt-oss-20b; Aider leaderboard appears unchanged since ~Oct 2025.
- Could not retrieve HumanEval/MBPP/BigCodeBench numbers for 2026 models (vendors no longer report saturated HumanEval).
- GLM (e.g. GLM-4.7-Flash), Phi, StarCoder2, Llama, Gemma 4 not researched in depth; Gemma4-31B only appears as a comparison row in Qwen's table (LCB v6 80.0, SWE-V 52.0).
- Qwen3-Coder-Next specs/license not verified against its model card (morphllm page returned HTTP 429).

## Hardware requirements at common quantizations and expected tokens/sec (CPU-only, 8/12/16/24 GB GPUs, laptops); context needs

### Takeaway
MoE models with ~3B active parameters (Qwen3.6-35B-A3B, Qwen3-Coder-30B-A3B, gpt-oss-20b) are the sweet spot for a Windows desktop/laptop: they run usably even with 8–12 GB VRAM via llama.cpp expert offload (`--n-cpu-moe`), reportedly ~20–47 tok/s, and ~10 tok/s CPU-only. Dense 27B needs ~24 GB VRAM to be fast. With a ~15k prompt + 3k output (+ thinking tokens), plan for a 32K context window.

### Cited Findings
- Download sizes (Ollama default quant, ~Q4): Qwen3.6-27B 17 GB; Devstral Small 2 15 GB; Qwen3-Coder-30B 19 GB; gpt-oss-20b 14 GB; Qwen2.5-Coder-7B 4.7 GB; gpt-oss-120b 65 GB; Devstral 2 123B 75 GB. RAM tiers: 32 GB for 27B/30B, 16–24 GB for gpt-oss-20b, 8–16 GB for 7B — [ModelFit, 2026-06-12](https://modelfit.io/guides/best-local-llm-for-coding/) [Aggregator]
- gpt-oss-20b runs within 16 GB memory (MXFP4) — [openai/gpt-oss-20b](https://huggingface.co/openai/gpt-oss-20b) [Official]
- Qwen3-Coder-30B-A3B Q4_K_M file ≈ 18.6 GB, so a 12 GB card must spill to system RAM; an estimator puts RTX 3060 12GB at ~7 tok/s — [willitrunai](https://willitrunai.com/es/can-run/qwen-3-30b-a3b-on-rtx-3060-12gb) [Aggregator/estimate — contradicted by measured anecdotes below]
- RTX 3060 12GB, Qwen3-30B-A3B, best tg128 ≈ **46.8 tok/s** at `-ncmoe 18` — [r/LocalLLaMA snapshot](https://reddit.sentinel-team.org/posts/1t7l56a/snapshots/2026-05-15T23%3A40%3A01.25497Z) [Anecdotal]
- Qwen3-Coder-30B-A3B Q4_K_M with `--n-cpu-moe 16 -ngl 99` ≈ **38 tok/s** using ~15 GB VRAM — [Habr comments](https://habr.com/en/articles/938036/comments) [Anecdotal]
- 8 GB VRAM: RTX 3070 Ti, Qwen3.6-35B went from 8.7 to 40+ tok/s after enabling expert offload — [Medium, Coding Nexus](https://medium.com/coding-nexus/one-flag-tripled-my-tokens-per-second-on-an-8gb-gpu-238f55d1e3bd) [Anecdotal]; GTX 1080 8GB ≈ 24 tok/s for Qwen3.6-35B-A3B Q4_K_M, `--n-cpu-moe 30`, 128k ctx (KV-quant fork) — [prismix mirror of r/LocalLLaMA](https://prismix.dev/news/9d1e7a1cab26) [Anecdotal]
- RTX 3060 12GB: ~8–11 tok/s standard generation for Qwen3.6 35B, ~76–82 tok/s with llama.cpp multi-token prediction (MTP) — [aiindigo](https://aiindigo.com/blog/high-performance-on-low-vram-running-qwen3-6-35b-with-llama-cpp-mtp) [Anecdotal; conflicts with the 24–40 tok/s reports above]
- CPU-only i7-8700: ~10.6 tok/s for a 30B-A3B MoE — [InventiveHQ MoE-on-CPU benchmark](https://inventivehq.com/blog/moe-on-cpu-benchmark) [Anecdotal/blog]
- RTX 3060 12GB runs dense 14B Q4 at ~23 tok/s via llama.cpp — [singhajit inference speed comparison](https://singhajit.com/llm-inference-speed-comparison/) [Aggregator]
- Devstral Small 2 often needs CPU offload, ~18 tok/s — [2026 guide via search](https://www.layer3labs.io/guides/best-local-llm-for-coding) [Aggregator]
- Qwen3-Coder card advises reducing context (e.g. to 32,768) on OOM — [Qwen3-Coder-30B-A3B card](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct)
- Decode speed is memory-bandwidth bound; full-VRAM fit is far faster than offload — [willitrunai](https://willitrunai.com/ja/can-run/qwen-3-30b-a3b-on-rtx-3060-12gb)

### Inferences
- Rough sizing rule (general knowledge, not sourced above): Q4_K_M ≈ 0.6 bytes/param, Q5_K_M ≈ 0.7, Q8_0 ≈ 1.06 → 7B ≈ 4.5/5.3/7.5 GB; 14B ≈ 9/10.5/15 GB; 30B ≈ 18.6/21.5/32 GB; 70B ≈ 42/50/75 GB, plus KV cache (a few GB at 32K for GQA models; Qwen3.6's DeltaNet hybrid layers should need less). Verify per-model GGUF file sizes on Hugging Face.
- Tier guidance: no discrete GPU (laptop, 32 GB RAM) → Qwen3.6-35B-A3B or Qwen3-Coder-30B-A3B Q4 on CPU at ~5–10 tok/s; a 3k-token answer + thinking is a few minutes, acceptable here. Prompt processing of a 15k prompt on CPU will be the slower part (likely minutes). 8–12 GB GPU → same MoE models with `--n-cpu-moe` (~20–45 tok/s anecdotally). 16 GB → gpt-oss-20b fully in VRAM, or MoE with light offload. 24 GB → Qwen3.6-27B dense Q4/Q5 fully on GPU. 70B dense is impractical on consumer Windows machines and no longer clearly better than 27–35B 2026 models.
- Context: 15k prompt + 3k output + thinking (could be 5–20k) → set 32K–48K context explicitly.

### Gaps
- No rigorous, controlled benchmark table (llama-bench) for these exact models across 8/12/16/24 GB GPUs; figures above are anecdotal and conflict.
- No measured prompt-processing (prefill) speeds for 15k-token prompts on CPU-only laptops found.
- 70B-class numbers not researched (no compelling 2026 70B coder found).

## Runtimes on Windows: install effort, OpenAI-compatible API, structured output, determinism, GPU support

### Takeaway
**Ollama** (easiest, OpenAI-compatible at `localhost:11434/v1`, supports `seed`) or **LM Studio** (GUI + `lms` CLI, OpenAI-compatible at `localhost:1234/v1`, json_schema structured output) are the low-effort choices; **llama.cpp llama-server** gives the most control (`--n-cpu-moe`, grammar/JSON-schema, explicit ctx). **vLLM has no official native Windows support** (WSL2/Docker only). Watch Ollama's context-length default, which can silently truncate a 15k prompt.

### Cited Findings
**Ollama**
- OpenAI-compatible `/v1/chat/completions`, `/v1/completions`, `/v1/models`, `/v1/embeddings`, `/v1/responses` (v0.13.3+); use OpenAI SDK with `base_url="http://localhost:11434/v1/"`, api_key ignored; supports `seed`, `temperature`, `top_p`, `max_tokens`, `stop`, `response_format` (JSON mode), `reasoning_effort`; not supported: `tool_choice`, `logit_bias`, `n`, logprobs — [Ollama OpenAI compatibility docs](https://docs.ollama.com/api/openai-compatibility) [Official]
- The OpenAI-compat API cannot set context size; use a Modelfile `PARAMETER num_ctx` (or native API `options.num_ctx`) — [Ollama docs](https://docs.ollama.com/api/openai-compatibility) [Official]
- Default context was 2048 → 4096 in v0.6.7; since a Feb 2026 change, default is VRAM-based (4096 below 23 GiB VRAM, 32768 at ≥23 GiB, 262144 at ≥47 GiB); Ollama's own docs disagree with each other; `OLLAMA_CONTEXT_LENGTH` server env var overrides — [particula.tech on silent prompt truncation](https://particula.tech/blog/ollama-num-ctx-silent-prompt-truncation); [Zed commit](https://git.secluded.site/zed/commit/6d687a2c2c26507d0dd8ab49ecc5c5871266a419) [Aggregator/secondary]

**llama.cpp (llama-server)**
- OpenAI-compatible `/v1/chat/completions`, `/v1/completions`, `/v1/responses`, `/v1/models`; `--grammar`/`--grammar-file` (GBNF), `--json-schema`; chat `response_format` supports `json_object` and `json_schema`; `--seed` (default -1 random); `-c/--ctx-size`; `-ngl` GPU layers (`auto` default) — [llama.cpp server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) [Official]
- Determinism caveat: logits are not bit-identical across batch sizes (prompt processing vs generation), so `cache_prompt` (on by default) can cause nondeterministic results — [llama.cpp server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) [Official]
- `--n-cpu-moe` expert offload is the key flag for MoE on small GPUs — [Medium](https://medium.com/coding-nexus/one-flag-tripled-my-tokens-per-second-on-an-8gb-gpu-238f55d1e3bd); [LocalAIMaster MoE calculator](https://localaimaster.com/tools/moe-vram-calculator) [Anecdotal/tool]

**LM Studio**
- OpenAI-compatible server at `http://localhost:1234/v1`; start from Developer tab or `lms server start` (CLI via `npx lmstudio install-cli`); structured output via `response_format: {type: "json_schema"}`; GGUF uses llama.cpp grammar sampling, MLX uses Outlines; warns structured output is unreliable below 7B — [LM Studio structured output docs](https://lmstudio.ai/docs/developer/openai-compat/structured-output) [Official]

**vLLM**
- No official native Windows support as of mid-2026; routes are WSL2, Docker Model Runner (vLLM on Docker Desktop for Windows with WSL2 + NVIDIA, Dec 2025), or unofficial community forks (e.g. SystemPanic/vllm-windows) — [Docker blog](https://www.docker.com/blog/docker-model-runner-vllm-windows); [fazm.ai state of support](https://fazm.ai/t/vllm-windows-support-2026); [dasroot.net](https://dasroot.net/posts/2026/05/run-vllm-natively-windows-without-wsl/) [Mixed official/aggregator]

### Inferences
- For this app's needs (one request occasionally, single user), Ollama or LM Studio is sufficient; vLLM's throughput advantages are irrelevant and its Windows story is poor.
- Structured output/grammars are not very useful for free-form Python output; better to request a fenced code block and validate with `ast.parse` + a signature check + unit tests. JSON-schema mode could wrap `{"code": "..."}` but adds escaping risk.
- Temperature 0 + fixed seed gives near-reproducible but not guaranteed bit-identical output in llama.cpp-based runtimes (Ollama and LM Studio both use llama.cpp for GGUF); disabling prompt cache improves reproducibility.
- Explicitly set context to ≥32K (Ollama Modelfile/`OLLAMA_CONTEXT_LENGTH`, or `-c 32768` in llama-server) or a 15k-token spec may be silently truncated on <23 GB-VRAM machines.
- GPU backends: llama.cpp ships CUDA and Vulkan builds (Vulkan helps AMD/Intel GPUs on Windows) — general knowledge, not verified in fetched pages.

### Gaps
- Jan and LocalAI not researched (tool budget); both are reported to be llama.cpp-based with OpenAI-compatible servers but unverified here.
- DirectML/Vulkan/ROCm-on-Windows support matrices for Ollama and LM Studio not verified.
- LM Studio licensing terms for work/commercial use not found on the fetched page.

## How much quality is lost vs a cloud flash-lite model for precise codegen? Evidence on small local models following exact numeric specs / index arithmetic

### Takeaway
On vendor-reported code benchmarks, 2026 mid-size open models (Qwen3.6-27B/35B-A3B, LCB v6 ~80–84) likely match or exceed a Gemini 2.5 Flash-Lite-class model (third-party LCB figures 40–69 depending on build/thinking), so a well-chosen ~30B local model is plausibly *not* a quality downgrade. But small models (≤7–14B) are measurably more bug-prone, and no study directly measures off-by-one/index-arithmetic fidelity to written specs — the app should rely on tests, not model choice, to catch these.

### Cited Findings
- Gemini 2.5 Flash-Lite LiveCodeBench figures conflict by build: 40.0 (GA listing), 49.5 (preview-06-17), 68.8 (preview-09-2025) — [LangDB flash-lite](https://langdb.ai/app/models/gemini-2.5-flash-lite); [LangDB preview-06-17](https://langdb.ai/app/models/openrouter/gemini-2.5-flash-lite-preview-06-17); [LangDB preview-09-2025](https://langdb.ai/app/models/openrouter/gemini-2.5-flash-lite-preview-09-2025) [Aggregator; not verified against Google's card]
- Gemini 3.5 Flash-Lite exists (comparison pages) — [benchlm.ai](https://benchlm.ai/md/compare/gemini-2-5-pro-vs-gemini-3-5-flash-lite.md) [Aggregator; scores not retrieved]
- Aider polyglot: gemini-2.5-flash (no think) 44.0% vs Qwen3 32B 40.0% vs Qwen2.5-Coder-32B 16.4% vs gemma-3-27b 4.9% (2025 data) — [Aider leaderboard](https://aider.chat/docs/leaderboards/) [Independent] — shows older ≤32B local models lagged badly on harder multi-language edit tasks.
- Qwen3.6-27B LCB v6 83.9 / Qwen3.6-35B-A3B 80.4 (vendor) — [Qwen3.6-27B card](https://huggingface.co/Qwen/Qwen3.6-27B) [Official]
- Survey: smaller models (e.g. PolyCoder) or general models were more prone to buggy code due to limited capacity, with exceptions (SantaCoder) — [A Survey of Bugs in AI-Generated Code, arXiv 2512.05239](https://arxiv.org/pdf/2512.05239)
- Study of six LLMs: smaller models (InCoder, CodeGen) tended to produce meaningless code / miss steps, while larger models (GPT-3.5/4) more often erred on constant values and arithmetic — [arXiv 2406.08731](https://arxiv.org/abs/2406.08731v2) (as summarized by [PromptHub](https://www.prompthub.us/blog/using-llms-for-code-generation-a-guide-to-improving-accuracy-and-addressing-common-issues)) [secondary summary]
- Off-by-one taxonomy (missing first/last element, index -1, index length) from student-bug research replicated with GPT-4 — [Synthetic Students, arXiv 2410.09193](https://arxiv.org/pdf/2410.09193)
- Thinking mode materially improved Gemini 2.5 Flash on Aider (44.0% → 55.1%) — [Aider leaderboard](https://aider.chat/docs/leaderboards/) [Independent]
- Third-party guides note top cloud models still lead on the hardest tasks; local models are a strong private option rather than a peak-quality match — [2026 local-coding guides via search](https://www.layer3labs.io/guides/best-local-llm-for-coding) [Aggregator]

### Inferences
- The off-by-one bugs from flash-lite are "constant/arithmetic"-type errors that the 2406.08731 study suggests persist even in large models — switching to a local model will not eliminate them. Mitigations independent of model: (a) enable reasoning/thinking; (b) put worked numeric examples (e.g. "for df of length N, window rows are iloc[-21:-1]") in the spec; (c) auto-generate golden-value unit tests from the spec and run them on compiled output, retrying on failure (cheap locally); (d) self-consistency: generate N candidates and pick the one passing tests.
- Expect a 7–14B model to be noticeably worse than flash-lite on a 300–550 line spec; 27–35B 2026 Qwen models are the minimum tier likely to be at parity or better.

### Gaps
- No direct head-to-head benchmark of Gemini Flash-Lite vs Qwen3.6/Qwen3-Coder on the same independent harness found.
- No study found that specifically measures spec-following on exact numeric conditions / pandas index arithmetic for local models; the user would need an in-house eval (e.g. compile existing strategy specs and diff against hand-verified modules).
- Google's official Flash-Lite model-card numbers not retrieved.

## Python client options: OpenAI SDK with local base_url, ollama package, litellm

### Takeaway
The lowest-friction path is the **OpenAI Python SDK** with `base_url` pointed at Ollama (`http://localhost:11434/v1`), LM Studio (`http://localhost:1234/v1`) or llama-server; Gemini also offers an OpenAI-compatible endpoint (general knowledge), so one SDK + config can switch providers. **litellm** offers a provider-agnostic `completion()` with `ollama_chat/<model>` and `gemini/<model>` strings if a heavier abstraction is preferred.

### Cited Findings
- OpenAI SDK against Ollama: `base_url="http://localhost:11434/v1/"`, api_key required but ignored — [Ollama docs](https://docs.ollama.com/api/openai-compatibility) [Official]
- OpenAI SDK against LM Studio: `http://localhost:1234/v1`, placeholder key `lm-studio` — [LM Studio docs](https://lmstudio.ai/docs/developer/openai-compat/structured-output) [Official]
- llama-server exposes `/v1/chat/completions` OpenAI-compatible — [llama.cpp server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) [Official]
- litellm: Ollama via `model="ollama/<name>"` with `api_base="http://localhost:11434"`; docs recommend `ollama_chat` route for better responses; litellm proxy can expose an OpenAI-compatible endpoint (port 4000) mapping names to backends — [LiteLLM Ollama provider docs](https://docs.litellm.ai/docs/providers/ollama) [Official]
- Context size (`num_ctx`) can't be set through Ollama's OpenAI-compat API; native API (`ollama` Python package / `/api/chat`) accepts `options.num_ctx` per request — [Ollama docs](https://docs.ollama.com/api/openai-compatibility); [particula.tech](https://particula.tech/blog/ollama-num-ctx-silent-prompt-truncation)

### Inferences
- Recommended design: a small `LLMClient` wrapper reading `provider`, `base_url`, `model`, `temperature`, `seed`, `max_tokens` from config, using the OpenAI SDK for both local and Gemini (via Gemini's OpenAI-compatible endpoint), or litellm if multiple vendor quirks need handling. If Ollama is used, either bake `num_ctx` into a custom Modelfile tag (e.g. `qwen3.6-27b-32k`) or use the native `ollama` package to pass `options={"num_ctx": 32768}`.
- Strip `<think>...</think>` blocks / reasoning fields from responses before extracting the code block when using thinking models.

### Gaps
- litellm `ollama_chat` exact syntax/section was truncated in results; verify in docs.
- Gemini OpenAI-compatible endpoint not verified in this research session.
