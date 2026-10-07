**Analyzer status:** `PRIMARY ANALYSES COMPUTED`; locked settings: True; seed 20261007; 2000 bootstrap draws; 2000 splits per size; sizes [25, 50, 100, 250]; inclusion ≥ 95% measured.

### Counts

| Quantity | Value |
|---|---:|
| Declared systems (pinned submission list) | 182 |
| Included systems (≥ 475/500 measured cells) | 129 |
| Excluded systems | 53 |
| Declared tasks per system | 500 |
| Common-cohort tasks (measured for every included system) | 432 |
| Declared cells (all systems) | 91000 |
| Measured cells (all systems) | 65018 |
| Unmeasured cells (all systems; listed in `per_cell_e07.jsonl.gz`) | 25982 |
| Inconsistent measured cells (resolved ≠ (G=1, T_fix=1, T_keep=1)) | 1 / 65018 = 0.0015% (stop rule 0.5%) |

### H1 — construct check: system SCS4C-T versus system pass@1 (common cohort)

Usable systems: 129 (0 with undefined scores excluded). p-val=n/a (no hypothesis test; intervals condition on the observed common cohort and are not task-and-system joint intervals).

| Statistic | Value | 95% task bootstrap | 95% system bootstrap |
|---|---:|---|---|
| Pearson r | 0.973 | [0.967, 0.976] (2000/2000 draws defined) | [0.963, 0.982] (2000/2000 draws defined) |
| Spearman ρ | 0.984 | [0.977, 0.986] (2000/2000 draws defined) | [0.963, 0.993] (2000/2000 draws defined) |
| Kendall τ-b | 0.920 | [0.899, 0.924] (2000/2000 draws defined) | [0.885, 0.947] (2000/2000 draws defined) |
| Mean system SCS4C-T | 0.748 | [0.727, 0.767] (2000/2000 draws defined) | [0.723, 0.772] (2000/2000 draws defined) |
| Mean system pass@1 | 0.552 | [0.518, 0.582] (2000/2000 draws defined) | [0.522, 0.582] (2000/2000 draws defined) |
| Mean bias (SCS4C-T − pass@1) | 0.197 | [0.182, 0.211] (2000/2000 draws defined) | [0.188, 0.205] (2000/2000 draws defined) |
| Mean absolute error | 0.197 | [0.182, 0.211] (2000/2000 draws defined) | [0.188, 0.205] (2000/2000 draws defined) |

- **Frozen prediction:** Spearman(system SCS4C-T, system pass@1) >= 0.90 (construct check, partly by construction)
- **Outcome:** prediction holds (Spearman 0.984 ≥ 0.90); construct check only, not evidence of usefulness.

### H1b — partial credit on unresolved cohort cells versus pass@1

Usable systems: 129 (0 without unresolved cohort cells have undefined partial credit and are excluded, never zero: none). p-val=n/a.

| Statistic | Value | 95% task bootstrap | 95% system bootstrap |
|---|---:|---|---|
| Pearson r | 0.805 | [0.641, 0.837] (2000/2000 draws defined) | [0.720, 0.869] (2000/2000 draws defined) |
| Spearman ρ | 0.779 | [0.584, 0.828] (2000/2000 draws defined) | [0.692, 0.846] (2000/2000 draws defined) |
| Kendall τ-b | 0.593 | [0.419, 0.647] (2000/2000 draws defined) | [0.514, 0.667] (2000/2000 draws defined) |

- **Frozen prediction:** Spearman(partial credit on unresolved cohort cells, pass@1) > 0 with 95% task-bootstrap interval excluding 0
- **Outcome:** **Positive**: partial credit carries capability signal (Spearman 0.779, task interval [0.584, 0.828] excludes 0).

### H2 — held-out prediction from random task splits

Δ = Spearman(SCS4C-T on A, pass@1 on B) − Spearman(pass@1 on A, pass@1 on B); B is the rest of the common cohort. Percentiles and shares summarise the split distribution; they are not population confidence intervals. Primary size n_A = 50; other sizes descriptive.

| n_A | n_B | Splits defined / requested | Median Δ | 5th–95th percentile of Δ | Splits with Δ > 0 | Share Δ > 0 | Median ρ(SCS4C-T on A, pass@1 on B) | Median ρ(pass@1 on A, pass@1 on B) |
|---:|---:|---|---:|---|---:|---:|---:|---:|
| 25 | 407 | 2000/2000 | -0.011 | [-0.033, +0.008] | 315 | 0.158 | 0.922 | 0.934 |
| 50 | 382 | 2000/2000 | -0.013 | [-0.027, -0.001] | 60 | 0.030 | 0.948 | 0.962 |
| 100 | 332 | 2000/2000 | -0.014 | [-0.023, -0.006] | 7 | 0.004 | 0.963 | 0.977 |
| 250 | 182 | 2000/2000 | -0.014 | [-0.020, -0.008] | 0 | 0.000 | 0.969 | 0.983 |

- **Frozen prediction:** At n_A = 50 over 2000 random splits: median Delta > 0 and share(Delta > 0) >= 0.60, Delta = Spearman(SCS4C-T on A, pass@1 on B) - Spearman(pass@1 on A, pass@1 on B)
- **Outcome at n_A = 50:** **No ranking advantage**: median Δ -0.013 (≤ 0), share Δ > 0 = 60/2000 = 0.030 (< 0.60).

### H3 — signal density (descriptive)

| Cohort | Declared cells | Measured | Unmeasured | Unresolved | Unresolved with SCS4C-T > 0 | Share | Resolved with score < 1 | Unresolved with score = 1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Included systems × common cohort | 55728 | 55728 | 0 | 24980 | 4490 | 0.180 | 1 | 0 |
| Included systems × own cohorts | 64500 | 64352 | 148 | 30009 | 5111 | 0.170 | 1 | 0 |
| All declared systems × all cells | 91000 | 65018 | 25982 | 30351 | 5127 | 0.169 | 1 | 0 |

### Sensitivity (protocol, not primary): one system per base model

Status: computed. Selection: one system per base model: the latest submission (folder-name date) per metadata tags.model_display, matched on an order-insensitive token key; same common cohort as the primary analysis. Systems: 53; skipped (model not named): 20; common-cohort tasks: 432.

| Hypothesis | Pearson r | Spearman ρ | Kendall τ-b | 95% task bootstrap of ρ | 95% system bootstrap of ρ | n systems |
|---|---:|---:|---:|---|---|---:|
| H1 (SCS4C-T vs pass@1) | 0.977 | 0.990 | 0.935 | [0.983, 0.992] (2000/2000 draws defined) | [0.970, 0.996] (2000/2000 draws defined) | 53 |
| H1b (partial credit vs pass@1) | 0.865 | 0.822 | 0.657 | [0.625, 0.877] (2000/2000 draws defined) | [0.664, 0.915] (2000/2000 draws defined) | 53 |

| n_A | n_B | Splits defined / requested | Median Δ | 5th–95th percentile of Δ | Splits with Δ > 0 | Share Δ > 0 | Median ρ(SCS4C-T on A, pass@1 on B) | Median ρ(pass@1 on A, pass@1 on B) |
|---:|---:|---|---:|---|---:|---:|---:|---:|
| 50 | 382 | 2000/2000 | -0.006 | [-0.022, +0.007] | 424 | 0.212 | 0.961 | 0.967 |

- Sensitivity H1 reading: prediction holds (Spearman 0.990 ≥ 0.90); construct check only, not evidence of usefulness.
- Sensitivity H1b reading: **Positive**: partial credit carries capability signal (Spearman 0.822, task interval [0.625, 0.877] excludes 0).
- Sensitivity H2 reading at n_A = 50: **No ranking advantage**: median Δ -0.006 (≤ 0), share Δ > 0 = 424/2000 = 0.212 (< 0.60).

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
- Gemini 3 Pro Preview: `20251120_livesweagent_gemini-3-pro-preview`
- Claude 3.5 Haiku: `20241022_tools_claude-3-5-haiku`
- Claude 3.5 Sonnet: `20250228_epam-ai-run-claude-3-5-sonnet`
- Gemini 3.5 Flash: `20260901_mini-v2.4.2_gemini-3-5-flash`
- Claude 3.7 Sonnet: `20250514_aime_coder`
- Qwen3-Coder-30B-A3B-Instruct: `20250901_entroPO_R2E_QwenCoder30BA3B_tts`
- Qwen2.5-Coder 32B Instruct: `20250803_mini-v1.0.0_qwen2-5-coder-32b-instruct`
- Claude 4 Opus: `20250802_mini-v1.0.0_claude-4-opus-20250514`
- Claude Sonnet 4: `20250924_artemis_agent_v2`
- Llama 4 Maverick Instruct: `20250720_mini-v0.0.0-Llama-4-Maverick-17B-Instruct`
- Llama 4 Scout Instruct: `20250720_mini-v0.0.0-Llama-4-Scout-17B-Instruct`
- Claude 4.5 Opus: `20251215_livesweagent_claude-opus-4-5`
- Claude 4.5 Sonnet: `20251103_sonar-foundation-agent_claude-sonnet-4-5`
- GLM-4.5: `20250728_zai_glm4-5`
- Claude 4.6 Opus: `20260217_mini-v2.0.0_claude-4-6-opus`
- GLM-4.6: `20250930_zai_glm4-6`
- Qwen3-Coder-480B-A35B-Instruct: `20250805_openhands-Qwen3-Coder-480B-A35B-Instruct`
- GPT 4o: `20250720_mini-v0.0.0-gpt-4o-2024-11-20`
- 4x Scaled: `20250203_openhands_4x_scaled`
- GPT-5: `20251015_Prometheus_v1.2.1_gpt5`
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
- DeepSWE-Preview: `20250629_deepswerl_r2eagent`
- Kimi K2 Instruct: `20250807_mini-v1.7.0_kimi-k2-instruct`
- Kimi K2: `20251014_Lingxi_kimi_k2`
- O3 Mini: `20250214_agentless_lite_o3_mini`
- o4-mini: `20250726_mini-v1.0.0_o4-mini-2025-04-16`
- Multiple: `20251103_SalesforceAIResearch_SAGE_OpenHands`
- o1-preview: `20250117_wandb_programmer_o1_crosscheck5`
- o3: `20250726_mini-v1.0.0_o3-2025-04-16`
- swe-search: `20241221_codestory_midwit_claude-3-5-sonnet_swe-search`

### Per-system table: the 15 highest-pass@1 included systems (full table in `expt_v1/results/per_system_e07.csv`)

| Submission | SCS4C-T (common) | pass@1 (common) | T_fix mean | T_keep mean | Measured / 500 | SCS4C-T (own) | pass@1 (own) | pass@1 declared |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `20251215_livesweagent_claude-opus-4-5` | 0.916 | 0.810 | 0.846 | 0.992 | 499 | 0.905 | 0.794 | 0.792 |
| `20251205_sonar-foundation-agent_claude-opus-4-5` | 0.917 | 0.808 | 0.845 | 0.995 | 500 | 0.912 | 0.794 | 0.794 |
| `20250928_trae_doubao_seed_code` | 0.911 | 0.801 | 0.834 | 0.995 | 500 | 0.904 | 0.788 | 0.788 |
| `20251120_livesweagent_gemini-3-pro-preview` | 0.904 | 0.794 | 0.826 | 0.990 | 499 | 0.896 | 0.776 | 0.774 |
| `20251127_openhands_claude-opus-4-5` | 0.912 | 0.792 | 0.840 | 0.990 | 500 | 0.904 | 0.776 | 0.776 |
| `20250819_ACoder` | 0.902 | 0.787 | 0.818 | 0.994 | 500 | 0.893 | 0.764 | 0.764 |
| `20250804_epam-ai-run-claude-4-sonnet` | 0.900 | 0.782 | 0.819 | 0.989 | 500 | 0.895 | 0.768 | 0.768 |
| `20250902_atlassian-rovo-dev` | 0.903 | 0.782 | 0.819 | 0.995 | 500 | 0.895 | 0.768 | 0.768 |
| `20260217_mini-v2.0.0_claude-4-6-opus` | 0.910 | 0.780 | 0.832 | 0.995 | 492 | 0.903 | 0.768 | 0.756 |
| `20250915_JoyCode` | 0.899 | 0.766 | 0.815 | 0.991 | 500 | 0.889 | 0.746 | 0.746 |
| `20251103_sonar-foundation-agent_claude-sonnet-4-5` | 0.885 | 0.766 | 0.796 | 0.985 | 500 | 0.878 | 0.750 | 0.750 |
| `20250720_Lingxi-v1.5_claude-4-sonnet-20250514` | 0.894 | 0.759 | 0.807 | 0.990 | 500 | 0.885 | 0.746 | 0.746 |
| `20250731_harness_ai` | 0.890 | 0.759 | 0.798 | 0.992 | 500 | 0.884 | 0.748 | 0.748 |
| `20250612_trae` | 0.891 | 0.757 | 0.802 | 0.989 | 499 | 0.890 | 0.754 | 0.752 |
| `20251015_Prometheus_v1.2.1_gpt5` | 0.895 | 0.757 | 0.814 | 0.985 | 500 | 0.889 | 0.744 | 0.744 |

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
| `20250120_Bracket` | 425 | 425/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20250120_Bracket/logs (483 report files); 75 cells: report unreadable |
| `20250225_sweagent_claude-3-7-sonnet` | 3 | 3/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20250225_sweagent_claude-3-7-sonnet/logs (498 report files); 497 cells: report unreadable |
| `20250511_sweagent_lm_32b` | 4 | 4/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20250511_sweagent_lm_32b/logs (496 report files); 496 cells: report unreadable |
| `20250522_tools_claude-4-opus` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20250522_tools_claude-4-opus/logs (500 report files); 500 cells: report unreadable |
| `20250522_tools_claude-4-sonnet` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20250522_tools_claude-4-sonnet/logs (500 report files); 500 cells: report unreadable |
| `20250623_warp` | 3 | 3/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20250623_warp/logs (494 report files); 494 cells: report unreadable; 3 cells: no report file |
| `20250720_mini-v0.0.0-claude-3-7-sonnet-20250219` | 99 | 99/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20250720_mini-v0.0.0-claude-3-7-sonnet-20250219/logs (98 report files); 401 cells: no report file |
| `20250720_mini-v0.0.0_gpt-4.1-mini-2025-04-14` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source none (0 report files); fetch error: no public logs located; tried s3://swe-bench-submissions/bash-only/20250720_mini-v0.0.0_gpt-4.1-mini-2025-04-14/logs, s3://swe-bench-submissions/verified/20250720_mini-v0.0.0_gpt-4.1-mini-2025-04-14/logs; 500 cells: no report file |
| `20250726_mini-v1.0.0_gemini-2.5-flash` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20250726_mini-v1.0.0_gemini-2.5-flash/logs (418 report files); 418 cells: report unreadable; 82 cells: no report file |
| `20250726_mini-v1.0.0_gpt-4.1-2025-04-14` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source none (0 report files); fetch error: no public logs located; tried s3://swe-bench-submissions/bash-only/20250726_mini-v1.0.0_gpt-4.1-2025-04-14/logs, s3://swe-bench-submissions/verified/20250726_mini-v1.0.0_gpt-4.1-2025-04-14/logs; 500 cells: no report file |
| `20250807_mini-v1.7.0_gpt-5` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20250807_mini-v1.7.0_gpt-5/logs (500 report files); 500 cells: report unreadable |
| `20250807_mini-v1.7.0_gpt-5-mini` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20250807_mini-v1.7.0_gpt-5-mini/logs (500 report files); 500 cells: report unreadable |
| `20250807_mini-v1.7.0_gpt-5-nano` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20250807_mini-v1.7.0_gpt-5-nano/logs (499 report files); 499 cells: report unreadable; 1 cells: no report file |
| `20250822_mini-v1.9.1_glm-4.5` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20250822_mini-v1.9.1_glm-4.5/logs (498 report files); 498 cells: report unreadable; 2 cells: no report file |
| `20250901_warp` | 10 | 10/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/verified/20250901_warp/logs (496 report files); 489 cells: report unreadable; 1 cells: no report file |
| `20250929_mini-v1.13.3_sonnet-4-5-20250929` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20250929_mini-v1.13.3_sonnet-4-5-20250929/logs (499 report files); 499 cells: report unreadable; 1 cells: no report file |
| `20251118_mini-v1.15.0_gemini-3-pro-preview-20251118` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20251118_mini-v1.15.0_gemini-3-pro-preview-20251118/logs (500 report files); 500 cells: report unreadable |
| `20251120_mini-v1.15.0_gpt-5.1-2025-11-13` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20251120_mini-v1.15.0_gpt-5.1-2025-11-13/logs (500 report files); 500 cells: report unreadable |
| `20251124_mini-v1.16.0_claude-opus-4-5-20251101` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20251124_mini-v1.16.0_claude-opus-4-5-20251101/logs (500 report files); 500 cells: report unreadable |
| `20251124_mini-v1.16.0_gpt-5.1-codex` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20251124_mini-v1.16.0_gpt-5.1-codex/logs (500 report files); 500 cells: report unreadable |
| `20251124_mini-v1.17.0_minimax-m2` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20251124_mini-v1.17.0_minimax-m2/logs (499 report files); 499 cells: report unreadable; 1 cells: no report file |
| `20251201_mini-v1.17.1_deepseek-v3.2-reasoner` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20251201_mini-v1.17.1_deepseek-v3.2-reasoner/logs (493 report files); 493 cells: report unreadable; 7 cells: no report file |
| `20251201_mini-v1.17.1_glm-4.6` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20251201_mini-v1.17.1_glm-4.6/logs (499 report files); 499 cells: report unreadable; 1 cells: no report file |
| `20251209_mini-v1.17.2_devstral-2512` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20251209_mini-v1.17.2_devstral-2512/logs (500 report files); 500 cells: report unreadable |
| `20251209_mini-v1.17.2_devstral-small-2512` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20251209_mini-v1.17.2_devstral-small-2512/logs (500 report files); 500 cells: report unreadable |
| `20251210_mini-v1.17.2_kimi-k2-thinking` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20251210_mini-v1.17.2_kimi-k2-thinking/logs (500 report files); 500 cells: report unreadable |
| `20251211_mini-v1.17.2_gpt-5.2-2025-12-11` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20251211_mini-v1.17.2_gpt-5.2-2025-12-11/logs (500 report files); 500 cells: report unreadable |
| `20251211_mini-v1.17.2_gpt-5.2-2025-12-11-high` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20251211_mini-v1.17.2_gpt-5.2-2025-12-11-high/logs (500 report files); 500 cells: report unreadable |
| `20260217_mini-v2.0.0_claude-4-5-haiku-high` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20260217_mini-v2.0.0_claude-4-5-haiku-high/logs (500 report files); 500 cells: report unreadable |
| `20260217_mini-v2.0.0_claude-4-5-opus-high` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20260217_mini-v2.0.0_claude-4-5-opus-high/logs (500 report files); 500 cells: report unreadable |
| `20260217_mini-v2.0.0_claude-4-5-sonnet-high` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20260217_mini-v2.0.0_claude-4-5-sonnet-high/logs (498 report files); 498 cells: report unreadable; 2 cells: no report file |
| `20260217_mini-v2.0.0_deepseek-3-2-high` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20260217_mini-v2.0.0_deepseek-3-2-high/logs (500 report files); 500 cells: report unreadable |
| `20260217_mini-v2.0.0_gemini-3-flash-high` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20260217_mini-v2.0.0_gemini-3-flash-high/logs (500 report files); 500 cells: report unreadable |
| `20260217_mini-v2.0.0_glm-5-high` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20260217_mini-v2.0.0_glm-5-high/logs (500 report files); 500 cells: report unreadable |
| `20260217_mini-v2.0.0_gpt-5-2-high` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20260217_mini-v2.0.0_gpt-5-2-high/logs (500 report files); 500 cells: report unreadable |
| `20260217_mini-v2.0.0_gpt-5-mini` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20260217_mini-v2.0.0_gpt-5-mini/logs (500 report files); 500 cells: report unreadable |
| `20260217_mini-v2.0.0_kimi-k2-5-high` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20260217_mini-v2.0.0_kimi-k2-5-high/logs (500 report files); 500 cells: report unreadable |
| `20260217_mini-v2.0.0_minimax-2-5-high` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20260217_mini-v2.0.0_minimax-2-5-high/logs (500 report files); 500 cells: report unreadable |
| `20260219_mini-v2.0.0_gpt-5-2-codex` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20260219_mini-v2.0.0_gpt-5-2-codex/logs (500 report files); 500 cells: report unreadable |
| `20260226_mini-v2.0.0_gemini-3-pro-high` | 0 | 0/500 measured cells, below the 475 inclusion threshold; logs source s3:s3://swe-bench-submissions/bash-only/20260226_mini-v2.0.0_gemini-3-pro-high/logs (500 report files); 500 cells: report unreadable |

### Validity checks

- **Consistency stop rule:** 1 inconsistent measured cells out of 65018 (0.0015%; stop at > 0.5%): 1 resolved with score < 1, 0 unresolved with score = 1.
- **Gold-list agreement:** 64 reports across 59 systems have FAIL_TO_PASS or PASS_TO_PASS test sets differing from the pinned gold lists (reported, not excluded): `20241202_amazon-q-developer-agent-20241202-dev` 3, `20241208_gru` 2, `20250122_autocoderover-v2.1-claude-3-5-sonnet-20241022` 2, `20260901_mini-v2.4.2_gemini-3-5-flash` 2, `20240620_sweagent_claude3.5sonnet` 1, `20240728_sweagent_gpt4o` 1, `20240820_epam-ai-run-gpt-4o` 1, `20240820_honeycomb` 1, `20240824_gru` 1, `20240918_lingma-agent_lingma-swe-gpt-72b` 1….
- **Report versus official resolved list:** 175 systems publish an official resolved list (`results.json` or `per_instance_details.json`); 62219 reports compared, 37 disagreements in 17 systems: `20250522_sweagent_claude-4-sonnet-20250514` 12/500, `20240612_MASAI_gpt4o` 3/473, `20250405_amazon-q-developer-agent-20250405-dev` 3/500, `20250410_cortexa` 3/500, `20250415_openhands` 3/498, `20250627_agentless_MCTS-Refine-7B` 2/461, `20241208_gru` 1/500, `20250110_learn_by_interact_claude3.5` 1/410, `20250122_autocoderover-v2.1-claude-3-5-sonnet-20241022` 1/495, `20250226_swerl_llama3_70b` 1/495.
- **Coverage:** 129 included systems (underpowered below 20); common cohort 432 tasks (unmeasured if empty).
- **Locked settings:** True. p-val=n/a; no hypothesis test run; protocol uses intervals and split summaries. Separate task/system percentile bootstraps conditional on the observed cohort; split percentiles are not population intervals.
