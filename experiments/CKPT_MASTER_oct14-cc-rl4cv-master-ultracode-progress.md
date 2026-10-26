# Master checkpoint: 10-14-2026 ultracode progress round

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/CKPT_MASTER_oct14-cc-rl4cv-master-ultracode-progress.md>

**TLDR:** Brando asked (10-14-2026, about 12:40 PDT) for a multi-agent "ultracode" push to make progress on experiments and the 10-13 meeting notes while he is away 1-2 hours. The master (Claude Code, claude-fable-5-1, effort max, tmux `oct14-cc-rl4cv-master-ultracode-progress` on Brando's Mac) launched one Workflow run with six parallel workers, each independently checked. Zero model calls this round: the Vals Valkyrie route returns HTTP 403 since 10-13 03:27 PDT.

Created: 10-14-2026 12:56 PDT
Last updated: 10-20-2026 13:38 PDT

## Goal
- Land verifiable progress on main for: the 10-13-2026 meeting record and decisions; experiment 10 phase A (locked, never run); experiment 08 v3 corpus admission and failure taxonomy; experiment 13 v2 R2 diagnosis (via its idle owner on skampere1); a new experiment 15 (IRT forecast of RL-signal onset, idea-page Q2); experiment 12's corrected adapter (version 2 preparation).

## What ran
- 10-14-2026 ~12:50 PDT: Workflow `rl4cv-ultracode-progress-10-14` (run id `wf_ff4d2560-7f8`, in-process agents at Brando's explicit ultracode request; script under the session's `workflows/scripts/`). Stages: Work (6) -> Verify (6) -> Fix (only on blocking findings). Workers run in detached worktrees and push `HEAD:main` with explicit pathspecs; host jobs run on skampere1 in named tmux sessions (`rl4cv-e10-phase-a-10-14`, `rl4cv-e08v3-admission-10-14`, `rl4cv-e12v2-census-10-14`; experiment 13 reuses `codex-rl4cv-e13v2-owner`).
- Pre-launch: pulled origin/main to d5c97ec (reconciled the identical untracked transcript copy); read agents-config rules 8/42/44/48/51/57/67/69/70; read issue #68 and both weekly-notes docs (newest sections 10-14 Vals, 10-09 Stanford).

## Results
- Workflow done 13:31 PDT: 12 agents (6 workers + 6 checkers), 0 errors, every worker PASS on independent check, no fix pass needed; 21 commits on origin/main from the round (c9fe074 .. 89604e3 plus 57c3bb6, 8c7976d).
- Meeting 10-13-2026: summary, action items, index, meetings/README.md; D-017 (warm-start ownership and readiness criteria), PLAN section 12.
- Experiment 10 phase A (locked protocol, 164 x 424, 1,000 splits x 1,000 dyadic draws): H1 scalar-rule harmful promotion rate 0.2580 [0.2410, 0.2821]; H2a 0.1265 [0.0840, 0.1675] (descriptive); H3 **no gate recommendation** (C_fac 0.0046 [-0.0027, 0.0117], C_bin 0.0163 [-0.0014, 0.0355], C_fac0 0.0210 [0.0017, 0.0403]); "just be stricter" S0+ safer than R3 by 0.0652 [0.0443, 0.0838]; p-val=n/a. Matched-test-lists sensitivity blocked by the pinned shape stop rule (164 x 421 vs 420).
- Experiment 15 (new; Q2): **NO ADVANTAGE**: final-rung MAE difference B1 - IRT 2PL -0.0066 [-0.0169, +0.0038]; B2 - IRT 2PL +0.1151 [+0.0992, +0.1300]; paired task bootstrap, 10,000 draws, 135 validation tasks, 4/4 sizes; p-val=n/a.
- Experiment 08 v3: failure taxonomy of 4 x 1,080 step-658 validation cells (no Lean file 183/134/106/85; compile error 844/846/870/865; kernel success 53/100/104/130 for 1.7B/4B/8B/14B; every capped cell is an unterminated file); expansion corpus admitted 2,585/2,587 (0 duplicates, 0/7,761 held-out hits, 5,429,531 new loss tokens); PROTOCOL.md drafted, not locked; no training.
- Experiment 12 v2: corrected adapter + 64 tests; static controls 882/882 and 0/882 wrong after V2-A1; census 3,121/4,626 cells fully mapped statically; protocol locked, forecast frozen (+A1); no hidden outcome computed.
- Experiment 13 v2: A3 adopted (57c3bb6) before outcomes; owner diagnosis (8c7976d): 49/49 classified, (a) 2 / (b) 0 / (c) 4 / (d) 43, all 4 unequal cells class (c); handed back to the v2 master session for exclusions, bounds and G0.

## Stuck / blocked
- Vals Valkyrie route: HTTP 403 "Managed AWS access is not available for this organization" since 10-13 03:27 PDT; Jaewon asked 10-14 03:43 PDT (issue #68 comment 6166535065). Blocks experiment 08 v2's matched test and all judged evaluation.
- Rakshit's SNAP access: IL Action ticket #149859 awaiting Prof. Koyejo (10-13 18:07 PDT). Brando's Slurm request: ticket #149865, unanswered since 10-13 12:27 PDT.
- make test on macOS has 4 pre-existing e13 v2 watchdog/A2 failures (Linux-only tests); workers treat that set as baseline.

## Next steps
- none owned by this session (CLOSED 10-20-2026). Experiments 08 v3 and 13 v3 are coordinated by the session "Oct 20 (from Oct 9): rl4cv factored-reward RL pilot (IRT/SCSC)" (13: expt_v3/CKPT_master_resume_10-20-2026.md); experiment 12 v2 completed 10-16-2026 (14764299) and v3 followed; experiment 10's matched-test-lists sensitivity still waits on Brando's amendment-or-expt_v2 choice unless a later checkpoint records it.
- [p 3/10] Unowned leftover: add the Q2 status line (rl4cv experiment 15, NO ADVANTAGE, 10-14-2026) to brando90/veribench experiments/ideas/irt_latent_factors_for_scsc_vs_pass1_and_rl_guidance/README.md.

## Brando to-do
- Nudge Vals (Jaewon) on the Valkyrie 403 if you see him before he answers; it blocks 08 v2, all SCSC judging and 13 phase 2.
- Experiment 10: choose a dated amendment (expected shape 164 x 421, rerun only the sensitivity) or an expt_v2; the primary verdicts do not depend on it.
- Chase SNAP tickets #149865 (your Slurm request) and #149859 (Rakshit's access, needs Prof. Koyejo).
- Read PR #13 (status page + folder-cleanup proposal) and say "archive" to execute its moves.

## Log
- 10-14-2026 12:56 PDT -- Workflow launched with six workers; checkpoint created.
- 10-14-2026 12:59 PDT -- Adopted experiment 13 v2 Amendment A3 (peer session's prospective rules) before any per-cell outcome; owner told to classify by A3; version 2 master resumes after this round.
- 10-14-2026 13:40 PDT -- Workflow complete (12 agents, all PASS); index rows for 08/10/12/13/14/15 applied; checker-flagged record fixes applied (e12 cc.md verification inputs, 379 vs 394 note, CKPT log corrections, transcript quote fidelity); worktrees and finished host sessions cleaned; e13 handed back to the v2 master.
- 10-20-2026 13:38 PDT -- Session retitled idle and closed; no owned step left. Relayed for the record: the Valkyrie HTTP 403 was resolved 10-14-2026 19:25 PDT (hosted route on main, a3d587b/7c7b64f) and rl4cv's Valkyrie usage was paused by Brando's spend rule 10-15-2026 09:39 PDT (local SNAP models fine; judge/teacher calls refused until an ALLOW glob; veribench experiments/CKPT_vals_spend_pause_10-15-2026.md). Owners of 08/13 are the Oct 20 coordinator session.
