# Experiment 01 results — small open-weight Qwen models on VeriBench V1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md>

**TLDR:** The GPU run on `skampere1` (GPUs 2–7) is **complete**: full G=1 eval (9 models × 896 tasks) and G=8 probe (8 models × 128 tasks × 8 samples) jobs, launched 09-30-2026 12:31, all generated, kernel-scored and FSC-judged as of 10-01-2026 12:35 — every declared cell has a terminal receipt (reopened 12:16 to fix one omission: Qwen3.5-0.8B's row and FSC audit, below). D-101 (self-hosted inference) and D-102 (FSC judge route: `vb103_judge` Valkyrie, payer: Vals gateway) are both accepted; the judge's own controls passed on a new, isolated Valkyrie benchmark service. Near-zero IC_tests/IC_proofs throughout, as hypothesized, with one exception: **Qwen3-14B produced the experiment's first (and only) fully-compiling, fully-proving cell** (1/896, SCSC≈0.928). **Gate G1 resolves to PASS**: two models (Qwen3-14B, 6 splits, max 0.333; Qwen3.5-9B, 4 splits, max 0.25) clear the locked kernel_binary mixed-group-share ≥ 0.20 threshold; the other 6 of 8 probe-scored models show exactly 0.0 overall mixed-group share — the signal is thin and concentrated in the two largest probed models. Interesting secondary observation (diagnostic only, not SCSC-relevant since still 0 positive cells): **Qwen3.6-27B's ungated audit FSC (0.771) is far higher than every smaller model's (0.01–0.46 range)** — a more capable model produces more plausible-looking Lean even when it still doesn't compile/prove. Total judge spend: **$106.37 of $400**.

## Judge spend (running total against the $400 cap) — final, all runs harvested

| Suite | Members | Cells | Status | Charges (USD) |
|---|---|---:|---|---:|
| `rl4cv-e01-controls` | H2_sol_high + H2_opus55_max | 60 × 2 | measured, verdict PASS | 4.57 |
| `rl4cv-e01:qwen3.5-4b` (audit only, 0 main cells) | H2_sol_high + H2_opus55_max | 60 × 2 | 117/120 measured (3 `unmeasured_infra` on H2_opus55_max) | 13.49 |
| `rl4cv-e01:qwen3-8b` (audit only, 0 main cells) | H2_sol_high + H2_opus55_max | 60 × 2 | 120/120 measured | 13.17 |
| `rl4cv-e01:qwen3-14b` (1 main cell + audit) | H2_sol_high + H2_opus55_max | 61 × 2 | 121/122 measured (1 `unmeasured_infra` on H2_opus55_max) | 14.67 |
| `rl4cv-e01:qwen3-4b` (audit only, 0 main cells) | H2_sol_high + H2_opus55_max | 60 × 2 | 120/120 measured | 12.90 |
| `rl4cv-e01:qwen3.5-9b` (audit only, 0 main cells) | H2_sol_high + H2_opus55_max | 60 × 2 | 118/120 measured (2 `unmeasured_infra` on H2_opus55_max) | 15.14 |
| `rl4cv-e01:qwen3.5-2b` (audit only, 0 main cells; only 51 audit cells — see note) | H2_sol_high + H2_opus55_max | 51 × 2 | 102/102 measured | 8.30 |
| `rl4cv-e01:qwen3-1.7b` (audit only, 0 main cells) | H2_sol_high + H2_opus55_max | 57 × 2 | 114/114 measured | 9.14 |
| `rl4cv-e01:qwen3.6-27b-local` (audit only, 0 main cells) | H2_sol_high + H2_opus55_max | 52 × 2 | 103/104 measured (1 `unmeasured_infra` on H2_opus55_max) | 11.17 |
| `rl4cv-e01:qwen3.5-0.8b` (audit only, 0 main cells; only 37 audit cells — see note; added 10-01-2026 12:16, the omission this reopen fixed) | H2_sol_high + H2_opus55_max | 37 × 2 | 74/74 measured | 3.82 |

**Final total: $106.37 of $400.** Every admitted FSC run is now harvested; no further Valkyrie spend is expected for this experiment.

Last updated: 10-01-2026 12:35.

## Pipeline validation on CPU (09-30-2026, not the locked preflight)

Run in a 4-CPU cloud container with no GPU, using the transformers backend, the current v7 pack, thinking off and 3 tasks. Every stage ran: prompt construction from experiment 103's pinned code, generation, extraction, scorer jobs, the frozen scorer (`59059a20d`, Lean v4.22.0, Mathlib v4.22.0 from `lake exe cache get`), collection and summary. Evidence: [`expt_v1/results/pipeline_validation_cpu_09-30-2026.json`](expt_v1/results/pipeline_validation_cpu_09-30-2026.json).

| Cell | IC_tests | IC_proofs | Theorems proved | Verdict |
|---|---:|---:|---|---|
| Gold `easy_set__1_myadd` | 1.0 | 1.0 | 6 / 6 | control passes |
| Gold `cs_set__binary_search` | 1.0 | 1.0 | 13 / 13 | control passes |
| Empty file | 0.0 | 0.0 | — | control passes |
| Gold with one proof replaced by `sorry` | 1.0 | 0.667 | 4 / 6 (the `sorry` also reaches a `@[simp]` user) | control passes |
| Qwen3-0.6B on `easy_set__1_myadd`, `easy_set__10_myevensumparity`, `cs_set__binary_search` | 0.0 | 0.0 | 0 compile of 3 | measured on 3 cells only |

Qwen3-0.6B's answers (305, 1,047 and 754 generated tokens, all finished cleanly and extracted) are Lean-3-like pseudo-code (`module`, `definition … where`, `is_int(a)`, `<name>_prop`), matching the failure pattern experiment 103 found for Qwen3.6-27B. Generation ran at about 3 tokens per second on CPU, so the declared 896-task run needs the GPU hosts in [`scripts/cc_prompt_run_experiment_on_snap.md`](../../scripts/cc_prompt_run_experiment_on_snap.md).

## VeriBench V1, G = 1, experiment 103 single-call protocol

The denominator is always 896 declared cells per model. Unmeasured cells are listed, never counted as 0.

| Model | Revision | Measured / 896 | Cut off | No Lean | Compile rate | IC_tests | IC_proofs | FSC | SCSC |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-0.8B | `2fc06364` | 896/896 | 661 | 95 | 0.45% | 0.0 | 0.0 | 0.011* | 0.0 (exact) |
| Qwen3.5-2B | `15852e8c` | 896/896 | 475 | 310 | 0.33% | 0.0 | 0.0 | 0.073* | 0.0 (exact) |
| Qwen3.5-4B | `851bf6e8` | 896/896 | 12 | 3 | 0.45% | 0.0011 | 0.0 | 0.328* | 0.0 (exact) |
| Qwen3.5-9B | `c2022362` | 896/896 | 5 | 1 | 0.56% | 0.0 | 0.0 | 0.414*† | 0.0 (exact) |
| Qwen3-1.7B | `70d244cc` | 896/896 | 252 | 290 | 0.0% | 0.0 | 0.0 | 0.097* | 0.0 (exact) |
| Qwen3-4B | `1cfa9a72` | 896/896 | 37 | 37 | 0.0% | 0.0 | 0.0 | 0.365* | 0.0 (exact) |
| Qwen3-8B | `b968826d` | 896/896 | 41 | 41 | 0.22% | 0.0022 | 0.0 | 0.372* | 0.0 (exact) |
| Qwen3-14B | `40c06982` | 896/896 | 21 | 21 | 0.56% | 0.0056 | 0.0011 | 0.462** | 0.00104 (exact) |
| Qwen3.6-27B (local route control) | `6a9e13bd` | 896/896 | 236 | 0 | 0.22% | 0.0011 | 0.0 | 0.771§ | 0.0 (exact) |
| *Reference: Qwen3.6-27B via Valkyrie (experiment 103)* | | *604* | *245 at cap* | | | *0.002* | *0.002* | *0.900* | *0.002* |

\* FSC for Qwen3.5-0.8B, Qwen3.5-2B, Qwen3.5-4B, Qwen3.5-9B, Qwen3-1.7B, Qwen3-4B and Qwen3-8B is the **ungated diagnostic mean over the core-split audit only** (0 cells reach the gated `fsc_compiled` scope per D-003, since all seven have 0 cells with IC_tests · IC_proofs > 0). SCSC is exact at 0.0 for all seven. Per-task FSC: `expt_v1/results/fsc_qwen3.5-0.8b.json`, `fsc_qwen3.5-2b.json`, `fsc_qwen3.5-4b.json`, `fsc_qwen3.5-9b.json`, `fsc_qwen3-1.7b.json`, `fsc_qwen3-4b.json`, `fsc_qwen3-8b.json`. Qwen3.5-0.8B's audit pack has only **37** cells and Qwen3.5-2B's only **51**, not 60 — one or more core splits had fewer than 12 tasks eligible for the audit at these models' scored output; `build-model`'s round-trip still returned `verdict: PASS` for both. Qwen3.5-0.8B's FSC audit was omitted from the first completion pass and added in the 10-01-2026 12:16 reopen (master-caught); see `REPORT.md` for the writeup.

† Qwen3.5-9B's `H2_opus55_max` member hit 2 `unmeasured_infra` cells (58/60 measured); its FSC mean (0.414) is over the 58 cells where both members measured, with the 2 incomplete items listed, not dropped or counted as zero (`expt_v1/results/fsc_qwen3.5-9b.json` → `items_incomplete`).

§ Qwen3.6-27B's judge run (52 audit cells × 2 members, port 9708) harvested 10-01-2026 09:08 — the last FSC measurement the experiment needed. Its own IC_tests (0.0011, i.e. 1/896) is nonzero like Qwen3-14B's, but that cell's IC_proofs is 0.0, so it still has **0** cells with IC_tests · IC_proofs > 0; SCSC stays exact at 0.0. Its ungated audit FSC mean (0.771, over 51/52 cells — 1 `unmeasured_infra`) is notably higher than every smaller model's (0.07-0.46): a qualitative sign that a more capable model produces more plausible/well-formed Lean even when it still doesn't compile or prove, consistent with — but not proof of — a capability gradient this project does not otherwise measure. Per-task FSC: `expt_v1/results/fsc_qwen3.6-27b-local.json`.

\*\* Qwen3-14B has **one** cell with IC_tests · IC_proofs > 0 — `hardware_set_real__my_interrupt_preempt` (IC_tests 1.0, IC_proofs 1.0, FSC 0.8) — the experiment's first fully-compiling, fully-proving, judge-scored cell among the ≤14B models. Its SCSC = (1.0 · 1.0 · 0.8)^(1/3) ≈ 0.928, which is why the model's overall `SCSC_exact_where_available` (0.00104, exact over all 896 cells now that this one cell's FSC landed) is nonzero while every other model's stays exactly 0.0. The 0.462 FSC column value is still the ungated mean over the 60-item audit plus this one positive cell (61 cells total, 1 `unmeasured_infra`); see `expt_v1/results/fsc_qwen3-14b.json`.

## Compute estimate (09-30-2026, skampere1, before launch)

- **Host/GPUs.** `skampere1`, 8× A100-SXM4-80GB. GPUs 0–2 belong to user `truongvo` (busy) and are never touched; GPUs 3–7 idle (0 MiB, 0%) at baseline. GPU rule (B200 → H200 first) not met: `skampere3` `/lfs` 100% full (21 GB free) and 7/8 GPUs busy; `skampere2` `/lfs` 100% full (99 GB free) and GPUs shared with 4 other users. Using `skampere1` instead.
- **G = 1 generation (9 models × 896 tasks).** From `PROTOCOL.md`: 1–3 GPU-hours/model up to 9B (7 models: Qwen3.5-0.8B/2B/4B/9B, Qwen3-1.7B/4B/8B → 7–21 GPU-hours), 3–8 GPU-hours for 14B and 27B (Qwen3-14B, Qwen3.6-27B-local → 6–16 GPU-hours). **Subtotal: 13–37 GPU-hours.**
- **G = 8 probe (8 models × 132 tasks × 8 samples, control excluded).** 1,056 generations/model at a 12,288-token cap (0.19× the eval cap) vs. 896 at 65,536. Estimated at ≈0.2–0.7 GPU-hours/model for the ≤9B/8B models and ≈0.7–1.8 GPU-hours for the 14B model. **Subtotal: ≈2–7 GPU-hours.**
- **Total generation: ≈15–44 GPU-hours.** Scoring: 1–5 CPU-hours per 896-file job × 9 eval jobs (9–45 CPU-hours) plus 64 probe scoring jobs (8 models × 8 samples) of 132 files each (≈10–50 CPU-hours combined), parallelizable across the host's 128 cores and independent of the GPU critical path.
- **Wall-clock.** One model per free GPU, in parallel across GPUs 3–7 (5 devices), smallest→largest: **≈4–12 hours** for all 9 eval + 8 probe jobs, dominated by the 14B/27B cells and by any cells that hit the token cap (experiment 103 saw 245/896 cells hit the 65,536 cap for Qwen3.6-27B).
- **Go.** Brando's "run my experiments on snap!" (09-30-2026) plus his earlier "just do the experiment ... Go" cover this GPU run (cc.md §5 "Ask"); posted to issue #3 before launch, launching without further wait per `DISPATCH_e01.md`.

## Signal probe, G = 8, 128 tasks (4/split × 32 present splits)

**Gate G1 verdict (PROTOCOL.md § Locked parameters), final over all 8 probe-scored models: PASS.** The locked criterion ("any model, any split reaches a mixed-group share ≥ 0.20") is monotonic and was already decisive early from Qwen3-14B alone; with all 8 models now scored, **two** models clear it, and the signal is otherwise thin:
- **Qwen3-14B**: `kernel_binary` mixed-group share (the fraction of its 8-sample groups with non-uniform kernel-binary reward — `rl4cv.experience.q_mixed_empirical`) reaches **≥ 0.20 on 6 splits** (max 0.333): `aerospace_set_real` 0.333, `concurrent_set_real` 0.25, `finance_set_synthetic` 0.25, `gov_cert_set_synthetic` 0.25, `hardware_set_real` 0.25, `medical_oss_set_real` 0.25.
- **Qwen3.5-9B**: reaches **≥ 0.20 on 4 splits** (max 0.25): `compilers_set_synthetic` 0.25, `concurrent_set_real` 0.25, `medical_oss_set_real` 0.25, `os_embedded_set_synthetic` 0.25 (overlapping `concurrent_set_real`/`medical_oss_set_real` with Qwen3-14B).
- Both channels (`kernel_binary`/`proof_fraction`) are identical for every model, since the only measured reward difference between the two channels anywhere in the probe is the same handful of proving cells.
- **The other 6 of 8 probe-scored models (Qwen3.5-0.8B, Qwen3.5-2B, Qwen3.5-4B, Qwen3-1.7B, Qwen3-4B, Qwen3-8B) show exactly 0.0 overall mixed-group share on every split** (0/128 groups mixed each) — consistent with their 0% proof rate on the full 896-task eval. The signal is thin: only the two largest probed models (9B, 14B) produce any mixed groups at all, and even for them the overall mixed-group share is small (3.1-4.7%) — it is the **per-split max**, not the overall rate, that clears the locked 0.20 threshold.

Per README §Decision criterion, the union of Qwen3-14B's 6 splits and Qwen3.5-9B's 4 splits (8 distinct: `aerospace_set_real`, `compilers_set_synthetic`, `concurrent_set_real`, `finance_set_synthetic`, `gov_cert_set_synthetic`, `hardware_set_real`, `medical_oss_set_real`, `os_embedded_set_synthetic`) seed experiment 02's pools.

| Model | Channel | Mean reward | Mixed-group share (overall) | ρ (overall) | H (overall) | Max per-split mixed-group share |
|---|---|---:|---:|---:|---:|---:|
| Qwen3.5-0.8B | kernel_binary | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Qwen3.5-0.8B | proof_fraction | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Qwen3.5-2B | kernel_binary | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Qwen3.5-2B | proof_fraction | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Qwen3.5-4B | kernel_binary | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Qwen3.5-4B | proof_fraction | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Qwen3.5-9B | kernel_binary | 0.0039 | 0.0312 | 2.06 | 0.0312 | **0.25** (`compilers_set_synthetic`, 3 others tied) |
| Qwen3.5-9B | proof_fraction | 0.0039 | 0.0312 | 2.06 | 0.0312 | **0.25** (`compilers_set_synthetic`, 3 others tied) |
| Qwen3-1.7B | kernel_binary | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Qwen3-1.7B | proof_fraction | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Qwen3-4B | kernel_binary | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Qwen3-4B | proof_fraction | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Qwen3-8B | kernel_binary | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Qwen3-8B | proof_fraction | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Qwen3-14B | kernel_binary | 0.0068 | 0.0469 | 5.98 | 0.0469 | **0.333** (`aerospace_set_real`, 5 others ≥0.20) |
| Qwen3-14B | proof_fraction | 0.0068 | 0.0469 | 5.98 | 0.0469 | **0.333** (`aerospace_set_real`, 5 others ≥0.20) |

"Overall" columns are group-weighted means across all 128 groups (32 splits × 4 tasks); per-split values and `pass@8` are in `expt_v1/results/summaries/rho_h_<label>_g8_<channel>.{json,md}`.
