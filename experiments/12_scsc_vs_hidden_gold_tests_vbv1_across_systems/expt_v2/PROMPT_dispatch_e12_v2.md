# Experiment 12 v2 dispatch prompt — Corrected Hidden Gold-Test Adapter on VeriBench V1 (`[p 9/10]`)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v2/PROMPT_dispatch_e12_v2.md>

**TLDR:** Execute `12_scsc_vs_hidden_gold_tests_vbv1_across_systems` (`expt_v2`) end to end on `skampere1` (CPU Lean v4.22.0 + Mathlib, zero model calls, `$0` Vals spend): verify the frozen forecast and static control hashes, build `runtime_v2.py`, `controls_v2.py`, `evaluate_v2.py`, and `analyze_v2.py` around the locked `adapter_v2.py`, run controls C1–C4, evaluate all 4,626 compiling primary cells across the 11 systems × 896 VeriBench V1 (VBV1) tasks (reusing version 1's compiled `.olean` candidate modules where hashes match), and publish the complete version-2 results and forecast verdicts in `expt_v2/results.md` and `results.md`.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## 0. Binding rules & scope

- Read `~/agents-config/INDEX_RULES.md`, the repository `CLAUDE.md`, and `experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v2/{README.md,DESIGN.md,PROTOCOL.md,cc.md,results.md,CKPT_e12_v2.md}`.
- **Zero model calls, zero judge calls, zero GPUs.** Never read sealed data (experiments 107, 109) or experiment 08's test split.
- **Uninterrupted full-set evaluation (Trigger Rule 61):** Evaluate all 4,626 declared compiling primary cells (and retain all 9,856 declared `11 × 896` system-task cells in full-denominator bounds). Never edit `adapter_v2.py`, the frozen forecasts (`forecasts/e12_v2_forecast.json`, `forecasts/e12_v2_forecast_amendment_A1.json`), or any version-1 file under `../expt_v1/`.
- **Polite CPU parallelism:** Run Lean with `nice -n 10` and 2 workers (or up to 4 workers if 1-minute load average on `skampere1` is below 20).

## 1. Host workspace setup on `skampere1`

```bash
export WORK=/lfs/skampere1/0/brando9/rl4cv_e12/v2
export V1=/lfs/skampere1/0/brando9/rl4cv_e12
mkdir -p "$WORK" "$WORK/controls_v2" "$WORK/evaluation_v2"
if [ ! -d "$WORK/rl-4-code-verification/.git" ]; then
  git clone https://github.com/brando90/rl-4-code-verification.git "$WORK/rl-4-code-verification"
fi
cd "$WORK/rl-4-code-verification"
git fetch origin '+refs/heads/main:refs/remotes/origin/main'
git checkout main && git pull --ff-only origin main
export PYTHONPATH="$PWD/src"
```

## 2. Step-by-step execution plan

1. **Preflight hash & test verification:**
   - Run `python3 -m pytest -q tests/test_e12_adapter_v2.py` (must pass all 64 tests).
   - Run the exact hash-verification block from `expt_v2/cc.md` § 2 verifying `e12_v2_forecast.json`, `e12_v2_forecast_amendment_A1.json`, `adapter_v2.py`, `mapping_census_v2.json`, `static_controls_v2.json`, `hidden_tests_manifest.json`, and `input_manifest_A1.json`.
2. **Send `[RUN START]` email (Trigger Rule 70):**
   - Send `[RUN START] rl4cv-e12-v2-hidden-gold-tests` To `brando.science@gmail.com` with CC `brandojazz@gmail.com,brando9@stanford.edu,brando@vals.ai` via `uutils.emailing.send_email_smtp()`.
3. **Implement and test `runtime_v2.py`, `controls_v2.py`, `evaluate_v2.py`, and `analyze_v2.py`:**
   - Following `expt_v2/cc.md` §§ 3–5 and `expt_v2/PROTOCOL.md` §§ 3–5:
     - `expt_v2/scripts/runtime_v2.py`: subclass `../expt_v1/scripts/runtime_e12.py`'s `Runtime` to call `adapter_v2.map_symbols`, `adapter_v2.per_test_plan`, `adapter_v2.bridge`, and `adapter_v2.cell_outcome`, preserving the 600s Lean runner and agreement-probe construction.
     - `expt_v2/scripts/controls_v2.py`: port `../expt_v1/scripts/controls_e12.py` to `runtime_v2` over the 50 prescribed tasks in `../expt_v1/results/control_selection.json`.
     - `expt_v2/scripts/evaluate_v2.py`: port `../expt_v1/scripts/evaluate_e12.py` to `runtime_v2`, reusing `$V1/evaluation_A2/modules/E12Eval<key[:24]>.olean` (by copying into `$WORK/evaluation_v2/modules/` when the `.lean` SHA-256 matches).
     - `expt_v2/scripts/analyze_v2.py`: port `../expt_v1/scripts/analyze_e12.py` for the version-2 cohorts (`PROTOCOL.md` § 5: primary P2/P3 cohort = fully applicable; sensitivities S-V2a through S-V2d; paired comparison on the 379 changed-entry-point cells and 20 inspected rows; 10,000 task-cluster bootstrap draws, seed `20261009`).
   - Add unit tests for the new scripts, run `make test`, commit, and push to `main`.
4. **Run Dynamic Controls C1–C4:**
   - Execute `controls_v2.py --work $WORK/controls_v2 --out $E/expt_v2/results/controls_v2.json`.
   - Verify C1 ≥ 98%, C2 ≥ 95%, C3 ≥ 60% (over ≥ 50 compiling mutants), C4 ≥ 95%. Commit `expt_v2/results/controls_v2.json` and update `expt_v2/results.md` + `expt_v2/CKPT_e12_v2.md`.
5. **Run Full Primary Evaluation (4,626 compiling cells across 11 systems × 896 tasks):**
   - Execute `evaluate_v2.py --work $WORK --panels primary`.
   - Publish progress milestones every 500 unique groups to `expt_v2/results.md` and `expt_v2/CKPT_e12_v2.md` and push to `main`.
6. **Analyze, Publish Results & Send `[RUN DONE]` Email:**
   - Run `analyze_v2.py` to produce `expt_v2/results/analysis_e12_v2.json` and per-system/per-cohort tables.
   - Update `expt_v2/results.md`, `results.md` (top status pointer + v2 summary), `experiments/README.md` row 12, and `expt_v2/CKPT_e12_v2.md` (`Status: DONE`).
   - Run `make test`, commit and `git push origin main`, and send `[RUN DONE] rl4cv-e12-v2-hidden-gold-tests: success` To `brando.science@gmail.com` with CC `brandojazz@gmail.com,brando9@stanford.edu,brando@vals.ai`.
