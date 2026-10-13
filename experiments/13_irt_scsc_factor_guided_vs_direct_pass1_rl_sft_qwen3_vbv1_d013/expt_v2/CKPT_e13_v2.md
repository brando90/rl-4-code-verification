# Experiment 13 v2 master checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/CKPT_e13_v2.md>

**TLDR:** The master's resumable record for experiment 13 version 2. The plan is at revision 2 after the single light review (FAIL, all 13 findings fixed). The SNAP owner is **RUNNING** on skampere1 in tmux `codex-rl4cv-e13v2-owner` (Codex `gpt-6-astra` high, full access), launched 10-13-2026 11:41 PDT.

Created: 10-13-2026 11:07 PDT
Last updated: 10-13-2026 14:45 PDT

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

## Exact next commands (master)

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
