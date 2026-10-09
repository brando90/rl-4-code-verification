# Checkpoint — experiment 12 phase A (SCSC versus hidden gold-reference tests)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v1/CKPT_e12.md>

**TLDR:** Resume record for the experiment 12 phase A worker: what is done, what runs where, and the exact next command.

**Created:** 10-09-2026 14:36 PDT
**Last updated:** 10-09-2026 14:45 PDT

- **Task:** `expt_v1/cc.md`. Brando, 10-09-2026: "Go" (measure hidden gold tests on existing outputs, zero model calls).
- **Owner:** Emily Xia (@emxia18), Ethan Li (@lethan3) advising; tracking issue: see Log. **Master:** Claude Code (Opus 5.5) on Brando's laptop, tmux `oct9-cc-rl4cv-master`, session https://claude.ai/code/session_01FgRzJQkGdRPP8sJU7XAYgv.
- **Worker:** Codex CLI 0.154.0, personal ChatGPT login, `gpt-6-astra` / high, host `skampere1`, tmux `oct9-codex-rl4cv-e12-hidden-gold-tests`; effective sandbox danger-full-access, approval never. Supersedes the Claude launch, which failed due to exhausted personal Claude credits.
- **Frozen forecast:** `expt_v1/forecasts/e12_phase_a_forecast.json`, SHA-256 `b29b71b7166b80df653220ddddec4b865a622ef9abc1fa42c6c1e559b067b0c5`, frozen 2026-10-09T21:35:33Z at git head `e851c02`.
- **State:** BLOCKED at PROTOCOL § 6; tracking issue #9. No experiment process remains running.
- **Next command (audit only):** `PYTHONPATH=src python3 experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v1/scripts/audit_inputs_e12.py` (expected exit 2). Evaluation cannot resume until the master records a prospective aggregation/denominator resolution.

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
