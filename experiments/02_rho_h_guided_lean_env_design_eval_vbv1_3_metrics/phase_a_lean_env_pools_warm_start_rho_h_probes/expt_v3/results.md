# Experiment 02A v3 results — Lean warm-start data from frontier teachers

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v3/results.md>

**TLDR:** Experiment 02A v3 (frontier teachers → kernel-verified Lean on 970 screened MBPP tasks, one single-call per (task, teacher) through Vals Valkyrie, frozen VeriBench scorer): **PARTIAL** — 587 kept (task, teacher) pairs over 455 distinct tasks of 970 (anthropic 55 / openai 382 / google 150; thresholds 1,024 pairs and 512 tasks for SUFFICIENT, 300 pairs for INSUFFICIENT), 42 of 2910 cells unmeasured. The Lean SFT set has 587 (prompt, file) pairs on the host; every count below carries its denominator.

**Status:** DONE (10-09-2026 01:46 UTC). Teacher runs, re-send, scoring, generated-Lean screen, analysis and SFT assembly complete; verdict **PARTIAL**.

| Step | Status | Evidence |
|---|---|---|
| Protocol lock | done | `LOCKED 2026-10-08 00:09 UTC at commit 879eefbb…` ([PROTOCOL.md](PROTOCOL.md)) |
| Source build and screens | done | MBPP `full` revision `4bb6404f`, 974 rows; 970 kept, 4 dropped (`harness_name_collision`, MBPP ids 56, 349, 899, 967); screens vs VeriBench `c11b99ba` (896 Python + 899 Lean files): 0 exact, 0 near (max word-5-gram Jaccard 0.103). [`results/mbpp_rewrite_manifest.json`](results/mbpp_rewrite_manifest.json), [`results/screen_report.json`](results/screen_report.json), [`results/declared_manifest.json`](results/declared_manifest.json) (970 task ids, list SHA-256 `ef51bae1…`, file SHA-256 `b85e5374…`) |
| Prompt pack and held-out check | done | 971 task dirs (970 declared + 1 preflight) from the agent-spec v6 adapter at VeriBench `85fd329c6`; [`results/pack_manifest.json`](results/pack_manifest.json); held-out prompt check PASS ([`results/heldout_prompt_check.json`](results/heldout_prompt_check.json)); service-loader round-trip 971/971 PASS ([`results/pack_roundtrip.json`](results/pack_roundtrip.json)) |
| Scorer adapter | done | mapping gate 971/971 PASS ([`results/mapping_gate.json`](results/mapping_gate.json)); adapter check PASS on 3 gold + 3 broken files, identical factors on both identity paths ([`results/scorer_adapter_check.json`](results/scorer_adapter_check.json)) |
| Route identity (D-108) | done | Valkyrie `bench`, Vals AWS account 613431292675, agent `vb103_single_call` = experiment 103's frozen bundle, payer Vals; selectors `anthropic/claude-fable-5-1-no-fallback` (compute_effort max), `openai/gpt-6-astra-max`, `google/gemini-4-argon` (reasoning high, T 1.0); all `max_tokens` 128,000 ([`results/route_identity_e02a_v3.json`](results/route_identity_e02a_v3.json)) |
| Service and preflight | done | collect-only service on `skampere1:9720` behind a bearer-protected tunnel (health 200 / 401, per-task limit 6,600 s; [`results/deployment_e02a_v3.json`](results/deployment_e02a_v3.json)); preflight 3 cells, infrastructure PASS ([`results/preflight.json`](results/preflight.json)) |
| Teacher runs | done (admitted 10-08-2026 00:09 UTC, all terminal 17:12 UTC) | 3 × 970 cells, concurrency 24: anthropic `1331991a…` (61 measured, 26 incomplete, 860 model_error `MaxOutputTokensExceededError`, 13 timeout, 10 no receipt; $499.80), openai `6ecd7da9…` (953 measured, 15 timeout, 2 no receipt; $1,995.08), google `2b3e9d64…` (952 measured, 14 timeout, 4 no receipt; $564.69); the 16 no-receipt cells re-sent once as identical cells in `recovery` runs ([`results/receipts/main/`](results/receipts/main/), [`results/resend_eligible.json`](results/resend_eligible.json)) |
| Scoring and verdict | done | frozen scorer over every served cell ([`results/scored_cells.jsonl`](results/scored_cells.jsonl)); generated-Lean screen ([`results/generated_lean_screen.json`](results/generated_lean_screen.json)); analysis ([`results/analysis_v3.json`](results/analysis_v3.json)); SFT manifest ([`results/sft_manifest.json`](results/sft_manifest.json)); verdict **PARTIAL** |

## Route evidence (D-108, D-014), recorded before the first teacher call

- **Route:** Valkyrie runs (`valk run start --agent vb103_single_call --benchmark rl4cv-e02a-v3-mbpp --model <selector> …`) from `skampere1`; the agent calls the Vals model gateway from inside the Valkyrie sandbox (not the Vals direct API from this host). Brando approved the single-call agent for this experiment as D-014 (10-07-2026).
- **Identity:** Valkyrie environment `bench`, log group `fellows/brando-miranda`, S3 bucket `fellow-brando-miranda`, sandbox provider daytona; AWS identity `arn:aws:iam::613431292675:user/brando` (Vals account 613431292675). The agent's only secret mapping is `MODEL_GATEWAY_API_KEY: fellows/brandoModelGatewayApiKey` (named, never copied). The installed `vb103_single_call` bundle is byte-identical to experiment 103's frozen receipt. **Payer:** Vals. Details: [`results/route_identity_e02a_v3.json`](results/route_identity_e02a_v3.json).
- **Teachers (from the gateway registry dump, 454 models):** `anthropic/claude-fable-5-1-no-fallback` (fallback_models empty, compute_effort max, max_tokens 128,000); `openai/gpt-6-astra-max` (reasoning_effort max, the highest served; temperature unsupported); `google/gemini-4-argon` (reasoning_effort high, temperature 1.0, max_tokens 128,000 of the 262,144 the registry allows, so every teacher has the same output budget). One declared call per (task, teacher), at most two requests per cell (the agent's own one re-send after HTTP 429/5xx).
- **Prompt bytes:** experiment 103's system prompt (`dc051963…`) and `addendum_vbv1.md` (`a7a0fc1b…`), agent-spec v6 instruction from the adapter at VeriBench `85fd329c6`; held-out check PASS ([`results/heldout_prompt_check.json`](results/heldout_prompt_check.json)).

## Preflight (PROTOCOL § 7; one cell per teacher on `mbpp__preflight_task_1`, excluded from the analysis)

| Teacher | Run | Agent status | Finish | Requests | Out / reasoning tokens | Wall (s) | Charge (USD) | Lean collected | Frozen-scorer class |
|---|---|---|---|---|---|---|---|---|---|
| anthropic (`anthropic/claude-fable-5-1-no-fallback`) | `34a00ede-f3ed-424d-9e42-66d23333ba26` | model_error | none | 1 | None / None | 1361.944 | None | 0 bytes | no_lean (IC_tests 0.0, IC_proofs 0.0) |
| openai (`openai/gpt-6-astra-max`) | `a92c284c-6916-4ccf-8604-d794f21ff759` | measured | stop | 1 | 6372 / 40849 | 1111.16 | 2.4047925 | 20529 bytes | no_typecheck (IC_tests 0.0, IC_proofs 0.0) |
| google (`google/gemini-4-argon`) | `adad43cb-5f01-47bf-bc72-c498f63d9c4d` | measured | stop | 1 | 11177 / 32836 | 503.309 | 0.89464 | 29076 bytes | no_typecheck (IC_tests 0.0, IC_proofs 0.0) |

Infrastructure verdict **PASS**: every cell was served by exactly one request with the locked selector and settings delivered (`config` in the receipts), prompt hashes matched the pack, the two completions were collected by the service and all three cells were scored end to end by the frozen scorer. Observations: Claude Fable 5.1 at compute_effort max returned `MaxOutputTokensExceededError` after 1,362 s (the provider exhausted the registry's 128,000-token ceiling without a completion; experiment 103 saw the same with Claude Opus 5 at max on about 17% of its cells and kept it as a model finding, which this protocol also does); the GPT-6 Astra and Gemini 4 Argon files did not typecheck on this task. Preflight charge reported: $3.2994. `valk run results` returns "tracker returned a malformed response", so per-cell rows (service-collected bytes and hashes) are read from the run record that `valk run output` delivers.

## Results (PROTOCOL § 6; every teacher over the same 970 declared tasks)

Experiment 02A v3 (frontier teachers → kernel-verified Lean on 970 screened MBPP tasks, one single-call per (task, teacher) through Vals Valkyrie, frozen VeriBench scorer): **PARTIAL** — 587 kept (task, teacher) pairs over 455 distinct tasks of 970 (anthropic 55 / openai 382 / google 150; thresholds 1,024 pairs and 512 tasks for SUFFICIENT, 300 pairs for INSUFFICIENT), 42 of 2910 cells unmeasured.

| Teacher | Declared | Measured | Unmeasured | Kept (post-screen) | Observed yield kept/declared | Measured-cell yield [Wilson 95%] | Bounds (all unmeasured fail / succeed) | Charge (USD, gateway-reported) |
|---|---|---|---|---|---|---|---|---|
| Claude Fable 5.1 (`anthropic/claude-fable-5-1-no-fallback`, compute_effort max) | 970 | 957 | 13 | 55 | 0.057 | 0.057 [0.044, 0.074] (n = 957 tasks) | 0.057 / 0.070 | 499.80 |
| GPT-6 Astra (`openai/gpt-6-astra-max`, reasoning_effort max) | 970 | 955 | 15 | 382 | 0.394 | 0.400 [0.369, 0.431] (n = 955 tasks) | 0.394 / 0.409 | 1999.86 |
| Gemini 4 Argon (`google/gemini-4-argon`, reasoning_effort high, T 1.0) | 970 | 956 | 14 | 150 | 0.155 | 0.157 [0.135, 0.181] (n = 956 tasks) | 0.155 / 0.169 | 568.24 |

**Union:** 587 kept (task, teacher) pairs (587 before the generated-Lean screen, 0 excluded) over 455 distinct tasks of 970; overlap: anthropic&openai = 37, anthropic&google = 30, openai&google = 90, all_three = 25. **Verdict: PARTIAL** (all-unmeasured-fail PARTIAL, all-unmeasured-succeed PARTIAL; 42 unmeasured cells).

| Failure class | anthropic | openai | google |
|---|---|---|---|
| kept | 55 | 382 | 150 |
| vacuous_theorem | 0 | 0 | 0 |
| unproved_theorem | 0 | 0 | 0 |
| forbidden_axiom | 0 | 0 | 0 |
| no_theorem | 0 | 0 | 0 |
| no_example | 0 | 0 | 0 |
| no_typecheck | 9 | 573 | 806 |
| no_lean | 893 | 0 | 0 |
| unscored | 0 | 0 | 0 |
| unmeasured | 13 | 15 | 14 |

| Teacher | Kept files | Qwen3 tokens mean / median / min / max | Theorems per kept file mean / median / min / max | Non-clean finish among responded cells | Provider model_error cells | Incomplete cells |
|---|---|---|---|---|---|---|
| anthropic | 55 | 4960 / 4662 / 2624 / 8661 | 20.33 / 19 / 10 / 40 | 26 | 870 | 26 |
| openai | 382 | 4248 / 3940 / 1345 / 16168 | 14.61 / 12.0 / 4 / 41 | 0 | 0 | 0 |
| google | 150 | 4147 / 3635 / 1646 / 14524 | 14.85 / 13.0 / 7 / 47 | 0 | 0 | 0 |

**Measured** = a model response was served (any content); **unmeasured** cells are listed, never counted as zero: anthropic: 13 (mbpp__task_16, mbpp__task_162, mbpp__task_182, mbpp__task_185, mbpp__task_186, mbpp__task_187…); openai: 15 (mbpp__task_151, mbpp__task_16, mbpp__task_160, mbpp__task_178, mbpp__task_192, mbpp__task_195…); google: 14 (mbpp__task_29, mbpp__task_291, mbpp__task_37, mbpp__task_371, mbpp__task_39, mbpp__task_395…). Every unmeasured cell is a `TimeoutError` after one request with no response (possibly served and billed, so never re-sent) or, for Anthropic, also a no-receipt cell whose single identical re-send returned `MaxOutputTokensExceededError`. The Wilson interval is conditional on measurement (unit = task); the two bounds assume every unmeasured cell fails or succeeds.

**Generated-Lean screen (held-out panels):** 587 kept files screened against VeriBench `py_src` + `lean_src` (1795 files) and the held-out panel files available at the pin (41 files from `experiments/97_vsb_multifile_python_to_lean/task, experiments/91_lean_to_python_hopefully_unsaturated_vb/expt_v5_full_source/data`; VeriBench V2's five full-source task inputs are private at the pin and could not be screened): 0 exact, 0 near hits (max word-5-gram Jaccard among clean 0.0209); excluded cells: none.

**SFT set (host only, `/lfs/skampere1/0/brando9/rl4cv_e02a_v3/sft/lean_warmstart_v3.jsonl`, SHA-256 `2a3380227dedcb53…`):** 587 (prompt, kept file) pairs over 455 distinct tasks, per teacher {'anthropic': 55, 'google': 150, 'openai': 382}; the committed [`results/sft_manifest.json`](results/sft_manifest.json) lists task ids, teachers and SHA-256s. Each row holds experiment 103's exact system prompt and user message (instruction + addendum) and the kept Lean file.

**Charges reported by the gateway (USD):** preflight 3.30; main + recovery 3067.90; total 3071.20. Anthropic `model_error` cells report no charge.

### Verdict

**PARTIAL** (rule: SUFFICIENT if kept pairs >= 1024 and distinct tasks >= 512; INSUFFICIENT if kept pairs < 300; else PARTIAL; UNRESOLVED when the missing-outcome bounds fall on different sides of a threshold). All-unmeasured-fail verdict PARTIAL; all-unmeasured-succeed verdict PARTIAL. Union kept pairs 587 (threshold 1,024 / 300), distinct tasks 455 (threshold 512); tasks kept by k teachers: {'1': 348, '2': 82, '3': 25}; pairwise overlap {'all_three': 25, 'anthropic&google': 30, 'anthropic&openai': 37, 'openai&google': 90}.

What this means for the warm start: the kept pairs are the Lean SFT part available by this route today. The hypothesis ("the Anthropic and OpenAI teachers each keep at least 40% of the screened tasks") is not supported on observed yields (anthropic 0.057, openai 0.394, google 0.155). The Anthropic teacher at the locked `compute_effort max` returned a provider `MaxOutputTokensExceededError` (the registry's 128,000-token output ceiling exhausted without a completion) on 870 of 970 cells and an incomplete completion on 26 more (23 with no Lean block, 3 cut at the output limit with Lean) (the same provider-side behaviour experiment 103 recorded for Claude Opus 5 at max); a lower effort or a vendor agent is a separately recorded condition for a later version, not a recovery pass.

### Deviations and observations (recorded, none changes a locked scientific setting)

1. MBPP `code` is stored with CRLF line endings; the rewrite normalizes them to LF and changes nothing else. Four MBPP tasks (56, 349, 899, 967) define a function named `check`, which the VeriBench layout reserves for the test harness; they are dropped and listed (`harness_name_collision`).
2. `valk run results` returned "tracker returned a malformed response" for every run; the per-cell rows (service-collected bytes and hashes) were read from the run record that `valk run output` delivers, with each cell's agent receipt.
3. Gemini 4 Argon ran with `max_tokens` 128,000 (the registry allows 262,144) so all three teachers share one output budget, as PROTOCOL § 4 permits.
4. The preflight infrastructure check counts a provider `model_error` as a recorded model outcome rather than a transport fault (Anthropic's preflight cell).
5. `skampere1` rebooted on 10-08-2026 15:34 PDT during scoring; the Anthropic shard and the 16 recovery cells were already scored, the Astra/Argon files were re-scored from the preserved materialized trial dirs (no teacher call repeated). Scoring provenance: `results/scored_cells.summary.json`.
6. Of the VeriBench V2 / V2.1 held-out panels only experiment 97's E97-P001 task files exist at the pin; the generated-Lean screen covers VeriBench V1 (896 Python + 899 Lean files) and those files.
7. The 13 + 15 + 14 `TimeoutError` cells (one request, no response within the agent's 3,000 s client timeout) stay unmeasured; a timeout may have been served, so the protocol forbids re-sending them.
