# Experiment 13 v3 execution checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/CKPT_factored_pilot.md>

**TLDR:** TECHNICAL_GATES_RUNNING; exact receipts and completed update counts are in results.md. No official SCSC result without validated coverage.

Created: 10-16-2026 18:21 PDT
Last updated: 10-16-2026 19:03 PDT

## Goal
- Complete `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3` at $0 provider spend.
## What ran
- Independent clone under `/lfs/skampere1/0/brando9/rl4cv_e13v3/rl-4-code-verification`, source `de73908`; old checkout and artifacts untouched.
- Full 256-rollout identity/hash verification against actual strict optimizer inputs. GPU worker PID 2431086, initial controller session `codex-rl4cv-e13v3-technical`; follow-through session `codex-rl4cv-e13v3-followthrough`.
## Results
- 255/256 measured, 21 positive, 14/31 active complete groups; NeMo confirms 112/248 nonzero advantages. Optimizer/refit unmeasured. 72 v3 tests pass; full suite passes 1,382 tests + 6 subtests, 3 skips, exit 0. Paired pilot and validation runners are implemented; technical update still active.
## Stuck / blocked
- Nothing at technical gate. Inherited validated coverage-judge dependency needs reconciliation before zero-cost new SCSC evaluation.
## Next steps
- [p 10/10] Inspect `tail -30 /lfs/skampere1/0/brando9/rl4cv_e13v3/technical_controller.log` and `technical_followthrough.log`; do not launch another update. The original controller's final gradient-list reporting mismatch is corrected in the waiting follow-through; all successful expensive stages must exist before it acts.
- [p 9/10] Publish full-suite success and live progress; then measured T2/T3/T4 results. Full source at launch is retained under `results/launch_source/` where later reporting-only repairs changed files.
- [p 9/10] Resolve inherited coverage/mutation requirements for a local-only pilot, complete paired B/A/P seeds, and publish without fabricated SCSC.
## Brando to-do
- None.
## Log
- 10-16-2026 18:21 PDT — Created isolated v3 checkout, verified retained cohort and started tests.
- 10-16-2026 18:33 PDT — Verified live worker, exact strict-input identity and 42 new tests; armed non-repeating follow-through and reran full suite with the temporary dependency alias.
- 10-16-2026 18:41 PDT — Full tests pass; exact tensor batches match in every field except advantages, including bitwise identical trainer probabilities. Publishing technical launch and evidence.
- 10-16-2026 19:03 PDT — Receipt event: TECHNICAL_GATES_RUNNING; completed updates B/1301=0, A/1301=0, P/1301=0, B/1302=0, A/1302=0, P/1302=0.
- 10-16-2026 19:13 PDT — Implemented six paired trajectories, validation and bounded publication; 72 focused tests and full suite pass. Validation preparation rendered all 1,080 prompts with zero model calls. Disclosed pre-update CPU RNG difference; weights, optimizer and all loss inputs except advantages match strict.
