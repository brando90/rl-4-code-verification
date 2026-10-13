# Experiment 13 v2 master checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/CKPT_e13_v2.md>

**TLDR:** The master's resumable record for experiment 13 version 2. It covers the plan → one light review (Codex GPT-6 Astra, ultra) → SNAP owner dispatch → run to completion, as Brando requested on 10-09-2026 and again on 10-13-2026 ("Try again").

Created: 10-13-2026 11:07 PDT
Last updated: 10-13-2026 11:07 PDT

## Task and owner

- **Requests:**
  - 10-09-2026: "write detailed plans, have codexd ultra astra gpt6 light qa and then run them all to completion!"
  - 10-13-2026: "Try again".
- **Master:** Claude Code session "Oct 9: IRT for eval metric decomposition" (`claude-opus-5-5`) on Brando's Mac. It orchestrates only (Rule 55).
- **Coordination:** On 10-13 11:03 PDT the master told the "Revive remote processes" session (the parent of version 1's recovery master) that it is taking the version 2 master role. Reply: pending.

## State verified 10-13-2026 11:00 PDT

- **Version 1:** BLOCKED (`../expt_v1/RESULTS_opaque_audit_terminal.md`): 21,504 accounted, 6,739 measured, 14,765 unmeasured.
  - Root-cause branches were identified in code (`expt_v2/PLAN.md` § 1).
  - No version 1 process is running, per its terminal record; not rechecked on the host, because SNAP is unreachable.
- **Related result:** experiment `14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems` is DONE with verdict CONTINUE. At n_A = 50 the 2PL level forecast has mean absolute error 0.0344 vs 0.0554, a difference of +0.0210 [+0.0195, +0.0224].
- **Experiment 10:** protocol revision 3 locked 10-09-2026 16:43 PDT; the IRT gate becomes experiment 13 Phase 1b's secondary analysis.
- **Earlier landings, verified on origin:**
  - rl4cv `08ee026` (design), `ef1c612` / `41aaf6b` / `d2305c3` / `4a94944` / `465225e` / `208d0a5` (version 1);
  - VeriBench `4e286485c2` (sparse worktrees and pruning) and `5be02de6e2` (idea page).
- **Blocker:** SSH to skampere1, skampere2 and skampere3 times out from the Mac (home network 192.168.4.x; Stanford VPN not connected). GitHub is reachable. Connecting the Cisco VPN needs Brando's login and Duo.

## In progress

- **Plan drafted, not yet published:** `expt_v2/PLAN.md`, `expt_v2/cc.md` and this checkpoint, in worktree `~/vb_worktrees/rl4cv-e13v2-plan-10-13-2026`.
- **Next steps:**
  1. Publish the draft.
  2. Run the light review (one round): Codex `gpt-6-astra`, effort ultra, read-only brief.
  3. Apply fixes and record the verdict in `expt_v2/REVIEW_v2.md`.
  4. Publish.

## Exact next commands (master)

1. Light review, run on the Mac:

   ```bash
   codex exec --dangerously-bypass-approvals-and-sandbox -m gpt-6-astra -c 'model_reasoning_effort="ultra"' - < /tmp/e13v2_qa_prompt.md
   ```

   The brief: review `expt_v2/PLAN.md`, `expt_v2/cc.md` and the version 1 root-cause claims against the code; read-only; end with the verdict block.
2. Once the VPN is up, preflight the host: `bash ~/agents-config/scripts/snap_health.sh --node skampere1`, plus `nvidia-smi` and `uptime`.
3. Dispatch the owner:

   ```bash
   ~/agents-config/scripts/snap_dispatch.sh run codex-rl4cv-e13v2-owner '<codexd with expt_v2/cc.md>'
   ```

   Verify full access, the model and effort actually used, and the first useful action. Record the PID, pane and boot ID here.
4. Arm the master's hourly check-in in this session. The watchdog lives on skampere1 and is installed by the owner per `cc.md` § 0.
