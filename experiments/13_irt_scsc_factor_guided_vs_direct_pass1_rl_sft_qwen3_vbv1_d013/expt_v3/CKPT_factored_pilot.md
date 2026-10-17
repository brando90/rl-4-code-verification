# Experiment 13 v3 execution checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/CKPT_factored_pilot.md>

**TLDR:** TECHNICAL_GATES_RUNNING; exact receipts and completed update counts are in results.md. No official SCSC result without validated coverage.

Created: 10-16-2026 18:21 PDT
Last updated: 10-16-2026 19:15 PDT

## Goal
- Complete `13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3` at $0 provider spend.
## What ran
- Independent clone under `/lfs/skampere1/0/brando9/rl4cv_e13v3/rl-4-code-verification`, source `de73908`; old checkout and artifacts untouched.
- Full 256-rollout identity/hash verification against actual strict optimizer inputs. GPU worker PID 2431086, initial controller session `codex-rl4cv-e13v3-technical`; follow-through session `codex-rl4cv-e13v3-followthrough`.
## Results
- 255/256 measured, 21 positive, 14/31 active complete groups; NeMo confirms 112/248 nonzero advantages. Optimizer/refit unmeasured. 75 v3 tests pass; full suite passes 1,382 tests + 6 subtests, 3 skips, exit 0. Paired pilot and validation runners are implemented; technical update still active.
## Stuck / blocked
- Nothing at technical gate. Inherited validated coverage-judge dependency needs reconciliation before zero-cost new SCSC evaluation.
## Next steps
- [p 10/10] Inspect `tail -30 /lfs/skampere1/0/brando9/rl4cv_e13v3/technical_controller.log` and `technical_followthrough.log`; do not launch another update. The original controller's final gradient-list reporting mismatch is corrected in the waiting follow-through; all successful expensive stages must exist before it acts.
- [p 9/10] Source `b2ac757` is pushed. Queued pilot/progress/publisher sessions are live: PIDs 524882/524898/622533; inspect `pilot_dispatch.log`, `progress.log`, `terminal_publication_v2.log` under the v3 work root. They require actual gate receipts and retain failures.
- [p 9/10] Complete the queued paired pilots under the explicit local-only scope in PILOT_EXECUTION.md. Report official SCSC values determined by local factors and bounds for unresolved coverage; never substitute the training proxy.
## Brando to-do
- None.
## Log
- 10-16-2026 18:21 PDT — Created isolated v3 checkout, verified retained cohort and started tests.
- 10-16-2026 18:33 PDT — Verified live worker, exact strict-input identity and 42 new tests; armed non-repeating follow-through and reran full suite with the temporary dependency alias.
- 10-16-2026 18:41 PDT — Full tests pass; exact tensor batches match in every field except advantages, including bitwise identical trainer probabilities. Publishing technical launch and evidence.
- 10-16-2026 19:03 PDT — Receipt event: TECHNICAL_GATES_RUNNING; completed updates B/1301=0, A/1301=0, P/1301=0, B/1302=0, A/1302=0, P/1302=0.
- 10-16-2026 19:13 PDT — Implemented six paired trajectories, validation and bounded publication; 72 focused tests and full suite pass. Validation preparation rendered all 1,080 prompts with zero model calls. Disclosed pre-update CPU RNG difference; weights, optimizer and all loss inputs except advantages match strict.
- 10-16-2026 19:15 PDT — Pushed paired-run implementation b2ac757; verified all three queued controllers and their watched process identity. Google Assistant-updates companion read back exactly; original notes and permissions preserved.
- 10-16-2026 19:18 PDT — Cost accounting retains timed-out scientific outcomes while requiring all eight opportunities and verified cleanup; included validation raw storage. All 73 focused tests pass. No pilot outcome measured.
- 10-16-2026 19:21 PDT — Verified terminal publication over unrelated remote commits without changing frozen checkout bytes or another writer’s index; all 75 focused tests pass. Publisher waiter will restart on this tested source before technical admission.
- 10-16-2026 19:22 PDT — Replaced only the idle publisher waiter after checking its PID/start ticks; current publisher PID 622533. Optimizer, replay follow-through and paired dispatcher remained untouched.
