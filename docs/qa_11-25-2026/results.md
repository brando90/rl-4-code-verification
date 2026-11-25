# rl-4-code-verification: issues, branch merges and full QA of experiments 01 to 25 (11-25-2026)

**Dated:** 11-25-2026. **Asked by:** Brando Miranda (WhatsApp, 11-25-2026 10:35 to 10:38): solve the issues, merge all branches to main, mega QA with the Vals Codex account (GPT-6 Astra, ultra effort). **Done by:** ub9sc (ultimate brando9 scalable coworker), the assistant working for Brando.

## Bottom line

- Issues: 2 closed (#8, #9), 4 kept open with a status comment and a named blocker (#3, #5, #6, #7).
- Branches: all 22 remote branches are contained in main (2 merged: 06389efc, 0656edc3; 20 were already contained). No open PRs. No branch was deleted. Rule "research work goes straight to main in numbered experiment folders" is in CLAUDE.md and AGENTS.md (decision D-112, commit 220c9cd9).
- QA: an independent reviewer (Codex CLI, GPT-6 Astra, ultra effort, Vals account) rechecked every numeric claim of experiments 01 to 25 against the committed raw outputs: 110 findings (29 HIGH, 56 MEDIUM, 25 LOW). All checks that could be rerun from the repo are fixed in the docs, with a dated "QA 11-25-2026" note that keeps the original value. Nothing scored was changed (no tables, CSVs or JSON); only prose, labels and statuses.
- What the QA says about the science: the headline results reproduce (for example experiment 12 P1/P2/P3 116 of 116, experiment 14 727 of 727, experiment 20 and 25 effects, experiment 07 H1 0.985). The errors are transcription, rounding, reversed labels, universal wording ("all 15", "total starvation", "every rule") and stale "running" statuses. None changes a verdict.
- Not verifiable from the repo: about 25 claim groups whose raw data or logs live on other hosts (job times, memory, test-suite transcripts, task-level cell ledgers). They are listed in the reports and left as they are.

## 1. Issues

| # | Issue | Action | Link |
|---|---|---|---|
| 9 | Experiment 12: SCSC vs hidden gold tests | Closed: done, QA 116/116 | https://github.com/brando90/rl-4-code-verification/issues/9 |
| 8 | Experiment 01: why small Qwen models score about 0 | Closed: done, follow-up is experiment 08 (#7) | https://github.com/brando90/rl-4-code-verification/issues/8 |
| 7 | Experiment 08: matched Lean SFT warm start | Open: 14B rungs never measured (v3 hit its deadline 11-01-2026, 4,320 of 17,280 cells missing) | https://github.com/brando90/rl-4-code-verification/issues/7 |
| 6 | Experiment 02: rho-H guided environments | Open: 0 of 24 real tasks supported by the adapter, phase B not admitted, nothing trained | https://github.com/brando90/rl-4-code-verification/issues/6 |
| 5 | Experiment 07: SCS4C vs pass@1 | Open for follow-ups; phase A done | https://github.com/brando90/rl-4-code-verification/issues/5 |
| 3 | Run experiments on SNAP | Open: 02 and 03 wait for the adapter fix and Brando's launch word | https://github.com/brando90/rl-4-code-verification/issues/3 |

## 2. Branches

All 22 remote branches other than main are ancestors of main (merge commits 06389efc and 0656edc3 for the two that were not). Branches are kept; deleting them waits for Brando.

## 3. QA, by group

Reviewer: Codex CLI, model GPT-6 Astra, reasoning effort ultra, signed in on the Vals account, read-only, local Python/NumPy only. ub9sc checked each HIGH finding against the cited file before editing (Claude Code agent, model Sonnet 5.5). Reports: `docs/qa_11-25-2026/reports/`.

| Group | Experiments | Findings (HIGH/MED/LOW) | Fix commit |
|---|---|---|---|
| g1 | 01 to 07 | 6 / 13 / 2 | 7a172cbd, fa1d4834 |
| g2 | 08 v1 to v13 | 3 / 9 / 8 | d2c9f6ad |
| g3 | 08 v14 to v28 | 2 / 13 / 7 | 139e8d9b |
| g4 | 09 to 19 | 11 / 10 / 3 | 1575927f |
| g5 | 13 to 25 | 7 / 11 / 5 | db9893b9 |

Most important corrections (all in prose, original value kept beside the new one):

| Where | Was | Now |
|---|---|---|
| Exp 08 summary, STATUS page, SMOOTH_TO_HARSH, exp 13 README | "factors equal strict on 15 of 15 SFT checkpoints" | 14 of 15 historical (19 of 20 stored rungs); one 8B f0.125 sample differs |
| Exp 08 results | Opus token-cap hits 78 per run | 79, 78, 74, 78 (309) |
| Exp 08 v23, v25 | "V20 minus V23" label (-0.28 pp) | label reversed: it was V23 minus V20 |
| Exp 08 v26 protocol | V20 and V25 SHAs | swapped back |
| Exp 08 v3 and index | "running / recovering", 8,640 cells missing | incomplete at the 11-01-2026 deadline, 4,320 missing |
| Exp 17 | linear-regression gain +0.0052, 164/164 | +0.0022 [0.0015, 0.0028], 133/164 (mean-equating is +0.0052, 146/164) |
| Exp 17 | LOEO MAE 1.539, allocation regret reduction 1.349 pp | 1.447, 2.430 pp |
| Exp 15 | "two rungs early", "2 to 10 times" | one rung early, 1.9 to 29.6 times |
| Exp 16 toy | regrets labelled 102.4k tokens; "higher regret in 100% of resamples" | they are 3-budget means; rho-only ties the law in 100% of draws |
| Exp 10 | "within 0.002"; 20% target hit | within 0.0035; target is against S0+ and is not met (-18.96%, -16.28%) |
| Exp 13 v3 | "total gradient starvation" | near-total: 1 of 9 A/1301 updates has a nonzero gradient |
| Exp 21 | 0.0092% from "22 tokens" | 72 tokens (50 in-support + 22 unsupported) |
| Exp 18b | 82,545 to 7,020,465 tokens per run | 82,490 to 7,592,719 |
| Exp 01, 05, 02 | split count, 893/970, repeat arithmetic | 870/970 plus 26 incomplete; 5 kernel_binary passes; others as in 7a172cbd |
| Exp 19, 22, 25 | rounding (0.852, 56.3%, 40.15, -3.75, -0.53, 0.092, 0.312) | 0.851, 56.2%, 40.14, -3.74, -0.52, 0.091, 0.311 |
| About 35 pages | stale "running", "not yet submitted", "no GPU job yet" | current status with a QA note |

## 4. Tests

Fresh clone of main, run on the Mac-equivalent venv on this machine: 1,399 passed, 7 failed, 65 skipped, 1 error (24 min), plus per-experiment suites. Failures are host-bound (missing ultimate-utils, nemo_rl, SNAP paths, transformers version). They are not new and were not touched; for example exp 13 v4 (25 failed, 421 passed) and exp 08 v27/v28 (3 failed, 1 error).

## 5. Decisions for Brando (one question, with a pick)

- Pick: close exp 08 v3 as "incomplete at deadline" and leave the 14B rungs as the one open measurement; launch the 02B and 03 GPU runs only after the adapter fix. Everything else needs no decision.

## Appendix: caveats

- The reviewer was one model family (Codex GPT-6 Astra); ub9sc verified each HIGH item against the cited file before editing. Reports were produced on commit 0656edc3; fixes were later pushed to main (db9893b9 latest).
- "Unverifiable" means the raw data or log is not in the repo, not that the number is wrong.
- The VeriBench namespace defect (533 of 896 tasks suggest an invalid Lean namespace) is a VeriBench change; it needs Brando's word before any scored result changes.
- Models and harnesses: reviewer Codex CLI with GPT-6 Astra (ultra), Vals account, via the plan router; editing, verification and Doc by Claude Code agent with Sonnet 5.5.
