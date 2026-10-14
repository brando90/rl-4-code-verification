# CKPT e12 v2 — corrected prospective hidden-test adapter (experiment 12 version 2)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v2/CKPT_e12_v2.md>

**TLDR:** Rule 44 checkpoint for experiment 12 version 2. This round (10-14-2026, zero model calls, zero Lean compilations, no GPU) delivered the design, the adapter with 64 passing tests, zero-Lean static controls over all 882 gold suites, a zero-call mapping census over 4,626 compiling primary cells on `skampere1`, a locked protocol (amendment V2-A1 after the static controls), and a frozen forecast with its amendment note. The Lean evaluation is Emily Xia's run per `cc.md`.

**Created:** 10-14-2026 13:20 PDT
**Last updated:** 10-14-2026 13:30 PDT

## Goal

Fix version 1's adapter defects prospectively (lexer without `?`/`!`, helper entry points, partial applicability counted as failure), measure the mapping change without computing any hidden outcome, lock the protocol and freeze the forecast so the owner can run the corrected evaluation.

## What ran

- Read version-1 README, PROTOCOL (A1, A2, § 8), results (inspection, post-lock limitation), `disagreements_e12.json`, the frozen scripts and tests, `cc.md`, `CKPT_e12.md`.
- Host (`brando9@skampere1`, read-only on version-1 data; host clone `/lfs/skampere1/0/brando9/rl4cv_e12/rl-4-code-verification` pulled to `main`; scratch `/lfs/skampere1/0/brando9/rl4cv_e12/v2_census/`): declaration skeletons of the 20 inspected candidates (names, headers, own example statements; no bodies) → `fixtures/disagreement_skeletons_e12v2.json`.
- `scripts/adapter_v2.py`; `tests/test_e12_adapter_v2.py` 64 passed; `make test` 398 passed / 36 skipped / the 4 pre-existing macOS-only failures (`test_e13_v2_a2.py::test_a2_process_retry_and_resume_preserve_originals`, three `test_e13_v2_watchdog.py` cases).
- `scripts/static_controls_v2.py` on the host (10.2 s): first run found 7/882 wrong static step-2b picks in the renamed-gold control → amendment V2-A1 (word-boundary suffix affinity with a reference veto) → rerun 0/882 wrong, gold self-mapping 882/882.
- `scripts/mapping_census_v2.py` on the host (26.2 s, no tmux needed, no Rule 70 email needed): `results/mapping_census_v2.json`, reads only mapping fields of version-1 receipts.
- Documents: `README.md`, `DESIGN.md`, `PROTOCOL.md` (locked at `af0af4f`; § 8 amendment at `830d3b2`), `results.md`, `cc.md`, this file; `../results.md` status line. Forecast frozen with `scripts/freeze_forecast_v2.py` (`e12_v2_forecast.json`, SHA-256 `f176c346…`, commit `3730e45`) and its amendment (`e12_v2_forecast_amendment_A1.json`, SHA-256 `30022b44…`, commit `68b47d2`).

## Results

- Census (4,626 compiling primary cells with tests): version 2 static maps every symbol in 3,121 (0.675), partial 315, probe 263, none 927; version 1 recorded 3,444 all / 3,911 any after Lean probes. Changed entry point in 379/3,624 cells both map; helper excluded in 364; result/argument type mismatch flagged in 272/266; 612 cells with zero self-test declarations (baseline 552, Leanstral 60). Tests mappable: 40,695/55,967; all tests mappable in 3,121 cells, none in 1,070. Gold side: 0 implementation symbols and 0 test symbol tokens affected by the lexer fix → version-1 suite reused unchanged. Deterministic counts, p-val=n/a.
- Static controls: C1-static 882/882; C2-static 0/882 wrong (855 deferred to the probe, 24 resolved correctly, 3 not applicable statically).
- No hidden pass/fail, pass rate, P1/P2/P3 or G-A value was computed in version 2.

## Stuck / blocked

- Nothing blocking this round. Not done here by design: the version-2 runtime/controls/evaluator/analyzer ports and the Lean evaluation (Emily; see `cc.md` § 3–5).
- Known residual limits are in `DESIGN.md` § 7 (no `Option`/`Except` unwrapping; the frozen `atom_at` helper; probe needs candidate examples).

## Next steps

1. Emily: `git pull`, run `cc.md` § 2 verification (now also checks `e12_v2_forecast_amendment_A1.json`'s adapter hash `da6fbe36…`), port `runtime_v2.py` / `controls_v2.py` / `evaluate_v2.py` / `analyze_v2.py` by swapping in `adapter_v2`, run C1–C4, then the 4,626-cell evaluation (≈ 4–5 h at two workers reusing version-1 modules), then the analyses and `results.md`.
2. Master: update `experiments/README.md` row 12 with the proposed text in the worker's final report.

## Brando to-do

- None required. Optional: confirm that version 2's P2/P3 primary cohort is the fully applicable cells (PROTOCOL § 5), decided here under Rule 57; the ≥ 1 evaluable cohort is reported as sensitivity S-V2a either way.

## Log

- 10-14-2026 13:20 PDT — Created after the census. Commit `d3c2777` (adapter, fixtures, tests, census script).
- 10-14-2026 13:30 PDT — Pushed `6abbb84` (design, README, census), `af0af4f` (protocol lock), `ec6c40c` (version-1 status line), `3730e45` (forecast), `830d3b2` (amendment V2-A1, static controls, census rerun), `68b47d2` (forecast amendment A1). Next commit: `cc.md` and this checkpoint. Host clone pulled to `main`; scratch outputs in `/lfs/skampere1/0/brando9/rl4cv_e12/v2_census/`.
