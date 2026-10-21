# Experiment 13 v4: certificates and ordered CPU runner

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/README.md>

**TLDR:** V4-A1 certificates and the ordered stage controller are implemented and tested with synthetic engines. Measured launch remains **BLOCKED**: uncertified generator probabilities have no specified treatment in the frozen importance correction, and the measured scorer/trainer/checkpoint adapter is not integrated. This is not a launch-ready runner.

`experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4` compares strict-reward training (A), factored-reward training (B), and a start-density placebo (P). No v4 model generation, optimizer step or device allocation has run. See [the checkpoint](CKPT_v4_implementation.md) for verification counts, admission digest, dry-run evidence, commands and remaining work.

## Frozen documents and amendments

- [Protocol](PROTOCOL.md), frozen at `d4778e25`; unchanged.
- [Amendment V4-A1](AMENDMENT_V4-A1_generator_support_receipt_10-20-2026.md), adopted at `7877faac`; unchanged. It replaces the generator receipt and T1 support criterion, and specifies trainer tie inclusion.
- [Dispatch 2 blocker](BLOCKER_V4_A1_importance_correction.md): installed loss evidence, CPU reproducer and smallest proposed fix. This report is **not** an amendment.

## V4-A1 implementation

The concrete launch-only generator constructor sets `max_logprobs=64`, and every request asks for 64 raw log-probabilities. Sampling stays temperature 0.6, top-k 20, top-p 0.95, at most 12,288 response tokens. The installed sampler's actual `forward` function is executed with CPU sampling dependencies in a test: switching receipt collection off/on preserves both the sampled token and random state. The real engine comparison remains a required T1 measurement.

`filtered_policy.certificate` requires `v64 < v20` for a truncated vocabulary. It includes all kth ties, reconstructs the ascending top-p tail, and refuses a boundary that splits equal values or falls within 1e-5 of 0.05. Both cumulative masses adjacent to the cut are checked. Complete tiny vocabularies use `min(20,V)`. The trainer retains the whole boundary tie group. Native generator filtering remains separately testable against installed source.

T1 counts uncertified positions as disagreements, uses only certified positions for error quantiles, and reports the uncertified denominator. Importance truncation receives lower/upper bounds when generator probabilities are unknown; the unchanged ≤1% limit is only certified if the upper bound satisfies it. Full top-64 receipts are retained for T1, G0 and T2 refit; updates keep sampled raw probability, certificate flags, support size and certified generator log probability. Unknown support sizes/probabilities are `null`, never imputed.

The installed NeMo loss wrapper still uses the fixed old trainer support and scales current logits once. Its separate capped actor correction consumes generator probabilities. A1 does not specify values at uncertified positions. The tests prove that changing these values changes the loss even when the policy ratio is unchanged. Admission therefore refuses measured execution rather than silently masking tokens, imputing trainer values or changing the loss.

## Runner and recovery

The `runner.py` stage entry points are:

```text
T1 -> G0_GENERATE -> G0_SCORE -> G0_SELECT -> T2 -> T3 -> T4 -> B_AUDITS
   -> PILOT30 -> T5_30 -> [PILOT60 -> T5_60, only on extension]
```

Each stage requires its predecessor's PASS receipt and binds its completed evidence to the admission digest. T5 stage completion is distinguished from its scientific gate verdict: a completed FAIL at 30 schedules extension of every admitted trajectory; a second failure stops. T2 with no varying reward stops without an update, refit or resampling. The main study is never automatically launched by this controller.

`stage_ledger.py` uses an exclusive controller lock and immutable operation inputs, outputs, hashes and statistic reservations. Completed operations can be accounted after a crash. Retry is permitted only with an explicit zero-response, no-optimizer, no-statistic infrastructure receipt, at most three starts in total. Missing files alone never prove that nothing was generated. Partial/unknown effects and interrupted statistics stop for diagnosis. Recovery never discards responses or repeats a completed optimizer operation. Optimizer replay after generation is deliberately not enabled without a measured restoration adapter and a proven pre-step failure.

G0 selection freezes all 30,720 placebo draws (two seeds × 60 updates × 256 slots) before P's first response. A derived admission supplement binds the observed distribution and draw file to the original admission; the original is never rewritten. The stub sequence preserves 256 declared slots and runs all six trajectories for 60 symbolic updates using one-token synthetic outputs. These are interface/control-flow tests, **not** scientific gate evidence, actual audits or memory measurements.

The `local` engine refuses execution. `generation_runtime.py` provides the guarded concrete generation primitive, but integration of real scoring with retained compiler diagnostics, trainer batching and checkpoint/export/replay, maximum-length worker dispatch and fixed-cohort B audits remains unfinished. The stub engines do not establish those capabilities.

## Files

| Files under `phase2/` | Purpose |
|---|---|
| `filtered_policy.py`, `generation_contract.py`, `generation_runtime.py` | Native/trainer supports, certificates, receipt reduction, guarded top-64 constructor |
| `trainer_support.py`, `worker_hooks.py`, `nemo_objective.py` | Fixed old supports and installed loss integration |
| `runner.py`, `stage_ledger.py`, `recovery.py` | Stage order, immutable receipts, bounded recovery and decisions |
| `stub_engine.py`, `dry_run.py`, `local_engine.py` | CPU end-to-end controls and explicit measured-adapter boundary |
| `device_guard.py`, `device_lease.py`, `gpu_inventory.py` | Idle-device checks, bounded lock/lease and read-only census |
| `build_plans.py`, `launch_plan.json`, `watchdog_plan.json` | Concrete future argument vectors; mirrored in the work directory |
| `launch_control.py`, `autoresume_watchdog.py`, `install_watchdog.py` | v4-only controller/watchdog commands; none installed or started |
| `admission.py`, `admission_runner.json` | Protocol, amendment, code, tests, plans and runtime binding; launch refusal |
| `group_selection.py`, `gates.py`, `placebo.py`, `pilot_metrics.py` | G0, technical gates, placebo and pilot decision reducers |
| `context_values.json`, `A6_counts.json` | Previously verified context and anonymous historical counts |

Both engines retain context 20,041 and response cap 12,288; validators reject the retired 15,945 and 8,192 settings. The unchanged anonymous A6 evidence retains all 512 slots. Shared runtime, v2/v3 files, sessions, hooks and cron are not modified.

## CPU verification

Run from the checkout root:

```bash
export CUDA_VISIBLE_DEVICES=''
export HF_HUB_OFFLINE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/lfs/skampere1/0/brando9/rl4cv_e13v4/test_deps:$PWD/src
V4_PY=/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python
V4_ROOT=$PWD/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4
"$V4_PY" -m pytest -q "$V4_ROOT/tests"
"$V4_PY" "$V4_ROOT/phase2/admission.py" check --record "$V4_ROOT/phase2/admission_runner.json"
# Expected refusal, with the precise unresolved contracts:
"$V4_PY" "$V4_ROOT/phase2/admission.py" launch-check --record "$V4_ROOT/phase2/admission_runner.json"
```

The new admission supersedes `admission_cpu.json`; that earlier immutable record describes the pre-A1 implementation and no longer validates current source. Reproduction of the GPU-free command-line dry run, complete logs and test counts are in the checkpoint.
