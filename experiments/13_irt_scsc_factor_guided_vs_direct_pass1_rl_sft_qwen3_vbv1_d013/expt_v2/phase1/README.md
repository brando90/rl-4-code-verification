# Experiment 13 version 2 Phase 1: CPU preparation while devices are busy

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1/README.md>

**TLDR:** `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013` passed G0. Phase 1 CPU preparation continues while LP-1 (generation resource and probability admission) waits for a device. No usable default device route was available in the 10-14-2026 snapshot below; this is not a scientific failure or experiment completion.

## Current preparation

`device_watch.py` now polls all five direct-access nodes every 15 minutes. Its first live poll on 10-14-2026 at 14:24 PDT and first scheduled poll at 14:30 PDT completed with zero candidates; all prior nine cron lines were preserved exactly and one line appended. It records every observation under `$WR/device_watch/` and never claims devices or starts a model. Candidate availability still needs current foreign-lease/master-reservation checks and the enforcing experiment-13 launcher before execution.

`sampler.json` records the prospective protocol sampler. `probability.py` checks actual generator/trainer token alignment, assistant and end-of-sequence masks, support errors, probability differences and importance truncation; it does not itself establish a passed LP-1 gate. `g1_bounds.py` supplies exact linear-metric and paired-bootstrap completion bounds and bounded policy-correlation enumeration. Their 29 synthetic tests pass, and 112 independent coefficient checks match the frozen evaluator. The full required suite passed 462 tests with 23 skips and zero failures in 223.40 seconds ([receipt](preparation_test.json)). The [G1 method draft](G1_BOUNDS_DRAFT.md) lists the remaining wrapper/diagnostic work. No real probability probe, fit, anchor, or training call has run. The frozen `prediction/` models remain unchanged.

CPU work continues on the lease launcher, the actual trainer probability runtime, anchor runner and complete G1 missing-data/bounds harness. No automatic execution or completed admission lock is claimed.

## Verified resource state

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

The experiment-13 registry at `$WR/leases/registry.json` has zero leases and zero device-hours. The inspected experiment-08 shared registry had 33 released records and no unreleased record; experiment 09's old preflight lease was expired. No separate lease file was found in the bounded experiment-12/14 work-root inventory. These historical checks confer no allocation: repeat every process, lease and master-reservation check immediately before any claim, as PLAN section 7 requires.

## Preparation retained

- Historical Base receipts use temperature 0.6, top-p 0.95, top-k 20 and a 12,288-token cap. They cannot replace an anchor batch using the Phase 2 sampler: temperature 1, top-p 1, top-k disabled, 8,192 new tokens.
- Four new train batches are therefore needed: Base, 50% supervised fine-tuning, full schedule batch 1, and independent full schedule batch 2 after calibration/item parameters/F2 are frozen. Each has 539 tasks × 8 samples = 4,312 cells; total 17,248 cells, maximum 141,295,616 generated tokens. PLAN's 4–6 large-device-hour estimate is unmeasured here and is not a lease or hard allocation.
- Both 4B export manifests were checked previously: ten files each, for steps 334 and 658. Their retained checks and sampler metadata are under `$WR/state/phase1_preparation_metadata.json`. Reverify exact export/config/tokenizer bytes in the prospective admission lock.
- The clean installed NeMo reinforcement-learning checkout at `$WR/../rl4cv_e08/nemo_rl` is revision `c751f811217db7df0d4c94abdeaada6626cfc150`. Its installed versions were inspected (PyTorch 2.7.1+cu128, Transformers 4.55.4, NeMo RL 0.4.0, vLLM 0.10.0, Ray 2.46.0). This is a technical candidate, not a frozen trainer choice or demonstrated probability agreement. The separate generation environment has different versions and is not assumed equivalent.

The required publication suite passed: `E13_REQUIRE_LEAN_INTEGRATION=1 make test`, 433 passed, 23 skipped, zero failed in 222.90 seconds. [Verification receipt](publication_test.json).

## Exact continuation

Continue implementation in the same owned checkout while polling. Execute only after an idle supported device and a checked storage route become available, or a valid scheduler account association is provisioned. No new permission is needed. Do not replay G0.

1. Refresh the device/process inventory and every required foreign lease and master reservation. Finish the experiment-13 lease launcher with identity checks, bounded accounting and exit release; the currently empty registry alone is not an enforcing launcher.
2. Finish and publish LP-1's bounded device plan, actual trainer/generator implementation and hashes, train-only probability probe, sampler/support/assistant masks and token caps. No LP-1 lock or executable generation runner is claimed to be finished by this resource report.
3. Run generation-only probability admission once. Generate the first three anchor batches only after admission. Before any fit, publish the A3 G1 bounds lock: fit with excluded cells missing, freeze forecasts, and bound held-out outcomes without refitting for each completion.
4. Freeze calibration, item parameters and F2; generate independent batch 2; report G1/H2 and the arm-C transition. Then follow PLAN section 6's Phase 2 gates. Validated Valkyrie formal specification coverage remains a separate later blocker.

Zero LP-1 probability measurements, anchor cells, fits, optimizer updates or device claims have occurred. PLAN section 7 forbids claiming busy devices; PROTOCOL sections 6 and 8 require a real allocation and permit no training beyond admitted diagnostic work on resource failure. No PLAN section 4 scientific failure transition has been triggered. The watchdog remains armed for owner/process monitoring; automatic device-triggered execution or executor replacement is not installed.

**TLDR-end:** [rl4cv: 13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013] Version 2 passed G0; CPU preparation and device polling continue while generation waits. All downstream scientific gates remain unattempted.
**Snapshot:** G0 PASS; skampere devices occupied 24/24; Mercury local free space 31.16/12.10 GiB; scheduler associations 0; anchor cells 0/17,248; training updates 0.
