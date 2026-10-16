# CKPT e12 v2 — corrected prospective hidden-test adapter (experiment 12 version 2)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v2/CKPT_e12_v2.md>

**TLDR:** Execute 12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v2 end to end under the frozen adapter, zero model/judge calls and $0 spend.

**Created:** 10-14-2026 13:20 PDT
**Last updated:** 10-15-2026 20:39 PDT
**Status:** RUNNING — implementation verified; ready to launch dynamic controls

## Goal
- Complete controls, all 4,626 eligible primary groups, 9,856-cell accounting, analysis and publication.
## What ran
- Both v2 forecasts and all five amendment-pinned inputs verified; 64 adapter + 13 runtime/evaluator/analysis tests pass. Lean v4.22.0 verified. Full suite: 1,191 passed / 18 skipped (277.51 s); latest targeted tests: 77 passed. Restored pinned external code/config dependency and installed missing Python packages in `$WORK/.venv`.
- START email sent (receipt `$WORK/start_email_receipt.json`). Owner: Codex in `codex-rl4cv-e12v2-run` on skampere1, full access/no approvals; dedicated checkout `$WORK/rl-4-code-verification`.
- Implemented runtime_v2.py, controls_v2.py, evaluate_v2.py, analyze_v2.py and support_v2.py. No dynamic control or candidate hidden outcome yet.
## Results
- Frozen artifacts unchanged. Runtime tests confirm partial applicability stays missing, probes exclude expected values, module reuse checks hashes and infrastructure retries stop at one.
## Stuck / blocked
- Nothing blocking. Synthetic Lean runtime: 2/2 evaluable, 1 pass / 1 deliberate failure. Pinned Mathlib manifest and all inherited v1 control helper hashes match. Host one-minute load exceeds 20: use two `nice -n 10` Lean workers. Health audit reported unrelated tool/shared-checkout warnings; local Lean and required data access verified.
## Next steps
- Commit/push the verified scripts, then run `python $E/expt_v2/scripts/controls_v2.py --work $WORK/controls_v2 --out $E/expt_v2/results/controls_v2.json` in named tmux.
- After all controls pass, run `evaluate_v2.py --work $WORK --panels primary`, publish every 500 groups, analyze and publish every forecast verdict; send DONE only after verified finalization.
- `WORK=/lfs/skampere1/0/brando9/rl4cv_e12/v2`; `E=experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems`. Read-only v1 root: `/lfs/skampere1/0/brando9/rl4cv_e12`.
## Brando to-do
- None.

## Log

- 10-14-2026 13:20 PDT — Created after the census. Commit `d3c2777` (adapter, fixtures, tests, census script).
- 10-14-2026 13:30 PDT — Pushed `6abbb84` (design, README, census), `af0af4f` (protocol lock), `ec6c40c` (version-1 status line), `3730e45` (forecast), `830d3b2` (amendment V2-A1, static controls, census rerun), `68b47d2` (forecast amendment A1). Next commit: `cc.md` and this checkpoint. Host clone pulled to `main`; scratch outputs in `/lfs/skampere1/0/brando9/rl4cv_e12/v2_census/`.
- 10-15-2026 20:25 PDT — User dispatched full v2 run; verified forecasts/hashes and 76 targeted tests, sent START email, implemented scripts; full-suite verification in progress.
- 10-15-2026 20:39 PDT — Implementation verified: full suite 1,191 passed / 18 skipped; 77 current targeted tests; synthetic Lean bridge produced one true and one false. Pinned dependency restored; no scientific input changes.
