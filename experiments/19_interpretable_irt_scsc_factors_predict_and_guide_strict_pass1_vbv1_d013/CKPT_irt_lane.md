# CKPT irt_lane: experiment 19, interpretable IRT for SCSC factors (explain/predict + guide strict pass@1)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013/CKPT_irt_lane.md>

**TLDR:** Resume record for the rl4cv IRT lane (Claude Code session local_268be283, assigned by the general coordinator local_82b6c38d on 10-20-2026). Zero paid model calls, CPU only.

Created: 10-20-2026 16:00 PDT
Last updated: 10-20-2026 19:01 PDT

## Goal
- Which SCSC factors and task features explain/predict held-out strict, harsh-SCSC and gold-check (VeriBench 111) success on VeriBench V1, and can an IRT forecast pick the prompts where experiment 13's start policy gives mixed strict groups?

## What ran
- 10-20-2026: inventory, task features, RC rows (with typechecks/statable) from VeriBench 111 @07c4b48, code + 16 unit tests, synthetic dry runs.
- Revision 1 locked 16:30 PDT as provisional experiment 18 (local commit cefd590a, never pushed); its SNAP run started 16:39 and was stopped at start (no output) because branch ub9/e18a claimed 18.
- Revision 2: renumbered 19; gold-check target added (coordinator handoff); forecast `e18_forecast.json` kept byte-identical; `e19_forecast_gold_target.json` frozen.
- Linux suite on skampere1 at cefd590a: 1,357 passed, 43 skipped, 3 failed; the same 3 fail at origin/main 57482ca2 (pre-existing).
- Locked run 23:52:11Z-01:50:56Z on skampere1 (tmux cc-rl4cv-e19-irt-run, lock 30db1fc3, 7,124 s, exit 0); Amendment 01 committed 00:20:27Z (19ba81ff) before any output existed; G3 frozen 01:58:55Z.

## Results
- G1 (primary): AUC 0.862 [0.792, 0.925] vs gate 0.70, n=135 (32 mixed); PASS, NOT IRT-SPECIFIC (IRT - panel strict rate +0.011 [-0.004, +0.027]); features only 0.954 [0.909, 0.987].
- E1-strict (primary): M1 - M2 = +0.0015 [-0.0059, +0.0086] (FALSE). Smooth score worse than raw rates for harsh/gold system forecasts. E2: features predict unseen-task difficulty (all three targets). M3 gate failed 8/11 folds -> E1 FSC-skill and E3a unavailable.

## Stuck / blocked
- nothing.

## Next steps
1. Send experiment 13's owner the frozen proposal (heuristic pool + G1 interval + IRT-specific contrasts).
2. Score G3 when 13 publishes V4-G0 per-task counts: `expt_v1/forecasts/e19_g3_forecast_v4_g0.json`.
3. VeriBench idea-page status line; cleanup of the e18 worktree and SNAP clone after publication.

## Brando to-do
- none

## Log
- 10-20-2026 16:00 PDT -- created; inventory done, features computed, protocol drafting.
- 10-20-2026 16:32 PDT -- revision 1 locked (pins + frozen forecast) as provisional 18.
- 10-20-2026 16:51 PDT -- renumbered 19 (ub9/e18a claimed 18); revision-1 run stopped at start, no output; gold-check target added as revision 2.
- 10-20-2026 17:20 PDT -- Amendment 01 (light QA, Fable 5.1 max, CORRECT 9/10) committed after run start, before any output read; SSH to skampere1 dropped at 00:08Z (watch exit 255); the run itself is in its own tmux session, status not yet re-checked.
- 10-20-2026 19:01 PDT -- locked run DONE (01:50:56Z, 7,124 s, exit 0); results.md published; G3 frozen 01:58:55Z (sha256 abb0cb31...).
