# Checkpoint — experiment 12 phase A (SCSC versus hidden gold-reference tests)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v1/CKPT_e12.md>

**TLDR:** Resume record for the experiment 12 phase A worker: what is done, what runs where, and the exact next command.

**Created:** 10-09-2026 14:36 PDT
**Last updated:** 10-09-2026 15:24 PDT

- **Task:** `expt_v1/cc.md`. Brando, 10-09-2026: "Go" (measure hidden gold tests on existing outputs, zero model calls).
- **Owner:** Emily Xia (@emxia18), Ethan Li (@lethan3) advising; tracking issue: see Log. **Master:** Claude Code (Opus 5.5) on Brando's laptop, tmux `oct9-cc-rl4cv-master`, session https://claude.ai/code/session_01FgRzJQkGdRPP8sJU7XAYgv.
- **Worker:** Codex CLI 0.154.0, personal ChatGPT login, `gpt-6-astra` / high, host `skampere1`, tmux `oct9-codex-rl4cv-e12-hidden-gold-tests`; effective sandbox danger-full-access, approval never. Supersedes the Claude launch, which failed due to exhausted personal Claude credits.
- **Frozen forecast:** `expt_v1/forecasts/e12_phase_a_forecast.json`, SHA-256 `b29b71b7166b80df653220ddddec4b865a622ef9abc1fa42c6c1e559b067b0c5`, frozen 2026-10-09T21:35:33Z at git head `e851c02`.
- **State:** BLOCKED at PROTOCOL § 3 C2; renamed-symbol recovery 2/50 (4%) versus ≥95%. A1 input checks and gold reproduction PASS. Tracking issue #9; predictions untested.
- **Next command:** `git pull --ff-only origin main`, then inspect any prospective protocol clarification before changing the adapter. Current gate reproduction: `PYTHONPATH=src python3 experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v1/scripts/controls_e12.py` (cached receipts; expected exit 2). Do not lock or evaluate real candidates while C2 fails.

## Log

### 10-09-2026 — Codex launch receipt

- Status: RUNNING; experiment 12 phase A, zero model calls.
- Client: Codex CLI 0.154.0; personal ChatGPT login; host skampere1.
- Model: gpt-6-astra; reasoning effort high (user-specified launch configuration).
- Effective session permissions: sandbox danger-full-access; approval never.
- tmux session: oct9-codex-rl4cv-e12-hidden-gold-tests.
- Handoff reason: the Claude worker could not start because the personal Claude account on this host is out of usage credits.
- Authorization: SNAP PRE-APPROVAL (Brando, 2026-09-14) supplied in this session; all task-required operations approved within the zero-model-call scope.
- First useful action: appended this receipt and wrote RUNNING to /lfs/skampere1/0/brando9/rl4cv_e12/STATUS_e12.
- Next: refresh/read shared instructions and project rules, publish launch receipt, verify frozen forecast SHA-256 before analysis output, then execute expt_v1/cc.md.

- Forecast verification: PASS via `rl4cv.forecast.verify_forecast`; stored digest hashes canonical JSON without its trailing newline, explaining the distinct whole-file digest.

### 10-09-2026 14:44 PDT — mandatory input aggregation stop

- Launch landed on main: `392ed49` (verified push).
- Primary manifest: 9,856/9,856 declared cells; 9,542 hash-bound, 176 located without recorded hash, 136 ambiguous original/recovery joins, 2 missing files. All cells retained; no hashes mismatched.
- PROTOCOL § 6: 4/11 systems reproduce the published aggregate; all seven experiment-103 systems fail the three-decimal gate. Their published mean-per-file scores are not geometric means of factor means. Example Astra: published 0.522 versus 0.642476 on 855/896 measured cells.
- Missing-factor issue: 576/6,272 experiment-103 cells lack at least one factor, so all-896 geometric aggregates are unavailable without changing the frozen missingness rule.
- Evidence: `results/input_manifest.json` and `results/aggregation_preflight.json`; deterministic census, intervals/p-values not applicable. Forecast verification PASS; frozen forecast and protocol untouched.
- Runbook short-circuited at its explicit stop: no gold extraction, controls, lock, compile reproduction, hidden evaluation, secondary evaluation, or P1/P2/P3/G-A outcome. Zero model/judge calls and zero graphics-processor use.
- Host health audit completed with exit 0; tool/storage warnings only. Shared host load was approximately 700; no Lean batch launched. Existing workers preserved.
- Recovery: master must reconcile the published aggregation and missing-factor denominator prospectively, preserve original forecast, and resolve remaining joins before continuing. Recommendation in results.md; no protocol amendment applied here.
- External status: `/lfs/skampere1/0/brando9/rl4cv_e12/STATUS_e12` = `BLOCKED: PROTOCOL section 6 aggregation mismatch in 7/11 systems`. Do not mark DONE: phase A remains unmeasured.

- Deterministic verification: `make test` 188 passed / 24 skipped; experiment-local audit tests 6 passed; manifest cell uniqueness and all recorded source/script/forecast hashes PASS; `git diff --check` PASS.

- PUBLISHED `c696725` to `origin/main` (10-09-2026 14:46 PDT): input audit, manifest, results and blocked state. Push confirmed; working tree clean afterward. Direct main publication follows the explicit repository/user instructions. No pending batch job. Final worker state remains BLOCKED, with the exact reproduction command above.

### 10-09-2026 14:53 PDT — Amendment A1 resume

- Pulled `a50618e`; read PROTOCOL § 8 and verified both frozen forecast hashes. Neither forecast edited.
- Master authorizes source-specific published-score checks, measured-cohort system score, A1 missingness sensitivity and source-consistent recovery joins.
- Status RUNNING; next: amend audit without overwriting pre-A1 receipts, run all section 1 checks including 100-file compilation reproduction; then extraction, controls, lock and full evaluation.
- CPU budget: initially two concurrent Lean processes, nice priority 10; monitor shared-host load. Zero model/judge calls.

### 10-09-2026 15:04 PDT — section 1 passes; controls running

- A1 published values 11/11 reproduced; 9,856 primary cells retained; joins 9,678 hash-bound, 176 unique-path flagged, 2 absent, zero ambiguous. All 896 gold files match pinned git bytes.
- 100-file frozen compilation sample: 100/100 agreement, gate ≥99%; 600-second cap, two nice-10 single-thread Lean workers, exact frozen grading project. Completed normally (exit 0).
- Secondary snapshot: 33,984 cells / 33 systems, 28,584 factor-measured; all 5,400 missing factors explicit. No experiment-08 test candidate accessed.
- Extracted/frozen 10,429 hidden tests from 881/896 references; 15 no_tests. No real candidate hidden-test evaluation.
- Control sample: first 50 eligible tasks in sha256(rl4cv-e12-ctl: + task_id) order. Gold and globally renamed-gold copies compile in tmux window `e12-controls`; two workers, host-only output `/lfs/skampere1/0/brando9/rl4cv_e12/controls_round1`.
- Preliminary C2 mapping: 48/50 tasks have multiple compatible renamed definitions (functional/imperative twins); no tie-breaking added. Await actual C1/C2 receipts before gate verdict.
- Live control progress: `results/controls_e12_progress.json`; final receipt `results/controls_e12.json`; terminal marker `/lfs/skampere1/0/brando9/rl4cv_e12/controls_round1.exit`.

### 10-09-2026 15:13 PDT — control round 1 archived; corrective round 2

- Round 1 completed all 50 tasks: C1 570/590 tests passing (96.61%, below 98%); C2 recovered 1/47 C1-passing tasks (2.13%, below 95%). Full receipts and original extraction/selection archived with `_round1` suffixes.
- Fixed equation-style definitions without `:=`, field-projection token re-pointing/renaming, and generic structural `DecidableEq` for `Except` in the evaluator. The comparator evaluates the entire returned value, without unwrapping, hypotheses, or gold implementation code. Focused actual Lean check returned true for equal Except values and false for unequal values.
- New extraction includes previously missed statements, without dropping any old tests. Prescribed first-50 control task IDs are unchanged. No real-candidate hidden outcome exists, and protocol is not locked. Both forecasts remain untouched.
- Rerun all C1/C2 controls on the same 50 tasks in private `controls_round2`; C2 recovery additionally requires all re-pointed tests to pass (guards against a complete but wrong mapping). C3/C4 stay pending the admission gates.

- Round-2 launch verified: first four tasks 42/42 gold tests pass, renamed recovery 0/4 due to identical-type alternatives. Current extraction 10,534 tests / 882 tasks (14 no_tests), same 50 control task IDs, all previous test statements preserved. Local tests 13/13 and make test 189 passed / 24 skipped.

### 10-09-2026 15:24 PDT — corrected controls complete; C2 structural blocker

- Round 2 completed all 50 prescribed tasks, exit 2: C1 **591/591 tests (100%), 50/50 tasks pass**; C2 **2/50 tasks (4%)**, below ≥95%. All 50 renamed modules compile; 48 have ambiguous mapping. No timeouts or infrastructure failures.
- Lean itself confirmed identical types for two renamed alternatives on each of three tasks (`results/ambiguity_witnesses.json`); these three alone force ≤47/50 recovery under strict uniqueness, below the 48/50 integer threshold. Full control receipts: `results/controls_e12.json`; code and input hashes retained.
- Blocking requirement: PROTOCOL § 3 maps by a unique same-arity compatible type after names change. Functional/imperative twins have exactly the same type. No compliant parser/type-unifier fix can choose uniquely; no arbitrary tie-break or threshold relaxation was introduced. A prospective master clarification is needed to define how such alternatives are treated; original forecasts and failed receipts must stay intact.
- C3/C4 were not run after the C2 failure. This worker short-circuit is a deviation from completing all four controls, explicitly recorded in results.md; it is not a protocol-defined sequential gate. Full evaluation, Core/IndustrySet analysis, A1 sensitivity, P1/P2/P3/G-A, disagreement inspection, and final DONE remain outstanding behind the lock.
- Both frozen forecasts verified unchanged before reading results. No real model-output hidden tests run; zero experiment model/judge calls, zero GPU use, no sealed data. Input compilation sample remains 100/100; source convention check 11/11.
- Deterministic verification: make test **189 passed / 24 skipped**; experiment-local tests **13 passed** in the preceding code milestone. Direct Lean ambiguity certificate exit 0. Two nice-10 single-thread Lean workers completed and exited; no remaining batch job.
- External status: `BLOCKED: PROTOCOL section 3 C2 renamed recovery 2/50 below 95%; identical-type alternatives violate unique-match requirement`. Status deliberately not DONE; experiment outcome remains unknown.
