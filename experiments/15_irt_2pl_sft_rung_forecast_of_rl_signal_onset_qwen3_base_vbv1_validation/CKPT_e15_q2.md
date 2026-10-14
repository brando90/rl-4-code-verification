# CKPT e15 Q2: IRT rung forecast of RL-signal onset (zero model calls)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/15_irt_2pl_sft_rung_forecast_of_rl_signal_onset_qwen3_base_vbv1_validation/CKPT_e15_q2.md>

**TLDR:** Rule 44 checkpoint for experiment `15_irt_2pl_sft_rung_forecast_of_rl_signal_onset_qwen3_base_vbv1_validation` (Q2 of the VeriBench item response theory (IRT) idea page), owned by the Claude Code ultracode worker (claude-fable-5-1, effort max) dispatched by the master session on 10-14-2026 during the Valkyrie outage. Zero model calls, zero GPU; everything runs on Brando's Mac from committed validation-split files.

Created: 10-14-2026 13:09 PDT
Last updated: 10-14-2026 13:09 PDT

## Goal

Design, lock, freeze and run a zero-call test of whether a two-parameter logistic (2PL) IRT model fitted on the earlier supervised fine-tuning (SFT) rungs of Qwen3 Base 1.7B/4B/8B/14B (experiments 05 and 08, 135 validation tasks × 8 attempts) forecasts the next rung's per-task success probability and expected mixed-group share better than the last rung carried forward (B1) and a scalar scaling curve (B2). Verdict rule: SUCCESS only if IRT beats both with 95% paired task-bootstrap intervals excluding 0.

## What ran

- 13:04 PDT: `pin_inputs_e15.py` pinned 29 input files (SHA-256); validation 135 and test 222 ids are disjoint; no test-split outcome file is an input.
- 13:05 PDT: `analyze_e15.py --synthetic 1 --boot 500` ran end to end in 16 s on a 2PL-generated stand-in (pipeline check only).
- 13:08 PDT: `tests/test_e15_irt.py`: 14 passed (gradients, binomial = expanded Bernoulli, recovery, baselines, bootstrap plumbing, split restriction with a smuggled test id, degenerate accounting, decision rule, synthetic end-to-end, forecast lookup).
- Full suite and commits: see Log.

## Results

None on real data yet (the forecast is frozen first).

## Stuck / blocked

Nothing. Valkyrie is down but this experiment makes no model calls.

## Next steps

1. Commit 1: folder (README, PROTOCOL, code, tests, pins) after `make test`.
2. Commit 2: the frozen forecast only (`freeze_forecast_e15.py`).
3. Run `analyze_e15.py` on the real validation files; write `results.md`; commit 3.

## Brando to-do

- None required. Optional: decide whether a SUCCESS here should feed experiment 08 v3's stopping-point choice (the protocol states how, acts on nothing).

## Log

- 10-14-2026 13:09 PDT: checkpoint created after the synthetic checks and unit tests passed; no real outcome read.
