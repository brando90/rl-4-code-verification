# Experiment 13 v4 Amendment V4-A3: when v4 starts, and pausing v3-A7

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/AMENDMENT_V4-A3_schedule_v4_start_and_v3_pause_10-20-2026.md>

**Status:** recorded 10-20-2026, before any v4 data and before any v3-A7 T5 statistic. It is subject to **Brando's veto until 10-21-2026 12:00 PDT**, which the general coordinator raises in his 07:35 PDT morning report. Nothing here runs before that window closes. If he vetoes, the frozen timing in [PROTOCOL.md](PROTOCOL.md) § 5 stands unchanged.

This schedule is option (c) from the coordinator's light QA (Claude Fable 5.1, max effort, run at Brando's request; grade 9/10). It replaces § 5's "Timing" bullet. All other § 5 rules stay, including idle GPUs only and never another user's GPU.

**TLDR:** v4 is the designed test of factored versus direct reward, and v3-A7 cannot answer that question because its arm A has almost no signal. So once v4 is admitted, five of the six v3-A7 trajectories pause at a clean point. B_1301 alone runs to its pre-registered T5_30 verdict, while v4's technical gates use a freed GPU. v4's learning pilot starts after B_1301's verdict, whether PASS or FAIL. v3-A7 runs no extension and no main study.

## Why

- **Measured pace.** Each v3-A7 update costs 2.6–3.2 GPU-hours, including a generation lease of about 35 minutes. Six trajectories share skampere1 GPUs 0, 5 and 7 at about 0.9–1.15 updates per hour.
- **Under the frozen § 5.** B_1301's T5_30 would arrive in about 2.8–3.6 days and all six `result_30.json` in about 4.4–5.7 days. A T5 FAIL would also start v3-A7's pre-registered extension to 60 updates and keep the GPUs.
- **v3-A7's limit.** Arm A has about 1 active group in 32, so v3-A7 cannot compare factored against direct reward.
- **What option (c) buys.** B_1301 alone reaches T5_30 in about 1.5–1.8 days. Meanwhile v4's gate chain (V4-T1, V4-G0, V4-T2, V4-T3, V4-T4 and the B audits, about 10–12 GPU-hours) runs on a freed device.
- **Why not stop v3-A7 outright.** That would waste about 60 completed updates and leave the pre-registered T5 unevaluated, while v4 is not yet admitted to use the GPUs.

## Rules

1. **Preconditions for the pause.** All three must hold:
   - the veto window has closed without a veto;
   - the v4 admission passes `launch-check`;
   - the v4 device guard is installed.

   Until then nothing changes, and the v3-A7 watchdog keeps all six trajectories running.
2. **The pause.**
   - Only these five trajectories pause: A_1301, A_1302, B_1302, P_1301 and P_1302.
   - Each pauses only at a clean stage boundary, while its runner holds no GPU lease and is waiting for one ("waiting for an idle GPU"), or right after a stage's receipt is durable.
   - A running generation, scoring or optimizer stage is never interrupted.
   - The master stops only the paused trajectories' own runner processes, recorded with process ID and start time, and adds them to a pause list. The v3 watchdog then skips them instead of relaunching them.
   - Paused trajectories are final for v3-A7. Their completed updates stay in the full declared denominator (30 planned updates each), and the updates they did not run are reported as unmeasured, not as zero.
3. **B_1301** continues on one of GPUs 0, 5 and 7 until its `T5_30.json`. Its verdict is computed by the frozen v3 rule and reported as is. v3-A7 then ends.
   - There is no extension to 60, even on a FAIL, and no v3 main study.
   - This is the one change to v3-A7's plan. It is made before any T5 statistic exists, and it is disclosed in v3's results.
4. **v4 order.**
   - The technical gates (V4-T1, V4-G0, V4-T2, V4-T3, V4-T4, B audits) may start on GPUs freed by the pause.
   - The learning pilot (A, B and P on seeds 1301 and 1302) starts after B_1301's `T5_30.json` exists and its GPU is released, and only if every gate passed.
   - v4 never takes a GPU from a running v3 stage.
5. **Reporting.** The master messages the general coordinator at the pause, at B_1301's T5_30 verdict, and at the v4 pilot launch. v3's results record the pause time, every trajectory's completed updates and this amendment.

## What does not change

- v4's design, gates, thresholds, arms, inference and claims.
- v3-A7's frozen T5 rule and the code bound in its admission.
- Device rules: only idle authorized GPUs, and never another user's process.
