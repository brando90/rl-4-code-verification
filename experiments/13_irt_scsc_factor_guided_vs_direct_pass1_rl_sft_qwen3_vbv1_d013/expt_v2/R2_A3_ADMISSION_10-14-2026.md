# Experiment 13 v2: R2 admission under adopted Amendment A3 (G0 admitted with bounded exclusions)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/R2_A3_ADMISSION_10-14-2026.md>

**TLDR:** **G0 is ADMITTED.** The version 2 master applied A3 rule 3 to the published [diagnosis](RESULTS_R2_diagnosis.md) (`8c7976d`), and all four conditions hold:

1. All 4 unequal ordinary cells are class (c).
2. The diagnosis's private manifest already excludes 217 ordinary cells from the G0 and G1 data.
3. G0 is computed by a new wrapper around the unchanged frozen `g0.py`, at every feasible completion of the excluded cells, and is INCONCLUSIVE if the verdict flips.
4. The opaque PASS stands.

The R2 FAIL under A2 and every earlier record are unchanged.

Created: 10-14-2026 13:41 PDT; G0 procedure fixed 14:20 PDT. Author: the v2 master (Claude Code `claude-opus-5-5`, session "Oct 9: IRT for eval metric decomposition"). It applies A3 as adopted at 12:59 PDT (`57c3bb6`) and uses only published records. No per-cell value, component or G0 statistic has been read or computed.

## A3 rule 3, checked

| Condition | Evidence | Verdict |
|---|---|---|
| (i) Each of the 4 unequal cells is class (a), (b) after a verified fix, or (c) | 4/4 class (c), all validation cells, value-only. History records `compiles=false`; the pinned historical scorer now compiles them, with matching source hashes and compile-environment fingerprint `5a95…e7dd`. No class (b) defect is established, and none of the 4 is class (d) | PASS |
| (ii) Class (a), (c) and unresolved (d) cells excluded from G0/G1 | Private manifest `R2_diagnosis_10-14-2026/a3_ordinary_exclusions_private.json` (SHA-256 `c00b35ab…4128`) lists 217 of 33,456 ordinary cells: 168 typed limits (167 original plus 1 A2 retry typed as a timeout) and the 49 A3 exceptions (2 (a), 4 (c), 43 (d)). It keeps 33,239 measured-equal cells. The declared denominator is unchanged | PASS, once the owner verifies the manifest and enforces it in code |
| (iii) Listed by ID; each G0/G1 statistic reported with full-manifest worst-case bounds | Procedure below, frozen before any G0 statistic | Required at G0 and G1 |
| (iv) Opaque PASS stands | 5,319 measured, 7 typed limits, 2 unresolved (`RuntimeError`); `equality_among_measured` PASS; no test detail disclosed | PASS |

With no class (b) defect, A3 selects no fix, no R0/R1 re-verification and no re-measurement.

## G0 under A3

### What stays frozen

`reproduction/g0.py` stays byte-identical; L1v2 binds it at SHA-256 `5042467c…`.

- **Its `main` is never run.** It requires R2 status PASS, and R2's A2 status stays FAIL.
- **Its `evaluate` is reused unchanged**, so the statistic definitions, bootstrap and thresholds are exactly the frozen ones:
  - **dense-only:** strict is constant across a task's eight full-schedule samples while B varies. The threshold is at least 21/135 for 4B.
  - **AUC:** on tasks with zero 50%-rung strict successes, mean 50%-rung B predicts any full-schedule strict success. The threshold is AUC ≥ 0.65; a one-class subset is undefined and fails.
  - The 1.7B and 8B strata are secondary and do not gate.

### Completions

For each excluded cell in a G0 stratum (validation cells of `sft_<size>_f0p5` and `sft_<size>_f1p0`):

- strict is 0 or 1;
- B is exactly 1 when strict is 1 (PROTOCOL § 3), and anywhere in [0, 1] when strict is 0.

Allowing all of [0, 1], instead of {0} ∪ [0.01, 1], only widens the bounds. Every other cell keeps its measured value. Each completion yields the complete 135 × 8 arrays that `evaluate` requires.

### Verdict (A3 rule 4)

| Verdict | Condition |
|---|---|
| **PASS** | Both statistics' minima over completions clear their thresholds, with AUC defined at every completion |
| **FAIL** | Either statistic's maximum misses its threshold |
| **INCONCLUSIVE** | Anything else |

This replaces `g0.py`'s rule that a missing sample makes its stratum INCOMPLETE, and only for listed excluded cells. Any other missing cell still makes the stratum INCOMPLETE, and an INCOMPLETE 4B stratum fails G0.

### Computation

- **Dense-only** depends on each task alone, so its minimum and maximum are sums of per-task extremes.
- **AUC** uses average ranks. Given the subset and the labels, raising a positive task's score or lowering a negative task's score never lowers it. So it suffices to enumerate, for each affected task, its subset membership and label where they are free, with scores at their extremes.
- **If enumeration exceeds 2^20 configurations,** use a valid outer bound and document it. An outer bound can only turn PASS or FAIL into INCONCLUSIVE, never the reverse.

### Report

For each stratum, publish:

- the number of affected tasks;
- each statistic's minimum and maximum;
- `evaluate`'s full output, including the grouped bootstrap interval, at the minimizing and maximizing completion of each statistic.

### Freeze before computing

Before any G0 statistic is computed, push to `main`:

- **the wrapper** `reproduction/g0_a3.py`;
- **its tests**, which must:
  - match exact enumeration on synthetic arrays;
  - cover a one-class completion and the monotonicity property;
  - show that every listed ID, including the 4 public class (c) cells, is excluded;
  - show that the wrapper refuses to run on any hash mismatch;
- **the lock** `locks/G0_A3.json`, binding the SHA-256 of `g0.py`, the wrapper, its tests, the exclusion manifest and this record.

The wrapper checks these hashes before it reads any validation row.

## Transitions and G1

- **An INCONCLUSIVE gate does not advance**, just as an INCOMPLETE R2 did not (PLAN § 4).
  - G0 INCONCLUSIVE has G0 failure's effect: arms B and C stop, and Phase 2 is not run.
  - G1 INCONCLUSIVE disables arm C only.
- **G1 bounds.**
  - Phase 1 fits treat excluded cells as missing, which is PROTOCOL § 4's rule for missing measurements.
  - Each held-out G1 metric is bounded over completions of the excluded held-out outcomes.
  - The fits are not repeated for each completion, which is infeasible. This is disclosed, and it touches 217/33,456 (0.65%) of ordinary cells.
  - The owner freezes this method in a lock before any Phase 1 fit.

## Effect on later phases

- **Phase 2 is unaffected.** It scores new policy outputs with the frozen official scorer. The excluded historical cells do not enter it.
- **The forecasts stay valid.** F0v2 (0.50) and F1v2 (0.85) were frozen at L1v2, before any validation factor was computed. They remain the forecasts for G0 and G1.
- **Valkyrie is still blocked.** It has returned HTTP 403 since 10-13-2026 (rl4cv issue #68). That blocks only Phase 2's formal specification coverage (FSC) test evaluation, which waits for Vals to restore access. Strict pass@1, the primary outcome, does not need Valkyrie.
