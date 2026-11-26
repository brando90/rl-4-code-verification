SHIP WITH FIXES

# Review B (lane: claude): VeriBench measurements PR, branch `prb`, commit a450f8b

**Date:** 11-25-2026
**Reviewer:** Claude Opus 5.5 in Claude Code (Vals grant), an independent reviewer. I did not edit the repository under review.
**Clone:** `~/at3557/review-cloneB-claude` (HEAD a450f8b, on top of d168e2a). **External pin:** `~/at3557/rl4cv-pin` at 139e8d9b47d44626035594c19d708d6b26a856cc. The tree is clean, and the commit is public on GitHub (the API returns the sha, committed 2026-11-25T21:16:44Z). The repository is public under Apache-2.0.

## Summary

Every number in the new README section and in `results/records.json` matches the raw machine-written JSON at the pin. All 7 SHA-256 digests match the committed blobs (`git show HEAD:<path> | sha256sum`). `extract_records.py --source ~/at3557/rl4cv-pin --check` passes, `audit_records.py` passes, and ruff, the prose check and the hygiene check pass. No figure is fabricated or mis-rounded. The B upper bound of 40.14 is correct against the raw value 40.14487…; the external results.md says 40.15, which is its own rounding error.

The problems are scope and framing, plus one false claim about the audit itself:

- The "Reproduce" paragraph says the audit checks "every figure above". In fact most README numbers can be changed without the audit failing, and a wrong digest also passes.
- Two of the cited experiments are still open at the pin (experiment 25 has a fourth seed RUNNING, and experiment 08 has expt_v3 INCOMPLETE). The page does not say so.
- The experiment 01 probe sentence makes thin evidence look stronger than it is.
- The "applies to every row" namespace sentence is only supported for experiment 01.
- The page does not label which VeriBench partitions these outcomes have already used. That matters for a study whose stated protocol is prospective.

## Findings

1. **should-fix (highest priority).** `experiments/mathematics/veribench/README.md:26` together with `scripts/audit_records.py:63-147`.
   - **Claim:** "It confirms that every figure above matches `results/records.json` after rounding, that each record carries the digest of its source file".
   - **Evidence (mutation tests in `$TMPDIR` copies, never the repository):** the audit still passes (rc=0) after each of these README edits:
     - step 658→659
     - 222→223 held-out tasks
     - 21,504→20,000 cells
     - "all 896 tasks"→500
     - 533→100
     - "one fully compiling"→"five"
     - probe of 128→64 tasks
     - 0.20→0.30
     - 135→99 validation tasks
     - update 48→32
     - "gives PARTIAL"→"gives PASS"
     - changing the backticked pin
     - moving the experiment 25 link from the pin to `blob/main`
     - rewriting "the arms cannot be separated" as "smooth reward is clearly worse"
   - The audit also passes after replacing a file's sha256 with 64 zeros, and after deleting the `e19.auc_irt_minus_panel_strict_rate` figure.
   - **Why:** lines 97-107 compare records to hard-coded constants (658, 334, 222, 1776, 21504), not to README text. The digest check (line 41) tests only the hex format. Figures for 896, 533, 128, 135, "one file", "nine models", "two/six models" and "update 48" do not exist in `records.json` at all.
   - **What the audit does catch:** edits to the 8B/14B/Base SCSC strings, the AUC 0.862, the 0.70 gate, the experiment 05 shares, a changed record value, and an absolute path.
   - **Fix, part (a):** for every integer in prose, check the README text against the record. For example, require `f"step {g['e08.8B.first_passing_step']}" in README`, `f"On {g['e08.test.n_tasks']} held-out" in README`, `f"{sum(cells):,} cells" in README`, and `"gives " + g["e08.verdict"] in README`.
   - **Fix, part (b):** add records, with an existing machine source, for the numbers that are now prose-only:
     - e01 per-model `cells_IC_tests_x_IC_proofs_positive` from `expt_v1/results/diagnostics_10-07-2026/combined_<label>_g1__0.json` → `as_written` (Qwen3-14B = [1, …])
     - `n_cells` = 896 per label, and the label count = 9
     - probe `labels/<m>/n_rows` = 1024 (128×8) from `probe_channels_summary.json`
     - e19 `G1/n_tasks` = 135
     - e25 `tasks` = 135 and the `u48` key
     - the 533 count, if a machine file holds it. I found it only in prose (`docs/FACTS_veribench_baselines.md:34`). If no such file exists, say in the README that this number is quoted from prose.
   - **Fix, part (c):** require every `rl-4-code-verification/blob/` URL in the README to contain the pin (regex over the README).
   - **Fix, part (d):** reword line 26 to describe what is actually checked. Either "each record names a SHA-256 digest; `extract_records.py --check` recomputes it against a checkout", or add a CI-free digest check that runs when a checkout path is supplied.

2. **should-fix.** `README.md:19` (experiment 25 row) and `README.md:3` (Status).
   - **Evidence:** `experiments/25_…/expt_v1/results/full_run_at3558/results.md` (dated 11-25-2026 10:55 PST, inside the pin) says "fourth seed of arm B (AT-3558) … Status: RUNNING, no result yet". The seed-3 run was launched specifically to test whether the seed-2 stall is a reward effect.
   - The row also omits the run-level test that results.md reports (exact 3-vs-3 permutation over the six run means, p=0.50). It omits the deviation that both seed-2 lanes were resumed from update 8 after a host reboot, with the resume path not checked. It omits the evaluation size (135 validation tasks × 32 samples = 4,320 cells per run), the start checkpoint (experiment 08 v1 `step_658`, update-0 strict pass@1 4.26% = 46/1080 in `analysis_e25.json` → `runs/u0`), and the release (`veribench@1.3`, D-013 split).
   - **Fix:** in "Present boundary", add: "Open at the pin: a fourth smooth-reward seed is running. Run-level permutation p=0.50 over six runs. Both seed-2 runs resumed from update 8 after a host reboot." In "Result", add: "135 validation tasks × 32 samples per run, starting from the experiment 08 1.7B checkpoint at step 658 (4.26% at update 0)". Record `runs/u0/pass_at_1` and `tasks`.

3. **should-fix.** `README.md:17` (experiment 08 row).
   - **Evidence:** the top of `08_…/results.md` says "Matched replay versus expansion continuation: expt_v3 … INCOMPLETE: 12,960/17,280 primary validation cells". Version 2 is "PARTIAL / route blocked". Only expt_v1 is DONE. `test_eval.json` → `paired_differences/8B/industryset/SCSC_diff` = 0.0 [0.0, 0.0] and `14B/industryset` = −0.0037 [−0.0120, +0.0048]. The whole gain is on the 152-task core. Also, `selection.json` → `earliest_passing_fraction_per_size` is 8B "1.0" and 14B "0.5". results.md: "The selected fractions differ, so the two trained sizes are unmatched diagnostics." The 8B model passes only at its final step (658 of 658 updates).
   - **Fix:** name `expt_v1`. Add to the boundary: "Follow-up versions 2 (blocked) and 3 (incomplete at the pin) are not reported." Add to the result: "No gain on the 70 IndustrySet test tasks (8B difference 0.0000, 14B −0.0037 [−0.0120, 0.0048]). The selected checkpoints sit at different token fractions (8B at 1.0, its last step; 14B at 0.5), so the two sizes are not matched." Add the paired-difference and IndustrySet figures to `records.json`.

4. **should-fix.** `README.md:15` (experiment 01 probe sentence).
   - **Evidence:** `PROTOCOL.md` puts the probe at 4 tasks per split (128 tasks in total; `probe_channels_summary.json` → `labels/*/n_rows` = 1024). A per-split share of 0.25 is 1 mixed task out of 4, and 0.333 is 1 out of 3. The overall shares from the results.md probe table (lines 286 and 316) are Qwen3-14B 0.0469 (6/128) and Qwen3.5-9B 0.0312 (4/128). Both are below the protocol's own 0.05 "fail" level, which the gate applies per model to the overall probe share. Only 8 of the 9 models were probed: Qwen3.6-27B, the route control, was not.
   - **Fix:** "In an eight-sample probe of 128 tasks (4 per split), run on 8 of the 9 models, Qwen3-14B and Qwen3.5-9B had mixed groups on 6 and 4 of 128 tasks (overall share 0.047 and 0.031). Each cleared the locked 0.20 per-split gate with one mixed task in a 3- or 4-task split, so Gate G1 is PASS. The other six had none." Record `gate_g1/locked_channel` and the overall shares, or the per-split counts.
   - Also: "one fully compiling, fully proved file" is correct. The diagnostic JSON has `compiles` = 5 and `cells_IC_tests_x_IC_proofs_positive` = 1 for Qwen3-14B. Say that the other 8 models had 0/896, and give the cell's SCSC (0.888) and the model's mean SCSC over 896 tasks (0.00099).

5. **should-fix.** `README.md:22` ("One limit applies to every row").
   - **Evidence:** the namespace diagnostic exists only for experiment 01 (`01_…/results.md` "Zero-score diagnostic" and `docs/FACTS_veribench_baselines.md:31-37`). A grep for "namespace" in 08/19/25 PROTOCOL.md and results.md finds nothing. Experiment 25 reaches a strict pass@1 of about 50%, so a claim that the hint limits that row is untested. The FACTS file also notes that the comparison is confounded and "does not measure the namespace hint's causal effect".
   - **Fix:** "The VeriBench task instruction suggests a namespace that is not a valid Lean identifier for 533 of the 896 tasks. In experiment 01, a namespace rewrite raised Qwen3-14B from 1 to 25 tasks with positive test and proof factors (a diagnostic, not a score). Its effect on the trained models in the other rows was not measured." This also removes the semicolon (writing rule 6).

6. **should-fix.** `README.md:18` (experiment 19 row).
   - **Evidence:** `analysis_e19.json` → `G1/auc_contrasts/q8_irt_2pl_minus_panel_strict_rate` = +0.011 [−0.004, +0.027], p=0.15. "Does no better" overstates this: the point estimate is higher, and the difference is simply not resolved.
   - The features-only AUC (0.954) is labeled "secondary, exploratory" in results.md. The page drops that label, which writing rule 7 requires.
   - The other primary endpoint (P2, E1-strict) is **FALSE** (M1 − M2 = +0.0015 [−0.0059, +0.0086]) and is omitted.
   - The starting policy is `sft_4B_f1p0`, an experiment 08 4B checkpoint that passed no validation rung. The 0.70 gate was written for 539 training tasks and is applied here to 135 validation tasks with 32 mixed.
   - **Fix:** "AUC 0.862 [0.792, 0.925] on 135 validation tasks (32 with mixed groups), above the 0.70 gate borrowed from experiment 13. Its margin over the panel pass rate is +0.011 [−0.004, +0.027]. In an exploratory comparison, task features alone reach 0.954. The second primary endpoint, whether IRT adds held-out information about strict success, was not supported." In the boundary, name the starting policy.

7. **should-fix.** `README.md:16` (experiment 05 row).
   - The row opens with "Across 21,504 cells", but the reported share is over 896 tasks per model, each task being one group of 8. Writing rule 8 asks for the independent unit to be named.
   - The channel (`kernel_binary`), the 0.05 decision threshold and the Wilson intervals (in records, not in the README) are missing.
   - **Fix:** "All 21,504 cells were scored. The `kernel_binary` mixed-group share over 896 tasks per model is 0.000 [0.000, 0.004] for 1.7B and 8B and 0.006 [0.002, 0.013] for 4B, against a 0.05 threshold." Note: `analysis_e05.json` still says `cells_compiling` = 34 for 1.7B, while results.md corrected that count to 2 on 10-09-2026. The page does not cite this field, so no change is needed here, but do not add it to the records.

8. **should-fix.** Scientific integrity and partitions: `README.md:11-22` against `README.md:51` ("Freeze … a held-out VeriBench evaluation split") and `experiments/mathematics/README.md:16` ("measurements must be collected … before downstream training outcomes are inspected").
   - **Evidence:** experiment 08 opened the D-013 test split (222 tasks) once. Experiments 19 and 25 read validation outcomes (135 tasks). `docs/DATASETS.md:22` in the external repository has the split manifest. AGENTS.md requires that "Development and prospective partitions must be explicit" and that "Exploratory results must not be relabeled as prospective".
   - **Fix:** add one sentence: "These measurements are retrospective development evidence. They used the D-013 train and validation splits, and experiment 08 evaluated the D-013 test split once. The prospective study must name which of these partitions it holds out." Also label each row's evidence tier (writing rule 7).

9. **should-fix.** Overlap and contradiction with `experiments/cyber/formal-verification/`.
   - **Evidence:** `SOURCE_LANDSCAPE.md:14-19` says the 896-task v1.3 candidate "still requires release and evaluator qualification". `source-qualification/README.md:173-176` says that VeriBench "comes from the research group of this repository's owner, so any qualification of it needs an independent auditor". The new page treats "VeriBench V1, 896 tasks" as settled and imports results from the owner's group without mentioning either point. The page uses "VeriBench V1", while the formal-verification page and experiment 25 use "v1.3" / `veribench@1.3` (writing rule 1, one term per concept).
   - The new "Relation" paragraph does not contradict anything, but it should carry this status.
   - **Fix:** add: "Anarres has not qualified VeriBench as a source (see [source qualification](../../cyber/formal-verification/source-qualification/README.md)). These results come from the benchmark authors' group and await independent qualification." Name the release once (`veribench@1.3`, task pack `c11b99ba`, scorer `59059a20`) and use one name throughout.

10. **should-fix.** `results/records.json` against AGENTS.md "External artifacts".
    - AGENTS.md asks that an artifact reference carry a URI, SHA-256, media type, size, license and producing run. Each `files[]` entry has only a path and a sha256.
    - **Fix:** add `size`, `media_type: application/json`, `license: Apache-2.0` (top level), and the producing experiment/run (for example `experiment: "25", run: "AT-2925"`) to each file entry. Emit them from `extract_records.py`, and have the audit require them.

11. **nit.** `scripts/extract_records.py:207-215` checks HEAD but not that the tree is clean.
    - `--check` would catch a dirty file through its digest. Without `--check`, however, the script silently writes digests of modified files.
    - **Fix:** fail if `git -C source status --porcelain -- <paths>` is non-empty, or read the bytes with `git show PIN:<path>` instead of from the working tree.

12. **nit.** `scripts/audit_records.py:16-18` reads its files at import time, and the audit has no unit test for its own failure modes.
    - **Fix:** move the reads into `main()`. Add a `test_audit_records.py` that mutates a temporary copy (for example the README step number or a digest) and asserts failure. Register it in `tools/check_study_reproduction.py` so that the check's teeth are themselves checked. CONTRIBUTING.md says study-check "fails when a reproducer changes tracked artifacts"; a negative test makes that claim testable for this entry.

13. **nit.** Writing standard in `README.md:13-22`.
    - Internal labels are not defined (rule 3): "Present boundary" (use "Scope and limits"), `kernel_binary`, "mixed-group share" (define it once: the fraction of tasks whose 8 samples do not all receive the same reward), "learnable prompts", "rung", "frozen validation rule", and GRPO and IRT (expand once).
    - The page uses two names for one score, SCSC and SCS4CV (rule 1). Keep SCSC and drop the alias sentence, or move it to a footnote.
    - "It measures a forecast, not training." and "not 896" are contrast-by-negation sentences (rule 4). The prose tool does not flag them.
    - "reinforcement-learning pilot measurements" in the Status line: experiment 25 is the locked full run (stage 4), not a pilot. Only experiment 09 was a pilot.

14. **nit (PR hygiene).**
    - The commit message gives no PR body and leaves the `.github/PULL_REQUEST_TEMPLATE.md` boxes unanswered. The PR should state:
      - `make check` status. It was not run here because of CPU load. The PR should say whether the author ran it.
      - Scientific impact: "adds retrospective external measurements; no protocol or frozen artifact changes".
      - No large artifacts: `records.json` is 415 lines, which is fine.
    - The README links use the commit hash, which is good.

## Would a maintainer accept this as a first integration PR?

The shape is right for Anarres:

- experiment-local files only
- a compact record file with digests
- a reproducer pinned to an immutable commit
- an entry in `study-check`
- no external code, checkpoints or machine paths copied in

A maintainer would likely also ask for:

- findings 1–3 and 8–9 before merge
- a one-line `CODEOWNERS` or reviewer note naming an independent research maintainer (the results come from the owner's group, per finding 9)
- an `experiments/mathematics/veribench/results/README.md` or dataset-card-style note describing `records.json` fields
- a decision on whether `extract_records.py --check` should run in some extended CI lane that fetches the pin (`make study-check-extended`), so the digests are verified somewhere and not only by hand
- a plan for updating the pin when experiment 25 seed 3 finishes. State that the page reflects the pin and will be refreshed by a new commit, not edited in place.

## What I ran

- Read every new README claim against:
  - `probe_channels_summary.json`, `diagnostics_10-07-2026/combined_qwen3-14b_g1__0.json`, the PROTOCOL.md and results.md (01)
  - `analysis_e05.json` and results.md (05)
  - `selection.json`, `test_eval.json` and results.md (08)
  - `terminal_receipt.json` and results.md (09)
  - `analysis_e19.json` and results.md (19)
  - `full_run_at2925/analysis_e25.json`, `full_run_at3558/results.md`, `stall_check_out.txt`, PROTOCOL.md and results.md (25)
  - `docs/FACTS_veribench_baselines.md` and `docs/DATASETS.md`
- Ran `audit_records.py` (pass), `extract_records.py --source ~/at3557/rl4cv-pin --check` (pass), and the digest comparison against git blobs (7/7 match).
- Ran 23 mutation tests in `$TMPDIR` copies, with results as listed in finding 1.
- Ran ruff 0.13.2 `format --check` and `check` on the three changed Python files (pass), and `tools/check_prose_style.py` and `tools/check_repo_hygiene.py` in a disposable clone (pass, 1,605 files).

## What I did not check

- Full `make check` and `make study-check`: the load average was about 420 on this node, so I read `tools/check_study_reproduction.py` and the Makefile instead. The new entry is a plain `python_check` like its neighbors.
- The repository-pinned ruff version (I used the local ruff 0.13.2).
- Whether the raw external numbers themselves are correct, for example rerunning the experiment 25 bootstrap or the experiment 08 analyzer. I checked only that the page and the records match the machine-written files.
- Whether experiment 25's update-0 value (46/1080) satisfies its protocol's "must reproduce 53/1080" precondition. This is an external-repository issue that the README does not cite. A maintainer may want it resolved before quoting experiment 25.
- Rendering of the GitHub table, and links other than the experiment 19 results link and the FACTS link (both returned 200).
- Experiments not cited on the page (02–04, 06–07, 10–24).
