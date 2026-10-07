# Experiment 07 results — SCS4C versus pass@1 on SWE-bench across models

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/07_scs4c_vs_pass1_swebench_across_models/results.md>

**TLDR:** Phase A compared SCS4C-T (the tests-only smooth conjunctive score for code: patch gate × √(T_fix · T_keep)) with pass@1 across every public SWE-bench Verified submission, using only the official per-instance `report.json` logs and zero model calls. On 164 of 182 submissions over a 424-task common cohort: **H1 holds** (system SCS4C-T ranks like pass@1, Spearman 0.985 [0.979, 0.987]); **H1b is positive** (a system's partial credit on the tasks it failed tracks its pass@1, Spearman 0.736 [0.507, 0.801], task bootstrap excluding 0); **the H2 forecast failed** (SCS4C-T measured on 50 tasks does not predict held-out pass@1 better than pass@1 on the same 50 tasks: median Δ −0.012, Δ > 0 in 92/2000 splits = 0.046 against a frozen 0.60 threshold); **H3**: 19.2% of unresolved common-cohort artifacts carry partial credit above 0. Per the README's decision rule (H1b positive, H2 not), partial credit is informative but not a better small-sample ranker, and phase C (SCS4C as a reward) remains justified; phase B still needs the D_gold harness and the Valkyrie service.

**Status:** DONE (phase A; 10-07-2026 16:29 PDT on `skampere1`; worker Claude Code `claude-fable-5-1` / `max`; receipts in [`expt_v1/CKPT_e07.md`](expt_v1/CKPT_e07.md))

**Last updated:** 10-07-2026 16:50 PDT (worker: landed on `main` at `788da95`; email and issue #5 comment sent)

## Phases

| Phase | Status | Evidence |
|---|---|---|
| A — definition, protocol, frozen forecast | DONE (10-07-2026) | [PROTOCOL.md](PROTOCOL.md), `expt_v1/forecasts/` (`verify_forecast` → True) |
| A — fetch public reports (182 submissions × 500 tasks) | DONE (10-07-2026 16:20 PDT) | `expt_v1/results/inventory.json`, `inputs_manifest.json`; raw logs on `skampere1` at `/lfs/skampere1/0/brando9/rl4cv_e07/data` (1.9 GB) |
| A — analysis (H1, H1b, H2, H3, sensitivity) | DONE (10-07-2026 16:25 PDT) | `expt_v1/results/analysis_e07.json`, `per_system_e07.csv`, `per_cell_e07.jsonl.gz`, `results_tables_e07.md` |
| B — full SCS4C on SWE-Bench Pro Verified | DESIGNED, not admitted | [README.md](README.md#phases) |
| C — SCS4C as an RL reward | DESIGNED, not admitted | [README.md](README.md#phases) |

## Headline

**rl4cv / experiment 07 phase A.** Hypothesis being de-risked: does SCS4C-T, a smooth conjunctive score with partial credit, track the downstream metric pass@1 across models, and does its partial credit carry capability signal that the binary `resolved` flag discards? Measured via SCS4C-T and pass@1 per system on the common cohort of SWE-bench Verified tasks measured for every included system (424 of 500), from the official per-instance `report.json` logs of 164 public submissions (18 excluded for missing or legacy logs; every cell listed).

- **Instrument:** no judge and no model calls. G = patch applied; T_fix and T_keep = passing fractions of the report's FAIL_TO_PASS and PASS_TO_PASS lists (the lists the official harness used for `resolved`); system score = geometric mean of the gated factor means (decision D-009). Consistency check: 1 of 82,905 measured cells violates resolved ⇔ (G = 1, T_fix = 1, T_keep = 1) (0.0012%; stop rule 0.5%).
- **H1 (construct check):** Spearman 0.985 [0.979, 0.987] task bootstrap, [0.969, 0.994] system bootstrap; Pearson 0.974; Kendall τ-b 0.923; n = 164 systems; p-val=n/a. Mean SCS4C-T 0.767 versus mean pass@1 0.574: mean bias +0.193 [0.178, 0.208], so SCS4C-T reads about 0.19 above pass@1 and the two are not interchangeable as levels. Frozen prediction ρ ≥ 0.90: **holds** (partly by construction, since `resolved` implies both factors equal 1).
- **H1b (partial credit on failed tasks):** Spearman 0.736 [0.507, 0.801] task bootstrap, [0.646, 0.808] system bootstrap; Pearson 0.800; Kendall τ-b 0.547; n = 164; p-val=n/a. Frozen prediction ρ > 0 with the task interval excluding 0: **positive**. Systems with higher pass@1 tend to earn more partial credit on their unresolved tasks.
- **H2 (held-out ranking from 50 tasks):** median Δ −0.012 (5th–95th percentiles [−0.025, −0.000]), Δ > 0 in 92/2000 splits (0.046); median ρ(SCS4C-T on A, pass@1 on B) 0.941 versus median ρ(pass@1 on A, pass@1 on B) 0.953. Frozen prediction median Δ > 0 and share ≥ 0.60: **fails**. At every size (25, 50, 100, 250) the median Δ is between −0.009 and −0.013: pass@1 on the same tasks is a slightly better predictor of held-out pass@1 than SCS4C-T.
- **H3 (signal density, descriptive):** 5,675 of 29,627 unresolved common-cohort cells (0.192) have SCS4C-T > 0; 6,661 of 36,604 over all measured cells (0.182). Zero unresolved cells score 1.
- **Sensitivity (one system per base model, 73 systems):** same pattern; H1 ρ 0.989, H1b ρ 0.795 [0.611, 0.854], H2 at n_A = 50 median Δ −0.007 with share 0.178.
- **Verdict?** The construct is sound (H1) and partial credit is real capability signal (H1b), but it does not improve small-sample ranking of systems by held-out pass@1 (H2 fails); thresholds were agent-suggested and frozen before any cross-system outcome was read ([PROTOCOL.md](PROTOCOL.md)). What the instrument has not been shown to do: track pass@1 as a level (bias +0.19), or add information beyond the per-test fractions the harness already records; D_gold (phase B) is untested.
- **Next step:** per the README's decision rule, phase C (SCS4C as an RL reward at G = 8, mixed-group share and ρ/H versus binary `resolved`) stays justified; phase B admission needs the frozen D_gold harness with passing controls and a verified Valkyrie service for SWE-Bench Pro Verified (owner Emily, @emxia18).

## Results

All numbers below are rendered by `expt_v1/render_results_e07.py` from `expt_v1/results/analysis_e07.json` and `per_system_e07.csv` (the rendered file is committed as `expt_v1/results/results_tables_e07.md`). Intervals are 95% percentile bootstraps (2,000 draws) that resample tasks or systems separately, conditional on the observed common cohort; they are not task-and-system joint intervals. p-val=n/a throughout: the protocol runs no hypothesis test. Dates are MM-DD-YYYY.

**Analyzer status:** `PRIMARY ANALYSES COMPUTED`; locked settings: True; seed 20261007; 2000 bootstrap draws; 2000 splits per size; sizes [25, 50, 100, 250]; inclusion ≥ 95% measured.

### Counts

| Quantity | Value |
|---|---:|
| Declared systems (pinned submission list) | 182 |
| Included systems (≥ 475/500 measured cells) | 164 |
| Excluded systems | 18 |
| Declared tasks per system | 500 |
| Common-cohort tasks (measured for every included system) | 424 |
| Declared cells (all systems) | 91000 |
| Measured cells (all systems) | 82905 |
| Unmeasured cells (all systems; listed in `per_cell_e07.jsonl.gz`) | 8095 |
| Inconsistent measured cells (resolved ≠ (G=1, T_fix=1, T_keep=1)) | 1 / 82905 = 0.0012% (stop rule 0.5%) |

### H1 — construct check: system SCS4C-T versus system pass@1 (common cohort)

Usable systems: 164 (0 with undefined scores excluded). p-val=n/a (no hypothesis test; intervals condition on the observed common cohort and are not task-and-system joint intervals).

| Statistic | Value | 95% task bootstrap | 95% system bootstrap |
|---|---:|---|---|
| Pearson r | 0.974 | [0.968, 0.977] (2000/2000 draws defined) | [0.964, 0.981] (2000/2000 draws defined) |
| Spearman ρ | 0.985 | [0.979, 0.987] (2000/2000 draws defined) | [0.969, 0.994] (2000/2000 draws defined) |
| Kendall τ-b | 0.923 | [0.902, 0.925] (2000/2000 draws defined) | [0.894, 0.946] (2000/2000 draws defined) |
| Mean system SCS4C-T | 0.767 | [0.748, 0.786] (2000/2000 draws defined) | [0.747, 0.787] (2000/2000 draws defined) |
| Mean system pass@1 | 0.574 | [0.543, 0.604] (2000/2000 draws defined) | [0.548, 0.599] (2000/2000 draws defined) |
| Mean bias (SCS4C-T − pass@1) | 0.193 | [0.178, 0.208] (2000/2000 draws defined) | [0.186, 0.200] (2000/2000 draws defined) |
| Mean absolute error | 0.193 | [0.178, 0.208] (2000/2000 draws defined) | [0.186, 0.200] (2000/2000 draws defined) |

- **Frozen prediction:** Spearman(system SCS4C-T, system pass@1) >= 0.90 (construct check, partly by construction)
- **Outcome:** prediction holds (Spearman 0.985 ≥ 0.90); construct check only, not evidence of usefulness.

### H1b — partial credit on unresolved cohort cells versus pass@1

Usable systems: 164 (0 without unresolved cohort cells have undefined partial credit and are excluded, never zero: none). p-val=n/a.

| Statistic | Value | 95% task bootstrap | 95% system bootstrap |
|---|---:|---|---|
| Pearson r | 0.800 | [0.613, 0.829] (2000/2000 draws defined) | [0.723, 0.862] (2000/2000 draws defined) |
| Spearman ρ | 0.736 | [0.507, 0.801] (2000/2000 draws defined) | [0.646, 0.808] (2000/2000 draws defined) |
| Kendall τ-b | 0.547 | [0.355, 0.611] (2000/2000 draws defined) | [0.471, 0.622] (2000/2000 draws defined) |

- **Frozen prediction:** Spearman(partial credit on unresolved cohort cells, pass@1) > 0 with 95% task-bootstrap interval excluding 0
- **Outcome:** **Positive**: partial credit carries capability signal (Spearman 0.736, task interval [0.507, 0.801] excludes 0).

### H2 — held-out prediction from random task splits

Δ = Spearman(SCS4C-T on A, pass@1 on B) − Spearman(pass@1 on A, pass@1 on B); B is the rest of the common cohort. Percentiles and shares summarise the split distribution; they are not population confidence intervals. Primary size n_A = 50; other sizes descriptive.

| n_A | n_B | Splits defined / requested | Median Δ | 5th–95th percentile of Δ | Splits with Δ > 0 | Share Δ > 0 | Median ρ(SCS4C-T on A, pass@1 on B) | Median ρ(pass@1 on A, pass@1 on B) |
|---:|---:|---|---:|---|---:|---:|---:|---:|
| 25 | 399 | 2000/2000 | -0.009 | [-0.030, +0.012] | 391 | 0.196 | 0.910 | 0.920 |
| 50 | 374 | 2000/2000 | -0.012 | [-0.025, -0.000] | 92 | 0.046 | 0.941 | 0.953 |
| 100 | 324 | 2000/2000 | -0.013 | [-0.021, -0.005] | 7 | 0.004 | 0.958 | 0.971 |
| 250 | 174 | 2000/2000 | -0.013 | [-0.018, -0.007] | 0 | 0.000 | 0.965 | 0.977 |

- **Frozen prediction:** At n_A = 50 over 2000 random splits: median Delta > 0 and share(Delta > 0) >= 0.60, Delta = Spearman(SCS4C-T on A, pass@1 on B) - Spearman(pass@1 on A, pass@1 on B)
- **Outcome at n_A = 50:** **No ranking advantage**: median Δ -0.012 (≤ 0), share Δ > 0 = 92/2000 = 0.046 (< 0.60).

### H3 — signal density (descriptive)

| Cohort | Declared cells | Measured | Unmeasured | Unresolved | Unresolved with SCS4C-T > 0 | Share | Resolved with score < 1 | Unresolved with score = 1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Included systems × common cohort | 69536 | 69536 | 0 | 29627 | 5675 | 0.192 | 1 | 0 |
| Included systems × own cohorts | 82000 | 81841 | 159 | 35980 | 6607 | 0.184 | 1 | 0 |
| All declared systems × all cells | 91000 | 82905 | 8095 | 36604 | 6661 | 0.182 | 1 | 0 |

### Sensitivity (protocol, not primary): one system per base model

Status: computed. Selection: one system per base model: the latest submission (folder-name date) per metadata tags.model_display, matched on an order-insensitive token key; same common cohort as the primary analysis. Systems: 73; skipped (model not named): 20; common-cohort tasks: 424.

| Hypothesis | Pearson r | Spearman ρ | Kendall τ-b | 95% task bootstrap of ρ | 95% system bootstrap of ρ | n systems |
|---|---:|---:|---:|---|---|---:|
| H1 (SCS4C-T vs pass@1) | 0.978 | 0.989 | 0.937 | [0.983, 0.991] (2000/2000 draws defined) | [0.973, 0.996] (2000/2000 draws defined) | 73 |
| H1b (partial credit vs pass@1) | 0.867 | 0.795 | 0.616 | [0.611, 0.854] (2000/2000 draws defined) | [0.667, 0.883] (2000/2000 draws defined) | 73 |

| n_A | n_B | Splits defined / requested | Median Δ | 5th–95th percentile of Δ | Splits with Δ > 0 | Share Δ > 0 | Median ρ(SCS4C-T on A, pass@1 on B) | Median ρ(pass@1 on A, pass@1 on B) |
|---:|---:|---|---:|---|---:|---:|---:|---:|
| 50 | 374 | 2000/2000 | -0.007 | [-0.023, +0.006] | 357 | 0.178 | 0.951 | 0.960 |

- Sensitivity H1 reading: prediction holds (Spearman 0.989 ≥ 0.90); construct check only, not evidence of usefulness.
- Sensitivity H1b reading: **Positive**: partial credit carries capability signal (Spearman 0.795, task interval [0.611, 0.854] excludes 0).
- Sensitivity H2 reading at n_A = 50: **No ranking advantage**: median Δ -0.007 (≤ 0), share Δ > 0 = 357/2000 = 0.178 (< 0.60).

Selected systems (base model → latest submission):

- Amazon.nova Premier v1:0: `20250527_amazon.nova-premier-v1.0`
- DeepSeek V3 0324: `20250806_SWE-Exp_DeepSeek-V3`
- gpt-oss-120b: `20250807_mini-v1.7.0_gpt-oss-120b`
- Frogmini 14B 2510: `20251110_frogmini-14b`
- Gemini 2.0 Flash (Experimental): `20250118_codeshellagent_gemini_2.0_flash_experimental`
- Gemini 2.0 Flash (v20241212-experimental): `20241212_google_jules_gemini_2.0_flash_experimental`
- Gemini 2.0 Flash: `20250726_mini-v1.0.0_gemini-2.0-flash`
- Gemini 2.5 Pro: `20250726_mini-v1.0.0_gemini-2.5-pro`
- CodeAct v2.1 (claude-3-5-sonnet-20241022): `20241029_OpenHands-CodeAct-2.1-sonnet-20241022`
- Claude 3.5-Sonnet-20241022: `20250122_autocoderover-v2.1-claude-3-5-sonnet-20241022`
- DevStral Small 2505: `20250520_openhands_devstral_small`
- DevStral Small 2507: `20250725_sweagent_devstral_small_2507`
- Frogboss 32B 2510: `20251110_frogboss-32b`
- Devstral (2512): `20251209_mini-v1.17.2_devstral-2512`
- Devstral Small (2512): `20251209_mini-v1.17.2_devstral-small-2512`
- Gemini 3 Flash: `20260217_mini-v2.0.0_gemini-3-flash-high`
- Gemini 3 Pro Preview: `20251120_livesweagent_gemini-3-pro-preview`
- Gemini 3 Pro: `20260226_mini-v2.0.0_gemini-3-pro-high`
- Claude 3.5 Haiku: `20241022_tools_claude-3-5-haiku`
- Claude 3.5 Sonnet: `20250228_epam-ai-run-claude-3-5-sonnet`
- Gemini 3.5 Flash: `20260901_mini-v2.4.2_gemini-3-5-flash`
- Claude 3.7 Sonnet w/ Review Heavy: `20250225_sweagent_claude-3-7-sonnet`
- Claude 3.7 Sonnet: `20250514_aime_coder`
- Qwen3-Coder-30B-A3B-Instruct: `20250901_entroPO_R2E_QwenCoder30BA3B_tts`
- SWE-agent-LM-32B: `20250511_sweagent_lm_32b`
- Qwen2.5-Coder 32B Instruct: `20250803_mini-v1.0.0_qwen2-5-coder-32b-instruct`
- Claude 4 Opus: `20250802_mini-v1.0.0_claude-4-opus-20250514`
- Claude Sonnet 4: `20250924_artemis_agent_v2`
- Llama 4 Maverick Instruct: `20250720_mini-v0.0.0-Llama-4-Maverick-17B-Instruct`
- Llama 4 Scout Instruct: `20250720_mini-v0.0.0-Llama-4-Scout-17B-Instruct`
- Claude 4.5 Haiku: `20260217_mini-v2.0.0_claude-4-5-haiku-high`
- Claude 4.5 Opus: `20260217_mini-v2.0.0_claude-4-5-opus-high`
- Claude 4.5 Sonnet: `20260217_mini-v2.0.0_claude-4-5-sonnet-high`
- GLM 4.5: `20250822_mini-v1.9.1_glm-4.5`
- Claude 4.6 Opus: `20260217_mini-v2.0.0_claude-4-6-opus`
- GLM 4.6: `20251201_mini-v1.17.1_glm-4.6`
- Qwen3-Coder-480B-A35B-Instruct: `20250805_openhands-Qwen3-Coder-480B-A35B-Instruct`
- GPT 4o: `20250720_mini-v0.0.0-gpt-4o-2024-11-20`
- 4x Scaled: `20250203_openhands_4x_scaled`
- GLM 5: `20260217_mini-v2.0.0_glm-5-high`
- GPT-5: `20251015_Prometheus_v1.2.1_gpt5`
- GPT 5 mini: `20260217_mini-v2.0.0_gpt-5-mini`
- GPT 5 nano: `20250807_mini-v1.7.0_gpt-5-nano`
- GPT 5.1 Codex: `20251124_mini-v1.16.0_gpt-5.1-codex`
- GPT 5.1: `20251120_mini-v1.15.0_gpt-5.1-2025-11-13`
- GPT 5.2 Codex: `20260219_mini-v2.0.0_gpt-5-2-codex`
- GPT 5.2: `20260217_mini-v2.0.0_gpt-5-2-high`
- Llama3-SWE-RL-70B: `20250226_swerl_llama3_70b`
- Qwen2.5 (7B + 72B): `20250306_SWE-Fixer_Qwen2.5-7b-retriever_Qwen2.5-72b-editor`
- Lingma SWE-GPT 72b (v0918): `20240918_lingma-agent_lingma-swe-gpt-72b`
- Lingma SWE-GPT 72b (v0925): `20241002_lingma-agent_lingma-swe-gpt-72b`
- Lingma SWE-GPT 7b (v0918): `20240918_lingma-agent_lingma-swe-gpt-7b`
- Lingma SWE-GPT 7b (v0925): `20241002_lingma-agent_lingma-swe-gpt-7b`
- MCTS Refine 7B: `20250627_agentless_MCTS-Refine-7B`
- TTS(Bo16): `20250629_deepswerl_r2eagent_tts`
- TTS(Bo8): `20250616_Skywork-SWE-32B+TTS_Bo8`
- Co-PatcheR: `20250528_patchpilot_Co-PatcheR`
- Doubao-Seed-Code: `20250928_trae_doubao_seed_code`
- DeepSeek V3.2 Reasoner: `20251201_mini-v1.17.1_deepseek-v3.2-reasoner`
- DeepSeek V3.2: `20260217_mini-v2.0.0_deepseek-3-2-high`
- DeepSWE-Preview: `20250629_deepswerl_r2eagent`
- Kimi K2 Instruct: `20250807_mini-v1.7.0_kimi-k2-instruct`
- Kimi K2: `20251014_Lingxi_kimi_k2`
- Kimi K2 Thinking: `20251210_mini-v1.17.2_kimi-k2-thinking`
- Kimi K2.5: `20260217_mini-v2.0.0_kimi-k2-5-high`
- MiniMax M2: `20251124_mini-v1.17.0_minimax-m2`
- MiniMax M2.5: `20260217_mini-v2.0.0_minimax-2-5-high`
- O3 Mini: `20250214_agentless_lite_o3_mini`
- o4-mini: `20250726_mini-v1.0.0_o4-mini-2025-04-16`
- Multiple: `20251103_SalesforceAIResearch_SAGE_OpenHands`
- o1-preview: `20250117_wandb_programmer_o1_crosscheck5`
- o3: `20250726_mini-v1.0.0_o3-2025-04-16`
- swe-search: `20241221_codestory_midwit_claude-3-5-sonnet_swe-search`

### Per-system table: the 15 highest-pass@1 included systems (full table in `expt_v1/results/per_system_e07.csv`)

| Submission | SCS4C-T (common) | pass@1 (common) | T_fix mean | T_keep mean | Measured / 500 | SCS4C-T (own) | pass@1 (own) | pass@1 declared |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `20251215_livesweagent_claude-opus-4-5` | 0.913 | 0.809 | 0.844 | 0.987 | 499 | 0.905 | 0.794 | 0.792 |
| `20251205_sonar-foundation-agent_claude-opus-4-5` | 0.915 | 0.804 | 0.842 | 0.995 | 500 | 0.912 | 0.794 | 0.794 |
| `20250928_trae_doubao_seed_code` | 0.909 | 0.797 | 0.831 | 0.994 | 500 | 0.904 | 0.788 | 0.788 |
| `20251127_openhands_claude-opus-4-5` | 0.908 | 0.788 | 0.834 | 0.988 | 500 | 0.904 | 0.776 | 0.776 |
| `20251120_livesweagent_gemini-3-pro-preview` | 0.901 | 0.785 | 0.820 | 0.990 | 499 | 0.896 | 0.776 | 0.774 |
| `20250819_ACoder` | 0.899 | 0.783 | 0.814 | 0.993 | 500 | 0.893 | 0.764 | 0.764 |
| `20250804_epam-ai-run-claude-4-sonnet` | 0.899 | 0.781 | 0.818 | 0.988 | 500 | 0.895 | 0.768 | 0.768 |
| `20260217_mini-v2.0.0_claude-4-5-opus-high` | 0.906 | 0.781 | 0.824 | 0.995 | 500 | 0.901 | 0.768 | 0.768 |
| `20250902_atlassian-rovo-dev` | 0.901 | 0.778 | 0.816 | 0.995 | 500 | 0.895 | 0.768 | 0.768 |
| `20250901_warp` | 0.893 | 0.771 | 0.802 | 0.995 | 499 | 0.885 | 0.760 | 0.758 |
| `20260217_mini-v2.0.0_claude-4-6-opus` | 0.904 | 0.769 | 0.822 | 0.995 | 500 | 0.896 | 0.756 | 0.756 |
| `20260217_mini-v2.0.0_gemini-3-flash-high` | 0.897 | 0.767 | 0.808 | 0.995 | 500 | 0.894 | 0.758 | 0.758 |
| `20251103_sonar-foundation-agent_claude-sonnet-4-5` | 0.884 | 0.764 | 0.794 | 0.984 | 500 | 0.878 | 0.750 | 0.750 |
| `20260217_mini-v2.0.0_minimax-2-5-high` | 0.896 | 0.764 | 0.812 | 0.989 | 500 | 0.894 | 0.758 | 0.758 |
| `20250731_harness_ai` | 0.890 | 0.759 | 0.799 | 0.992 | 500 | 0.884 | 0.748 | 0.748 |

### Excluded systems

| Submission | Measured / 500 | Reason |
|---|---:|---|
| `20231010_rag_claude2` | 1 | 1/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20231010_rag_claude2/logs (0 report files); 499 cells: no report file |
| `20231010_rag_gpt35` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20231010_rag_gpt35/logs (0 report files); 500 cells: no report file |
| `20231010_rag_swellama13b` | 21 | 21/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20231010_rag_swellama13b/logs (0 report files); 479 cells: no report file |
| `20231010_rag_swellama7b` | 6 | 6/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20231010_rag_swellama7b/logs (0 report files); 494 cells: no report file |
| `20240402_rag_claude3opus` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20240402_rag_claude3opus/logs (0 report files); 500 cells: no report file |
| `20240402_rag_gpt4` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20240402_rag_gpt4/logs (0 report files); 500 cells: no report file |
| `20240402_sweagent_claude3opus` | 45 | 45/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20240402_sweagent_claude3opus/logs (0 report files); 455 cells: no report file |
| `20240402_sweagent_gpt4` | 31 | 31/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20240402_sweagent_gpt4/logs (0 report files); 469 cells: no report file |
| `20240509_amazon-q-developer-agent-20240430-dev` | 3 | 3/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20240509_amazon-q-developer-agent-20240430-dev/logs (0 report files); 497 cells: no report file |
| `20240615_appmap-navie_gpt4o` | 6 | 6/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20240615_appmap-navie_gpt4o/logs (0 report files); 494 cells: no report file |
| `20240617_factory_code_droid` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20240617_factory_code_droid/logs (0 report files); 500 cells: no report file |
| `20240628_autocoderover-v20240620` | 8 | 8/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20240628_autocoderover-v20240620/logs (0 report files); 492 cells: no report file |
| `20240721_amazon-q-developer-agent-20240719-dev` | 1 | 1/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20240721_amazon-q-developer-agent-20240719-dev/logs (0 report files); 499 cells: no report file |
| `20250120_Bracket` | 425 | 425/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20250120_Bracket/logs (483 report files); 75 cells: report file empty, malformed or for another instance |
| `20250720_mini-v0.0.0-claude-3-7-sonnet-20250219` | 99 | 99/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20250720_mini-v0.0.0-claude-3-7-sonnet-20250219/logs (98 report files); 401 cells: no report file |
| `20250720_mini-v0.0.0_gpt-4.1-mini-2025-04-14` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source none (0 report files); fetch error: no public logs located; tried s3://swe-bench-submissions/bash-only/20250720_mini-v0.0.0_gpt-4.1-mini-2025-04-14/logs, s3://swe-bench-submissions/verified/20250720_mini-v0.0.0_gpt-4.1-mini-2025-04-14/logs; 500 cells: no report file |
| `20250726_mini-v1.0.0_gemini-2.5-flash` | 418 | 418/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20250726_mini-v1.0.0_gemini-2.5-flash/logs (418 report files); 82 cells: no report file |
| `20250726_mini-v1.0.0_gpt-4.1-2025-04-14` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source none (0 report files); fetch error: no public logs located; tried s3://swe-bench-submissions/bash-only/20250726_mini-v1.0.0_gpt-4.1-2025-04-14/logs, s3://swe-bench-submissions/verified/20250726_mini-v1.0.0_gpt-4.1-2025-04-14/logs; 500 cells: no report file |

### Validity checks

- **Consistency stop rule:** 1 inconsistent measured cells out of 82905 (0.0012%; stop at > 0.5%): 1 resolved with score < 1, 0 unresolved with score = 1.
- **Gold-list agreement:** 66 reports across 61 systems have FAIL_TO_PASS or PASS_TO_PASS test sets differing from the pinned gold lists (reported, not excluded): `20241202_amazon-q-developer-agent-20241202-dev` 3, `20241208_gru` 2, `20250122_autocoderover-v2.1-claude-3-5-sonnet-20241022` 2, `20260901_mini-v2.4.2_gemini-3-5-flash` 2, `20240620_sweagent_claude3.5sonnet` 1, `20240728_sweagent_gpt4o` 1, `20240820_epam-ai-run-gpt-4o` 1, `20240820_honeycomb` 1, `20240824_gru` 1, `20240918_lingma-agent_lingma-swe-gpt-72b` 1….
- **Report versus official resolved list:** 175 systems publish an official resolved list (`results.json` or `per_instance_details.json`); 79189 reports compared, 396 disagreements in 22 systems: `20260226_mini-v2.0.0_gemini-3-pro-high` 353/500, `20250522_sweagent_claude-4-sonnet-20250514` 12/500, `20240612_MASAI_gpt4o` 3/473, `20250405_amazon-q-developer-agent-20250405-dev` 3/500, `20250410_cortexa` 3/500, `20250415_openhands` 3/498, `20250623_warp` 2/494, `20250627_agentless_MCTS-Refine-7B` 2/461, `20260217_mini-v2.0.0_claude-4-5-haiku-high` 2/500, `20241208_gru` 1/500.
- **Coverage:** 164 included systems (underpowered below 20); common cohort 424 tasks (unmeasured if empty).
- **Locked settings:** True. p-val=n/a; no hypothesis test run; protocol uses intervals and split summaries. Separate task/system percentile bootstraps conditional on the observed cohort; split percentiles are not population intervals.

### Reading the validity checks

- **The one inconsistent cell** is `20250516_cortexa_o3` on `matplotlib__matplotlib-20826`: the report says `resolved: true` while listing PASS_TO_PASS failures (T_keep 0.079). It is kept as measured (the stop rule is 0.5%); it is the single "resolved with score < 1" cell in every H3 row.
- **Gold-list drift** (66 reports in 61 systems) is concentrated on a handful of tasks whose test lists changed between dataset revisions (for example `astropy__astropy-7166`, `-7336`, `-7671`); the protocol uses the report's own lists as denominators, so these cells are measured, and the count is reported for transparency.
- **Report versus official resolved list.** 353 of the 396 disagreements come from `20260226_mini-v2.0.0_gemini-3-pro-high`, whose committed `per_instance_details.json` marks every one of its 500 tasks unresolved while its reports resolve 353/500 (70.6%) against a leaderboard entry of 69.6%; the official file is a placeholder, and the reports are the measurement. `20250522_sweagent_claude-4-sonnet-20250514` has 12 matplotlib tasks resolved in its reports but absent from its `results.json` (345 versus 333). Both are reported, neither is excluded; pass@1 everywhere in this record is the report's `resolved` flag, as the protocol specifies.
- **Sensitivity caveat.** `tags.model_display` is submitter-provided: 20 included systems name no model ("Undisclosed" or absent) and are skipped; a few values name a system rather than a model (for example "4x Scaled", "Multiple", "TTS(Bo8)"); and spelling variants beyond token order (for example "Claude 3.5-Sonnet-20241022" versus "Claude 3.5 Sonnet") are not merged. The sensitivity is reported as-is and is not primary.

## Deviations and open questions

- **10-07-2026, adapters for where the public logs actually live (recorded before the analysis ran).** The protocol names `s3://swe-bench-submissions/verified/<submission>/logs/<instance>/report.json` or the repository in `assets.repo`. At the pinned commit, 163 entries' `assets.logs` point to S3 (the mini-SWE-agent "bash-only" runs live under `bash-only/`, not `verified/`); 10 list `logs: null` although their logs are public beside `assets.trajs`; 3 differ from the S3 prefix by letter case, 1 names the submission root without `/logs`, 2 have a null or relative `assets.logs` but exist under the folder-name convention, and 1 (`20260901_mini-v2.4.2_gemini-3-5-flash`) is self-hosted on GitHub (`assets.repo`, commit `2f6637a2`, 441 instance folders, fetched by a blobless depth-1 sparse clone). `fetch_e07.py` resolves the location from metadata in that order and records the rule per row in `inventory.json`; two submissions publish `all_preds.jsonl` as a JSON array and are rewritten as JSON Lines; an invalid predictions file is discarded rather than read as "no generation".
- **10-07-2026, second official `report.json` shape (a parser fix after a first analysis run; both runs preserved).** The first analysis run (16:21 PDT) left 17,964 cells unmeasured as "report unreadable": sb-cli and mini-SWE-agent (2025 onward) write the report dict at the top level of `report.json` with no instance-id key, while the 2024 harness nests it under the instance id. `read_report` now accepts both shapes (a file keyed by another instance is still no evidence). Run 1 (129 systems, 432-task cohort) is kept in `expt_v1/results/run1_before_report_format_fix/`; run 2 (164 systems, 424 tasks) is the published analysis. The verdict pattern is identical in both runs (run 1: H1 ρ 0.984, H1b ρ 0.779 [0.584, 0.828], H2 median Δ −0.013 with share 0.030, H3 share 0.180). The frozen forecast, thresholds and `PROTOCOL.md` were not touched.
- **Official resolution fallback.** The mini-SWE-agent entries have no `results.json`; `per_instance_details.json` (committed in SWE-bench/experiments) supplies known official resolutions for the declared-denominator diagnostic `pass1_declared` and for the report-versus-official validity check. Measured cells always use the report's own `resolved` flag.
- **10-07-2026, review fixes.** Prediction validation now rejects non-string, non-null patches both during fetch and when reading an existing cache; ambiguous duplicate patch presence stays unknown unless a report or official no-generation list supplies evidence. Identical duplicate rows remain usable. Metadata-copy and source-resolution failures now produce per-submission error receipts instead of aborting the inventory. The H1b headline's reversed interpretation was corrected. A full locked rerun leaves every analysis value, system row and cell receipt unchanged; no threshold, forecast, task or submission changed.
- **Exclusions (18 of 182, all listed above with counts).** 13 submissions from 2023-10 to 2024-07 publish only the legacy flat `<instance>.<submission>.eval.log` text files, with no `report.json` and no structured per-test status, so they are excluded with that reason (protocol: "a submission whose logs lack per-test status is excluded"); parsing those text logs would be a new, unlocked parser. 2 submissions have no public logs at all (only `trajs/` on S3). 3 have partial public logs (98, 418 and 483 report files; `20250120_Bracket`'s 75 missing reports are zero-byte files at the source). The 95% inclusion rule and the 500-task denominator are unchanged.
- **Code revision.** Protocol pin: the commit that added `PROTOCOL.md` (`7b3ad352`). Reviewed fixes before dispatch: `5feb25b` / `39b575e` (master's Codex light QA). Worker changes (adapters, flat-report parsing, unmeasured reasons, exclusion reasons, official-resolution fallback, report-versus-official check, base-model sensitivity, renderer, `Cell.unmeasured_reason`) are in `main` commits `42384e0` (phase A) and `e9f6062` (Codex light-QA round), landed through merge commit `788da956ffccb1ccca18a4a47f5eb80c72afdf30` (`LANDED` line in `expt_v1/CKPT_e07.md`).
- **Open questions (for Emily and Brando).** (1) H2's negative Δ is small but consistent across sizes: is the partial credit adding noise at the system level, or is 2,000-split Spearman simply saturated near 0.95? A per-task variance decomposition would tell. (2) The level bias (+0.19) means SCS4C-T cannot replace pass@1 as a headline number without a mapping. (3) Phase B's D_gold factor is the untested part of the definition.

## Local light-review receipt — 10-07-2026

- **Scope:** original base `7b3ad352088753b3cce27063d662b37b0c2ecabc` through `94c95efdfaaca2956fb4d406cfe1c689132022a6` and owned working-tree corrections; no commit or push. Other sessions' paths were not edited.
- **Reviewer:** Codex, launched as `gpt-6-astra` with `model_reasoning_effort=ultra` and `--dangerously-bypass-approvals-and-sandbox` (verified process flags); one review round, with bounded read-only source lookups. Builder recorded as Claude Code / Opus 5.5 in the protocol; builder effort unverified. Classification: scoring/scientific integrity and funding rules; no benchmark reference edits.
- **Verification:** `make test` passed after every code edit; final suite 71 passed, 2 skipped. The skips require an available VeriBench experiment-103 checkout. Synthetic regressions cover parser gaps, constant/nonfinite correlations, all-undefined splits, zero/underpowered/empty-common cohorts, inconsistent reports, manifest membership, input pins, interrupted downloads and complete cell receipts. No real phase A outcomes were read for this review.
- **Integrity:** `git diff --check` passed; no broken local Markdown paths found; all three frozen forecast files match `94c95ef` byte for byte and `verify_forecast` returned true. Protocol prediction and threshold rows are unchanged.
- **Structural finding (minor):** `analyze_e07.py:main` remains 77 lines with input validation, orchestration and status assembly. Output writing and shared report parsing are separated; a broader refactor was deferred to keep this correction focused. No dead code or material duplication requiring removal was identified.
- **Verdict:** FIXED. Required log adapters, model sensitivity, dispatch receipt and real-data reporting remain explicitly assigned to the worker; this receipt does not claim completion of the experiment.

## Fetch and analysis receipts — 10-07-2026 (worker)

- **Host and process:** `skampere1`, tmux `rl4cv-e07-worker`, Claude Code `claude-fable-5-1` / `max` with `--dangerously-skip-permissions` (pid 2601116); isolated clone `/lfs/skampere1/0/brando9/rl4cv_e07/rl-4-code-verification` on `main`, started at `1fa4520`.
- **Environment:** `uv venv` Python 3.12.14; numpy 2.5.3, scipy 1.18.1, datasets 5.1.0, boto3 1.43.109, pyyaml 6.0.3, pytest 9.1.1, aws-cli 1.46.1 (unsigned S3). `make test`: 81 passed, 2 skipped (the skips need a VeriBench experiment-103 checkout).
- **Inputs:** `SWE-bench/experiments` at `40f164d5b8f1d249bf95a6df8b74b577fd8e519d` (182 `evaluation/verified` entries, clean tree); gold lists from `princeton-nlp/SWE-bench_Verified` split `test` revision `c104f840cc67f8b6eec6f759ebc8b2693d585d4a` (500 tasks; SHA-256 in `expt_v1/results/inputs_manifest.json`). Frozen forecast verified (`verify_forecast` → True; sidecar `af0d4678…`).
- **Fetch:** two runs of the identical command (16:08–16:15 and 16:17–16:20 PDT; the second added the asset-resolution fixes and layout fields), 8 parallel unsigned `aws s3 sync` jobs plus one GitHub sparse clone; 1.9 GB of `report.json` and `all_preds.jsonl` files stay on the host. Inventory: 47 submissions with 500 reports, 105 with 475–499, 15 with 1–474, 15 with 0.
- **Analysis:** `analyze_e07.py` with locked defaults (seed 20261007, 2,000 bootstrap draws, 2,000 splits, sizes 25/50/100/250, inclusion ≥ 95%); run 1 16:21–16:22 PDT, run 2 16:24–16:25 PDT (64 s each). `locked_settings: true`. Outputs committed: `analysis_e07.json`, `per_system_e07.csv`, `per_cell_e07.jsonl.gz` (0.65 MB, one receipt per declared cell), `results_tables_e07.md`, `inventory.json`, `inputs_manifest.json`, and `run1_before_report_format_fix/`.
- **Model calls:** none for the experiment; the only model use is the requested Codex light-QA review (receipt below). VeriBench untouched.

## Worker-change light-review receipt — 10-07-2026

- **Reviewer and round (Brando requested light QA with Codex):** Codex CLI 0.154.0, model `gpt-6-astra`, `model_reasoning_effort="ultra"`, `--dangerously-bypass-approvals-and-sandbox`, ChatGPT subscription login (banner verified in the run log; session `01a118b7-3fb9-7ab2-87b9-18cb7de2d11f`); one round 16:33–16:43 PDT, stdin closed; acceptance role; classification: scientific results and scoring integrity (strongest-model reviewer required and used). Builder: Claude Code `claude-fable-5-1` / `max`. Fixes were applied by the reviewer and verified deterministically by the builder: `make test` 93 passed, 2 skipped; a locked rerun of the analysis reproduced `per_system_e07.csv`, all 91,000 cell receipts and the rendered tables byte for byte (the JSON differs only in the recorded output directory); all 32 prose figures re-checked against `analysis_e07.json`; `git diff --check` clean. No second review round (one-round light QA).

```
VERDICT: FIXED
CRITICAL_ISSUES: 0
MAJOR_ISSUES: 3
FIXES_APPLIED: 3
STRUCTURAL: IMPROVED
SUMMARY: Fixed three major issues; 93 tests passed, two skipped. The locked analysis and all 91,000 receipts reproduce unchanged; frozen files remain untouched, with no experiment model calls, VeriBench changes, commits, or pushes.
```

- **Scope and outcome:** Codex reviewed base `1fa4520f813ac56e1b4813a444e303d22f677bb2` through the owned working tree, including worker commit `42384e0` and uncommitted changes; one requested round. Three major findings fixed: invalid or conflicting prediction evidence, incomplete per-submission error capture, and the reversed H1b interpretation. No critical finding; no commit or push.
- **Verification:** `make test` passed after each code change; final suite 93 passed, 2 skipped. A full analysis rerun with locked settings reproduces every analysis value, all 182 system rows and all 91,000 cell receipts. An independent raw-input audit reconciles all 91,000 cells; the six primary correlation estimates match SciPy. Every rendered numerical section matches the source analysis and system table; all 73 sensitivity selections and 20 unnamed-system skips match metadata.
- **Integrity:** `PROTOCOL.md` and all frozen forecast files are unchanged, and the forecast hash verifies. Checks used existing public inputs, with no experiment model calls, data downloads or VeriBench data access. The existing checkpoint edits were preserved.
- **Structure (minor, deferred):** the analysis `main` remains 84 lines; the parsers, source resolver, bootstrap and sensitivity functions also contain multiple decision branches. Prediction validation is shared between fetch and analysis; no further refactor was needed for these corrections, and no dead code requiring removal was identified.

**TLDR-end:** [rl4cv: experiment 07 phase A, SCS4C-T versus pass@1 across SWE-bench Verified submissions] Across 164 public submissions, SCS4C-T ranks systems like pass@1 (H1 holds) and its partial credit on failed tasks tracks capability (H1b positive, ρ 0.736 [0.507, 0.801]), but 50-task SCS4C-T predicts held-out pass@1 slightly worse than pass@1 itself (H2 forecast failed, median Δ −0.012); partial credit is informative, not a better ranker, so phase C stays justified while phase B awaits the D_gold harness.
