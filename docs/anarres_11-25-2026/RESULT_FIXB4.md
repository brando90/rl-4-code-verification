# RESULT_FIXB4: review fixes for the VeriBench study page (11-25-2026)

As of 11-25-2026. Writer: Claude Code, Claude Opus 5.5 (Vals), working for Brando Miranda.

- Branch: `pb` in `~/at3557/fixB` (fresh clone of anarres-organization/anarres, branch from `../prB-v3.bundle`).
- New commit: `d6655dc` "Tie each VeriBench statement to its row, model, and record", on top of `80c80e6`. Plain message, no amend.
- Bundle: `~/at3557/prB-v4.bundle` (`d168e2a..HEAD HEAD`). `git bundle verify` reports it is okay.
- External source: `~/at3557/rl4cv-pin` at `139e8d9b47d44626035594c19d708d6b26a856cc` (checked with `git rev-parse HEAD`). The working tree is clean.
- Review applied: `~/at3557/reviewB-astra.md` (GPT-6 Astra ultra, Codex CLI, SHIP WITH FIXES, 10 items).
- Nothing was pushed or posted.

Files changed: `experiments/mathematics/veribench/{README.md, results/records.json, scripts/audit_records.py, scripts/extract_records.py, scripts/test_audit_records.py}`. Records now hold 178 figures (up from 126) from 32 pinned source files (up from 16).

## Infrastructure change (needed by items 3, 4, 6, 8)

`extract_records.py` now reads CSV files as rows and scripts, configs, and code as text, alongside JSON. Each figure from a non-JSON file is a `DERIVED` figure with a named function, and its docstring is stored as a `derivation` field in `records.json`. Each source file gets a media type: `application/json`, `text/csv`, `text/x-python`, `text/x-shellscript`, or `application/yaml`. The audit accepts those five.

## Changes per item

1. **Row-scoped audit.** `audit_records.sections()` gives each experiment its table row plus its scope-list item. It also gives the tasks, outcomes, exposure, and namespace paragraphs their own sections. Every check now runs inside its section only.
   - Experiment 08's SCSC is checked as one model-qualified sentence: "SCSC is … for the selected 8B model against … for Base 8B, and … for the selected 14B model against … for Base 14B".
   - Experiment 25's update number is parsed from the record key (`bootstrap_points/u48/...`). The check confirms that every update-48 figure comes from the same update.
   - Scope counts are checked in their own rows: 128 probe tasks and per-family counts, 222/152/70 test tasks, 135×8 validation, 1,308 outcomes and 11 systems, 100 clusters, seeds, and samples.
   - `test_audit_records.py` now has:
     - `test_figures_are_tied_to_their_model_and_update`: the review's three counterexamples (Base 8B changed to 0.7777, selected 8B/14B pairs swapped, "At update 48" changed to "At update 49"). All three now fail the audit.
     - `test_new_claims_are_checked`: 40 mutations, at least one per new claim.
     - `test_statement_in_another_row_is_rejected`
     - `test_manifest_digest_is_checked`
   - I confirmed that each mutation fails on its intended check, not on some other one.
   - The README guarantee is narrowed. The Reproduce section lists the prose-only statements the audit does not tie to a record: the namespace suggestion in the task instruction, the `veribench@1.3` label and the Harbor candidate's status, the inspection history of the test tasks, the smooth reward's three-factor form, fp16 evaluation, the seed-2 stall and resume history, the running fourth seed, and the interpretation of experiment 09.
2. **D-013 exposure.** I used the review's wording exactly: "Experiments 01 and 05 evaluated all 896 tasks before D-013. Experiment 08 used D-013 train and validation for training and selection, then evaluated each selected trained checkpoint once on its 222 test tasks. Historical baseline and teacher outcomes on those tasks had already been inspected." Row 08's evidence cell now reads "Retrospective. Each selected trained checkpoint was evaluated once after selection." All rows keep the label "Retrospective".
   - The audit checks 896 against `e01.*.cells`, `e05.*.tasks_measured`, and `e08.split.tasks`. It checks 222 against `e08.test.n_tasks` and the split counts.
3. **Namespace evidence.**
   - New extracted file: `combined_qwen3-14b_g1__1.json` (`n_cells` 896, rewrite count 25, `work_dirs` ending in `full_nsfix`, plus the limitation and `guarded_counterfactual` strings).
   - The audit checks the 1-to-25 claim.
   - 533 is derived in code from `vbv1_split_manifest.csv` with `Path(py_relpath).stem[0].isdigit()`. The result is easy_set 41/41, realcode_set 32/32, security_set 460/460.
   - The manifest's SHA-256 is recorded, and the audit checks it equals `manifest_sha256` in `vbv1_split_summary.json` (`157ce781…`).
   - The false "no machine-written record" sentence is gone. "Diagnostic" is kept, along with the unrecompiled-counterfactual caveat.
4. **Definitions and experiment 25 harness.**
   - The new Outcomes paragraph defines cell, IC_tests, IC_proofs, FSC, SCSC, `kernel_binary`, strict success, strict pass@1, group, mixed group, and task cluster.
   - SCSC is checked against `test_eval.json` `aggregate_rule`. `kernel_binary` is checked against the `reward_kernel_binary` docstring in `src/rl4cv/rewards.py` at the pin.
   - The row 25 scope adds:
     - the harness: `train_e25.py`, vLLM, and the local frozen scorer
     - fp16, from `--dtype float16` in both launch scripts
     - "No DT (differential testing)."
     - the review's strict-criterion and three-factor sentences
     - "The evaluation leaves the vacuous-theorem count at zero, so strict success there does not establish non-vacuity." This is derived from `scored_response` in `src/rl4cv/veribench/jobs.py`, which never sets the vacuous count.
   - Row 05 now says "kernel-scored" and "FSC and SCSC were not measured". The second phrase is checked against the recorded channel names.
5. **Resampling units.**
   - Experiment 25: "The 95% cluster bootstrap intervals resample the 100 D-013 task clusters containing these 135 tasks, with the six trained models held fixed." Sources are `groups`/`tasks` in `analysis_e25.json` and `stats_e20.py` (`np.percentile(boot, [2.5, 97.5])`, "(cluster bootstrap)").
   - Experiment 19: the intervals "resample the 100 D-013 task clusters that contain the 135 validation tasks and condition on the fitted models". Sources are `G1/n_groups`, `p_test`, and the `BOOT` comment in `analyze_e19.py`.
   - Both are cross-checked against the manifest: 135 validation tasks fall in 100 clusters, and no cluster spans two splits.
   - The Outcomes paragraph distinguishes groups (eight responses) from task clusters.
6. **Experiment 19 populations.**
   - The forecast policy is `sft_4B_f1p0`, taken from `input_pins_e19.json` `paths/start_policy`. Its SHA-256 equals `analysis_e19.json` `inputs/start_policy`.
   - The second endpoint: "uses 1,308 validation outcomes from 11 systems in leave-one-system-out prediction". Sources are `E1/strict/cells` and `panel/systems`.
   - The text says intervals condition on fitted models and "the 11 folds … are not 11 independent interventions".
7. **Probe tasks per family.** The row now says "128 tasks (up to 4 per benchmark family)". The count per family is derived from `rho_h_qwen3-14b_g8_kernel_binary.json` (`{"4": 31, "3": 1, "1": 1}`). The scope says "31 families hold 4 probe tasks, one holds 3, and one holds 1". "Benchmark family" replaces "split" for this concept, and the README notes that the source calls it a split. The audit text is updated to match.
8. **Labels.** Each was checked against a pinned file before I wrote it.
   - Experiment 05: "95% Wilson intervals over tasks" (key `mixed_share_wilson95`).
   - Experiment 08:
     - "95% task bootstrap intervals" (`bootstrap95_task`, unit "task (all 8 samples carried together)")
     - one training run per size, with seed 20260830 from `configs/e08_sft_8B.yaml` and `e08_sft_14B.yaml`
     - five checkpoints per size on 135 tasks × 8 samples, from `ladder_manifest.json`
   - Experiment 25:
     - seeds 0, 1, and 2 (per-run keys)
     - sampler seed 91 (`--seed 91` in `eval_local.sh`)
     - eight samples at update 0 against 32 at update 48 (`samples_scored`)
   - "Percentage points" is used for the experiment 25 differences. AUC is spelled out as "area under the ROC curve".
9. **Version attribution.** The page now says the external experiments label the task set `veribench@1.3`, with a pinned link to experiment 25 `PROTOCOL.md#L9`.
   - Their task-pack pin `c11b99ba` comes from `vbv1_split_summary.json` `veribench_commit`, and the scorer `59059a20` from `scorer_adapter_check.json`.
   - The page distinguishes this pin from the unmerged Harbor v1.3 candidate `c9dfd8e3b535`. The audit reads that commit from `experiments/cyber/formal-verification/SOURCE_LANDSCAPE.md` and requires the two to differ.
   - It also says the two task manifests were not compared and source qualification is pending for both. I did not edit `SOURCE_LANDSCAPE.md`.
10. **Fourth seed.** "Open at the pin: [a fourth smooth-reward seed is running](…/blob/139e8d9…/experiments/25_…/expt_v1/results/full_run_at3558/results.md#L6)". The audit requires this exact pinned link, ending in `#L6`.

The README table is slimmer: Question | Result | Evidence. Scope detail moved into a "Scope and limits of each row" list under the table. A prose scan found no em dashes and no semicolons in the README.

## Commands on the final tree (in order)

| # | Command | Exit | Final line |
| --- | --- | --- | --- |
| 1 | `uvx ruff format --check` (3 changed scripts) | 0 | `3 files already formatted` |
| 2 | `uvx ruff check` (3 changed scripts) | 0 | `All checks passed!` |
| 3 | `python3 tools/check_prose_style.py` | 0 | `Prose style check passed` |
| 4 | `python3 tools/check_repo_hygiene.py` | 0 | `repository hygiene passed for 1606 files` |
| 5 | `python3 -m unittest discover -p test_audit_records.py` (in `scripts/`) | 0 | `OK` (12 tests) |
| 6 | `extract_records.py --source ~/at3557/rl4cv-pin --check` | 0 | `results/records.json matches the extraction` |
| 7 | `audit_records.py --source ~/at3557/rl4cv-pin` | 0 | `All VeriBench record checks passed` |
| 8 | `make check` | 0 | `Prose style check passed` (then `exit=0`) |
| 9 | `make study-check` | 0 | `All 34 study checks passed in 145.90s.` |
| 10 | `git diff --check d168e2a..HEAD` (after commit) | 0 | (no output) |

Rows 1 to 9 ran on the working tree just before the commit, and the commit contains exactly that tree. Row 10 ran on the commit.

Two earlier failed attempts, both my own setup errors, which I then fixed:

- My first `make check` exited 2 because I had written its log inside the repo, and hygiene flagged `.make_check.log`. The logs now sit in `.git/fixb-logs/`, outside the tree that hygiene scans.
- My first `make study-check` exited 2 with "missing study-check commands … run `make setup` first". I ran `make setup` (exit 0) and reran both targets.

Host load was about 250 on 128 CPUs during these runs.

## What I did not verify

- I did not open the VeriBench adapter source to confirm the task instruction suggests `namespace {file stem}`. That claim is quoted from the external FACTS document and marked prose-only.
- I did not compare the task manifests of `c11b99ba` and the Harbor candidate `c9dfd8e3b535`.
- Which 14B layout config actually trained the run. Every 14B config file at the pin carries seed 20260830. `sft_layout_admission_14B.json` lists `e08_sft_14B.yaml` as the admitted route, and the record uses that file.
- That fp16 evaluation holds. The launch scripts confirm fp16 training, and `eval_local.sh` takes its precision from the checkpoint config. The fp16-evaluation statement itself comes from external prose.
- That the pinned `eval_local.sh` and `stats_e20.py` are byte-identical to the copies the runs used on the host.
- That the fourth seed is still running now. The page asserts its status only at the pin.
- I reran no model generation, training, Lean scoring, FSC judging, or external analysis pipeline.
- No model-reviewer QA round ran on this change.
- Nothing was pushed, and no PR was opened or updated.
