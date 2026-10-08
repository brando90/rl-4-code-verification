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
