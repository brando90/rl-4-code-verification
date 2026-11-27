# 02B v2 prerequisites prepared 11-27-2026

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/prep_11-27-2026/prerequisites_11-27-2026.md

**TLDR:** The production config pins public `Qwen/Qwen3-1.7B-Base` at `ea980cb0a6c2ae4b936e82123acc929f1cec04c1` and the locked 2×2×64 design, and it stays `PREPARED_NOT_ADMITTED`. Accepted reference proofs still need Lean on SNAP. No forecast was frozen, because no pre-RL probe was read and none may be invented.

**Authorization:** Brando, 11-27-2026, for the non-GPU half of item R2. Owner of the remaining Lean work: lethan3. No GPU job was launched. No outcome file was opened.

## What is pinned

`production_config_11-27-2026.json` matches the 10-06-2026 readiness manifest and `PROTOCOL.md`:

- Model: `Qwen/Qwen3-1.7B-Base`, revision `ea980cb0a6c2ae4b936e82123acc929f1cec04c1` (the manifest's `reachable_local_revision`). Commit `db70b465` allows this public Base initialization for bounded 02B v2. Experiment 08's VeriBench-trained checkpoints are not a substitute.
- Arms: `full_file` and `theorem_completion`. Two seeds each, 64 optimizer steps, reward `kernel_binary`, Lean 4.22.0, VeriBench excluded.
- `training_entrypoint` stays null. The 11-25 `verina_adapter.py` is a behavioral evaluator (24/24 tasks, 158/158 fixed tests, commit `8ac36188`). It is not a GRPO rollout.

Fields the locked protocol does not name stay null: group size, response cap, rollout-token cap, learning rate, dtype, seed integers. Heuristics rule 1 forbids picking fp16 or bf16 for this run before a mismatch measurement.

Check, from the repository root (this exits 2, which means not admitted):

```bash
python3 experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/prep_11-27-2026/validate_production_config_11-27-2026.py
```

The historical launcher is unchanged and still exits 2:

```bash
env -u BASH_ENV bash --noprofile --norc experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/launch_11-25-2026.sh
```

## Accepted reference proofs — remaining blocker

Committed phase A v2 `results.md`: VERINA original reference theorems are **6/24 kernel-honest, 16/24 forbidden `sorryAx`, 2/24 unknown** after original-source compilation. FVAPPS rows are candidate-only because `spec` contains `sorry`. The 11-25 adapter README says those diagnostics were not repaired.

There is no in-repo command that turns the 16 forbidden proofs into accepted ones. That needs Lean 4.22.0 and a person (lethan3) to materialize references whose named theorems use only `propext`, `Classical.choice` and `Quot.sound`, and that pass the non-vacuity check. The commands that do exist, and that must not be reported as acceptance, are:

Candidate rebuild (CPU, does not accept a `sorry` stub; do not overwrite the frozen manifest):

```bash
python3 experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v2/scripts/build_fvapps_external24.py \
  --fvapps-train /lfs/$(hostname -s)/0/$USER/inputs/fvapps_train_3552a173.jsonl \
  --veribench-root /lfs/$(hostname -s)/0/$USER/veribench \
  --out /lfs/$(hostname -s)/0/$USER/rl4cv_e02b_v2/fvapps_external24_rerun_11-27-2026.json
```

Behavioral adapter regression (skips unless `VERINA_ROOT`, `VERINA_LEAN` and `VERINA_LEAN_PATH` point at Lean 4.22.0; a skip is not 24/24, and a pass is not proof acceptance):

```bash
python3 -m pytest -q experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/adapter_11-25-2026
```

Receipt the new references must carry before the config can move off `PREPARED_NOT_ADMITTED`: per-task Lean 4.22.0 compile, allowed-axiom set, non-vacuity, and a screen against the protected VeriBench corpus. Write that receipt beside `results/`; do not edit `results/training_readiness_manifest_2026-10-06.json`.

## Forecast freeze — command, not a frozen file

`src/rl4cv/utility_model.py` now has `paper_frozen_14b_model()`. That fit is OpenR1-Math. The freeze script rejects `standardizer_source = paper_frozen_14b_model`. It also rejects an empty prediction, so this commit did not invent a winner or a delta, and it did not read a training outcome.

Print the skeleton (writes nothing, exits 2):

```bash
python3 experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/prep_11-27-2026/forecast_freeze_11-27-2026.py
```

After both environments have measured ρ and H, and before either arm trains, fill `prediction` and only then:

```bash
python3 experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/prep_11-27-2026/forecast_freeze_11-27-2026.py \
  --forecast /lfs/$(hostname -s)/0/$USER/rl4cv_e02b_v2/prediction.json \
  --out-dir /lfs/$(hostname -s)/0/$USER/rl4cv_e02b_v2/forecasts \
  --commit-freeze
```

`--outcomes-observed` and any path whose name looks like an outcome are refused. Copy the frozen JSON and the ledger line into `expt_v2/` in a later commit. Do not freeze a synthetic prediction into the repository.

## Still blocked on SNAP, not on this commit

1. Lean 4.22.0 reference acceptance (lethan3), command above.
2. Re-hash of `Qwen/Qwen3-1.7B-Base` @ `ea980cb0a6c2ae4b936e82123acc929f1cec04c1` on the host.
3. One-GPU mismatch and Lean-throughput baseline before dtype or a GPU-hour estimate.
4. Pre-RL probes, then the freeze command, then a fresh H200 inventory. The 11-25-2026 19:54 PST note that skampere2 GPUs 4–7 were idle is not a current inventory. Placement stays B200 skampere3, then H200 skampere2, then A100-80GB skampere1, free hardware only.

**TLDR-end:** [rl4cv: 02B v2 prep 11-27] Public Qwen3-1.7B-Base is pinned and the freeze command is ready. Reference proofs, probes and the forecast still wait on SNAP Lean and a fresh GPU inventory.
