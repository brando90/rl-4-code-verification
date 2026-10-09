# Experiment 05 results — Qwen3 Base 1.7B/4B/8B on VeriBench V1 at G=8

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/results.md>

**TLDR:** The Qwen3 Base G=8 signal check that decides whether RL on Lean code verification needs a supervised fine-tuning (SFT) warm start is complete. All 21,504 declared cells (3 models × 896 VeriBench V1 tasks × 8 samples) are generated and kernel-scored. The `kernel_binary` mixed-group share over 896 tasks is 0.000 for Qwen3-1.7B-Base (the deciding model, 95% Wilson [0.000, 0.004], p=1.1e-20 against the 0.05 threshold) and Qwen3-8B-Base, and 0.006 for Qwen3-4B-Base (95% Wilson [0.002, 0.013], p=2.4e-14) — all three verdicts are **SFT warm start needed**.

**Status:** DONE (10-05-2026 23:56)

**Last updated:** 10-09-2026 (count correction, see note below)

**Correction (10-09-2026):** two counts below were wrong; the verdicts and every other number are unaffected.
- The execution-diagnostics table's Qwen3-1.7B-Base "Compiling (`IC_tests=1`)" cell said 34 of 7,168. The receipts (`IC_tests` mean 0.00028 × 7,168 ≈ 2) show only **2 of 7,168** cells satisfy `IC_tests = 1`; corrected below.
- The "Representative completions" section said "the one genuine `kernel_binary = 1` pass across all 21,504 cells." The headline table's own Qwen3-4B-Base pass@8 share (0.006 ≈ 5/896 tasks) and the Core/IndustrySet histograms (1 task at k=1 in Core, 4 at k=1 in IndustrySet) show **5 passes for Qwen3-4B-Base alone**, not 1 across the whole run; corrected below. Cross-checked against the independent recount in VeriBench `experiments/ideas/rl4cv_factored_scsc_results_implications_for_vb/AUDIT.md` (`e05_qwen3-1.7b-base.ic_tests_samples = 2`, `e05_qwen3-4b-base.binary_pass_samples = 5`).

## Phases

| Phase | Status | Evidence |
|---|---|---|
| Preflight: 5 tasks × 2 samples, Qwen3-1.7B-Base | DONE, PASS (10-05-2026 18:09) | `expt_v1/results/preflight_qwen3-1.7b-base.json` |
| Generation, 896 × 8 per model (1.7B, 4B, 8B) | all 3 models DONE (4B 20:09:57, 8B 20:23:02, 1.7B 21:55:41 via the rebalanced helpers), all exact 7,168-cell manifests (see Deviations) | per-model shard logs under `/lfs/skampere1/0/brando9/rl4cv_e05/logs/` |
| Kernel scoring, 24 jobs of 896 files | all 3 models DONE (8B 22:50:17, 1.7B 23:16:33, 4B 23:56:36); 21,504/21,504 cells scored, 0 unscored | `expt_v1/results/summary_<label>_g8.json` |
| Analysis and verdicts | DONE (10-05-2026 23:57) — all three **SFT warm start needed** | `expt_v1/results/analysis_e05.json`, `analysis_e05_table.md`, `per_task_<label>_g8.csv` |

## Compute estimate (10-05-2026, before launch)

- **Host.** `skampere1`, 8× A100-SXM4-80GB. At 17:41, GPUs 0–3 and 5–7 were idle (0 MiB) and GPU 4 held another user's job (36.7 GB, 89%), which is never touched. `skampere2` (`/lfs` 46 GB free, 7 of 8 GPUs in use) and `skampere3` (`/lfs` 99% full, all 8 B200s holding memory) were not usable. The CPU load average was about 3,000 on 128 cores (another user's jobs); the kernel's per-session CPU scheduling (`sched_autogroup_enabled = 1`) shares the CPU across sessions, and one gold-file Lean compile took 1.5 s.
- **GPU plan.** Qwen3-1.7B-Base on GPU 0; Qwen3-4B-Base on GPUs 1–2; Qwen3-8B-Base on GPUs 3, 5, 6 (one vLLM process per GPU, tasks sharded by line index). GPU 7 stays free; it hosts the preflight.
- **Memory.** bf16 weights about 3.4 GB (1.7B), 8 GB (4B) and 16.4 GB (8B); vLLM reserves 88% of each 80 GB GPU for weights plus KV cache. Decode is compute- and memory-bandwidth-bound.
- **Generation.** 7,168 cells per model, up to 12,288 output tokens each. Experiment 01's post-trained Qwen3 probe averaged 5,700–6,500 tokens per cell at about 1,400–1,900 tokens/s per GPU with 64 prompts in flight; this run submits 1,024 at a time. Estimate 1–4 h wall-clock, 6–20 GPU-hours in total.
- **Scoring.** 24 jobs × 896 files; about 2 h per job at experiment 01's 8 files per minute, 4 concurrent scorers per model (12 in total), overlapping generation: about 4 h, about 45 CPU-hours.
- **Total:** about 5–9 h. No judge and no API spend.
- **Go.** Brando, 10-05-2026: "evaluate the qwen models we discussed ... 1.7b 4.b 8b on vbv1 ... Go!", plus the standing SNAP pre-approval (agents-config Trigger Rule 51).

## Preflight (10-05-2026, GPU 7, Qwen3-1.7B-Base, 5 tasks × 2 samples)

| Check | Result |
|---|---|
| Locked prompt hashes (addendum `a7a0fc1b…`, system `dc051963…`) | match on 10/10 cells |
| Rendered prompt vs post-trained Qwen3-1.7B (`70d244cc`) | byte-identical on 5/5 tasks |
| Finish reasons | 5 `stop` (the `<|im_end|>` stop fires), 5 `length` (12,288-token cap) |
| Extraction | 4 no Lean block, 3 longest bare block, 2 file blocks, 1 single bare block |
| Kernel scoring | 10/10 scored; IC_tests 0 and IC_proofs 0 on all 10 |
| Mean generated tokens | 6,853 |

Qualitatively, the Base model writes Lean-like files (`import Mathlib`, a namespace, `example … := by native_decide`, `sorry`), with invalid comment syntax (`/ * … * /`), and some samples loop on one tactic (`nth_rewrite 1`, `nth_rewrite 2`, …) or on copied Python test lines until the cap. Smoke-test evidence only; the verdict comes from the full run.

## Results

Full run: 3 models × 896 VeriBench V1 (VBV1) tasks × 8 samples = 21,504 declared cells, all generated and kernel-scored (0 unscored, exact denominators throughout). Generated with `rl4cv.veribench.generate`, kernel-scored with the frozen scorer (`--skip-tc`), channels and statistics from `expt_v1/analyze_e05.py` (full output: `expt_v1/results/analysis_e05.json`, `analysis_e05_table.md`, `per_task_<label>_g8.csv`).

### Headline table (verdict channel: `kernel_binary`)

| Model | Tasks measured | Mixed share [95% Wilson] | p (H0 ≥ 0.05) | pass@8 share | all-pass share | Mean pass rate [95% bootstrap] | Mixed share `ic_tests` | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Qwen3-1.7B-Base (decider) | 896/896 | 0.000 [0.000, 0.004] | 1.1e-20 | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.004] | 0.0000 [0.0000, 0.0000] | 0.002 [0.001, 0.008] | **SFT warm start needed** |
| Qwen3-4B-Base | 896/896 | 0.006 [0.002, 0.013] | 2.4e-14 | 0.006 [0.002, 0.013] | 0.000 [0.000, 0.004] | 0.0007 [0.0001, 0.0014] | 0.011 [0.006, 0.020] | **SFT warm start needed** |
| Qwen3-8B-Base | 896/896 | 0.000 [0.000, 0.004] | 1.1e-20 | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.004] | 0.0000 [0.0000, 0.0000] | 0.000 [0.000, 0.004] | **SFT warm start needed** |

Every mixed-group share is far below the locked 0.05 threshold (gate G1, reused from experiment 01's `PROTOCOL.md`), each with p ≤ 2.4e-14 against H0: share ≥ 0.05 (one-sided exact binomial, unit = task, n = 896). Qwen3-1.7B-Base is the project-level decider (Varun, 10-05-2026: "if it's too hard for 1.7, then we have to reevaluate"): **SFT warm start needed.** No model reaches the 0.20 "RL from Base viable" threshold or even the "marginal" band.

### Core (614) and IndustrySet (282), reported separately

| Model | Split | Tasks | `kernel_binary` pass-count histogram (k=0..8) | Mixed share [95% Wilson] | p (H0 ≥ 0.05) |
|---|---|---:|---|---:|---:|
| Qwen3-1.7B-Base | Core 614 | 614/614 | {0: 614} | 0.000 [0.000, 0.006] | 2.1e-14 |
| Qwen3-1.7B-Base | IndustrySet 282 | 282/282 | {0: 282} | 0.000 [0.000, 0.013] | 5.2e-07 |
| Qwen3-4B-Base | Core 614 | 614/614 | {0: 613, 1: 1} | 0.002 [0.000, 0.009] | 7.0e-13 |
| Qwen3-4B-Base | IndustrySet 282 | 282/282 | {0: 278, 1: 4} | 0.014 [0.006, 0.036] | 1.4e-03 |
| Qwen3-8B-Base | Core 614 | 614/614 | {0: 614} | 0.000 [0.000, 0.006] | 2.1e-14 |
| Qwen3-8B-Base | IndustrySet 282 | 282/282 | {0: 282} | 0.000 [0.000, 0.013] | 5.2e-07 |

All three models' full-896 `kernel_binary` histograms are the degenerate case k=0 for every task except Qwen3-4B-Base's 5 mixed tasks (k=1 for all 5; see `per_task_qwen3-4b-base_g8.csv` for the task IDs). No task reaches k=8 (all-pass) for any model — the "too easy" check is clean.

### Execution diagnostics (per model, over all 7,168 cells)

| Model | Scored | Cut off at 12,288 tokens | No Lean block extracted | Compiling (`IC_tests=1`) | Mean generated tokens | IC_tests mean | IC_proofs mean | SCSC |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Qwen3-1.7B-Base | 7,168/7,168 | 4,411 (61.5%) | 3,154 (44.0%) | 2 (0.028%) | 8,026 | 0.00028 | 0.00016 | exact 0.0 on every cell |
| Qwen3-4B-Base | 7,168/7,168 | 704 (9.8%) | 1,029 (14.4%) | 10 (0.14%) | 2,219 | 0.00140 | 0.00070 | unmeasured on 5 cells (listed below), exact 0.0 elsewhere |
| Qwen3-8B-Base | 7,168/7,168 | 1,099 (15.3%) | 1,160 (16.2%) | 0 (0%) | 2,819 | 0.0 | 0.0 | exact 0.0 on every cell |

Qwen3-4B-Base has 5 cells with `IC_tests · IC_proofs > 0` (both channels positive), which per the locked protocol keep FSC and SCSC **unmeasured** rather than scored (no FSC judge runs in this experiment): `compilers_set_synthetic__my_boolean_double_neg#s2`, `compilers_set_synthetic__my_peephole_add_zero#s5`, `finance_set_synthetic__my_slippage_charge#s6`, `gov_cert_set_synthetic__my_audit_hash_chain_extend#s2`, `security_set__security_6858__vulnerabilities__107_unsafeprofilesandbox#s6`. These are listed, not counted as zero, consistent with the protocol; `#s2` of `my_boolean_double_neg` is the one cell that also reaches a full `kernel_binary = 1` pass (it needs no FSC judge because SCSC is exact wherever `IC_tests · IC_proofs = 0`, which does not apply here — SCSC for these 5 cells is the one quantity left unmeasured, while `kernel_binary` itself, which only needs the kernel axiom check, is measured and scored).

Qwen3-1.7B-Base's much higher mean token count (8,026 vs. 2,219–2,819) and cut-off rate (61.5% vs. 9.8–15.3%) is consistent with the preflight note: Base-model samples sometimes loop on a repeated tactic or re-emit the whole file until the 12,288-token cap, rather than stopping cleanly.

### ρ (usable signal density) and H (effective coverage), by split

`rl4cv.probe --group-by split` for `kernel_binary` and `proof_fraction` (full detail: `expt_v1/results/rho_h_<label>_g8_<channel>.json`). Qwen3-1.7B-Base and Qwen3-8B-Base: ρ = 0 and H = 0 on every one of the 33 splits for both channels (zero reward everywhere, so there is no admitted leave-one-out advantage mass to measure). Qwen3-4B-Base: ρ = 0 and H = 0 on 29 of 33 splits; the 4 splits with any signal, both channels:

| Split | Mean reward (`proof_fraction`) | ρ | H |
|---|---:|---:|---:|
| `compilers_set_synthetic` | 0.0167 | 15.40 | 0.133 |
| `finance_set_synthetic` | 0.0104 | 11.01 | 0.083 |
| `gov_cert_set_synthetic` | 0.0078 | 6.32 | 0.063 |
| `security_set` | 0.00027 | 0.30 | 0.0022 |

These are the same splits (plus the single `kernel_binary` pass) driving Qwen3-4B-Base's nonzero but still far-sub-threshold headline numbers; every other split carries zero usable RL signal for every model.

### Paired comparison with experiment 01's post-trained models (128-task probe subset)

Base minus post-trained `kernel_binary` mixed-group share, 95% paired task-bootstrap interval, exact two-sided McNemar p-value (`probe_task_ids.txt`, 128 tasks):

| Model size | Mixed share, Base | Mixed share, post-trained | Difference (Base − post) [95% bootstrap] | Discordant (Base-only / post-only) | McNemar p (exact, two-sided) |
|---|---:|---:|---:|---:|---:|
| 1.7B | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0 / 0 | 1.0 |
| 4B | 0.0078 | 0.000 | 0.0078 [0.000, 0.0234] | 1 / 0 | 1.0 |
| 8B | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0 / 0 | 1.0 |

No significant difference between Base and post-trained checkpoints on this 128-task probe at any size (experiment 01: 0/128 mixed groups for all three post-trained sizes). Base checkpoints do no better than post-trained ones, confirming the README's prior-evidence expectation.

### Representative completions

Two or three samples showing what the Base checkpoints actually write (first 15 lines; full rows in the raw generation files on the host, not committed per the data-layout policy):

**1. One of Qwen3-4B-Base's 5 genuine `kernel_binary = 1` passes (corrected 10-09-2026; see note above)** — `compilers_set_synthetic__my_boolean_double_neg`, sample 2 (`finish_reason: stop`):
```lean
import Mathlib

-- Module docstring describing the file
namespace MyBooleanDoubleNeg

-- Implementation (functional definition)
def my_boolean_double_neg (p : Bool) : Bool :=
  p

-- Unit tests using `example : ... := by native_decide` and `#eval`
example : my_boolean_double_neg false = false := by native_decide
example : my_boolean_double_neg true = true := by native_decide
#eval my_boolean_double_neg false
#eval my_boolean_double_neg true

-- Pre-condition predicate (`def Pre`)
def Pre (p : Bool) : Prop :=
  true
```
The function is the identity on `Bool`; the stated theorem `Pre p → my_boolean_double_neg_prop p` reduces to `p = p` and is proved by `fun _ => rfl`. A genuine, if trivial, pass — not vacuous, not `sorry`.

**2. Compiles, never proves** — Qwen3-1.7B-Base, `aerospace_set_synthetic__my_nav_seq_rollover`, sample 5 (`finish_reason: length`, cut off at the cap):
```lean
import Mathlib

namespace MyNavSeqRollover

def Pre (seq : Nat) (cycle_len : Nat) (expected : Nat) : Prop :=
  0 < cycle_len ∧ expected < cycle_len

def _prop (seq : Nat) (cycle_len : Nat) (expected : Nat) : Prop :=
  seq % cycle_len == expected

theorem my_nav_seq_rollover_pre : ∀ seq : Nat, ∀ cycle_len : Nat, ∀ expected : Nat,
  Pre seq cycle_len expected → _prop seq cycle_len expected :=
  sorry
```
All three stated theorems are `sorry` (worth zero under the prove-first contract), and after `end MyNavSeqRollover` the model re-emits a near-identical file from scratch rather than stopping — one instance of the cap-exhausting repetition noted in the preflight.

**3. No Lean block extracted** — Qwen3-8B-Base, `aerospace_set_synthetic__my_airspeed_squat_gate`, sample 1 (`finish_reason: length`, `extraction: no_lean_block`):
```lean
FILE: /home/user/lean_project/Veribench/MyAirspeedSquatGate.lean

import Mathlib

namespace MyAirspeedSquatGate

/-- Pre: all engineering-unit inputs are non-negative integers. -/
def Pre (airspeedKt taxiLimitKt : Nat) : Prop := airspeedKt ≥ 0 ∧ taxiLimitKt ≥ 0

/-- Accepts weight-on-wheels ground state only when calibrated airspeed is at or below the taxi threshold in knots. -/
def my_airspeed_squat_gate (airspeedKt taxiLimitKt : Nat) : Prop :=
  airspeedKt ≤ taxiLimitKt
```
The leading `FILE: ...` line (not valid Lean) is enough for `extract_files`/`resolve_paths` to reject the block entirely, so this cell counts as "no Lean block extracted" despite otherwise-plausible-looking content.

## Deviations and open questions

- **10-05-2026 19:07 — orchestration rebalance of Qwen3-1.7B-Base generation (agents-config Trigger Rule 57; `PROTOCOL.md` unchanged).** Qwen3-1.7B-Base ran alone on 1 GPU and was the long pole (~9 h) while Qwen3-4B-Base and Qwen3-8B-Base (on 2 and 3 GPUs) were on track to finish generating around 20:45, leaving GPUs idle. The master directed `expt_v1/rebalance_1p7b_e05.sh`: as GPUs free up, they generate 1.7B-base's not-yet-started 128-task blocks (1,024-cell batches) top-down with the identical pack, prompt, decoding and per-sample seed formula (`91·100003 + k`, a function of sample index only, so it does not depend on task order or which GPU runs a task — reordering tasks across GPUs is bit-for-bit equivalent to the original single-shard plan). A watcher stops the original shard only once it finishes a block whose successor is already claimed by a helper GPU, so no cell is generated twice by design; the merge keeps the first copy of any infrastructure duplicate (never chosen by score) and still requires an exact 896 × 8 manifest before scoring proceeds. This changes only execution orchestration (which process generates which task, in what order); no prompt, decoding parameter, scorer setting or threshold changed. Full detail and the dry-run receipt are in `expt_v1/CKPT_e05.md`.
- **10-05-2026 21:53 — infra incident during the rebalance, recovered, no data lost.** All six helper-generated blocks plus shard 0's two blocks merged correctly (exact 7,168-cell manifest, 0 missing/extra/duplicate), but the rebalance script's final step — killing and restarting the `qwen3-1.7b-base` tmux window to launch scoring — silently failed because tmux's target syntax misparsed the `.` in that window's name as a `window.pane` separator, and the script still logged a false `EXIT=0`. No generation or scoring cell was affected; the merge had already completed correctly. Recovered by sending the identical intended restart command into the existing window addressed by index instead of name; scoring for all 8 of 1.7B-base's samples started immediately afterward. Full detail in `expt_v1/CKPT_e05.md`.

**TLDR-end:** [rl4cv: 05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk] Qwen3 Base 1.7B/4B/8B G=8 VeriBench V1 signal check: all 21,504 cells measured; `kernel_binary` mixed-group share is 0.000 (1.7B, the decider) / 0.006 (4B) / 0.000 (8B), all far below the 0.05 threshold — **SFT warm start needed** for RL on Lean code verification at this scale. Next: `expt_v2` on Varun's SFT warm-start weights once D-105 resolves.
