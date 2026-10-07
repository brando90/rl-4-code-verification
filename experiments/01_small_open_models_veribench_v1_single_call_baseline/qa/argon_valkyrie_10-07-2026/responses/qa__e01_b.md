### QA Review — `experiments/01_small_open_models_veribench_v1_single_call_baseline/`

---

#### F1 — CRITICAL: Declared model `Qwen3.5-0.8B` (`qwen3.5-0.8b`) is missing from the G=1 evaluation table and was never FSC-judged, contradicting completion claims (`STATUS_e01 = DONE`)

- **Files:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/README.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/CKPT_e01.md`
  - `experiments/README.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/results/judge/state.json`
- **Evidence:**
  - `results.md` (G=1 table, line 43):
    `| Qwen3.5-0.8B | — | unmeasured | | | | | | | |`
  - `README.md` (Status table, lines 72–75):
    `| G = 1 evaluation, 9 models (8 + 27B control) | Done (10-01-2026 06:45) | all 896/896 cells generated and kernel-scored for every model |`
    `| FSC judging | Done (10-01-2026 09:08) | route: vb103_judge Valkyrie, payer: Vals gateway; all 9 suites (controls + 8 models) admitted and harvested, $102.55 of $400 spent |`
  - `CKPT_e01.md` (lines 9, 23):
    `FSC judging: controls + all 8 non-control models + the 27B route control, all admitted and harvested`
    `Killed all 9 service+tunnel PID pairs: 9700 controls (2844733/2847847), 9701 qwen3.5-4b (284032/289990), 9702 qwen3-8b (3526349/3528318), 9703 qwen3-14b (3584059/3588813), 9704 qwen3-4b (1282797/1285879), 9705 qwen3.5-2b (747670/749896), 9706 qwen3.5-9b (568476/570184), 9707 qwen3-1.7b (2223668/2226251), 9708 qwen3.6-27b-local (279053/281164).`
- **Why it is wrong:**
  `expt_v1/models.yaml` declares 8 small models plus 1 route control = 9 models (which, together with `rl4cv-e01-controls`, requires 10 judge suites). Only 8 models (7 small models + the 27B control) were judged and populated into `results.md`. `Qwen3.5-0.8B` has no `fsc_qwen3.5-0.8b.json`, no `judge_pack_qwen3.5-0.8b.json`, no harvest files, no entry in `results/judge/state.json`, no row in the Judge spend table, and remains blank (`unmeasured`) in the G=1 evaluation table in `results.md`. Marking the experiment `DONE` in `CKPT_e01.md`, `README.md`, and `experiments/README.md` violates `PROTOCOL.md` ("The experiment is complete when every declared cell (9 models × 896 at G = 1, and 8 models × 132 × 8 at G = 8) has a terminal receipt and a scored or explicitly unmeasured status, and both tables are published with full denominators").
- **Minimal fix:**
  Populate `Qwen3.5-0.8B`'s G=1 kernel-scored metrics and revision (`2fc06364`) into `results.md`, run the FSC judge suite `rl4cv-e01:qwen3.5-0.8b` (or explicitly report its FSC as unmeasured with the reason), and commit `fsc_qwen3.5-0.8b.json` and its judge receipts.

---

#### F2 — CRITICAL: Four of the eight declared G=8 probe models (`Qwen3.5-2B`, `Qwen3.5-9B`, `Qwen3-1.7B`, `Qwen3-4B`) and required probe metrics/channels (`pass@8`, `scsc`, `fsc_compiled`) are missing from `results.md`

- **Files:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/PROTOCOL.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/README.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/run_model.sh`
- **Evidence:**
  - `results.md` (Signal probe table, lines 75–88): lists only `Qwen3.5-0.8B`, `Qwen3.5-4B`, `Qwen3-14B`, and `Qwen3-8B`, followed by:
    `Qwen3.5-9B, Qwen3-1.7B, Qwen3-4B still probing/scoring.`
  - `PROTOCOL.md` (Locked parameters):
    `| FSC judge | ... Scope: every cell with IC_tests · IC_proofs > 0, plus a 60-file audit per model ... |`
    `| Reward channels in the probe | kernel_binary, proof_fraction (plus scsc and fsc_compiled once judged) |`
  - `README.md` (§Method step 7):
    `Probe table: mean reward, pass@8, mixed-group share, ρ and H per split, for kernel_binary and proof_fraction.`
  - `run_model.sh` (line 66):
    `for CH in kernel_binary proof_fraction; do`
- **Why it is wrong:**
  1. Despite `results.md`'s TLDR and `README.md` claiming all 8 probe models are complete, 4 of the 8 probe models (`Qwen3.5-2B`, `Qwen3.5-9B`, `Qwen3-1.7B`, `Qwen3-4B`) are missing from the Signal probe table in `results.md`, and line 88 still says 3 of them are "still probing/scoring" (omitting `Qwen3.5-2B` entirely).
  2. `pass@8` is missing from the probe table in `results.md`.
  3. `Qwen3-14B` has positive (`IC_tests · IC_proofs > 0`) cells in the G=8 probe (`Mean reward = 0.0068` on `kernel_binary`, i.e., 7/1024 cells), but `judge_rl4cv_e01.py` only inspects `jobs/<label>_g1_s0` and never judged positive probe cells, nor did `run_model.sh` compute the `scsc` and `fsc_compiled` probe channels required by `PROTOCOL.md` and `cc.md` §6.
- **Minimal fix:**
  Add the missing 4 models (`Qwen3.5-2B`, `Qwen3.5-9B`, `Qwen3-1.7B`, `Qwen3-4B`) and `pass@8` to the G=8 probe table in `results.md`, remove the stale "still probing/scoring" text, judge any G=8 probe cells with `IC_tests · IC_proofs > 0`, and run `rl4cv.probe` for `scsc` and `fsc_compiled`.

---

#### F3 — CRITICAL: Kernel-scoring and probe summary files (`expt_v1/results/summaries/summary_*.json`, `rho_h_*.{json,md}`, and `results_summary_*.md`) were never committed to the repository, and FSC was never re-collected

- **Files:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/cc.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/run_model.sh`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/judge_rl4cv_e01.py`
- **Evidence:**
  - `results.md` (line 88):
    `per-split values and pass@8 are in expt_v1/results/summaries/rho_h_<label>_g8_<channel>.{json,md}.`
  - `cc.md` (§6 and §7.2–7.3):
    `Write $OUT/fsc/<job>.json as a map from task_id to FSC, then rerun collect, summarize and probe so that scsc and fsc_compiled appear.`
    `2. Write the summary. Add expt_v1/results/results_summary_<MM-DD-YYYY__HH-MM-SS>.md ...`
    `3. Commit summaries only. Commit the JSON summaries, model_revisions.json, preflight.json, REPORT.md and the probe rho_h_*.json and .md.`
- **Why it is wrong:**
  `run_model.sh` wrote `summary_${NAME}.json` and `rho_h_${NAME}_${CH}.json` to `$OUT/summaries/` on `/lfs/skampere1/0/brando9/rl4cv_e01/out/summaries/` outside the git repository. None of `expt_v1/results/summaries/summary_*.json`, `expt_v1/results/summaries/rho_h_*.{json,md}`, or `expt_v1/results/results_summary_*.md` exist in the repository manifest. As a result, the path cited in `results.md` (`expt_v1/results/summaries/...`) is a broken reference, and none of the kernel-scoring or probe numbers in `results.md` can be verified from committed summary files. Additionally, `judge_rl4cv_e01.py` writes `expt_v1/results/fsc_<label>.json` rather than `$OUT/fsc/<job>.json` and never reran `collect`, `summarize`, and `probe`.
- **Minimal fix:**
  Export `$OUT/fsc/<job>.json`, rerun `collect`, `summarize`, and `probe`, copy `$OUT/summaries/*` into `expt_v1/results/summaries/`, write `expt_v1/results/results_summary_<MM-DD-YYYY__HH-MM-SS>.md`, and commit them.

---

#### F4 — CRITICAL: `judge_rl4cv_e01.py` (`build_model_pack`) filters to `r.get("measured")` (`finish_reason == "stop"`) before selecting positive cells and the 60-file audit, violating `PROTOCOL.md`'s outcome-blind 60-file audit rule and introducing survivorship bias

- **Files:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/judge_rl4cv_e01.py`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/PROTOCOL.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md`
- **Evidence:**
  - `judge_rl4cv_e01.py` (lines 166–176):
    ```python
    rows = [json.loads(l) for l in scored_jsonl.read_text().splitlines() if l.strip()]
    measured = [r for r in rows if r.get("measured")]
    positives = [r for r in measured if (r.get("IC_tests") or 0) * (r.get("IC_proofs") or 0) > 0]
    by_split: dict[str, list[dict]] = {}
    for r in measured:
        by_split.setdefault(r["task_id"].split("__", 1)[0], []).append(r)
    # PROTOCOL.md's 60-file audit: 12 per core split, outcome-blind hash order (never based on score).
    audit = []
    for split in CORE_SPLITS:
        pool = sorted(by_split.get(split, []),
                     key=lambda r: sha(f"rl4cv-e01-audit:{label}:{r['task_id']}".encode()))
        audit.extend(pool[:per_core_split])
    ```
  - `PROTOCOL.md` (Locked parameters):
    `| Measured cell | finish reason stop (clean); length is recorded as cut off (not admitted under overlong filtering) and still scored as it stands |`
    `| FSC judge | ... Scope: every cell with IC_tests · IC_proofs > 0, plus a 60-file audit per model (12 per core split, outcome-blind hash order, compiling or not). |`
  - `fsc_qwen3.5-2b.json` (`"n_items_judged": 51`), `fsc_qwen3-1.7b.json` (`"n_items_judged": 57`), `fsc_qwen3.6-27b-local.json` (`"H2_sol_high": {"measured": 52}`).
- **Why it is wrong:**
  1. In `rl4cv.veribench.generate`, `measured` is `True` only when `finish_reason == "stop"`, whereas cells cut off at the token cap (`finish_reason == "length"`) have `measured == False` even though `PROTOCOL.md` mandates they are "still scored as it stands". Filtering to `measured` before computing `positives` and `by_split` drops any cut-off cell with `IC_tests · IC_proofs > 0` from `positives` and excludes all cut-off cells from the 60-file audit.
  2. For models with many cut-off cells (`qwen3.5-2b`: 475/896 cut off; `qwen3-1.7b`: 252/896 cut off; `qwen3.6-27b-local`: 236/896 cut off), core splits like `cs_set` and `realcode_set` had fewer than 12 non-cut-off cells, shrinking their audit packs to 51, 57, and 52 cells instead of the locked 60 cells (12 per core split).
  3. Conditioning the audit pool on `finish_reason == "stop"` is not outcome-blind: it excludes a model's 65,536-token timeout/cut-off failures (and if a cell had no Lean extracted, `solution.lean` is also skipped at line 183). This survivorship bias directly affects the finding highlighted in `results.md`'s TLDR (`Qwen3.6-27B's ungated audit FSC (0.771) is far higher than every smaller model's (0.07–0.46 range)`), because 236 cut-off cells were pre-filtered out of `Qwen3.6-27B`'s pool while `Qwen3.5-4B`/`9B`/`14B` had only 5–21 cut-off cells filtered out. In addition, salting the audit hash with `{label}` (`rl4cv-e01-audit:{label}:{task_id}`) causes every model to be audited on a different subset of core tasks.
- **Minimal fix:**
  Select the 60 audit tasks (12 per core split) from all 896 declared tasks in outcome-blind hash order (`sha256("rl4cv-e01-audit:" + task_id)`, without filtering on `r.get("measured")` or salting by `label`), compute `positives` over all scored rows regardless of `finish_reason`, and judge the missing audit cells so every model has the full 60-cell audit.

---

#### F5 — MAJOR: Violation of `CLAUDE.md` VeriBench evaluation rules — Core 614 and IndustrySet 282 are not reported separately, unmeasured FSC cells are dropped from denominators, and `qwen3-1.7b`'s FSC mean is misrounded

- **Files:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md`
  - `CLAUDE.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/README.md`
- **Evidence:**
  - `CLAUDE.md` (Scientific integrity):
    `SCSC = (IC_tests · IC_proofs · FSC)^(1/3) is the only aggregate, always shown with its three factors and n. Core 614 and IndustrySet 282 are reported separately.`
    `Unmeasured cells stay in the denominator and are listed, never counted as zero.`
  - `README.md` (§Method step 7):
    `Per-model table: IC_tests, IC_proofs, FSC, SCSC and n, with core 614 and IndustrySet 282 reported separately, cut-off and unextracted counts, and mean generated tokens.`
  - `results.md` (lines 41–58):
    Reports only a single combined 896-task row per model; omits `mean generated tokens`; reports FSC means by dividing by the reduced measured count (`18.7 / 57 = 0.328` for `Qwen3.5-4B`, `24.0 / 58 = 0.414` for `Qwen3.5-9B`, `27.7 / 60 = 0.462` for `Qwen3-14B`, `39.3 / 51 = 0.771` for `Qwen3.6-27B`, `3.7 / 51 = 0.073` for `Qwen3.5-2B`, and `5.5 / 57 = 0.09649` reported as `0.097` for `Qwen3-1.7B`).
- **Why it is wrong:**
  1. `results.md` does not report Core 614 and IndustrySet 282 separately, nor does it report `mean generated tokens`.
  2. When judge cells failed with `unmeasured_infra` (3 cells in `qwen3.5-4b`, 2 in `qwen3.5-9b`, 1 in `qwen3-14b`, 1 in `qwen3.6-27b-local`) or when audit cells were skipped (9 in `qwen3.5-2b`, 3 in `qwen3-1.7b`, 8 in `qwen3.6-27b-local`), `results.md` dropped them from the denominator instead of keeping the full declared audit denominator (60, or 61 for `qwen3-14b`) and listing the unmeasured count in the table. Footnotes in `results.md` also omit that `Qwen3.5-4B` had 3 `unmeasured_infra` cells and that `Qwen3-1.7B` and `Qwen3.6-27B` had fewer than 60 audit cells (57 and 52).
  3. For `Qwen3-1.7B`, the sum of the 57 task FSC values in `fsc_qwen3-1.7b.json` is `5.5`; `5.5 / 57 = 0.096491...`, which rounds to `0.096` (or `5.5 / 60 = 0.092` over 60 audit cells), not `0.097`.
- **Minimal fix:**
  Report Core 614 and IndustrySet 282 separately (along with `mean generated tokens`), keep all declared audit cells in the denominator while explicitly listing unmeasured counts alongside each FSC number (or retry the `unmeasured_infra` cells per `CLAUDE.md`), and fix the rounding of `Qwen3-1.7B`'s FSC mean.

---

#### F6 — MAJOR [UNCERTAIN]: `judge_rl4cv_e01.py` builds only 1 repeat (`repeat=1`) per cell instead of the locked 3 repeats per ensemble member

- **Files:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/judge_rl4cv_e01.py`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/PROTOCOL.md`
  - `docs/DECISIONS.md`
- **Evidence:**
  - `PROTOCOL.md` (Locked parameters) & `docs/DECISIONS.md` (D-102):
    `vb103_judge (experiment 100 H2: GPT-6 Sol high plus Claude Opus 5.5 max, median of 3 each, mean of the 2, divided by 5).`
  - `judge_rl4cv_e01.py` (line 143):
    `cells = judge_run.build_cells(None, 1, CONTROL_KINDS, items_path=items_path)`
  - `judge_rl4cv_e01.py` (line 207):
    `cell = {"cell": f"{row['item']}__r1", "item": row["item"], "task": row["task"], "repeat": 1, "kind": "main"}`
  - `judge_rl4cv_e01.py` (lines 382–393):
    ```python
    for cell in harvested["cells"]:
        if cell["status"] == "measured":
            by_item.setdefault(cell["item"], []).append(cell["score_raw"])
    ...
    medians = [statistics.median(members[c][item]) for c in CONFIGS if members[c].get(item)]
    ```
- **Why it is wrong:**
  `judge_rl4cv_e01.py` creates only a single repeat (`__r1`, `repeat=1`) per item in both `build_controls` and `build_model_pack`, and then `fsc()` calls `statistics.median(members[c][item])` on a 1-element list. Unless the external `vb103_judge` Valkyrie agent internally performs 3 repeat calls and returns their median inside a single `solution_b64` verdict (which is UNCERTAIN from this packet because `external/veribench` is git-ignored, though the explicit `repeats=1` argument to `judge_run.build_cells` and the `statistics.median` aggregation over `by_item` in `fsc()` indicate repeats are meant to be separate `__r1..__r3` cells), the judge was run with 1 sample per member instead of the locked median of 3.
- **Minimal fix:**
  Verify whether `vb103_judge` already takes a 3-sample median inside a single Valkyrie cell; if not, build 3 repeats (`__r1`, `__r2`, `__r3`) per item or document the single-repeat deviation in `REPORT.md`.

---

#### F7 — MAJOR: Concurrency, race, and process-management bugs in `score_worker_shared.sh`, `score_worker.sh`, `wait_and_merge_27b_shard2.sh`, and `judge_rl4cv_e01.py`

- **Files:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/orchestration/score_worker_shared.sh`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/orchestration/score_worker.sh`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/orchestration/wait_and_merge_27b_shard2.sh`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/judge_rl4cv_e01.py`
- **Evidence:**
  - `score_worker_shared.sh` (line 25):
    `running() { pgrep -cf "score_scsc.py --job-dir" 2>/dev/null || echo 0; }`
  - `score_worker.sh` & `score_worker_shared.sh` (lines 40–42):
    ```bash
    [ -f "$LOCK" ] && continue
    while [ "$(running)" -ge "$MAX_CONCURRENT" ]; do sleep 15; done
    touch "$LOCK"
    ```
  - `wait_and_merge_27b_shard2.sh` (lines 20–56):
    Polls `wc -l < "$MAIN"` every 30s for `[ "$n" -ge 640 ]`, kills `rl4cv.veribench.generate`, and runs `cat "$SHARD2" >> "$MAIN"`.
  - `judge_rl4cv_e01.py` (lines 253–267):
    `spent_so_far()` sums `charges_usd` only over `(RESULTS / "harvests").glob("cells_*.json")`.
- **Why it is wrong:**
  1. `REPORT.md` Deviation 13 states that the `pgrep -cf ... || echo 0` double-stdout bug (which prints `"0\n0"` when no scorer is running, breaking `[ "$(running)" -ge "$MAX_CONCURRENT" ]`) was fixed in the committed copy, but it was only fixed in `score_worker.sh`, leaving the exact bug in `score_worker_shared.sh` line 25.
  2. In both `score_worker.sh` and `score_worker_shared.sh` (which run concurrently), `[ -f "$LOCK" ]` is checked *before* sleeping in `while [ "$(running)" -ge "$MAX_CONCURRENT" ]; do sleep 15; done`, and `touch "$LOCK"` is executed *after* the loop, creating a TOCTOU race if both workers inspect an overlapping job or across iterations.
  3. In `wait_and_merge_27b_shard2.sh`, during the 30-second polling window after `$MAIN` reaches 640 rows, the main job starts batch `[641–896]` (the same task IDs as `SHARD2`); if any row is flushed before `kill` completes, `cat "$SHARD2" >> "$MAIN"` produces >896 rows with duplicates, causing `run_model.sh`'s manifest check (`len(rows) != len(got)`) to fail. It also never kills the parent `run_all_e01.sh` driver process.
  4. In `judge_rl4cv_e01.py`, `spent_so_far()` ignores admitted runs that have not yet been harvested and checks `SPEND_CAP_USD` only once before iterating over `configs`, so admitting multiple suites before harvesting bypasses the spend-cap guard.
- **Minimal fix:**
  Fix `running()` in `score_worker_shared.sh` to match `score_worker.sh`; acquire the lock atomically via `mkdir "$LOCK"` *after* the concurrency wait (and `continue` if `mkdir` fails); deduplicate or truncate `$MAIN` to the first 640 rows before appending `$SHARD2` in `wait_and_merge_27b_shard2.sh`; and include an estimated or state-tracked cost for unharvested runs in `spent_so_far()`.

---

#### F8 — MINOR: Contradictory/stale status lines across markdown files and missing required file headers in `cc.md` and `DISPATCH_e01.md`

- **Files:**
  - `experiments/README.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/README.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/CKPT_e01.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/orchestration/README.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/cc.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/DISPATCH_e01.md`
- **Evidence:**
  - `experiments/README.md` (line 5): `Experiment 01 is the shared baseline and is running on SNAP.` vs. line 9: `**Done (10-01-2026 09:08)** on skampere1`.
  - `README.md` (line 5): `Nothing has been run yet.` vs. line 79: `**Experiment complete as of 10-01-2026 09:08**`.
  - `CKPT_e01.md` (line 7): `## EXPERIMENT COMPLETE — 10-01-2026 09:08 (STATUS_e01 = DONE)` vs. line 115: `- **State files:** $WORK/STATUS_e01 = RUNNING.`
  - `orchestration/README.md` (line 7): `See expt_v1/CKPT_e01.md → "LIVE STATUS SNAPSHOT" for what's running where right now.` (no such section exists in `CKPT_e01.md`).
  - `results.md` (line 5): `as of 10-01-2026 09:08` vs. line 23: `Last updated: 10-01-2026 01:15.`
  - `CLAUDE.md` (Repository conventions): `Every document starts with # Title, a **Doc link:** line and a **TLDR:**.` (`DISPATCH_e01.md` has neither `**Doc link:**` nor `**TLDR:**`; `cc.md` lacks `**Doc link:**`).
- **Why it is wrong:**
  Top-level TLDRs and bottom status lines were left in pre-run or mid-run states while other sections of the same files were updated to "complete", and two markdown documents lack the required header lines specified in `CLAUDE.md`.
- **Minimal fix:**
  Reconcile the status lines across `experiments/README.md`, `README.md`, `CKPT_e01.md`, `orchestration/README.md`, and `results.md`, and add the missing `**Doc link:**` and `**TLDR:**` lines to `DISPATCH_e01.md` and `cc.md`.

---

VERDICT: FAIL
CRITICAL_ISSUES: 4
MAJOR_ISSUES: 3
MINOR_ISSUES: 1
SUMMARY: Experiment 01 is marked `DONE`, but `Qwen3.5-0.8B` is missing from the G=1 table and was never FSC-judged, 4 of the 8 probe models and `pass@8`/`scsc`/`fsc_compiled` are missing from the G=8 probe table, none of the required `expt_v1/results/summaries/` JSON/MD files were committed, and `judge_rl4cv_e01.py` violated the locked outcome-blind 60-file audit protocol by pre-filtering out cut-off generations.