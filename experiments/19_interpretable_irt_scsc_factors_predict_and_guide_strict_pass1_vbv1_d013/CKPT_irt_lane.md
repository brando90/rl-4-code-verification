# CKPT irt_lane: experiment 19, interpretable IRT for SCSC factors (explain/predict + guide strict pass@1)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013/CKPT_irt_lane.md>

**TLDR:** Resume record for the rl4cv IRT lane (Claude Code session local_268be283, assigned by the general coordinator local_82b6c38d on 10-20-2026). Zero paid model calls, CPU only.

Created: 10-20-2026 16:00 PDT
Last updated: 10-20-2026 16:51 PDT

## Goal
- Which SCSC factors and task features explain/predict held-out strict, harsh-SCSC and gold-check (VeriBench 111) success on VeriBench V1, and can an IRT forecast pick the prompts where experiment 13's start policy gives mixed strict groups?

## What ran
- 10-20-2026: inventory, task features, RC rows (with typechecks/statable) from VeriBench 111 @07c4b48, code + 16 unit tests, synthetic dry runs.
- Revision 1 locked 16:30 PDT as provisional experiment 18 (local commit cefd590a, never pushed); its SNAP run started 16:39 and was stopped at start (no output) because branch ub9/e18a claimed 18.
- Revision 2: renumbered 19; gold-check target added (coordinator handoff); forecast `e18_forecast.json` kept byte-identical; `e19_forecast_gold_target.json` frozen.
- Linux suite on skampere1 at cefd590a: 1,357 passed, 43 skipped, 3 failed; the same 3 fail at origin/main 57482ca2 (pre-existing).

## Results
- none yet (no real-data fit has run)

## Stuck / blocked
- nothing.

## Next steps
1. Push the revision-2 lock, then on skampere1: fresh clone `/lfs/skampere1/0/brando9/rl4cv_e19` at the lock commit; in tmux `cc-rl4cv-e19-irt-run`: `E19_PY=/lfs/skampere1/0/brando9/uv_envs/rl4cv_e18/bin/python bash expt_v1/run_e19_snap.sh <lock>` (venv rl4cv_e18 = numpy 2.2.6, scipy 1.16.3, pytest, psutil, pyyaml).
2. Copy `expt_v1/results/` back, render tables, write results.md, report to the coordinator (Rule 74).
3. Freeze G3 (`expt_v1/freeze_g3_forecast_e19.py --judgement <json>`) before any experiment 13 v4 generation.
4. Cleanup (Rule 19): remove `/lfs/skampere1/0/brando9/rl4cv_e18` (provisional clone) and `~/vb_worktrees/rl4cv-e18-irt-lane` after publishing.

## Brando to-do
- none

## Log
- 10-20-2026 16:00 PDT -- created; inventory done, features computed, protocol drafting.
- 10-20-2026 16:32 PDT -- revision 1 locked (pins + frozen forecast) as provisional 18.
- 10-20-2026 16:51 PDT -- renumbered 19 (ub9/e18a claimed 18); revision-1 run stopped at start, no output; gold-check target added as revision 2.
