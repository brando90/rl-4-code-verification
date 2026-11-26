# Anarres PR A (#66 formal contracts) and PR B (VeriBench results): results, 11-26-2026

As of 11-26-2026 about 8:30 AM PST (PR B updated after the third review; PR A unchanged from 11-25-2026 10:00 PM). Written by ub9sc (Brando Miranda's assistant). Google Doc with the same content: https://docs.google.com/document/d/1tLFOdKvwoqv1RLyCTBVP_KYFfOh_SOOldZsLnEURFRU/edit

## Bottom line

- PR A (issue #66, Lean-first portable formal contracts): branch `formal-portable-contracts-pr1` on brando90/anarres, head `402e26e`, base `d168e2a`. Three review passes (GPT-6 Astra ultra in Codex CLI, Claude Code, GPT-6 Astra ultra) found 3, 5 and 2 should-fix items. All are fixed, each with a test shown to fail without its fix.
- PR B (VeriBench measurements on the study page): branch `veribench-rl4cv-study-page`, head `31a9ca0`, base `d168e2a`. Three review passes (Claude Code, GPT-6 Astra ultra, GPT-6 Astra ultra) found 10, 10 and 4 items (the last: SHIP WITH FIXES, 3 should-fix and 1 nit, no wrong number among the 178 figures it checked). All are fixed. The audit is now row-scoped, model-qualified, and ties definitions, the experiment 25 model and checkpoint, the experiment 19 comparator, and the experiment 08 settings to records. Records: 203 figures from 46 pinned source files (was 178 and 32).
- Both pass every gate on a fresh clone (below). Neither PR is open on GitHub yet. The final Astra pass on PR B is done and its fixes are in.
- `make benchmark` fails the same five timing guards on this branch and on unmodified main under server load. Not a pass.

## Fresh-clone gates (skampere1, 11-25-2026 about 10 PM; clone of anarres main plus the bundle)

PR A, head `402e26e`:

| Command | Exit | Final line |
| --- | --- | --- |
| `test_formal_portable*.py` | 0 | OK (32 tests) |
| `test_vero_released_manifest_regression.py` | 0 | OK (3 tests) |
| `cargo test -p anarres-cli --locked` | 0 | 14 unit and 32 integration tests pass |
| `make check` | 0 | Prose style check passed (346 Python integration tests) |
| `make study-check` | 0 | All 32 study checks passed in 141.45s. |
| `make adapter-smoke` | 0 | fixture qualified, 4 attempts planned, deterministic, held-out task absent |
| `cargo fmt --all -- --check` | 0 | no output |
| `git diff --check d168e2a..HEAD` | 0 | no output |

PR B, head `31a9ca0` (fresh clone of the fork branch on skampere1, 11-26-2026 about 8 AM; the first run at `f1e3e1b` failed `make check` on ruff format and one over-long line, fixed in `31a9ca0`):

| Command | Exit | Final line |
| --- | --- | --- |
| `test_audit_records.py` | 0 | OK |
| `extract_records.py --source <pin> --check` | 0 | results/records.json matches the extraction |
| `audit_records.py --source <pin>` | 0 | All VeriBench record checks passed |
| `make check` | 0 | Prose style check passed |
| `make study-check` | 0 | All 34 study checks passed in 135.03s. |
| `git diff --check d168e2a..HEAD` | 0 | no output |

The pin is brando90/rl-4-code-verification at `139e8d9b47d44626035594c19d708d6b26a856cc`.

## PR B third review (11-26-2026)

The pass found 3 should-fix items and 1 nit. All four were true at the pin and are fixed in `f1e3e1b` and `31a9ca0`. The table is in `RESULT_FIXB5.md`; the review is `REVIEWB4_astra.md`.

## Harness and model per piece

- PR A authoring: Codex CLI, GPT-6 Astra ultra (Vals Codex). PR A fixes: Claude Code 2.1.318, Claude Opus 5.5 (Vals).
- PR B authoring and fixes of the first two rounds: Claude Code, Claude Opus 5.5 (Vals). PR B final fixes (`f1e3e1b`, `31a9ca0`): Claude Code, Claude Sonnet 5.5, by the assistant.
- Reviews: Codex CLI with GPT-6 Astra ultra (Vals Codex; final pass 11-25-2026 11:16 PM), and Claude Code (Opus 5.5 per the launch briefs).
- Gates: shell commands, no model.

## Files in this folder

- `PR_A_body.md`, `PR_B_body.md`: the pull request texts.
- `issues_table.md`, `MERGE_PLAN_rl4cv_into_anarres_11-25-2026.md`: who is on each code-verification issue and the four-step merge plan.
- `RESULT_FIX3.md`, `RESULT_FIXB4.md`, `RESULT_FIXB5.md`: the fix runs with mutation proof and exit codes. `REVIEW*.md` and `REVIEWB4_astra.md`: the review reports.
- `prA-v4.bundle`, `prB-v4.bundle`: git bundles (base `d168e2a`).

## Not checked

- No Lean build, real Vero checkout, prover call, Dafny, Verus or Rocq work. Nothing in PR B was re-run: the page only reads recorded results.
- `make benchmark` (timing guards fail under load on main too).
- PR B final review items: the pass reviewed `d6655dc`; its fixes in `f1e3e1b` and `31a9ca0` were checked by my own gates and mutation tests, not by a fourth Astra pass. The audit does not tie to a record: the checkpoint `step_658_float16` being the experiment 08 Qwen3-1.7B final checkpoint, the follow-up versions of experiment 08, vLLM sampling and the local scorer of experiment 25 (the page lists these).
