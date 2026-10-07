# Fix experiment 01's FSC repeat deviation: judge repeats 2 and 3, recompute FSC as the locked median of 3

**TLDR:** Experiment 01's `PROTOCOL.md` (line 38) locks the FSC judge as "GPT-6 Sol high plus Claude Opus 5.5 max, median of 3 each, mean of the 2, divided by 5", but `judge_rl4cv_e01.py` built only repeat 1 of every main cell (line 240: `__r1`), so every reported FSC is a median of one call. You complete the locked design: for every main cell already judged in the 9 model suites, judge repeats 2 and 3 with both members through the same `vb103_judge` Valkyrie route (D-102), with byte-identical prompts. Then recompute FSC and SCSC as median of 3 and update `results.md`, `REPORT.md` and the checkpoint with old and new values side by side. You never overwrite the repeat-1 harvests.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## 0. Facts, verified by the master on 10-07-2026

- **Deviation evidence:** `PROTOCOL.md:38` (median of 3 each); `expt_v1/judge_rl4cv_e01.py:240` builds `cell = {"cell": f"{row['item']}__r1", … "repeat": 1}` only; every `expt_v1/results/judge/harvests/cells_<label>__H2_*.json` holds repeat-1 cells only (for example qwen3-14b, H2_sol_high: 61 cells, all repeat 1). Found by the Gemini 4 Argon QA test (`qa/argon_valkyrie_10-07-2026/results.md`); confirmed by the master.
- **Reference implementation:** VeriBench experiment 103's `scripts/judge_vbv1.py` (pinned commit `c11b99ba`) defaults to `--repeats 3` and names cells `<item>__r1`…`__r3`. Experiment 100's `judge_run.build_cells(split, repeats, controls)` builds main cells for `r in 1..repeats`, but builds every control cell as `__r1` only. Experiment 01's controls (`build_cells(None, 1, CONTROL_KINDS)`, line 152) therefore match the reference design: **controls are not part of this fix.**
- **Spend:** $106.37 of the code's `SPEND_CAP_USD = 400` used, of which $4.57 is controls. Repeats 2–3 for the main cells should cost about 2 × $101.80 ≈ $204 (total about $310). If the next admission would push the total past $400, stop and write `BLOCKED: spend cap`.
- **Zero-score diagnostic** (another session, commit `e5073b8`): "zeros are real", so the set of main cells (IC_tests · IC_proofs > 0 plus the 60-file audit) is unchanged.
- **Out of scope** (record as still open; do not fix here): the audit drew only from clean-finish cells; 11 proving G = 8 probe cells were never judged; some `results.md` summary sources were never committed; the checkpoint names 6 seed splits for experiment 02 while `results.md` names 8.

## 1. Setup

- Host `skampere1`. Experiment 01's private judge tree (rendered prompts, inputs, packs) lives under the experiment 01 clone: `/lfs/skampere1/0/brando9/rl4cv_e01/rl-4-code-verification/external/veribench/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/judge/rl4cv_e01/`. Work in that clone. Check `git status` first; commit nothing that is not yours. `git pull --ff-only origin main` (or merge), and push each landed step (`CLAUDE.md` D-012). If the clone is dirty with someone else's work, copy the private judge tree into a fresh clone under `/lfs/skampere1/0/brando9/rl4cv_e01_fsc3/` and work there instead.
- Write `RUNNING` to `/lfs/skampere1/0/brando9/rl4cv_e01/STATUS_e01_fsc_median3` and keep `expt_v1/CKPT_e01_fsc_median3.md` live: Created / Last updated from `date "+%m-%d-%Y %H:%M %Z"`, step, run ids, ports, exact next command, blockers. Append your launch receipt there first: client, host, model, effort, permission mode, tmux session. Commit and push it.
- Never touch other sessions' tmux sessions, ports or files: `rl4cv-e02a-v3-*`, `rl4cv-e07-*`, `rl4cv-e08-*`, `rl4cv-e01-zero-diag-*`. Experiment 02A v3 owns port 9720 and up.

## 2. Build repeat packs (zero model calls)

- Extend `judge_rl4cv_e01.py`, keeping the TLDR header and changing no existing behaviour:
  - `build-repeats --label <label> --repeats 2,3` reads the suite's existing `cells_receipt.json` and `rendered/<item>__r1.json`, writes `rendered/<item>__r2.json` and `__r3.json` with **byte-identical** system and user text, and builds a pack `packs/judge_rl4cv_e01_<label>_r23`. It writes receipt `results/judge/judge_pack_<label>_r23.json` with `round_trip`, `verdict`, and `n_cells` = 2 × the repeat-1 main cells.
  - A new `PARTS` entry `"r23"`.
  - A suite benchmark name `veribench-rl4cv-e01-<label>-r23`.
  - The harvest output `harvests/cells_<label>__<config>@r23.json`.
- Assert, per cell, that the r2/r3 `prompt_sha256` equals the recorded r1 `prompt_sha256`. Any mismatch is a hard stop.
- Do this for all 9 model suites. Labels are the existing `judge_pack_<label>.json` receipts (not `controls`): qwen3.5-0.8b, qwen3.5-2b, qwen3.5-4b, qwen3.5-9b, qwen3-1.7b, qwen3-4b, qwen3-8b, qwen3-14b, qwen3.6-27b-local.
- Add an offline test or self-check, commit and push.

## 3. Deploy, admit, harvest (same route as repeat 1)

- Deploy one collect-only judge service per suite with `expt_v1/deploy_rl4cv_e01_judge_service.py`, pointing its pack at the `_r23` pack. Use a claimed free port block in 9700–9719: check `ss -tlnp`, write the claim file under `/lfs/skampere1/0/brando9/valkyrie_port_claims/`, and remove it at teardown. Require health 200 with the bearer and 401 without.
- `admit --part r23 --suite rl4cv-e01:<label>` for both configs (`H2_sol_high`, `H2_opus55_max`), unchanged from repeat 1. Supervise with `poll` until terminal, then `harvest --part r23`.
- Retry policy: re-send a cell only when its receipt shows no model request was served, at most once and as the identical cell. Served or possibly served calls are never re-sent; unrecoverable cells stay `unmeasured_infra` and are listed, never dropped.
- Teardown: stop every service and tunnel you started, remove the claim, confirm with `ss -tlnp`.

## 4. Recompute, publish

- Add `fsc-median3 --suite rl4cv-e01:<label>`, which combines the repeat-1 and `@r23` harvests per member.
- **Missing-repeat rule:** first read VeriBench experiment 103's FSC aggregation at the pinned commit (`judge_cells.py` / `judge_controller.py` / `build_summary.py`) and apply its rule for items with fewer than 3 measured repeats verbatim, citing file and line. If it has none, use this rule and record it: the member's value is the median of its measured repeats; an item is FSC-incomplete only if a member has zero measured repeats; report the count of items whose median rests on 1 or 2 repeats.
- Write `results/fsc_median3_<label>.json` with per-item member repeat scores, member medians, FSC, and the old single-repeat FSC for the same items. Never edit or delete `fsc_<label>.json` or any repeat-1 harvest.
- Recompute every reported FSC aggregate (core-split audit means; Qwen3-14B's main cell and its SCSC ≈ 0.928; Qwen3.6-27B's 0.771). Then update `results.md`:
  - Tables show the median-of-3 values.
  - A dated "FSC repeat correction (10-07-2026)" section gives a per-model table: old (1 repeat) vs new (median of 3), n, delta, mean absolute change, and items resting on fewer than 3 repeats.
  - It reports the new total spend and states whether any conclusion changes, including the TLDR's FSC-ordering claim.
  - Follow Hard Rule 11: report paired old-vs-new mean differences with a 95% task-bootstrap interval (10,000 resamples, seed 20261007).
- Add a numbered `REPORT.md` entry describing the deviation, how it was found, the fix and the outcome. Update `README.md` status and the `experiments/README.md` row 01 (Done, FSC corrected to median of 3).
- Write `DONE` to the status file, give the checkpoint its final state, and push. Report the per-model old→new FSC table and total spend in the checkpoint.

**TL;DR:** Judge repeats 2 and 3 for every repeat-1 main cell with byte-identical prompts on the same route, recompute FSC as the locked median of 3 without overwriting repeat-1 evidence, and publish old-versus-new values with spend and any changed conclusions.
