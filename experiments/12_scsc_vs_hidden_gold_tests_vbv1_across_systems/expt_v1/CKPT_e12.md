# Checkpoint — experiment 12 phase A (SCSC versus hidden gold-reference tests)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v1/CKPT_e12.md>

**TLDR:** Resume record for the experiment 12 phase A worker: what is done, what runs where, and the exact next command.

**Created:** 10-09-2026 14:36 PDT
**Last updated:** 10-10-2026 03:51 PDT

- **Task:** `expt_v1/cc.md`. Brando, 10-09-2026: "Go" (measure hidden gold tests on existing outputs, zero model calls).
- **Owner:** Emily Xia (@emxia18), Ethan Li (@lethan3) advising; tracking issue: see Log. **Master:** Claude Code (Opus 5.5) on Brando's laptop, tmux `oct9-cc-rl4cv-master`, session https://claude.ai/code/session_01FgRzJQkGdRPP8sJU7XAYgv.
- **Worker:** Codex CLI 0.154.0, personal ChatGPT login, `gpt-6-astra` / high, host `skampere1`, tmux `oct9-codex-rl4cv-e12-hidden-gold-tests`; effective sandbox danger-full-access, approval never. Supersedes the Claude launch, which failed due to exhausted personal Claude credits.
- **Frozen forecast:** `expt_v1/forecasts/e12_phase_a_forecast.json`, SHA-256 `b29b71b7166b80df653220ddddec4b865a622ef9abc1fa42c6c1e559b067b0c5`, frozen 2026-10-09T21:35:33Z at git head `e851c02`.
- **State:** RUNNING under Amendment A2 (`a7c2ea2`); all three forecasts verified; round-2 controls archived unchanged.
- **Next command:** `tail -n 2 /lfs/skampere1/0/brando9/rl4cv_e12/evaluation_A2.log`; inspect tmux `e12-evaluate`, child process liveness and exit marker. After complete, run analysis with the local `.venv` and one BLAS thread, then inspect disagreements and publish DONE.

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

- PUBLISHED `02b59d4` to `origin/main` (10-09-2026 15:25 PDT): corrected control receipts, direct Lean ambiguity witnesses, results and blocked continuation record. Pull-before-push and remote tracking equality verified; working tree clean after push; no control tmux window remains. Final worker state is BLOCKED, with no background experiment job.

### 10-09-2026 15:36 PDT — Amendment A2 resume

- Master reports prospective Amendment A2 at `a7c2ea2`, before protocol lock and real-candidate outcomes. Status RUNNING.
- Next: pull main, read PROTOCOL § 9, verify original/A1/A2 forecasts, archive round-2 receipts unchanged, implement A2 mapping and rerun all four controls on the same 50 tasks. Preserve all expectations; lock only after all pass.
- Shared host: retain two low-priority single-thread Lean workers; zero experiment model/judge calls.

### 10-09-2026 15:40 PDT — round-3 control design frozen before outcomes

- Same original 50 tasks; all four controls run for every task. Two nice-10 Lean workers, one Lean thread each, 600-second per-file timeout.
- A2 implementation: normalized names, unique signature, candidate-to-candidate agreement on parsed hidden argument tuples only, candidate example/theorem reference counts, and per-symbol deciding step. No expected values enter the agreement probe.
- C3 private copies omit example/theorem/lemma declarations so an intentionally changed implementation can compile. Enumerate single operator or literal edits within tested definition bodies in source order; retain the first compiling edit without reading hidden-test outcomes. Record every attempted edit and compilation.
- C4 pairs each selected task with the next task in the frozen hash order, cyclically. Wrong-task source remains unchanged.
- Round-2 receipt copied byte-for-byte to controls_e12_round2.json; old adapter/control source archived. Focused local tests: 17 passed.

### 10-09-2026 15:45 PDT — round-3 construction correction

- Attempt 3a stopped after a reproducible mutant-construction error: deleting theorem/example commands left orphan documentation comments before `end`, preventing compilation. Preserved partial receipts as `controls_e12_round3a_partial.json`, private sources/logs in `controls_round3`, implementation commit `9c8cb5b`. Only this runner and its verified process descendants were terminated.
- Fixed by masking comments in private mutant copies before deleting proof declarations. Added array literals and field suffixes to argument parsing; expected values still excluded from comparison probes. Focused tests 19/19.
- Attempt 3b reruns all four controls on every original selected task with fresh private receipts in `controls_round3b`; no task/pair/mutation-order/threshold changes. First 3a wrong-task acceptance remains recorded; it is an equality-check pair.

- A2 milestone published `9c8cb5b`. Corrected attempt 3b verified active with actual Lean outputs; first four tasks C1 42/42, C2 4/4, C3 4/4 compiling mutants killed, C4 3/4 rejected.
- Evaluation/analysis implementation prepared but not executed on candidate outcomes; fixed denominator 43,840 cells, 5,434 recorded compiling candidates before excluding no-test tasks. A2 sensitivity retains only cells whose mappings all used steps 1–2.
- Local isolated analysis environment `/lfs/skampere1/0/brando9/rl4cv_e12/.venv`: numpy 2.5.3, scipy 1.18.1, pytest 9.1.1. Focused tests 25 passed; make test 189 passed / 24 skipped.

- Live attempt-3b milestone 10-09-2026 15:57 PDT: 22/50 tasks complete; C1 224/224; C2 22/22; C3 20/21; C4 21/22. String-repeat mutant construction requires a string-literal fallback after existing edits exhaust; no mutant will be chosen using hidden results. Current full round continues unchanged before the corrective rerun. Repository tests 189 passed / 24 skipped; local tests 25 passed.

### 10-09-2026 16:16 PDT — complete round 3b archived; corrected round 4

- All 50 tasks completed all four controls: C1 591/591, C2 47/50 (fails ≥95%), C3 42/48 compiling mutants killed (rate passes, but two missing mutants fail the ≥50-task requirement), C4 49/50 (passes ≥95%). Full receipts archived unchanged as `controls_e12_round3b.json`; extraction/selection archived before corrections.
- C2 failures: heap max/min operations; counter increment/decrement operations; Floyd–Warshall graph input aliases incorrectly treated as implementation symbols. The first two are A2 step-4 choices and remain failures; no rule or threshold changed.
- Extraction correction under PROTOCOL § 2 / § 3: closed literal aliases used exclusively inside implementation-call argument positions become their original literal input data. Never expand an expected-result alias, nonliteral body, or constant directly under test. No function body or gold definition enters a bridge. All 10,534 statements are retained, including original text in changed rows; expected expressions unchanged. Exactly 23 aliases across 10 tasks / 70 tests normalized. Original 50 control task IDs unchanged; reconciliation in `fixture_input_normalization.json`.
- C3 correction: after existing numeric/operator edits exhaust without compiling, try single string-literal edits in source order. Never choose an edit based on hidden-test success. This covers string repetition and path concatenation; successful existing selections stay the same.
- Round 4 reruns C1–C4 on every original selected task, fresh private receipts in `controls_round4`, two nice-10 single-thread Lean processes, 600-second cap. No real-candidate outcome, protocol still unlocked; all three forecasts preserved. Focused tests 29 passed.

- PUBLISHED `b1bb5d3` (merge preserving concurrent `08ee026`) with literal-input normalization and string-mutation fallback; remote push verified. All three forecasts reverified unchanged. Current code checks: 189 repository tests passed / 24 skipped; 29 local tests passed.
- 10-09-2026 16:22 PDT round-4 milestone: 11/50 complete; gold 134/134, renamed 11/11, mutants 10/11, wrong-task rejection 10/11. String-repeat fallback compiles and is killed (first nine numeric/operator attempts failed compilation, tenth changed one string literal). Live counts: `results/controls_round4_status.json`; run remains active and unlocked.

- 10-09-2026 16:31 PDT midpoint: 27/50 tasks; C1 305/305, C2 26/27, C3 24/27, C4 26/27. Every completed task now has a compiling mutant. Full cohort continues; no lock or model-output hidden evaluation. Last verified publication `db78fcd`; concurrent experiment-10 changes preserved and merged repository tests passed 197 / 24 skipped.
- Third forecast canonical digest: A2 `674be36bb7a67d6a61f8cf85f2ddd2879792f604dbaa4e9919e21fdcddb3772a`; all three forecast verifications remain PASS.

### 10-09-2026 16:39 PDT — pre-lock recovery verification

- Round 4 active: 41/50 tasks; C1 479/479, C2 39/41, C3 37/41, C4 40/41. All completed tasks have compiling mutants. Two low-priority workers remain alive. Protocol not locked; no real-candidate hidden outcome.
- Evaluator now preserves logs and retries once only for a signaled infrastructure failure; timeouts and ordinary Lean errors are not retried. Interrupted trailing JSONL writes are archived before safe truncation; malformed committed records stop the run. Fatal future errors cancel queued work promptly.
- Deterministic checks: 31 experiment-local tests passed; 197 repository tests passed / 24 skipped. No control implementation or frozen input changed.
- Hourly shared-instruction refresh reached `1b35660`; read new Rule 69. Existing liveness checks include process/window existence, exit markers, progress age and log errors rather than completion-only polling.

### 10-09-2026 16:44 PDT — round 4 complete; helper-mutation fallback

- Round 4 completed C1 591/591 PASS, C2 48/50 (96%) PASS, C3 43/49 kills (87.76%) with only 49 compiling mutants FAIL, C4 49/50 (98%) PASS. Archived byte-identical receipt `controls_e12_round4.json`, SHA-256 `6b4ddbeb681672bac235c0b27997f1d39283ff73122bf1a948212385ed7c3fb3`. Exit 2.
- Floyd–Warshall now recovers all renamed tests with the original literal graph inputs preserved. Its tested functions delegate computation to helper definitions and contain no direct mutable operator/literal, so round 4 attempted no mutant. This is a construction failure, not a failed detection result.
- Added final mutation fallback after existing operator/numeric/string attempts: follow exact local qualified or same-namespace definition references from tested functions, enumerate reachable helpers in source order, and keep the first compiling single operator/literal edit. Test-only fixtures are not roots. Mutation choice never sees hidden outcomes. Prior successful choices remain unchanged.
- Round 5 is rerunning all four controls on the same 50 tasks in `controls_round5`, two nice-10 single-thread Lean processes with 600-second caps. Mapping/extraction/inputs/thresholds unchanged, forecasts verified, protocol still unlocked, zero real-candidate outcomes. Local deterministic tests: 32 passed.
- Round-5 first useful action verified: private candidate modules compiled and compiler logs written under `controls_round5/modules`; actual worker process alive. Repository verification completed: 197 passed / 24 skipped.

- 10-09-2026 16:51 PDT round-5 milestone: 10/50 tasks; gold 122/122, renamed 10/10, mutants killed 9/10, wrong-task rejection 9/10. No timeouts in completed receipts; two low-priority Lean workers active. Published `2b36cfb` after merging concurrent experiment-10 work; merged repository tests 204 passed / 24 skipped. Next: finish controls, publish complete receipts, lock and push before any real-candidate outcome.

- 10-09-2026 16:59 PDT round-5 midpoint: 26/50 tasks; gold 293/293, renamed 25/26, mutants killed 23/26, wrong-task rejection 25/26. The known heap rename failure is reproduced; all completed tasks have compiling mutants. All three forecasts reverified, and the archived round-2 receipt is byte-identical to `02b59d4`. No lock or real-candidate outcome; worker active. Last publication `8a44a67`.

### 10-09-2026 17:13 PDT — all four admission controls PASS

- Round 5 finished all original 50 tasks, exit 0: C1 591/591 (100%, ≥98%); C2 48/50 (96%, ≥95%); C3 44/50 compiling mutants detected (88%, ≥60%, all 50 constructed); C4 49/50 wrong-task pairs rejected (98%, ≥95%). All gates PASS; no timeouts.
- Only outcome change from complete round 4 is Floyd–Warshall C3: fourth attempted edit, `optAdd` addition changed to subtraction, compiled and 4/12 hidden tests failed. All prior controls/mutant choices unchanged. Same normalized graph inputs preserved.
- All six implementation hashes match the receipts; selection equals the frozen 50 tasks; all three forecast verifications PASS; real-candidate outcome file absent. Protocol remains unlocked pending publication of this milestone, then lock and push before evaluation.
- Deterministic verification remains 32 local tests and 204 repository tests passed / 24 skipped. No source change since those checks. Two control workers have exited; status remains RUNNING for the full evaluation/analysis phase.

### 10-09-2026 17:14 PDT — protocol LOCKED before real-candidate outcomes

- Complete controls published as `a1d985c`; local and remote main matched. Lock timestamp `2026-10-10T00:13:36.605087+00:00`, code commit `a1d985c82a8ad85b866f88aaea9a951394078319`. Adapter/extractor/runtime/control hashes and all exact input hashes recorded in `results/protocol_lock.json`; all three forecasts verified.
- The lock commit must be pushed before the evaluation command starts. No `cells_e12.jsonl` exists at lock. Full declared evaluation set remains 43,840 cells (9,856 primary + 33,984 secondary); each missing/noncompiling/no-test cell stays explicit. Compiling applicable candidates run with two nice-10 single-thread Lean workers; 600-second per-invocation timeout and at most one identical infrastructure retry.
- Outstanding: full candidate evaluation, paired task-bootstrap analyses (10,000 draws, seed 20261009), A1/A2 sensitivities, Core/IndustrySet descriptives, 20 manual disagreements, final publication and DONE.

### 10-09-2026 17:16 PDT — full evaluation launch verified

- Protocol lock pushed as `f64c084`, remote equality and ancestry verified before launch. tmux window `e12-evaluate`, log `/lfs/skampere1/0/brando9/rl4cv_e12/evaluation_A2.log`, exit marker alongside. All forecasts verified again before reading progress.
- First useful outputs: 38,454 immediate cell records plus 9 actual candidate receipts. Full compilation queue is 5,386 unique task/code pairs (48 of 5,434 recorded compiling cells are no-test tasks). Two active priority-10, single-thread Lean children verified; zero model/judge calls or GPU use.
- Current results remain provisional until all 43,840 cells finish. Keep every failure/missing cell, never select by outcome; preserve locked source/input hashes. Publish summaries at milestones and poll process/log/exit state with bounded sleeps. Several hours of compilation remain at this concurrency.

- 10-09-2026 17:33 PDT evaluation milestone: 100/5,386 unique jobs; 38554/43,840 cell records. 106 candidate receipts inspected for operational status: 0 timeouts, 0 infrastructure retries. Forecasts and every locked source/input hash reverified. Runner and both Lean children active; full-cohort analyses remain pending. Last published launch `58ac188`.

- 10-09-2026 17:56 PDT evaluation milestone: 250/5,386 unique jobs; 38,704/43,840 cell records. 256 candidate receipts: 0 timeouts, 0 infrastructure retries. Forecasts and every locked source/input hash reverified. Runner/two Lean children active; no fatal log error. Last publication `16c63b8`. Shared-instruction hourly refresh at 17:36 PDT was unchanged (`1b35660`). Read-only monitor: `python3 /lfs/skampere1/0/brando9/rl4cv_e12/poll_e12.py`; it checks progress age, runner/children, exit marker and fatal log errors.

- 10-09-2026 18:31 PDT evaluation milestone: 500/5,386 unique jobs; 38,954/43,840 cell records. 503 candidate receipts: 0 timeouts, 0 infrastructure retries. Forecasts and all locked source/input hashes reverified. Both priority-10 Lean workers active; no fatal log error. Last publication `53e5013`. Full-cohort analyses and manual disagreements still pending.

- 10-09-2026 19:08 PDT evaluation milestone: 750/5,386 unique jobs; 39,204/43,840 cell records. 754 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `b667176`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.

- 10-09-2026 19:47 PDT evaluation milestone: 1,000/5,386 unique jobs; 39,454/43,840 cell records. 1,002 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `4c72dfc`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.
- Shared-instruction refresh at 19:28 PDT was unchanged (`a2e2cfc`). Host check at 19:31 PDT: load averages 571.39 / 557.77 / 553.67, 7.9 TB free on the work filesystem. Continue two priority-10 single-thread Lean workers.

- 10-09-2026 20:28 PDT evaluation milestone: 1,250/5,386 unique jobs; 39,704/43,840 cell records. 1,254 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `ca0d73b`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.
- Shared-instruction refresh at 20:25 PDT was unchanged (`a2e2cfc`). Host load averages 495.55 / 503.49 / 514.81; two priority-10 single-thread Lean workers retained.

- 10-09-2026 21:06 PDT evaluation milestone: 1,500/5,386 unique jobs; 39,954/43,840 cell records. 1,506 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `be43d3a`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.

- 10-09-2026 21:43 PDT evaluation milestone: 1,750/5,386 unique jobs; 40,204/43,840 cell records. 1,751 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `8600731`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.
- Shared-instruction refresh at 21:22 PDT was unchanged (`a2e2cfc`). Host load averages 380.86 / 406.29 / 423.74; two priority-10 single-thread Lean workers retained.
- Publication synchronized concurrent upstream `41aaf6b` (experiment 13) by a conflict-free merge; merged repository verification: 227 passed / 24 skipped. Experiment-12 locked implementation and inputs unchanged.

- 10-09-2026 22:19 PDT evaluation milestone: 2,000/5,386 unique jobs; 40,454/43,840 cell records. 2,003 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `6a5d2d8`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.
- Shared-instruction refresh at 22:17 PDT was unchanged (`a2e2cfc`). Host load averages 410.41 / 406.12 / 408.44; two priority-10 single-thread Lean workers retained. Latest merged repository checks: 227 passed / 24 skipped; local experiment checks: 32 passed.
- 10-09-2026 22:23 PDT: publication synchronized concurrent upstream `7014bae` (experiment 13 declaration adapter) by a conflict-free merge; merged repository verification: 234 passed / 24 skipped. Locked experiment-12 implementation and inputs unchanged.

- 10-09-2026 22:50 PDT evaluation milestone: 2,250/5,386 unique jobs; 40,704/43,840 cell records. 2,256 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `39f41e6`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.

- 10-09-2026 23:22 PDT evaluation milestone: 2,500/5,386 unique jobs; 40,954/43,840 cell records. 2,503 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `e5c2b40`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.
- Shared-instruction refresh at 23:13 PDT was unchanged (`a2e2cfc`). Host load averages 362.53 / 371.53 / 390.32; two priority-10 single-thread Lean workers retained.
- 10-09-2026 23:27 PDT: publication synchronized concurrent upstream `ebc31b2` (experiment 13 opaque audit) by a conflict-free merge; merged repository verification: 237 passed / 24 skipped. Locked experiment-12 implementation and inputs unchanged.

- 10-10-2026 00:04 PDT evaluation milestone: 2,750/5,386 unique jobs; 41,204/43,840 cell records. 2,756 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `b7639d0`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.

- 10-10-2026 00:42 PDT evaluation milestone: 3,000/5,386 unique jobs; 41,454/43,840 cell records. 3,005 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `056ea45`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.

Report presentation prepared while evaluation continues: expose primary and secondary missing/no-test denominators beside bounds, show secondary kernel-conditioned bounds, label primary-panel mapping shares, and retain round-1 through round-5 history. `python3 -m py_compile` passed for the renderer. No locked scientific source changed. Hourly shared-instruction refresh at 00:11 PDT remained `a2e2cfc`; host load at 00:13 PDT was 328.26/329.04/335.84 with two nice-10 Lean workers.

- 10-10-2026 01:22 PDT evaluation milestone: 3,250/5,386 unique jobs; 41,704/43,840 cell records. 3,252 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `f589cc1`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.

- Hourly instruction refresh at 10-10-2026 01:08 PDT: unchanged `a2e2cfc`; shared host load 335.69/323.37/319.39. Evaluation remains two nice-10 single-thread Lean workers.

- 10-10-2026 01:44 PDT evaluation milestone: 3,500/5,386 unique jobs; 41,954/43,840 cell records. 3,506 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `c9164ce`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.

- 10-10-2026 02:03 PDT evaluation milestone: 3,750/5,386 unique jobs; 42,204/43,840 cell records. 3,758 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `3ed8eea`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.

- Hourly instruction refresh at 10-10-2026 02:03 PDT: unchanged `a2e2cfc`; shared host load 300.60/310.87/313.51. Two nice-10 single-thread Lean workers remain active.

- 10-10-2026 02:14 PDT evaluation milestone: 4,000/5,386 unique jobs; 42,454/43,840 cell records. 4,006 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `56d2f06`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.

- 10-10-2026 02:25 PDT evaluation milestone: 4,270/5,386 unique jobs; 42,724/43,840 cell records. 4,272 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `c23e8f5`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.

- 10-10-2026 02:36 PDT evaluation milestone: 4,510/5,386 unique jobs; 42,964/43,840 cell records. 4,519 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `dddd7e9`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.

- 10-10-2026 02:42 PDT evaluation milestone: 4,630/5,386 unique jobs; 43,084/43,840 cell records. 4,636 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `6b807d0`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.

- Primary-panel evaluation complete: all 9,856 declared cells retained. The unchanged evaluator is now processing the secondary panels; full-cohort analysis remains pending until all 43,840 cells are complete.

- 10-10-2026 03:05 PDT evaluation milestone: 4,750/5,386 unique jobs; 43,204/43,840 cell records. 4,753 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `c89a43e`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.

- Hourly instruction refresh at 10-10-2026 02:57 PDT: unchanged `a2e2cfc`; shared host load 313.85/322.94/319.73. Two nice-10 single-thread Lean workers remain active.

- 10-10-2026 03:51 PDT evaluation milestone: 5,000/5,386 unique jobs; 43,454/43,840 cell records. 5,003 candidate receipts: 0 timeouts, 0 infrastructure retries. All three forecasts and every locked source/input hash reverified. Process/exit/log monitor checked separately before publication. Last publication `808c738`. Continue the unchanged full cohort; analyses and manual disagreements remain pending.

- Hourly instruction refresh at 10-10-2026 03:51 PDT: unchanged `a2e2cfc`; shared host load 321.78/315.58/317.21. Two nice-10 single-thread Lean workers remain active.
