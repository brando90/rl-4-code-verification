# CKPT irt_lane: experiment 19, interpretable IRT for SCSC factors (explain/predict + guide strict pass@1)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013/CKPT_irt_lane.md>

**TLDR:** Resume record for the rl4cv IRT lane (Claude Code session local_268be283, assigned by the general coordinator local_82b6c38d on 10-20-2026). Zero paid model calls, CPU only.

Created: 10-20-2026 16:00 PDT
Last updated: 10-21-2026 13:45 PDT

## Goal
- Which SCSC factors and task features explain/predict held-out strict, harsh-SCSC and gold-check (VeriBench 111) success on VeriBench V1, and can an IRT forecast pick the prompts where experiment 13's start policy gives mixed strict groups?

## What ran
- 10-20-2026: inventory, task features, RC rows (with typechecks/statable) from VeriBench 111 @07c4b48, code + 16 unit tests, synthetic dry runs.
- Revision 1 locked 16:30 PDT as provisional experiment 18 (local commit cefd590a, never pushed); its SNAP run started 16:39 and was stopped at start (no output) because branch ub9/e18a claimed 18.
- Revision 2: renumbered 19; gold-check target added (coordinator handoff); forecast `e18_forecast.json` kept byte-identical; `e19_forecast_gold_target.json` frozen.
- Linux suite on skampere1 at cefd590a: 1,357 passed, 43 skipped, 3 failed; the same 3 fail at origin/main 57482ca2 (pre-existing).
- 10-21-2026: results published (rl4cv 46c955aa); frozen proposal to experiment 13's owner (d8dc4813, delivered to session local_47bef804); VeriBench idea page synced (e44b2d30a6); SNAP checkout and local worktrees removed (receipts kept in /lfs/skampere1/0/brando9/e19_receipts).
- Locked run 23:52:11Z-01:50:56Z on skampere1 (tmux cc-rl4cv-e19-irt-run, lock 30db1fc3, 7,124 s, exit 0); Amendment 01 committed 00:20:27Z (19ba81ff) before any output existed; G3 frozen 01:58:55Z.

## Results
- G1 (primary): AUC 0.862 [0.792, 0.925] vs gate 0.70, n=135 (32 mixed); PASS, NOT IRT-SPECIFIC (IRT - panel strict rate +0.011 [-0.004, +0.027]); features only 0.954 [0.909, 0.987].
- E1-strict (primary): M1 - M2 = +0.0015 [-0.0059, +0.0086] (FALSE). Smooth score worse than raw rates for harsh/gold system forecasts. E2: features predict unseen-task difficulty (all three targets). M3 gate failed 8/11 folds -> E1 FSC-skill and E3a unavailable.

## Stuck / blocked
- nothing.

## Next steps
0. Supervise experiment 20, the online test of IRT guidance (its worker owns that folder). Verdict file: `/lfs/skampere1/0/brando9/e20_watch/STATE.txt` on skampere1 (history in `watch.log`), written by tmux `watch-e20` when worker tmux `codex-rl4cv-e20-irt-prompt-selection` (Codex since 13:41 PDT 10-21-2026) is DONE, DEAD, BLOCKED or IDLE for 75 min. On anything but DONE, recover under agents-config Rules 58/69 from the worker's checkpoint and re-arm the watch.
1. When experiment 13 publishes per-task V4-G0 strict counts (32 train tasks x 32 samples), score `expt_v1/forecasts/e19_g3_forecast_v4_g0.json`: for each of the three forecasts, Spearman vs the unbiased per-task G=8 mixed probability and AUC for 1 <= s <= 31; Brier for the judgement events.
2. [p 7/10] G2: CPU re-score of experiment 08's stored sft_4B_f1p0 validation files with experiment 13's declaration probe.
3. [p 6/10] After 11-06-2026: add VeriBench 107/109's 2026 systems; refit the two-skill model on a finer grid.

## Brando to-do
- none

## Log
- 10-20-2026 16:00 PDT -- created; inventory done, features computed, protocol drafting.
- 10-20-2026 16:32 PDT -- revision 1 locked (pins + frozen forecast) as provisional 18.
- 10-20-2026 16:51 PDT -- renumbered 19 (ub9/e18a claimed 18); revision-1 run stopped at start, no output; gold-check target added as revision 2.
- 10-20-2026 17:20 PDT -- Amendment 01 (light QA, Fable 5.1 max, CORRECT 9/10) committed after run start, before any output read; SSH to skampere1 dropped at 00:08Z (watch exit 255); the run itself is in its own tmux session, status not yet re-checked.
- 10-20-2026 19:01 PDT -- locked run DONE (01:50:56Z, 7,124 s, exit 0); results.md published; G3 frozen 01:58:55Z (sha256 abb0cb31...).
- 10-20-2026 19:05 PDT -- proposal to 13's owner sent, idea page synced, cleanup done; lane idle until 13 publishes V4-G0 counts.
- 10-21-2026 11:30 PDT -- Brando asked to use Sang Truong's textbook and lecture picks for an excellent prompt and to test whether Azalia's idea works with IRT. Experiment 20 claimed (d4f08581, merged be2e8d03); runbook `expt_v1/cc.md` sha256 2dc453bc8f13.... Worker dispatched on skampere1 (deploy_cc deployment deploy_ed87a5b1900b45d2af6e22c1707cc31e; Claude Code claude-fable-5-1, max effort, profile cc = `clauded` personal config, bypass permissions on; the dispatcher accepted the folder-trust prompt). Useful progress verified 18:26:36Z (runbook read; routed rules and reusable code loading). Completion-marker note queued to the worker; watch armed 18:29:16Z.
- 10-21-2026 12:36 PDT -- The watch reported BLOCKED at 19:17:17Z: the shared personal Claude account hit its session limit at 19:16:51Z, and other personal-account workers on skampere1 draw on it too. Claude Code auto-continued at the 19:21:21Z reset, so no relaunch or account switch was needed. The watcher now re-checks auto-continuing limit pauses every 10 min and reports only one that lasts over 6 h. It was re-armed at 19:36:04Z; the old verdict is archived as `e20_watch/STATE_20261021T191717Z_blocked_autoresumed.txt`.
- 10-21-2026 13:45 PDT -- Worker change at the general coordinator's request: Brando's personal Claude weekly allowance (85% used) is reserved for vb-private's Rule 43 reviews. The Claude Fable 5.1 worker handed off at e39d620a (12:40 PDT; Sherlock 48841018 running, 48845232 pending, untouched) and was fenced (session closed, no process left). Codex gpt-6-astra ultra (personal ~/.codex; probe PONG; weekly 26% used, no purchased credits) was deployed 20:41:51Z in tmux `codex-rl4cv-e20-irt-prompt-selection` (deploy_50715cf54e614ecf914f0f7da4aae03c) with brief `/lfs/skampere1/0/brando9/e20_watch/resume_codex_e20.md`. This is an implementation-only role, so no measured model or protocol changed. The watch was re-armed 20:42:52Z on the new session.
