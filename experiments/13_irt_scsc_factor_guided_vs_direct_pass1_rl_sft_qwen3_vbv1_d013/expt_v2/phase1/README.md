# Experiment 13 version 2 Phase 1: LP-1 startup stop and retained preparation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1/README.md>

**TLDR:** G0 remains PASS. LP-1, the generation resource and probability admission, is INCOMPLETE: one attempt produced 0/8 responses because the launcher supplied a graphics processor identifier where vLLM expected a numeric index. Cleanup passed, the lease was released after 0.014593276 device-hours, and automatic launch was retired. The no-retry rule stops downstream execution; no anchor or Phase 2 run occurred.

## Current state — 10-14-2026 15:36 PDT

The frozen LP-1 attempt started on an idle, unreserved skampere1 device at 15:30 PDT and failed before producing any response. See the [failure report](../RESULTS_LP1.md) and [result receipt](../LP1/result.json). Lease release and process cleanup are verified. The private launch plan was retired; the fifteen-minute poller remains observation-only and all ten cron entries are unchanged. No retry is admitted.

Retained preparation includes the anchor generation/scoring runners, four 4,312-cell train-only manifests, sampler/token caps, source-bound A3 missingness loader, conjunctive and two-parameter logistic item-response fitting controls, and completion bounds. Features for 539 train/135 validation tasks are prepared without test content or actual-data fitting. The final G1 driver and executable lock were not completed; [G1_A3_DRAFT.json](../locks/G1_A3_DRAFT.json) remains non-executable. These are tested preparation artifacts, not measured Phase 1 results.

Required publication suite: **528 passed, 23 skipped, zero failed in 247.80 seconds**, with Lean integration required ([receipt](scoring_inputs_publication_test.json)).

The following resource snapshot and preparation records are historical; they explain the earlier WAIT and do not supersede the terminal LP-1 result.

## Historical verified resource state

Snapshot: 10-14-2026 14:14 PDT. The [machine-readable receipt](resource_inventory_10-14-2026.json) records exit codes, resolved process ownership, storage bytes and the hash of the private raw inventory. These are point-in-time operational counts; confidence intervals and p-values are not applicable (p-val=n/a).

| Host | Occupied devices / total | Compute processes | Local free GiB | Local free percent | Admission obstacle |
|---|---:|---:|---:|---:|---|
| skampere1 | 8/8 | 23 | 5,236.19 | 9.186% | Every device has another user's compute process |
| skampere2 | 8/8 | 21 | 329.62 | 0.578% | Every device occupied; local storage below headroom |
| skampere3 | 8/8 | 12 | 146.31 | 0.171% | Every device occupied; local storage below headroom |
| mercury1 | 0/10 | 0 | 31.16 | 0.439% | Local storage below headroom; devices have 16 GiB each |
| mercury2 | 0/10 | 0 | 12.10 | 0.171% | Local storage below headroom; devices have 16 GiB each |

All compute-process owners resolved. Idle utilization alone was not treated as a free device: an existing compute process excludes it. The shared SNAP host instructions require addressing relevant disk failures below 5% free. Borrowed environments and other owners' storage were preserved.

The scheduler controller `ilc.stanford.edu` was reachable. `showaccount` listed zero account associations. A non-submitting `sbatch --test-only --partition=il --account=infolab --gres=gpu:1 --time=00:10:00 --wrap=true` returned exit 1 with `Invalid account or account/partition combination specified`. No scheduler job was submitted. Gated nodes therefore do not supply an alternative allocation under the current account.

At that snapshot, the experiment-13 registry at `$WR/leases/registry.json` had zero leases and zero device-hours. The inspected experiment-08 shared registry had 33 released records and no unreleased record; experiment 09's old preflight lease was expired. No separate lease file was found in the bounded experiment-12/14 work-root inventory. These historical checks confer no allocation: repeat every process, lease and master-reservation check immediately before any claim, as PLAN section 7 requires.

## Preparation retained

- Historical Base receipts use temperature 0.6, top-p 0.95, top-k 20 and a 12,288-token cap. They cannot replace an anchor batch using the Phase 2 sampler: temperature 1, top-p 1, top-k disabled, 8,192 new tokens.
- Four new train batches are therefore needed: Base, 50% supervised fine-tuning, full schedule batch 1, and independent full schedule batch 2 after calibration/item parameters/F2 are frozen. Each has 539 tasks × 8 samples = 4,312 cells; total 17,248 cells, maximum 141,295,616 generated tokens. PLAN's 4–6 large-device-hour estimate is unmeasured here and is not a lease or hard allocation.
- Both 4B export manifests were checked previously: ten files each, for steps 334 and 658. Their retained checks and sampler metadata are under `$WR/state/phase1_preparation_metadata.json`. Reverify exact export/config/tokenizer bytes in the prospective admission lock.
- The clean installed NeMo reinforcement-learning checkout at `$WR/../rl4cv_e08/nemo_rl` is revision `c751f811217db7df0d4c94abdeaada6626cfc150`. Its installed versions were inspected (PyTorch 2.7.1+cu128, Transformers 4.55.4, NeMo RL 0.4.0, vLLM 0.10.0, Ray 2.46.0). This is a technical candidate, not a frozen trainer choice or demonstrated probability agreement. The separate generation environment has different versions and is not assumed equivalent.

The required publication suite passed: `E13_REQUIRE_LEAN_INTEGRATION=1 make test`, 433 passed, 23 skipped, zero failed in 222.90 seconds. [Verification receipt](publication_test.json).

## Transition

PLAN section 5 requires LP-1 admission before anchor generation. The attempt did not pass, and the explicit no-retry rule remains binding. No downstream run is admitted. G0 remains PASS; anchors, calibration, G1/H2 and Phase 2 remain unmeasured. The watchdog completion notice follows verified publication of this stop.

## Earlier CPU preparation record, 10-14-2026 14:47 PDT

The prospective generation runner (`panel.py`, `runtime.py`) retains exclusive batch/slot attempts, full token and probability receipts, the 539 × 8 denominator and batch-2 prerequisite. It calls installed vLLM 0.10.0 and the clean NeMo RL distributed-tensor worker for sequential probability evaluation, with no optimizer. CPU imports succeeded; actual device admission is unmeasured. The installed newer worker needs an absent `nemo-automodel` package, so the original installed worker is the technical candidate before any efficacy outcome.

Train-only tokenization prepared an eight-response LP-1 probe and four 4,312-cell anchor manifests. Maximum prompt length is 7,753 tokens; model context is 15,945 = 7,753 + 8,192, preserving the full new-token cap. Terminal tokens are 151643 and 151645; both belong in the assistant probability mask. The full-export chat template uses thinking enabled. Public hashes/counts are in `manifest_preparation.json`; private prompts/IDs remain under the work root. No model weights were loaded for this preparation.

The generation and probability code is prospective until the final runtime/device/manifest lock is published. Remote hosts do not mount skampere1 files, so verified own runtime/export deployment is required for automatic remote execution. Mercury generation is explicitly permitted by the master's 10-14 steer when bounded storage and admission hold; percentage-free disk alone is not a terminal blocker.

Required publication suite: **502 passed, 23 skipped, zero failed in 230.51 seconds**, with Lean integration required. [Receipt](runner_publication_test.json). All 49 focused generation, missingness/bounds, lease and cleanup tests passed. The [G1 lock draft](../locks/G1_A3_DRAFT.json) binds the prospective implementation; final input bindings and publication still precede actual fits.


Publication verification: `E13_REQUIRE_LEAN_INTEGRATION=1 make test` exited 0; **512 passed, 23 skipped, zero failed in 240.62 seconds**. Receipt: [LP1_publication_test.json](LP1_publication_test.json).

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2 stops at incomplete LP-1 startup under the no-retry rule; G0 remains PASS and later scientific gates are unmeasured.
**Snapshot:** LP-1 attempts 1; responses 0/8; tokens 0; optimizer updates 0; retries 0; device-hours 0.014593276; cleanup PASS; lease RELEASED.
