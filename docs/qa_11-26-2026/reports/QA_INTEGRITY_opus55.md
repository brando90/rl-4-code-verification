# QA integrity review of rl-4-code-verification main at a47acee9

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/docs/qa_11-26-2026/reports/QA_INTEGRITY_opus55.md

**TLDR:** All 22 non-main branches are fully contained in main and the D-112 merges are real and lossless. Six index rows contradict their own experiment files and two superseded branches hold the only copies of six files. One repository-settings finding was delivered to the owner directly and is withheld from this file.

Reviewer: Claude Opus 5.5, read-only, 11-26-2026. Snapshot `/home/claude/qa_snapshot` (main a47acee9) is a shallow clone with depth 1, so all history checks used the read-only GitHub REST API. Scratch outputs are in `/home/claude/qa_work/integrity/`.

## Findings by severity

### Critical

**C1. One repository-settings finding.** Details are withheld from this file and were delivered to the owner directly; the fix is an owner-only decision (see D-113 and `NEXT_STEPS_11-26-2026.md`, section 5).

### High

**H1. `docs/anarres_11-25-2026/` puts another project's material and binaries on main, and its documents break the header rule.**
- Commits `bcf1ea68` and `1c08c172` add `prA-v4.bundle` (45,847 B) and `prB-v4.bundle` (44,525 B). These are git bundles with HEADs `402e26e5…` and `d6655dc5…`.
- The folder also holds 14 review and PR-body documents about the external "Anarres" repository.
- I could not check Anarres's visibility because this session has no access to it.
- None of the 14 documents has a `**Doc link:**` line or a `**TLDR:**`, and 8 do not start with `# Title` (list in R6).
- **Fix:** move the folder to private storage or the Anarres repository, then `git rm -r docs/anarres_11-25-2026` (the owner decides). If it stays, add the three header lines to each `.md` file.

**H2. Six index rows contradict their own experiment files.** The corrected cell text for each row follows.

- **Row 25** (`experiments/README.md:41`) says "(QA 11-25-2026: protocol locked 11-09-2026, final three-seed results 11-11-2026) PROTOCOL not locked; stage 0 … running", and its next action is "Lock PROTOCOL…".
  - Evidence: `25_smooth_vs_strict…/README.md:30` (PROTOCOL locked 11-09-2026, forecast frozen) and `README.md:5` (third seed done 11-11-2026).
  - Corrected status: "DONE 11-11-2026: protocol locked 11-09-2026; over three seeds per arm, update-48 B minus A is −16.25 points [−19.17, −13.28], so the decision rule is not met (see results (…/results.md))."
  - Corrected next action: "None; result final."
- **Row 18** (`:37`) says "…package built on branch `ub9/e18a-…`; no GPU job yet (QA 11-25-2026: stale; 114 18a cells and 32 18b runs have completed)", and its next action is "Smoke, then the full FarmShare chain (AT-597)". It also omits 18c.
  - Evidence: `18_…/results.md:5` (96 environment + 18 target cells complete), `18_…/README.md:5`, and `18_…/expt_18c/results_18c.md:6` (all 48 runs finished).
  - Corrected status: "18a COMPLETE (96 environment + 18 target cells); 18b COMPLETE (32 runs); 18c COMPLETE 11-26-2026 (48 token-matched runs; the law ranks environments better than chance but its top pick is poor). See results.md, expt_18b/results_18b.md, expt_18c/results_18c.md."
  - Corrected next action: "None queued."
  - The experiment's own `README.md:47-49` Status section still says "Next: AT-597 runs the smoke". Update it the same way.
- **Row 08** (`:26`) says "expt_v3 RECOVERING (checked 10-19-2026…)", and its next action is "Leave the waiter in place…". This conflicts with the section at `:49`, with `08_…/expt_v3/closing_note_11-25-2026.md:7` and `expt_v3/results.md:9` (INCOMPLETE), and with issue #7 (closed, not_planned).
  - Corrected status: "expt_v3 INCOMPLETE, closed 11-25-2026: 12,960/17,280 validation cells measured; the four 14B rungs (4,320 cells) were not measured by the 11-01-2026 deadline and continue in issue #34 (closing note (…/expt_v3/closing_note_11-25-2026.md))."
  - Corrected next action: "v3 none; 14B rungs tracked in #34."
  - "v6 RUNNING (10-19-2026)" matches `expt_v6/results.md:5`, but that file was last updated 10-19-2026. It is stale; ask the owner for the current state.
- **Row 13** (`:31`) says "v3 PILOT_RUNNING (checked 10-19-2026…)", with next action "Leave resume session running".
  - This matches `expt_v3/results.md:7` but conflicts with `expt_v3/CKPT_factored_pilot.md:5` (INCOMPLETE).
  - The row also ignores `expt_v4/`, whose amendments are dated 10-20-2026.
  - The experiment `README.md:15` still reports only v2 (10-16-2026).
  - Corrected status: "v3 pilot INCOMPLETE (CKPT_factored_pilot.md); v4 (dispatch redesign, amendments 10-20-2026) — status: see expt_v4/README.md." The owner should supply the current v4 state; I did not verify it.
- **Row 20** (`:39`) has the next action "Review PR #20". `gh api …/pulls/20` shows PR #20 closed and merged.
  - Corrected next action: "PR #20 merged; IRT comparison blocked until the trainer passes the 1% log-probability gate (fixed route: experiments 21–25)."
- **Row 25b** (`:42`) has the next action "Night 6 CPU toy; Lean pilot after trainer wiring". Evidence that Night 6 is done: `25_checkpoint_reuse…/expt_v6/results.md`, `OUTCOME.md:1-3` (label dated 10-30-2026) and `stage2a/`.
  - Corrected status addition: "Night 6 done (492 runs); 10-30-2026 outcome: toy supports ADOPT for dense-checkpoint curves, P2 weak, rolling ρ/H not supported; formal label pending the Lean pilot (Stage 2b, not run) — OUTCOME.md."
  - Corrected next action: "Lean pilot (Stage 2b)."
- **Rows 06, 16, 16 (toy) and 17** are consistent with their READMEs and results files. Spot-checked numbers: 0/16, 0/8 and 0/56; 0.287 and 4.423; 0.96 [0.56, 1.73]; RMSE 1.372.

### Medium

**M1. Two superseded branches hold the only copies of six files.** For each branch I took the recording merge's first parent P, compared P with the branch tip T, and looked up each changed file on main.

| Branch (recorded by) | P…T | Identical | Evolved | Absent on main |
|---|---|---|---|---|
| `claude/admiring-heisenberg-eok3j4` (eeea5b1b, PR #24) | 43116095…b5e31259 | 0 | 2 | 4 |
| `ub9/valkyrie-hosted-migration` (43116095, PR #24) | 1767c996…e9d69a38 | 0 | 6 | 2 |
| `ub9/e22-e25-chain` (644e026d, PR #29; tip c5f0c5be) | 81cada99…c5f0c5be | 48 | 4 | 0 |

Absent files:
- `experiments/01_predict_rl_env_utility_veribench_qwen35_snap/` files: `README.md` (23,953 B), `config.yaml` (5,586 B), `scripts/cc_prompt_launch_phase0_on_snap.md` (5,460 B) and `scripts/cc_runbook_phase0_coverage_census.md` (7,956 B).
  - The claimed successors are experiments 02 and 03, with old-to-new numbering in `experiments/README.md:51-62`.
  - Main's experiment 01 is a different experiment (`01_small_open_models…`).
  - No verbatim carryover was found.
- `src/rl4cv/valkyrie_hosted.py` (12,256 B) and `tests/test_valkyrie_hosted.py` (14,714 B).
  - The successors exist on main: `src/rl4cv/valkyrie_transport.py`, `tests/test_valkyrie_transport.py` and `docs/valkyrie_hosted_transport.md`.

Evolved files lose some branch lines on main, so the "superseded" claims are about design rather than verbatim content:
- `judge_rl4cv_e08v2.py` is missing 49 of 587 branch lines.
- `deploy_service_e08v2.py` is missing 39 of 254.
- `argon_qa.py` is missing 24 of 365.
- `judge_service_e09.py` is missing 22 of 74.

The e22-e25 evolved files are only the four READMEs, each missing 1–3 lines of QA wording, which is expected.

**Fix:** add a line to D-112: "branches `claude/admiring-heisenberg-eok3j4` and `ub9/valkyrie-hosted-migration` hold the only copies of the files listed above. Tag them (`archive/…`) before any deletion."

**M2. Three folders share number 25, and one of them is not indexed.**
- The folders are `25_checkpoint_reuse_for_rho_h_law`, `25_exp20_smoke_8update_fp16_real_lean_reward_qwen3_1p7b_sft` and `25_smooth_vs_strict_reward_grpo_qwen3_1p7b_sft_vbv1_3_d013`.
- `experiments/README.md` never links `25_exp20_smoke…` (grep count 0). The row "21 to 24" at `:43` links nothing.
- **Fix:** add a row "25 (fp16 real-Lean smoke) | 25_exp20_smoke… (…/README.md) | 8-update fp16 smoke with real Lean reward | job 49639114 results | used by exp 25", and give folders 21–24 their own links.

### Low

- **L1.** `experiments/README.md:49` says "The historical status rows below are retained", but the rows are above it (lines 24–43). Change "below" to "above".
- **L2.** `docs/qa_11-25-2026/results.md:64` reports "1,399 passed, 7 failed, 65 skipped, 1 error (24 min)". The committed log `make_test_at3598_11-25-2026.log` (last line) and `at3598_issues_11-25-2026.md:38` both say "7 failed, 1,440 passed, 48 skipped (726 s)". Either cite the second run's log or correct the numbers to match.
- **L3.** Merge `06389efc` (e13v3) changes 0 files relative to its first parent, because all 7 branch files were already on main with identical blobs. D-112's wording "merged … two with unmerged commits" is accurate about commits. Optional: add "(content was already on main)".
- **L4.** Stale TLDRs:
  - `experiments/16_toy_env_generation…/README.md:114` (TLDR-end) still describes only Night 1.
  - `experiments/13_…/README.md:15` reports only v2.

## Checks that passed

1. **Branches.** `gh api …/branches --paginate` lists 23 branches: main plus 22 others. That matches D-112's 22, with none added or missing. `compare/main...<b>` gives `behind`, `ahead_by=0` for all 22 (`/home/claude/qa_work/integrity/compare.tsv`).
2. **D-112 merges.** `06389efc` has parents `ef6c838a`,`9b144949` and `0656edc3` has parents `06389efc`,`34489cfc`. Both are merges whose second parents are the stated branch tips.
   - e13v3: 7 of 7 branch files are identical on main.
   - wip: 14 of 15 are identical. The other one, `expt_v4/validation/results.md`, differs only by an added QA status note. Nothing was dropped.
3. **No open PRs.** `gh api …/pulls?state=open` returns 0. Open issues are #3, #5, #6 and #34, consistent with `experiments/README.md:49`.
4. **Links.** `python3 -I scripts/links.py`: 126 relative links in README.md, CLAUDE.md, AGENTS.md, experiments/README.md, docs/PLAN.md, docs/DECISIONS.md and docs/qa_11-25-2026/*.md. 0 broken. Anchors not checked; `docs/qa_11-25-2026/reports/` not included.
5. **Frozen files.** None of the 207 file changes in the 25 newest commits touches a `PROTOCOL.md` or forecast file. 199 are additions and 8 are modifications, all to results, notes or code.
6. **README dates.** The READMEs touched in the 25 newest commits contain no ISO or month-name dates.
7. **Secrets.** A case-sensitive token-pattern scan of the snapshot found no hits.

## R6 detail: header-rule violations in the 25 newest commits

The following files lack the Doc link line and TLDR, plus the leading title where marked:
- Title also missing: `docs/anarres_11-25-2026/PR_A_body.md`, `PR_B_body.md`, `RESULT_FIX3.md`, `REVIEW1.md`, `REVIEW3_astra.md`, `REVIEWB4_astra.md`, `REVIEWB_astra.md`, `REVIEWB_claude.md`.
- Title present: `MERGE_PLAN_rl4cv_into_anarres_11-25-2026.md`, `RESULT_FIXB4.md`, `RESULT_FIXB5.md`, `REVIEW2.md`, `issues_table.md`, `results.md`.
- `experiments/08_…/expt_v28_llama32_family/gemma_smoke_oom_fix_11-26-2026.md` (title present).
- `experiments/18_…/expt_18c/results/perrun_18c.md` and `results_18c_table.md` (title also missing; these may be generated tables).

Binary files committed: `docs/anarres_11-25-2026/prA-v4.bundle` and `prB-v4.bundle`. Older binaries elsewhere include `.pt` checkpoints in `16_toy…/expt_v5` and `.tar.gz` curricula in 08 v5/v6, but those fall outside the 25-commit window.

## Not done

- I could not check the Anarres repository's visibility (no access).
- I did not inspect the contents of exp 12's "hidden tests" manifests.
- I did not check link anchors.
