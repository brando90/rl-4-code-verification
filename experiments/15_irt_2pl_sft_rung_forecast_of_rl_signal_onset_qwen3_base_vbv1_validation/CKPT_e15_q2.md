# CKPT e15 Q2: IRT rung forecast of RL-signal onset (zero model calls)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/15_irt_2pl_sft_rung_forecast_of_rl_signal_onset_qwen3_base_vbv1_validation/CKPT_e15_q2.md>

**TLDR:** Rule 44 checkpoint for experiment `15_irt_2pl_sft_rung_forecast_of_rl_signal_onset_qwen3_base_vbv1_validation` (Q2 of the VeriBench item response theory (IRT) idea page), owned by the Claude Code ultracode worker (claude-fable-5-1, effort max) dispatched by the master session on 10-14-2026 during the Valkyrie outage. Zero model calls, zero GPU; everything ran on Brando's Mac from committed validation-split files. DONE: verdict NO ADVANTAGE under the frozen rule.

Created: 10-14-2026 13:09 PDT
Last updated: 10-14-2026 13:14 PDT

## Goal

Design, lock, freeze and run a zero-call test of whether a two-parameter logistic (2PL) IRT model fitted on the earlier supervised fine-tuning (SFT) rungs of Qwen3 Base 1.7B/4B/8B/14B (experiments 05 and 08, 135 validation tasks × 8 attempts) forecasts the next rung's per-task success probability and expected mixed-group share better than the last rung carried forward (B1) and a scalar scaling curve (B2). Verdict rule: SUCCESS only if IRT beats both with 95% paired task-bootstrap intervals excluding 0.

## What ran

- 13:04 PDT: `pin_inputs_e15.py` pinned 29 input files (SHA-256); validation 135 and test 222 ids are disjoint; no test-split outcome file is an input.
- 13:05 PDT: `analyze_e15.py --synthetic 1 --boot 500` ran end to end in 16 s on a 2PL-generated stand-in (pipeline check only).
- 13:08 PDT: `tests/test_e15_irt.py`: 14 passed. 13:10 PDT: full suite 334 passed, 36 skipped, the 4 known macOS-only failures.
- 13:10 PDT: commit 1 pushed (design, protocol, code, tests, pins): `0ccfa1e`.
- 13:10:53 UTC+0 (13:10 PDT): forecast frozen (`e15_forecast.json`, SHA-256 `06847d32…31d5`); commit 2 pushed: `69ae5be`.
- 13:11 PDT: `analyze_e15.py` on the real validation files, 10,000 bootstrap draws, 13.65 s; 112/112 fits converged.
- 13:12 PDT: `posthoc_mixed_share_e15.py` (labelled post hoc) for the mixed-share intervals and the onset table.

## Results

- **NO ADVANTAGE.** Final rung MAE difference B1 − IRT 2PL −0.0066 [−0.0169, +0.0038] p-val=n/a; B2 − IRT 2PL +0.1151 [+0.0992, +0.1300] p-val=n/a (paired task bootstrap, 10,000 draws, 135 tasks, 4 sizes). IRT worse than B1 at every earlier rolling-origin rung (25 / 50 / 75%: −0.0093, −0.0344, −0.0270 with intervals excluding 0).
- Eligibility 4/4 sizes; 0/16 degenerate target rungs; degenerate rungs Base 1.7B and Base 8B only.
- Mixed share at 100% (realized 0.148 / 0.237 / 0.237 / 0.289 for 1.7B / 4B / 8B / 14B): IRT 2PL mean absolute error 0.027 against B1 0.065 and B2 0.411; post hoc B1 − IRT +0.0378 [−0.0089, +0.0684].
- Onset against the 0.05 gate: realized at Base (14B), 12.5% (8B), 25% (4B), 50% (1.7B); IRT forecasts 25% for all (two rungs early for 1.7B), B1 one rung late for 1.7B and 4B.
- Frozen forecast scored: 8/16 numeric predictions inside their 80% intervals; mean Brier 0.105 over 9 probabilities; P(SUCCESS) = 0.45 was the wrong lean.
- Full ledger: `results.md`.

## Stuck / blocked

Nothing. Valkyrie is down but this experiment made no model calls. The git harness refuses commands that touch another repository from this worktree, so the one-line idea-page status update in brando90/veribench is left as a next step.

## Next steps

1. (Done in commit 3) results, post hoc file and this checkpoint.
2. Master: add the experiment 15 row to `experiments/README.md` (text in the worker's structured return).
3. Optional prospective follow-up (new expt_v2, frozen first): the log-tokens trend form on experiment 08 v3's ladders; prompt-pool selection from the pooled item difficulties.
4. One status line on the VeriBench idea page (Q2 DONE, NO ADVANTAGE, 10-14-2026).

## Brando to-do

- None required. Optional: decide whether the item-difficulty side (stable across rungs and sizes) should feed experiment 13 phase 2's prompt pool as a frozen forecast.

## Log

- 10-14-2026 13:09 PDT: checkpoint created after the synthetic checks and unit tests passed; no real outcome read.
- 10-14-2026 13:14 PDT: real run complete, verdict NO ADVANTAGE; results.md written; post hoc mixed-share analysis added and labelled.
