### QA Review — `experiments/01_small_open_models_veribench_v1_single_call_baseline/`

#### F1 [CRITICAL] — Committed summary artifacts (`expt_v1/results/summaries/*` and `results_summary_*.md`) are missing from the repository, leaving `results.md` with a broken reference and unbacked metrics
- **Files:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/cc.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/run_model.sh`
  - `CLAUDE.md`
- **Evidence:**
  - `results.md` (final line): `"Overall" columns are group-weighted means across all 128 groups (32 splits × 4 tasks); per-split values and pass@8 are in expt_v1/results/summaries/rho_h_<label>_g8_<channel>.{json,md}.`
  - `cc.md` (§7.2–7.3): `2. **Write the summary.** Add expt_v1/results/results_summary_<MM-DD-YYYY__HH-MM-SS>.md ... 3. **Commit summaries only.** Commit the JSON summaries, model_revisions.json, preflight.json, REPORT.md and the probe rho_h_*.json and .md.`
  - `CLAUDE.md`: `Raw generations stay on the host; commit summaries.`
  - File manifest (84 files): `expt_v1/results/` contains no `summaries/` subdirectory, no `summary_<label>_g1.json` or `summary_<label>_g8.json`, no `rho_h_<label>_g8_<channel>.{json,md}`, and no `results_summary_<MM-DD-YYYY__HH-MM-SS>.md`.
- **Why it is wrong:** `run_model.sh` writes all evaluation and probe summaries to `$OUT/summaries/` (`/lfs/skampere1/0/brando9/rl4cv_e01/out/summaries/`) outside the repository checkout, and the worker never copied or committed them into `expt_v1/results/`. As a result, `results.md` references a non-existent path (`expt_v1/results/summaries/rho_h_<label>_g8_<channel>.{json,md}`), and none of the kernel-scored G=1 evaluation metrics or G=8 probe metrics (including the Gate G1 PASS numbers) can be verified from committed summary artifacts in the repository.
- **Minimal fix:** Copy `summary_<label>_g{1,8}.json` and `rho_h_<label>_g8_<channel>.{json,md}` from `/lfs/skampere1/0/brando9/rl4cv_e01/out/summaries/` into `expt_v1/results/summaries/`, write `expt_v1/results/results_summary_<MM-DD-YYYY__HH-MM-SS>.md`, and commit them.

---

#### F2 [CRITICAL] — Positive (`IC_tests · IC_proofs > 0`) cells in the G=8 probe were never FSC-judged, and `collect` / `summarize` / `probe` were never rerun with FSC scores (`scsc` and `fsc_compiled` probe channels omitted)
- **Files:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/PROTOCOL.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/cc.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/judge_rl4cv_e01.py`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/run_model.sh`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md`
- **Evidence:**
  - `PROTOCOL.md` (§ Locked parameters):
    - `FSC judge | vb103_judge (experiment 100 H2: GPT-6 Sol high plus Claude Opus 5.5 max, median of 3 each, mean of the 2, divided by 5). Scope: every cell with IC_tests · IC_proofs > 0, plus a 60-file audit per model (12 per core split, outcome-blind hash order, compiling or not). Runs only after D-102.`
    - `Reward channels in the probe | kernel_binary, proof_fraction (plus scsc and fsc_compiled once judged)`
  - `cc.md` (§6): `- **Export and re-collect.** Write $OUT/fsc/<job>.json as a map from task_id to FSC, then rerun collect, summarize and probe so that scsc and fsc_compiled appear.`
  - `results.md` (§ Signal probe): `Qwen3.5-9B` has `Mean reward = 0.0039` (`4/1024` cells with `kernel_binary = 1`) and `Qwen3-14B` has `Mean reward = 0.0068` (`7/1024` cells with `kernel_binary = 1`), i.e., 11 probe cells with `IC_tests · IC_proofs > 0`.
  - `judge_rl4cv_e01.py` (line 444) and `expt_v1/results/judge/state.json`: `judge_rl4cv_e01.py` was only run on the G=1 evaluation suites and writes `expt_v1/results/fsc_<label>.json`, not `$OUT/fsc/<job>.json`.
- **Why it is wrong:** Once D-102 was decided and `vb103_judge` ran, the protocol and agent prompt required judging every cell with `IC_tests · IC_proofs > 0`, exporting `$OUT/fsc/<job>.json`, and rerunning `collect`, `summarize`, and `probe` to populate the `scsc` and `fsc_compiled` probe channels. The 11 positive cells in the G=8 probe (`4` in `qwen3.5-9b_g8` and `7` in `qwen3-14b_g8`) were never judged, `$OUT/fsc/<job>.json` was never written, `collect`/`summarize`/`probe` were never rerun with `--fsc-root`, and the probe table in `results.md` omits `scsc` and `fsc_compiled`.
- **Minimal fix:** Judge the 11 positive G=8 probe cells via `vb103_judge`, export `$OUT/fsc/<job>.json` as a `task_id -> FSC` map for both G=1 and G=8 jobs, rerun `collect`, `summarize`, and `probe` (including `scsc` and `fsc_compiled`), and add the `scsc` and `fsc_compiled` channels to the probe table in `results.md`.

---

#### F3 [MAJOR] — `judge_rl4cv_e01.py` runs 1 repeat per judge member (`repeat = 1`) instead of the locked 3 repeats ("median of 3 each")
- **Files:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/judge_rl4cv_e01.py`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/PROTOCOL.md`
  - `docs/DECISIONS.md`
- **Evidence:**
  - `PROTOCOL.md` (§ Locked parameters): `FSC judge | vb103_judge (experiment 100 H2: GPT-6 Sol high plus Claude Opus 5.5 max, median of 3 each, mean of the 2, divided by 5).`
  - `docs/DECISIONS.md` (D-102): `Route: experiment 103's vb103_judge Valkyrie agent (experiment 100 H2 ensemble: GPT-6 Sol high + Claude Opus 5.5 max, median of 3 each, mean of the 2, divided by 5).`
  - `judge_rl4cv_e01.py` (line 135): `cells = judge_run.build_cells(None, 1, CONTROL_KINDS, items_path=items_path)`
  - `judge_rl4cv_e01.py` (lines 206–213):
    ```python
    cell = {"cell": f"{row['item']}__r1", "item": row["item"], "task": row["task"], "repeat": 1,
            "kind": "main"}
    ```
  - `judge_rl4cv_e01.py` (line 438): `medians = [statistics.median(members[c][item]) for c in CONFIGS if members[c].get(item)]`
- **Why it is wrong:** `build_controls` and `build_model_pack` generate only 1 cell (`__r1`, `repeat: 1`) per item per member instead of 3 repeats (`__r1..__r3`), so `statistics.median(members[c][item])` takes the median of a 1-element list rather than the median of 3 repeats per member as specified in `PROTOCOL.md` and `D-102`. This deviation is also undocumented in `expt_v1/results/REPORT.md`.
- **Minimal fix:** Either build and run 3 repeats per item per member (`repeat in (1, 2, 3)`) as locked in `PROTOCOL.md` and `D-102`, or explicitly document the single-repeat (`repeat = 1`) deviation in `expt_v1/results/REPORT.md` and `results.md`.

---

#### F4 [MAJOR] — `build_model_pack` filters the 60-file core-split audit to `r.get("measured")` (`finish_reason == "stop"`), violating the locked outcome-blind 60-file audit rule and shrinking audit denominators
- **Files:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/judge_rl4cv_e01.py`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/PROTOCOL.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md`
- **Evidence:**
  - `PROTOCOL.md` (§ Locked parameters): `FSC judge | ... Scope: every cell with IC_tests · IC_proofs > 0, plus a 60-file audit per model (12 per core split, outcome-blind hash order, compiling or not).`
  - `judge_rl4cv_e01.py` (lines 170–179):
    ```python
    measured = [r for r in rows if r.get("measured")]
    positives = [r for r in measured if (r.get("IC_tests") or 0) * (r.get("IC_proofs") or 0) > 0]
    by_split: dict[str, list[dict]] = {}
    for r in measured:
        by_split.setdefault(r["task_id"].split("__", 1)[0], []).append(r)
    # PROTOCOL.md's 60-file audit: 12 per core split, outcome-blind hash order (never based on score).
    ```
  - `expt_v1/results/fsc_qwen3.5-0.8b.json` (`n_items_judged: 37`, 0 items in `realcode_set`), `fsc_qwen3.5-2b.json` (`n_items_judged: 51`), `fsc_qwen3-1.7b.json` (`n_items_judged: 57`), `fsc_qwen3.6-27b-local.json` (`n_items_judged: 51` of 52 admitted).
- **Why it is wrong:**
  1. Filtering `rows` to `r.get("measured")` (`finish_reason == "stop"`) before constructing `positives` and `by_split` conditions the audit sample on a generation outcome (whether the model finished before the 65,536-token cap), violating `PROTOCOL.md`'s "outcome-blind hash order" and "60-file audit per model (12 per core split)".
  2. Because length-truncated outputs (`finish_reason == "length"`) were excluded from `by_split`, models with high truncation rates had fewer than 12 eligible tasks in several core splits: `qwen3.5-0.8b` had only 37 audit cells (and 0 in `realcode_set`), `qwen3.5-2b` had 51, `qwen3.6-27b-local` had 52 (despite `No Lean = 0`), and `qwen3-1.7b` had 57. Note also that `results.md` footnote `*` mentions the reduced audit count only for `qwen3.5-0.8b` (37) and `qwen3.5-2b` (51), omitting that `qwen3-1.7b` had 57 and `qwen3.6-27b-local` had 52.
  3. Furthermore, `fsc()` in `judge_rl4cv_e01.py` (lines 436–443) excludes the 7 `unmeasured_infra` cells (`3` in `qwen3.5-4b`, `2` in `qwen3.5-9b`, `1` in `qwen3-14b`, `1` in `qwen3.6-27b-local`) from the audit mean denominator instead of retrying those infrastructure failures per `CLAUDE.md` ("Infrastructure retries rerun the identical cell").
- **Minimal fix:** Select `positives` and the 60-file core-split audit (12 per core split) over all 896 rows without filtering on `r.get("measured")`, retry the `unmeasured_infra` judge cells so all 60 audit cells per model have measured verdicts, and report exact audit denominators (`n_measured / 60`) for every model in `results.md`.

---

#### F5 [MAJOR] — Violation of `CLAUDE.md` and `README.md` reporting rules: Core 614 and IndustrySet 282 are not reported separately, and `mean_generated_tokens` and `pass@8` are omitted
- **Files:**
  - `CLAUDE.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/README.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md`
- **Evidence:**
  - `CLAUDE.md` (§ Scientific integrity): `SCSC = (IC_tests · IC_proofs · FSC)^(1/3) is the only aggregate, always shown with its three factors and n. Core 614 and IndustrySet 282 are reported separately.`
  - `README.md` (§ Method step 7):
    - `Per-model table: IC_tests, IC_proofs, FSC, SCSC and n, with core 614 and IndustrySet 282 reported separately, cut-off and unextracted counts, and mean generated tokens.`
    - `Probe table: mean reward, pass@8, mixed-group share, ρ and H per split, for kernel_binary and proof_fraction.`
  - `results.md`: Reports only a single combined 896-task G=1 table without `mean_generated_tokens`, and a G=8 probe table without `pass@8`.
- **Why it is wrong:** `results.md` never separates Core 614 and IndustrySet 282. In particular, `Qwen3-14B`'s only positive cell (`hardware_set_real__my_interrupt_preempt`) is in `IndustrySet 282`, meaning its Core 614 `IC_proofs` and `SCSC` are `0.0` while its IndustrySet 282 `SCSC` is non-zero (`0.9283 / 282 = 0.00329`). Omitting the Core 614 vs. IndustrySet 282 split, `mean_generated_tokens`, and `pass@8` violates `CLAUDE.md` and `README.md`.
- **Minimal fix:** Add separate Core 614 (`n = 614`) and IndustrySet 282 (`n = 282`) factor/SCSC columns or sub-tables plus `mean_generated_tokens` to the G=1 table in `results.md`, and include `pass@8` in the G=8 probe table.

---

#### F6 [MAJOR] — Inconsistent definition of `Measured / 896` in `results.md` (conflating "scored" with `finish_reason == "stop"` across local vs. reference rows) and missing route-control comparison
- **Files:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/PROTOCOL.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/README.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/cc.md`
- **Evidence:**
  - `PROTOCOL.md` (§ Locked parameters): `Measured cell | finish reason stop (clean); length is recorded as cut off (not admitted under overlong filtering) and still scored as it stands`
  - `results.md` (§ VeriBench V1, G = 1 table):
    - `| Qwen3.5-0.8B | 2fc06364 | 896/896 | 661 | 95 | 0.45% | 0.0 | 0.0 | 0.011* | 0.0 (exact) |`
    - `| Qwen3.6-27B (local route control) | 6a9e13bd | 896/896 | 236 | 0 | 0.22% | 0.0011 | 0.0 | 0.771§ | 0.0 (exact) |`
    - `| Reference: Qwen3.6-27B via Valkyrie (experiment 103) | | 604 | 245 at cap | | | 0.002 | 0.002 | 0.900 | 0.002 |`
  - `README.md` (§ Method step 8): `Rerun Qwen3.6-27B locally to compare with experiment 103's Valkyrie row. Report any gap as a route difference rather than hiding it.`
  - `cc.md` (§7.1): `Fill results.md. Both tables, the gate G1 verdict with the numbers that decide it, and the route-control comparison with experiment 103's Valkyrie row.`
- **Why it is wrong:** Under `PROTOCOL.md`, a "Measured cell" is one with `finish_reason == "stop"` (clean, not cut off at `length`), which is `896 - Cut off` (e.g., `235/896` for `Qwen3.5-0.8B` and `660/896` for `Qwen3.6-27B-local`), whereas all `896/896` cells are *scored*. In `results.md`, the `Measured / 896` column reports `896/896` (scored count) for all 9 Experiment 01 models, but reports `604` (non-truncated/clean measured count) for Experiment 103's Valkyrie reference row in the same column. In addition, `results.md` footnote `§` only compares `Qwen3.6-27B-local` against the smaller models (`0.07–0.46`) and never provides the required route-control comparison explaining the differences between the local run (`660` clean / `236` cut off, `IC_tests = 0.0011`, `IC_proofs = 0.0`, `FSC = 0.771`, `SCSC = 0.0`, `tp=2`) and Experiment 103's Valkyrie row (`604` measured / `245` cut off, `IC_tests = 0.002`, `IC_proofs = 0.002`, `FSC = 0.900`, `SCSC = 0.002`).
- **Minimal fix:** Report clean (`finish_reason == "stop"`) and scored counts consistently across all rows in `results.md`, and add a dedicated route-control comparison paragraph comparing `Qwen3.6-27B (local route control)` against Experiment 103's Valkyrie row.

---

#### F7 [MAJOR] [UNCERTAIN] — `Qwen3-14B`'s max per-split mixed-group share on `aerospace_set_real` is reported as `0.333` (`1/3`) despite every probe split having 4 declared tasks (`32 × 4 = 128`)
- **Files:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/PROTOCOL.md`
  - `CLAUDE.md`
- **Evidence:**
  - `results.md` (§ Signal probe): `## Signal probe, G = 8, 128 tasks (4/split × 32 present splits)` and `Qwen3-14B: kernel_binary mixed-group share ... reaches ≥ 0.20 on 6 splits (max 0.333): aerospace_set_real 0.333, concurrent_set_real 0.25, finance_set_synthetic 0.25, gov_cert_set_synthetic 0.25, hardware_set_real 0.25, medical_oss_set_real 0.25.`
  - `CLAUDE.md` (§ Scientific integrity): `Unmeasured cells stay in the denominator and are listed, never counted as zero.`
- **Why it is wrong:** Because `rl4cv.veribench.pack --per-split 4` caps each split at 4 tasks and produced `128` tasks across `32` splits (`32 × 4 = 128`), every one of the 32 splits in `probe_task_ids.txt` has **exactly 4 declared tasks** (4 groups). A mixed-group share of `0.333` (`1/3`) on `aerospace_set_real` indicates that 1 of the 4 declared tasks in `aerospace_set_real` was dropped from the per-split denominator (e.g., because all 8 samples hit the 12,288-token cap and were filtered as unmeasured/overlong), whereas the overall mixed-group share (`6 / 128 = 0.0469`) kept all 128 tasks in the denominator. This finding is marked **UNCERTAIN** because `rho_h_qwen3-14b_g8_kernel_binary.json` was not committed (F1). (Note: even with a full 4-task denominator, `1/4 = 0.25 ≥ 0.20`, so Gate G1 still passes.)
- **Minimal fix:** Commit the `rho_h_*.json` summaries (per F1), keep all 4 declared tasks per split in the per-split mixed-group-share denominator (reporting `0.25` for `aerospace_set_real` if 1 of 4 declared tasks was mixed), and list any unmeasured/all-truncated groups explicitly.

---

#### F8 [MINOR] — Stale status, timestamps, suite counts, spend totals, and seed-split counts across `README.md`, `experiments/README.md`, and `CKPT_e01.md`
- **Files:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/README.md`
  - `experiments/README.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/CKPT_e01.md`
- **Evidence:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/README.md` (line 5): `**TLDR:** ... Nothing has been run yet.`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/README.md` (lines 77–80): `| FSC judging | Done (10-01-2026 09:08) | route: vb103_judge Valkyrie, payer: Vals gateway; all 9 suites (controls + 8 models) admitted and harvested, $102.55 of $400 spent |` and `**Experiment complete as of 10-01-2026 09:08**`.
  - `experiments/README.md` (line 12): `**Done (10-01-2026 09:08)** on skampere1; full declared set generated, scored and FSC-judged; Gate G1 **PASS**`.
  - `expt_v1/CKPT_e01.md` (line 51): `If experiment 02 or a follow-up uses this experiment's 6 kernel_binary splits ...` (contradicting line 13's `8 distinct` splits across Qwen3-14B and Qwen3.5-9B), and line 138: `- **State files:** $WORK/STATUS_e01 = RUNNING.`
- **Why it is wrong:** After the 10-01-2026 12:16–12:35 reopen (which added the missing 10th judge suite `rl4cv-e01:qwen3.5-0.8b`, increased judge spend from `$102.55` to `$106.37`, and expanded the qualifying probe splits from 6 to 8), `README.md` and `experiments/README.md` were left at the pre-reopen `09:08` state, `README.md`'s TLDR still claims `"Nothing has been run yet."`, and `CKPT_e01.md` still has `STATUS_e01 = RUNNING` at the bottom.
- **Minimal fix:** Update `README.md` (remove `"Nothing has been run yet."` from the TLDR; update the Status table to `10-01-2026 12:35`, `10 suites (controls + 8 models + 27B control)`, and `$106.37 of $400 spent`), update `experiments/README.md` to `10-01-2026 12:35`, and update lines 51 and 138 of `CKPT_e01.md`.

---

#### F9 [MINOR] — Missing document headers in `expt_v1/DISPATCH_e01.md` and `expt_v1/cc.md`, and 1-ulp rounding discrepancy for `Qwen3-1.7B` FSC in `results.md`
- **Files:**
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/DISPATCH_e01.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/cc.md`
  - `experiments/01_small_open_models_veribench_v1_single_call_baseline/results.md`
  - `CLAUDE.md`
- **Evidence:**
  - `CLAUDE.md` (§ Repository conventions): `**File headers.** Every document starts with # Title, a **Doc link:** line and a **TLDR:**.`
  - `expt_v1/DISPATCH_e01.md` (lines 1–4): starts with `# Dispatch brief: ...` and `SNAP PRE-APPROVAL...` with no `**Doc link:**` or `**TLDR:**`.
  - `expt_v1/cc.md` (lines 1–3): has `# Experiment 01 v1 — ...` and `**TLDR:**`, but no `**Doc link:**`.
  - `results.md` (G=1 table, `Qwen3-1.7B` row): reports `FSC = 0.097*`, whereas in `expt_v1/results/fsc_qwen3-1.7b.json` the 57 task scores sum to `5.5` (`5.5 / 57 = 0.096491...`, which rounds to `0.096` at 3 decimal places).
- **Why it is wrong:** `DISPATCH_e01.md` and `cc.md` omit required header lines under `CLAUDE.md`, and `5.5 / 57` rounds to `0.096`, not `0.097`.
- **Minimal fix:** Add `**Doc link:**` and `**TLDR:**` to `expt_v1/DISPATCH_e01.md`, add `**Doc link:**` to `expt_v1/cc.md`, and update `Qwen3-1.7B` FSC in `results.md` from `0.097*` to `0.096*`.

---

VERDICT: FAIL
CRITICAL_ISSUES: 2
MAJOR_ISSUES: 5
MINOR_ISSUES: 2
SUMMARY: Experiment 01 failed to commit its evaluation and probe summary artifacts (`expt_v1/results/summaries/*` and `results_summary_*.md`) referenced by `results.md`, never judged the 11 positive G=8 probe cells or reran collection/probing for the locked `scsc` and `fsc_compiled` channels, and deviated from `PROTOCOL.md` and `CLAUDE.md` in judge repeat count (`repeat=1` vs. 3), outcome-blind 60-file audit selection, and Core 614 vs. IndustrySet 282 reporting.