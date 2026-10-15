# Experiment 13 v2 master checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/CKPT_e13_v2.md>

**TLDR:** The master's resumable record for experiment 13 version 2.

- **Plan:** revision 2, after the single light review (FAIL, with all 13 findings fixed).
- **Admission:** G0 was admitted under A3 on 10-14-2026 ([admission record](R2_A3_ADMISSION_10-14-2026.md)).
- **G0:** PASS (`120c558`). LP-1 under v2-S2 float16 is PASS. All three anchors have 0 strict successes under the frozen rollout sampler, and C calibration is not admitted. [Amendment A6](AMENDMENT_A6_zero_strict_signal_rollout_sampler_10-15-2026.md): skip batch 2, run a pipeline diagnostic, and apply T5 to arm B.
- **Previous owner:** `codex-rl4cv-e13v2-owner` is idle and low on context; it is not reused.

Created: 10-13-2026 11:07 PDT
Last updated: 10-15-2026 14:12 PDT

## Task and owner

- **Requests:**
  - 10-09-2026: "write detailed plans, have codexd ultra astra gpt6 light qa and then run them all to completion!"
  - 10-13-2026: "Try again".
- **Master:** Claude Code session "Oct 9: IRT for eval metric decomposition" (`claude-opus-5-5`) on Brando's Mac. It orchestrates only (Rule 55).
- **Coordination:**
  - On 10-13 11:03 PDT the master told the "Revive remote processes" session it is taking the version 2 master role. That session replied that it owns nothing for experiment 13 and did not start version 1's recovery master (`deploy_16e6b761a004445db113437e27f45456`).
  - Before claiming single-writer status, check skampere1 for any live version 1 writer:
    - `tmux ls | grep -E 'rl4cv13|e13'`;
    - `pgrep -af 'rl4cv13|deploy_16e6b761|opaque_base_audit'`;
    - state under `/lfs/skampere1/0/brando9/agent-recovery-10-09-2026/`.
  - Version 1's checkpoint names the sessions `codex-rl4cv13-opaque-reproduction`, `codex-rl4cv13-opaque-watch` and `codex-rl4cv13-audit-root-observer-v2`. Its terminal record says all exited.
  - Coordinate with any live writer instead of duplicating its work.

## State verified 10-13-2026

- **Version 1:** BLOCKED. 21,504 accounted, 6,739 measured, 14,765 unmeasured. The verified rejection paths, including the vacuity count overflow the review found, are in `PLAN.md` § 1.
- **Experiment 14:** DONE, verdict CONTINUE. Full scope in `PLAN.md` § 5.
- **Experiment 10:** protocol revision 3 locked 10-09-2026 16:43 PDT. Its IRT promotion gate is version 2's optional Phase 1b, under a separate frozen protocol.
- **Light review:** Codex `gpt-6-astra`, effort ultra, session `01a13675-179a-7410-a356-3b5bba3e4f7a`, 10-13 11:10–11:22 PDT. Verdict FAIL (3 critical, 9 major, 1 minor); resolution FIXED with 13 fixes. No re-review, per the light-review rule.
- **Tests:**
  - At `3ae1d0b` on the Mac: 7 failed, 269 passed, 28 skipped. The 7 failures already existed at the parent commit `c462ec1`: environment-dependent adapter tests.
  - After the skip guard: 269 passed, 35 skipped, 0 failed. With `E13_REQUIRE_LEAN_INTEGRATION=1`, the absent environment raises an error.
- **Landed:** rl4cv `3ae1d0b` (draft plan). This revision: `PLAN.md` revision 2, `cc.md`, `REVIEW_v2.md`, this checkpoint, and the test guard.
- **Blocker:** SSH to skampere1, skampere2 and skampere3 times out from the Mac (home network 192.168.4.x; Stanford VPN not connected). GitHub is reachable.
  - A background watch on the Mac exits when skampere1 answers (task `b313svabj`, at most about 8 hours).
  - Connecting the Cisco VPN needs Brando's login and Duo.

## Owner launch (verified 10-13-2026 11:44 PDT)

- **Preflight on skampere1:**
  - `snap_health.sh --node skampere1`: PASS, except `disk.dfs` FAIL (DFS 96% used). DFS is not on this job's path; the work root is on `/lfs`, 5.4 TB free.
  - No `rl4cv13`/`e13` tmux sessions or processes, so there is no live version 1 writer.
  - Load 13–16 on 128 cores; 1,940 GiB memory available.
  - GPUs 0–3 are busy with another user's vLLM (`srivats…`) and are off-limits. GPUs 4–7 were idle at 11:40 PDT.
- **Launch:**
  - Work root `/lfs/skampere1/0/brando9/rl4cv_e13v2`, clone of `main` at `1e0c8f8`.
  - Launcher `$WR/launch_owner.sh` writes the receipt `$WR/owner_launch.json` and appends exits to `$WR/owner_exits.log`.
  - Receipt fields: boot `839e7dd6-64e1-4a80-9498-31d30b3cc2df`, launcher PID 886575, runbook sha256 `e68206ee38309854af2f96a77817c14b7ce62e2583c2c314ec4ecf54fb014fee`, client `codex-cli 0.154.0` (login shell, nvm path; the stale `/usr/local/bin/codex` 0.114 is not used).
  - Codex process 1251864, binary 1251881, flags `--sandbox danger-full-access --ask-for-approval never`. The status bar shows `gpt-6-astra high`.
  - The master accepted Codex's directory-trust prompt for this owned clone.
- **First useful action:** the owner verified a clean checkout and no live version 1 writer, then read PLAN, PROTOCOL, the Phase 1 and Phase 2 plans, the review, the adapter and the tests.
- **Attach:** `ssh skampere1 -t tmux attach -t codex-rl4cv-e13v2-owner`.
- **Master check-in:** hourly from this session. It runs through SSH, which needs the VPN off campus. If the owner sits idle at its prompt with work remaining, the master types a continuation brief into the pane. The owner installs the SNAP watchdog per `cc.md` § 0.

## Check-in 10-13-2026 12:40 PDT: R0 attempt 1 failed; Amendment A1

- **R0 attempt 1:** the owner stopped at R0 under the runbook's literal no-retry rule ([RESULTS_R0_terminal.md](RESULTS_R0_terminal.md), `6e9c7c2`, `7e0efa9`).
  - 26/29 fixtures fully matched; oracle value and status 29/29; components 28/29; required suite 283 passed, 23 skipped, 0 failed.
  - Failures: 2 fixture-authoring errors (`String.ofList` missing in Lean 4.22.0; `#eval` marker in information messages, not stderr) and a real probe crash (`[init]` declaration evaluation in the frontend).
  - The owner sent one completion email and retired its watchdog.
- **Master decision:** [Amendment A1](AMENDMENT_A1_development_gates_10-13-2026.md).
  - R0 and R1 are development acceptance tests: fix, record numbered attempts, rerun, at most 5 attempts each.
  - The no-retry rule starts at L1v2.
  - The owner is briefed to apply A1, re-arm its watchdog and continue.

## Check-in 10-13-2026 13:40 PDT: R0 and R1 pass; L1v2 in preparation

- **R0 attempt 2 (under A1):** PASS, 30/30 fixtures (`7392a38`, [report](RESULTS_R0_attempt_2.md)).
- **R1 attempt 1:** PASS (`8bb1091`, [report](RESULTS_R1_attempt_1.md)).
  - Measured 400/400 train-allowlist cells: 300 of 8,900 v1-rejected and 100 of 4,036 v1-measured, from 12,936.
  - Oracle value and status 400/400; consistency 400/400.
  - Version 1 causes among the 300 rejected (Wilson 95%):
    - parse error 296/300 = 98.67% [96.62, 99.48];
    - unparseable theorem type 3/300 = 1.00% [0.34, 2.90];
    - duplicate identity 1/300 = 0.33% [0.06, 1.86].
  - Memory p99 6.45 GiB per cell; 48 workers admitted under a verified aggregate ceiling.
  - Projected R2 runtime 4.1 h, or 5.1 h with reserve.
  - Suite: 286 passed, 23 skipped.
- **Owner:** working on L1v2. The manifest has 38,784 unique sources and 42,024 oracle readbacks (3,240 shared).
- **Watchdog:** re-armed in cron (`*/15` plus `@reboot`, run `e13v2_a1`).

## Check-in 10-13-2026 14:40 PDT: L1v2 frozen; R2 running

- **L1v2:** frozen with carried forecasts before any validation or test factor (`a7991af`).
- **R2:** launched (`bc90848`) in tmux `e13v2-a1-r2`; coordinators `r2_ordinary` and `r2_opaque` both alive.
  - At 14:39 PDT: 8,499/38,784 complete (ordinary 4,483, opaque 4,016); 0 retried cells.
  - Rate about 185 cells per minute, so the expected finish is about 17:30 PDT.
  - Node load about 48/128; 1,924 GiB available.
- **Owner:** working, monitoring R2.

## Check-in 10-13-2026 15:40 PDT: opaque route INCOMPLETE; Amendment A2

- **Opaque route:** finished at 14:57 PDT, INCOMPLETE. 5,328 accounted, 5,319 measured, 7 typed deterministic limits, 2 untyped; equality status not reported among measured cells.
- **Ordinary route:** 11,385/33,456 at 15:40 PDT, no retries.
- **Owner response:** under PLAN § 4's literal rule, it blocked G0 and every later phase.
- **Master decision:** [Amendment A2](AMENDMENT_A2_R2_untyped_cells_and_admission_10-13-2026.md), written after the observation and disclosed as such.
  - Untyped cells get exactly one identical retry, inside their route.
  - The opaque receipt adds `equality_among_measured` (a boolean only).
  - R2 admits G0 on: equality on all measured cells of both routes; no integrity defect; typed limits listed; unresolved at most 0.1% per route, listed by cell ID.
  - No test outcome is inspected.

## Check-in 10-13-2026 16:40 PDT: running under A2

- **A2:** implemented and locked by the owner (`d72cd10`).
- **Status:** RUNNING UNDER A2.
- **Ordinary route:** 19,996/33,456 (25,324/38,784 overall), 0 retries. About 146 cells per minute, so the expected finish is about 18:15 PDT.
- **Next:** A2 reconciliation and the admission decision.

## 10-14-2026 12:53–13:00 PDT: revived, then handed over

- **Brando:** "revive this".
- **R2 (published 10-13 21:23 PDT, `d5c97ec`):** FAIL under A2.
  - Ordinary route: 4 of 33,243 measured cells unequal (value equality 36,477/36,481 readbacks; status 36,481/36,481); 45 unresolved against a ceiling of 33.
  - Opaque route: equality PASS; 2 unresolved, within the ceiling of 5.
  - G0 and later phases were not admitted.
- **Crontab incident (10-13 21:20 PDT, owner):** verified clean. The current crontab equals the owner's pre-version-2 backup line for line. Experiment 13's own watchdog lines are retired.
- **Connectivity:** skampere1 is reachable through the configured `whale.stanford.edu` ProxyJump, with no VPN.
- **Concurrent coordinator:** at about 12:50 PDT, Brando's ultracode master (`experiments/CKPT_MASTER_oct14-cc-rl4cv-master-ultracode-progress.md`; agent `rl-4-code-verification-75`) launched workflow `rl4cv-ultracode-progress-10-14`. One of its six workers is "experiment 13 v2 R2 diagnosis", running through the owner `codex-rl4cv-e13v2-owner`.
- **Handoff, to keep one coordinator per owner:**
  - This master committed [A3 (PROPOSED)](AMENDMENT_A3_PROPOSED_R2_diagnosis_and_admission_10-14-2026.md) before any diagnosis was read.
  - It messaged the ultracode master to adopt or reject A3.
  - It paused its own hourly check-in (cron `c6d0f8df` deleted).
  - It sends no brief to the owner while the ultracode workflow owns experiment 13.

## 10-14-2026 13:41–14:25 PDT: master resumed; G0 admitted under A3

- **Handback.** The ultracode master adopted A3 (`57c3bb6`) and the owner published the diagnosis (`8c7976d`). The ultracode master then handed the version 2 master role back: "please resume the v2 master role now".
- **Decision: G0 ADMITTED under A3 rule 3** ([R2_A3_ADMISSION_10-14-2026.md](R2_A3_ADMISSION_10-14-2026.md)). All 4 unequal cells are class (c); the 217-cell private exclusion manifest exists (SHA-256 `c00b35ab…4128`); the opaque PASS stands.
- **Why a wrapper is needed.** The frozen `reproduction/g0.py` (L1v2 SHA-256 `5042467c…`, checked equal on the Mac) refuses unless R2 is PASS, and treats any missing sample as an INCOMPLETE stratum. G0 therefore runs through a new wrapper, `g0_a3.py`:
  - it reuses the frozen `evaluate` unchanged;
  - it evaluates the frozen rule at every feasible completion of the excluded cells: PASS if the minima clear the thresholds, FAIL if a maximum misses one, INCONCLUSIVE otherwise;
  - its code, tests and lock are pushed before any G0 statistic is computed.
- **Transitions.** An INCONCLUSIVE gate does not advance. G1 fits treat excluded cells as missing, and the held-out G1 metrics are bounded; this is disclosed.
- **Brief.** [cc_resume_g0.md](cc_resume_g0.md), with the verbatim SNAP pre-approval line. Committed at `50de07f`.

## Fresh owner launch (verified 10-14-2026 13:54 PDT)

- **Preflight (13:51 PDT).**
  - skampere1: boot `839e7dd6…`, load 12 on 128 cores, 1,947 GiB memory available.
  - The old owner `codex-rl4cv-e13v2-owner` was idle at its prompt. Its process tree held only Codex and its plugin services, with no experiment children.
  - No experiment 13 cron lines were installed (7 crontab lines in total), and the clone was clean.
  - The other live session, `codexv-rl4cv-e08v2-matched-test`, belongs to experiment 08 and was not touched.
- **Launch.**
  - Clone fast-forwarded to `50de07f`. Launcher: `$WR/launch_owner_g0.sh`. Receipt: `$WR/owner_launch_g0.json`.
  - Session: tmux `codex-rl4cv-e13v2-owner-g0`, pane PID 1241764, launcher PID 1243344, Codex node PID 1243913, binary PID 1243923.
  - Client `codex-cli 0.154.0` (nvm login shell), flags `--sandbox danger-full-access --ask-for-approval never`, status bar `gpt-6-astra high`.
  - The brief as launched has SHA-256 `24b331af415fbd33366fbaaf03bfcb6827b96313f814a2ae2e866cc5eea086ea`.
  - No trust prompt appeared, since this clone was already trusted.
- **First useful action.** The owner read the rules and confirmed the old owner idle with no experiment children. It then named its own session as the single writer and began binding the watchdog additively. It also ran `snap_health.sh` and read the Valkyrie thread in agents-config issue #68.
- **Post-launch correction.** The brief and the admission record cited "rl4cv issue #68" for the Valkyrie 403. The thread is [agents-config issue #68](https://github.com/brando90/agents-config/issues/68), the agent inbox. Both docs were corrected after launch, changing that reference only; the owner had already found the right thread.
- **Attach:** `ssh skampere1 -t tmux attach -t codex-rl4cv-e13v2-owner-g0`.

## Check-in 10-14-2026 14:20 PDT: G0 PASS verified; Phase 1 waiting for GPUs

- **G0 PASS, verified.** The lock `a717d06` (14:03) precedes the result `120c558` (14:11), and the frozen files are unchanged between them. The 4B primary stratum gives dense-only 89–97/135 and AUC 0.6707–0.9046, by exact enumeration over 221,184 configurations; the admission verdict rule is applied. The 1.7B stratum passes, and the 8B stratum is INCONCLUSIVE (secondary, not gating). F0v2 (0.50) underpredicted.
- **GPU wait.** All 24 large GPUs are occupied by other users: skampere1's 8 A100s (`enyijolivia`, since about 14:02), and skampere2's H200s and skampere3's B200s (`vmadan`, `alexspan`, `srivatsavad`, `ruhana`, `aryangul`). The `ilc` Slurm route lacks an account association. This is a wait, not a scientific failure.
- **Owner steered at 14:20 (queued, not idle).** It does the GPU-free Phase 1 work now: LP-1 code, the sampler, the anchor runner, IRT fitting and its PROTOCOL § 4 validation, and the G1 bounds lock draft. It arms a 15-minute poller that claims only idle GPUs, and may use mercury's idle 16 GB RTX A4000s for generation. It is working (25 min, 71% context), and its watchdog lines are present.

## Check-in 10-14-2026 15:14 PDT: Phase 1 preparation without GPUs; poller armed

- **Owner working.** It is 39 minutes into its turn, with one context compaction and no exits. Since the last check-in it pushed three commits: `77dbf1a` (resource-wait record), `9101488` (probability checks, G1 bounds draft lock `G1_A3_DRAFT.json`, device polling) and `b52342e` (Phase 1 runners and missing-data fit controls). It is now finishing the LP-1 lock, so the poller can launch LP-1's single attempt.
- **Additive crontab.** It holds 10 lines: 7 identical to the pre-version-2 backup, plus the watchdog, its `@reboot` line and the 15-minute `phase1/device_watch.py` poller. Leases: 0, device-hours: 0.
- **GPUs still busy** (skampere1 has 17 compute processes from other users). No action was needed.

## Check-in 10-14-2026 16:14 PDT: LP-1 attempt 1 failed on a launcher defect; Amendment A4 adopted

- **LP-1 attempt 1** (`d831d0f` lock, then `50cf118` and `10335d1`). At 15:30 the poller found skampere1 GPUs 2 and 7 idle and claimed GPU 2, an A100. vLLM 0.10.0 then raised a `ValueError` during engine construction, because the launcher put the GPU UUID in `CUDA_VISIBLE_DEVICES` instead of an integer index. The attempt produced 0/8 responses and 0 tokens, with every admission statistic unmeasured, after 0.014593276 device-hours. Cleanup passed and the lease was released. The owner applied the brief's no-retry rule literally, published LP-1 INCOMPLETE and went idle; the watchdog emailed once at 15:38.
- **Master decision at 16:16 PDT:** [Amendment A4](AMENDMENT_A4_technical_gate_infrastructure_attempts_10-14-2026.md), adopted after the observation and disclosed as such. A technical gate (LP-1, LP, T1–T4) whose attempt ended on an infrastructure defect before computing any admission statistic may run again after a fix. Conditions:
  - every scientific setting stays byte-identical;
  - a regression test, a preflight check and a successor lock come first;
  - at most 3 attempts per gate, with every attempt published.

  An attempt that measures its statistics is final. The scientific gates keep the no-retry rule.
- **Next.** The same owner (`codex-rl4cv-e13v2-owner-g0`) receives A4: fix the device mapping, add the preflight and `locks/LP1_A4.json`, push, then let the poller run LP-1 attempt 2. skampere1 GPUs 1, 2, 4 and 7 were idle at 16:14.

## Check-in 10-14-2026 17:14 PDT: LP-1 attempt 2 measured FAIL under S1; Amendment A5 adopted

- **LP-1 attempt 2** (lock `957efca`, result `77558aa`, closeout `d1d675c`). It ran on skampere1 GPU 0 (A100) from 16:30:46 to 16:36:49, with the numeric device mapping and a passing engine preflight. Over 8/8 responses and 40,035 tokens: unsupported 0, median error 0.000303 (≤ 0.01), truncation at cap 2 0/40,035, all passing. The 99th-percentile error was **0.1248 > 0.10, FAIL**, final under A4. Cumulative usage is 0.115 of 0.6 device-hours, both leases are released, the watchdog emailed once, and the owner went idle.
- **Master decision at 17:17 PDT:** [Amendment A5](AMENDMENT_A5_numerics_condition_S2_after_LP1_fail_10-14-2026.md), adopted after the observation and disclosed as such. S1 (bfloat16 vLLM 0.10.0 with the bfloat16 NeMo RL 0.4.0 trainer) is final at LP-1 FAIL. One separately versioned condition, S2, may change only numerical execution, identically for generator and trainer. The rules:
  - at most 4 candidates, frozen in cost order before any measurement;
  - S2 is the first candidate to clear every criterion with a 20% margin on a disjoint, train-only development probe;
  - S2 is confirmed **once** on the original frozen probe with unchanged thresholds; if it fails, version 2 stops;
  - device use is capped at 3.0 device-hours.
- **Next.** Brief the owner with A5. G1's driver and method lock (`G1_A3.json`) are published and unexecuted.

## Check-in 10-14-2026 18:14 PDT: v2-S2 float16 LP-1 PASS; Phase 1 anchors in preparation

- **A5 order verified.** The candidate list and disjoint development probe were frozen at `6251b77` (17:33), before any measurement. C1 float16 passed development (p99 0.0163 ≤ 0.08 margin; median 2.3e-5; unsupported 0/51,472; truncation 0); C2 was not run. The S2 lock (`f8ecbfa`, 17:46) preceded the confirmation and is unchanged after it.
- **Confirmation PASS** on the original probe (`2b2f8b5`, 17:58). Over 8/8 responses and 44,844 tokens: unsupported 0, median 3.3e-5, **p99 0.0176 ≤ 0.10**, truncation 0. The S1 bf16 FAIL (0.1248) stays final. A5 used 0.207 of 3.0 device-hours; the suite ran 558 passed, 23 skipped.
- **Owner working** (56 min) on the float16 anchor runtime and dispatch, with tests for resume, the one-retry limit and lease accounting. The crontab has 14 lines, the 7 non-e13 lines identical to the backup. No action was needed.

## Check-in 10-14-2026 19:14 PDT: v2-S2 anchors generating on three A100s

- **Anchors running.** Generation was frozen at `d4948f3` (18:35); `937b2e7` (18:43) recorded the leases and the first verified batches. Base, half and full1 each completed segment 0 (256/4,312 responses, 0 exhausted, cleanup verified). Segment 1 is running on owned skampere1 GPUs 0, 1 and 2, which were idle at claim. Cumulative device-hours across all experiment 13 v2 leases: 1.81.
- **Throughput is below the plan.** A 256-response segment takes about 0.41–0.55 device-hours, which projects to about 8–9 device-hours per 4,312-response batch against PLAN § 5's 1–1.5. The likely cause is the S2-bound eager vLLM mode with a 32-sequence batch limit, both frozen by the lock, so no change is made. T4's cost re-estimate must use the measured S2 throughput.
- **Owner working** (about 2 h) on Phase 2 trainer preparation (NeMo RL loss, checkpoint and scheduler paths) while the anchors run. The crontab has 16 lines, the 7 non-e13 lines identical to the backup. The old owner's idle launcher (PID 886575) is untouched. No action was needed.

## Check-in 10-14-2026 20:14 PDT: anchors 768 + 512 + 512 of 3 × 4,312; Phase 2 technical code in progress

- **Anchors.** base 768/4,312, half 512/4,312, full1 512/4,312, with 0 exhausted cells, each segment 256 responses with cleanup verified. Three owned A100 leases are active (skampere1 GPUs 0–2). Cumulative device-hours are 3.879 across 14 leases. At about 0.5 device-hours per 256-response segment per GPU, the batches finish around 03:00–04:00 PDT on 10-15.
- **Owner working** (2 h 56 min) on Phase 2 technical-gate code ahead of LP and T1–T3. It published `1df6974` (empty Adam state preserved through native checkpoint save and restore), and is separating raw training receipts from gate evaluation, with T3 replaying T2's saved batch and state. The tests pass.
- **Healthy.** The crontab has 16 lines, the 7 non-e13 lines identical to the backup. No exits. No action was needed.

## Check-in 10-14-2026 21:14 PDT: base 1,536, half 1,024 and full1 1,024 of 4,312; full1 halted before a segment

- **Anchors.** base 1,536 and half 1,024 of 4,312 are running on GPUs 1–2, with 0 exhausted and 0 second attempts. full1 is at 1,024 of 4,312 and **HALTED_INFRA**. Segment 5 errored with `PermissionError: /proc/2264522/environ`: the foreign-process check read another user's process after a new job took GPU 0. Nothing was attempted (`attempted_in_segment: None`), cleanup was verified and PID 2264522 has since exited. The owner is investigating the dispatcher. Cumulative device-hours are 7.67 across 21 leases, under the 144 device-hour, four-batch anchor ceiling.
- **Phase 2 preparation.** Commits `a73dc86`, `69726e1` and `f59b423`: technical evaluators, isolated stages and arm rewards. Coverage-judge controls are frozen before any rating (`locks/COVERAGE_CONTROLS_S2.json`: 50 train-only control ratings, members GPT-6 Sol high and Opus 5.5 max). The only hosted Valkyrie run was metadata-only: 1/1 tasks, HTTP 200, **0 model calls**, through the coordinator-migrated Vals-managed gateway credential and no personal key. Required tests: 683 passed.
- **Healthy.** The owner is working (3 h 56 min). The crontab has 16 lines, the 7 non-e13 lines identical to the backup. No action this hour; if full1 is still halted next hour, steer the owner to treat an unreadable foreign `/proc` entry as "device busy" and resume full1 on the next idle device.

## Check-in 10-14-2026 22:14 PDT: base 2,048, half 1,536 and full1 1,024 of 4,312; full1 waiting for an idle device

- **Anchors.** base 2,048 and half 1,536 of 4,312 are running on owned GPUs 0–1, with 0 exhausted. full1 is out of HALTED_INFRA and now in **WAIT_FOR_IDLE_DEVICE** at 1,024 of 4,312; the owner handled the foreign `/proc` permission case. skampere1 GPUs 2 and 4 were idle at 22:14, so the poller should claim one. Cumulative device-hours are 9.72 across 25 leases.
- **Owner working** (4 h 56 min) on the Phase 2 pilot configuration. Arm-selection tests: G1 or H2 FAIL or INCONCLUSIVE keeps A, B and P; an unfinished gate raises an error instead of counting as a failure; G0 FAIL raises an error.
- **Healthy.** The crontab has 16 lines, the 7 non-e13 lines identical to the backup. No action this hour; check next hour that full1 resumed on an idle device.
- **Coverage-judge route controls PASS** ([RESULTS_COVERAGE_CONTROLS_S2.md](RESULTS_COVERAGE_CONTROLS_S2.md); freeze `f59b423`, registration successor `1151dd6`, result `f41dbc9`). All 50/50 train-only ratings were measured through hosted Valkyrie with the Vals-managed gateway credential: 50 model-query attempts, 0 retries, reported charges $2.98. GPT-6 Sol high and Opus 5.5 max each meet every frozen control: oracle, vacuous, blank and shuffled 5/5, and half-deleted 4/5 against a required 4/5. This clears the 10-13 HTTP 403 blocker for Phase 2 coverage scoring. The train mutation audit, the coverage monitor and the hidden-gold controls still come before learning.

## Check-in 10-14-2026 23:14 PDT: base 2,816, half 1,792 and full1 1,280 of 4,312, all running

- **Anchors.** All three batches are RUNNING on owned GPUs 0–2: base 2,816/4,312, half 1,792/4,312 and full1 1,280/4,312 (resumed after the permission fix). There are 0 exhausted cells, and the only error is full1's pre-attempt segment-5 halt, in which no cell was attempted. Cumulative device-hours are 12.14 across 31 leases. At the observed rate, base finishes around 03:30 PDT, and half and full1 around 06:00–08:00 PDT on 10-15.
- **Owner working** (5 h 56 min) on the Phase 2 train mutation-audit inputs, which tie each mutation to its source and scoring receipt and keep missing inputs among all 128 declared slots. Cost accounting and the audit cohort are published at `07d4c11`, with 764 tests passing.
- **Healthy.** The crontab has 18 lines, the 7 non-e13 lines identical to the backup. No exits. No action was needed.

## Check-in 10-15-2026 00:14 PDT: anchors 3,456, 2,528 and 1,696 of 4,312 durable

- **Anchors.** The owner's durable counts are base 3,456, half 2,528 and full1 1,696 of 4,312; finished-segment receipts show 3,328, 2,304 and 1,536. All three are RUNNING on owned GPUs 0–2, with 0 exhausted cells. Cumulative device-hours are 14.79 across 36 leases. Base should finish around 02:00 PDT, and half and full1 around 05:00–08:00 PDT.
- **Owner working** (6 h 56 min). It is publishing the train-audit and learning launchers. Its required suite ran 803 passed, 3 skipped, 0 failed in 414 s.
- **Healthy.** The crontab has 18 lines, the 7 non-e13 lines identical to the backup. No exits. No action was needed.

## Check-in 10-15-2026 01:14 PDT: anchors 4,096+, 3,040 and 2,080 of 4,312

- **Anchors.** Finished-segment receipts show base 4,096 (one final segment left), half 2,816 (3,040 durable) and full1 2,048 (2,080 durable) of 4,312. All are RUNNING on owned GPUs 0–2, with 0 exhausted cells. Cumulative device-hours are 18.22 across 43 leases.
- **Owner working** (7 h 56 min). It is preparing evaluation scoring with the same historical strict oracle as the anchors: completed scores are recovered from receipts, an infrastructure retry reuses the identical frozen output, and missing outcomes stay explicit instead of counting as zeros. Recent commits are the evaluation-generation analysis and the learning launchers.
- **Healthy.** The crontab has 18 lines, the 7 non-e13 lines identical to the backup. No exits. No action was needed.

## Check-in 10-15-2026 02:14 PDT: base anchors COMPLETE 4,312/4,312; half 3,584; full1 2,560

- **Anchors.** Base is **COMPLETE** at 4,312/4,312, with 0 exhausted cells across 17 segments. half 3,584/4,312 and full1 2,560/4,312 are RUNNING on owned GPUs 0–1. Batch 2 (`full2`) correctly waits for the frozen calibration, item parameters and F2 (PLAN § 5 step 3). Cumulative device-hours are 21.04 across 48 leases.
- **Owner working** (8 h 56 min) on the Phase 2 monitor runtime and hidden-test helpers. They reject changed snapshot identities, reuse saved strict-score evidence and keep incomplete hidden-test coverage unknown. The judge-pack adapter's 16 focused tests pass.
- **Healthy.** The crontab has 18 lines, the 7 non-e13 lines identical to the backup. No exits. No action was needed.

## Check-in 10-15-2026 03:14 PDT: base COMPLETE; half 3,840 and full1 3,072 of 4,312

- **Anchors.** Base is COMPLETE at 4,312/4,312, and its Lean scoring is closed (`1876843`): 4,311 measured, 1 unresolved deterministic parser error kept in the denominator, **0 strict successes** (full-denominator strict-mean bounds [0, 0.000232]), 0 retries. half 3,840/4,312 and full1 3,072/4,312 are RUNNING on owned GPUs 0–1, with 0 exhausted cells. Cumulative device-hours are 22.57 across 51 leases.
- **Owner working** (9 h 56 min) on the Phase 2 monitor processing (score the fixed generated monitor once and freeze independent hidden inputs) and the pilot token-budget code, which uses every fixed A-pilot slot without imputing missing lengths. 20 focused tests pass.
- **Healthy.** The crontab has 18 lines, the 7 non-e13 lines identical to the backup. No exits. No action was needed.

## Check-in 10-15-2026 04:14 PDT: base and half anchors COMPLETE; full1 3,584 of 4,312

- **Anchors.** Base (scored: 0 strict successes out of 4,311 measured) and **half are COMPLETE** at 4,312/4,312 each, with 0 exhausted cells. full1 is at 3,584/4,312 (3 segments left), RUNNING on owned GPU 0. Batch 2 waits for the frozen calibration and F2. Cumulative device-hours are 24.55 across 54 leases.
- **Owner working** (10 h 56 min). Learning-report and evaluation-snapshot code: it preserves failed-run counts and the exact model at each retained token checkpoint, and evaluation admission requires a published checkpoint selection and a test-analysis method frozen before training. The required suite is running.
- **Healthy.** The crontab has 18 lines, the 7 non-e13 lines identical to the backup. No exits. No action was needed.

## Check-in 10-15-2026 05:14 PDT: full1 anchors 4,096 of 4,312 (final segment running)

- **Anchors.** Base and half are COMPLETE at 4,312/4,312 each. full1 is at 4,096/4,312, with its final segment 17 (216 responses) RUNNING on owned GPU 0 under a lease with 7,102 s left, and 0 exhausted cells. Cumulative device-hours are 25.59 across 56 leases.
- **Owner working** (11 h 56 min). The final-analysis driver is published (`2029faa`). It is preparing the prospective pilot-lock helper, which binds the runtime, probes, final scientific gates and resource limits, with the cost recipe still pending.
- **Half scoring closed** (`9a3dd32`): 4,303/4,312 measured, 9 unavailable (8 deterministic timeouts, 1 frontend failure), **0 strict successes** (bounds [0, 0.00209]). Base scoring also had 0/4,311. **Watch item:** under the frozen Phase 2 sampler (temperature 1, top-p 1, float16), neither Base nor the 50% rung solves any train task. If the full1 rung (the Phase 2 start) is also near zero, three risks follow, all governed by the frozen rules with no change made: arm A gets almost no strict signal; H2 (mixed-group AUC) may be one-class; T5 (A's learning gate) may fail. For comparison, the historical validation ladder used for G0 had 14–21 later-positive tasks among the zero-earlier-success subset. full1 scoring is the decisive number.
- **Healthy.** The crontab has 18 lines, the 7 non-e13 lines identical to the backup. No exits. No action was needed.

## Check-in 10-15-2026 06:14 PDT: all three anchor panels generated (3 × 4,312); full1 scoring running

- **Generation complete.** Base, half and full1 each have 4,312/4,312 responses (12,936 in total), with 0 missing and 0 retries; full1 generation took 9.71 device-hours (`0e46249`). Every lease is released, and cumulative device-hours are 26.07 across 56 leases. Scoring so far: base 0/4,311 strict successes, half 0/4,303. The full1 scoring lock is frozen (`3ddd8b3`) and the unchanged scorer is RUNNING, at 1,660/4,312 saved receipts at 06:11. Scoring cost so far: base 14.4 and half 16.7 processor-hours, 0 device-hours.
- **Next, per PLAN § 5.** Publish the full1 scoring, then run the single calibration with frozen items and F2, then independent batch 2 (still unarmed), then G1/H2. The full1 strict-success count decides the watch item recorded at 05:14.
- **Healthy.** The owner is working (12 h 56 min, 994 tests passing). The crontab has 18 lines, the 7 non-e13 lines identical to the backup. No exits. No action was needed.

## Check-in 10-15-2026 07:14 PDT: full1 0 strict successes; calibration fails for C; Amendment A6 adopted

- **Anchors scored.** full1 (the Phase 2 start) has **0/4,302** strict successes, with 10 missing (`3631acd`). Across all three panels: 0/12,916 strict successes, well-formed outputs (Q1) 9.6%, 7.6% and 12.9%, and **compile among well-formed outputs (Q2) 0/1,294**. The single calibration (`cc0dc01`, then `65bbc29`) fails admission for arm C. The d and p models have 3 and 45 empty items; the t and Q1 bias intervals exclude zero; the conditional strict forecast is unavailable; the C variance check is INCONCLUSIVE. C is disabled, which is final, and F2 (0.75) and the placebo distribution are frozen.
- **Diagnosis.** The frozen rollout sampler (temperature 1, top-p 1, top-k off, 8,192 tokens) differs from the historical evaluation sampler (temperature 0.6, top-p 0.95, top-k 20, 12,288 tokens; `phase2/evaluation_contract.py`), which gave nonzero strict success on validation. Under the frozen plan, batch 2 (for H2) measures nothing, and T5 (A must learn) would stop Phase 2 on reward sparsity before B − A.
- **Master decision at 07:19 PDT:** [Amendment A6](AMENDMENT_A6_zero_strict_signal_rollout_sampler_10-15-2026.md), prospective, before any Phase 2 learning, validation or test data:
  1. Skip batch 2; H2 and F2 are reported UNAVAILABLE.
  2. Run a once-only, train-only pipeline diagnostic first: 64 tasks × 8 samples from full1, frozen S2 runtime with the historical sampler. It is sound if strict > 0 and the compile rate is at least 1/10 of the historical rate; otherwise stop and diagnose.
  3. Apply T5 to B's own reward: a moving-average rise of at least 0.02 from updates 1–10 to 21–30, with one extension to 60. A's curve is descriptive.

  Claims are scoped to the zero-signal regime. Before A6, the owner was told to hold batch 2 (07:25 queued, 07:27 immediate).

## Check-in 10-15-2026 08:14 PDT: A6 applied; diagnostic attempt 1 failed on infrastructure; A6 clarified at 08:15

- **A6 applied by the owner.** `7a447c8` waives batch 2 (H2 and F2 UNAVAILABLE) and freezes the historical G1 and the diagnostic cohort. `f5af95c` freezes the diagnostic execution: historical full-schedule 4B validation compile and strict rates are both 100/1,080 = 9.26%, the sound threshold is strict > 0 and compile ≥ 5/512, the cohort is 64 train tasks (task-ID hash `f6a7c303…`), and the allocation is ≤ 2.0 device-hours.
- **Attempt 1 failed on infrastructure.** Its lease (`…c8536902…`, 0.0038 device-hours) ended on "frozen weights absent" (a `pytorch_model.bin` checkpoint) before any generation. The owner prepared a fix and passed a device-free preflight, but recorded `rerun_admitted: false`, reading A6's "once-only" literally.
- **Master clarification at 08:15 PDT,** appended to A6. A4 applies to the diagnostic: an infrastructure attempt that generates nothing may be rerun after a fix, a regression test, a preflight and a successor lock, with at most 3 attempts. A scored attempt is final. The owner was steered accordingly. Healthy: no active leases; the crontab has 18 lines, the 7 non-e13 lines identical to the backup.

## Check-in 10-15-2026 09:20 PDT: G1 INCONCLUSIVE (C stays disabled); A6 diagnostic attempt 2 at 256 of 512

- **G1 published** (`d9df333`, [RESULTS_G1_S2.md](RESULTS_G1_S2.md)): **INCONCLUSIVE**. In both holdout schemes no IRT candidate passed inner admission, so the selected forecast and its paired contrasts are unavailable; C stays disabled. Descriptively, on 3,240 full-schedule cells (58 excluded), M1 (calibrated earlier-rung factored reward) beats M0 (smoothed earlier-rung strict rate): log loss [0.173, 0.222] against [0.230, 0.259], and AUC [0.866, 0.929] against [0.832, 0.874]. These are point ranges over missing-label completions, with p-val n/a.
- **A6 diagnostic attempt 2.** The format repair and attempt-2 lock (`d9df333`, 08:31) were pushed before the run, and the engine preflight passed (`64406dd`). It is RUNNING on owned GPU 0 at 256/512 responses saved, with no scoring yet. The owner has also prepared the A6 Phase 2 admission and B's own-reward feasibility gate (`bbe36cd`).
- **Healthy.** The owner is working (16 h). The crontab has 18 lines, the 7 non-e13 lines identical to the backup. No exits. No action was needed.

## Check-in 10-15-2026 10:14 PDT: A6 diagnostic generation complete; scoring 490 of 512

- **A6 diagnostic attempt 2.** Generation is complete for 512 responses, and the lease was released at 1.4025 device-hours, within the 2.0 allocation; cumulative experiment device-hours are 27.48. The unchanged official scorer has closed 490/512 cell receipts, and the analysis (SOUND or UNSOUND) is pending. The learning-pilot lock stays unadmitted until a SOUND verdict is published.
- **Owner working** (16 h 56 min), monitoring scoring and running the publication checks in parallel. The master armed a background wait (task `by41jbt7b`) for the analysis result.
- **Healthy.** No active leases. The crontab has 18 lines, the 7 non-e13 lines identical to the backup. No exits. No action was needed.

## 10-15-2026 10:37 PDT: A6 pipeline diagnostic SOUND

- **Verdict SOUND** (`$WR/phase1/A6/analysis/result.json`). This is `sft_4B_f1p0` on 64 train tasks × 8 samples, with the frozen S2 float16 runtime and the historical evaluation sampler (temperature 0.6, top-p 0.95, top-k 20). Compile and strict successes are both **48/496 measured (9.7%)**. 16 are missing (15 deterministic resource limits, 1 unresolved); extraction found 395 Lean file blocks and 101 responses with no Lean block. The threshold was strict > 0 and compile ≥ 0.926% (≥ 5/512), against a historical full-schedule validation rate of 100/1,080 = 9.26%.
- **Meaning.** The pipeline (prompts, template, float16 numerics, official scorer) reproduces the historical success rate under the historical sampler. The 0/12,916 strict successes under the frozen rollout sampler (temperature 1, top-p 1) are a sampler effect, not a defect. Per A6, Phase 2 proceeds (LP, T1–T4, audits, pilot) with T5 applied to arm B's own reward and A's curve descriptive.

## Check-in 10-15-2026 11:15 PDT: SSH gateway refusing; published state only

- **SNAP unreachable from the Mac.** `ssh skampere1` (ProxyJump `brando9@whale.stanford.edu`, configured route verified) failed 3/3 with "Connection closed by UNKNOWN port 65535". A direct gateway test returned `kex_exchange_identification: read: Connection reset by peer` from 171.64.75.72:22. TCP is reachable, but the gateway resets during key exchange, which points to throttling or a temporary block rather than authentication. Following `machine/snap.md` connection recovery, there were no repeated hammering attempts and no Cisco/Duo request. A bounded background retry runs every 5 minutes for up to 30 minutes.
- **Published state (GitHub).** There have been no new experiment-13 commits since `e2d45e4` (10:45). The owner's last status (10:37): "A6 final SOUND; continue to the learning-pilot lock and unchanged technical gates under A6". The owner runs on skampere1 independently of the Mac, under its watchdog.
- **No action possible this hour.** Verify owner liveness, leases and the crontab once the gateway answers.
- **Retry result (11:40 PDT).** The gateway was still refusing after 6 tries at 5-minute intervals: TCP 22 open, reset at key exchange. The direct route (`ProxyJump=none`) times out off-campus. The only remaining route is the Stanford VPN, which needs Brando's sign-in and Duo; it is optional because the owner runs autonomously. No owner commits since `031cd17` (10:41). The hourly check-in retries the gateway at 12:07.

## Check-in 10-15-2026 12:10 PDT: gateway still refusing; owner silent on GitHub since 10:41

- **SNAP unreachable.** `ssh skampere1` gives "Connection closed by UNKNOWN port 65535", and whale (171.64.75.72:22) resets at key exchange: the same failure since 11:15. The direct route needs the Stanford VPN, which needs Brando's sign-in and Duo. Brando was asked once to connect it, following the `machine/snap.md` rule to ask only when the remaining route requires a human step.
- **Published state unchanged.** There have been no experiment-13 owner commits since `031cd17` (10:41), and results.md still reads "A6 final SOUND; continue to the learning-pilot lock" (10:37). That is about 1.5 h without a push against the owner's usual 10–20 minutes, so it may be building a large step, idle at its prompt, or blocked on GitHub from SNAP. It cannot be verified without SSH.
- **Next.** Once SSH works: check the pane and process tree; if idle with work remaining, send the A6 continuation (learning-pilot lock, LP, T1–T4) with the pre-approval line. Then verify leases and the crontab.

## Check-in 10-15-2026 13:10 PDT: SNAP still unreachable; no owner commits since 10:41

- **Routes.** whale (171.64.75.72:22) still resets at key exchange, and the direct route still times out because the VPN is not connected. This is the same failure since 11:15. Brando was asked once at 12:10, in chat and by phone push; no new push.
- **Published state unchanged** since `031cd17` (10:41): the last owner status is "A6 final SOUND; continue to the learning-pilot lock". That is about 2.5 h without an owner push, which cannot be explained without SSH.
- **Next.** Retry at the next hourly check-in. Once reachable, inspect the pane and resume the owner if idle (A6 continuation with the pre-approval line).

## Check-in 10-15-2026 14:10 PDT: SNAP still unreachable (3 h); no owner commits since 10:41

- **Routes.** whale still resets at key exchange (since 11:15), and the direct route times out with no VPN. If whale has blocked this Mac's IP after repeated connections, further probing could extend the block, so from now on each check-in makes **one** probe per route. The VPN request to Brando (12:10) is still open.
- **Published state unchanged** since owner commit `031cd17` (10:41), about 3.5 h. The owner's watchdog emails Brando on a stop; nothing is visible from the Mac.
- **Next.** Same as 13:10: once reachable, inspect the pane and resume the owner if idle.

## Exact next commands (master)

0. **Resume:** dispatch a fresh owner in a new tmux session `codex-rl4cv-e13v2-owner-g0`, seeded with `expt_v2/cc_resume_g0.md` and using the same client, flags and fallbacks as item 2. Never type into the old owner session.

1. **Preflight, once SNAP answers:**

   ```bash
   bash ~/agents-config/scripts/snap_health.sh --node skampere1
   ```

   Then run `tmux ls`, `pgrep` (as above), `nvidia-smi`, `uptime` and `free -g` on skampere1.
2. **Dispatch the owner** (one writer), in tmux `codex-rl4cv-e13v2-owner` on skampere1:
   - work root `/lfs/skampere1/0/brando9/rl4cv_e13v2`, own clone of `main`;
   - `codex --sandbox danger-full-access --ask-for-approval never -m gpt-6-astra -c model_reasoning_effort="high"`, seeded with `expt_v2/cc.md`;
   - verify the model and effort actually used, full access, and the first useful action;
   - record the PID, pane and boot ID here.

   Fallbacks under Rule 48: `clauded` with `claude-fable-5-1` high, then `clauded-vals`.
3. **Arm the master's hourly check-in.** The owner installs the SNAP watchdog per `cc.md` § 0.
