# Experiment 13 v4: operational change to V4-A3, pausing one v3 run instead of five

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/OPERATIONAL_V4-A3_single_pause_10-21-2026.md>

**Status:** recorded 10-21-2026 at 11:35 PDT by the experiment 13 master, before any pause and before any v4 data. This changes the operations of [V4-A3](AMENDMENT_V4-A3_schedule_v4_start_and_v3_pause_10-20-2026.md) only. It changes nothing in the v4 protocol, its gates, its arms or its inference.

**TLDR:** Brando chose to pause exactly one v3-A7 run so that v4's technical gates can start. That run is **A_1302**, picked by the rule stated below before any pause. The other five v3 runs, B_1301 included, continue untouched.

## Decision and timeline (PDT, 10-21-2026)

- About 11:00: Brando wrote "Go do it and test it". The master armed V4-A3's five-run pause for 12:00:30, the earliest time the admitted tool allows.
- 11:13: Brando to the coordinator: "ps: don't pause things unless it's necessary...or I say it?"
- 11:14:48: on the coordinator's relay, the master stopped the pause loop before it acted. Nothing was paused or signalled.
- 11:15: the master's census found **0 of 24** skampere1–3 GPUs idle. skampere1 devices 0, 5 and 7 hold v3, and mercury1/mercury2 GPUs 0–7 are excluded for experiment 120. The master offered three options: pause all five, pause one, or no pause.
- About 11:2x: Brando's own choice, relayed by the coordinator: **"Pause one run only."** He is away rating for about 5 hours and asked that this be carried out without him.

## Pause rule (stated before choosing the run)

Pause the one v3-A7 run least needed for v3-A7's planned analysis. Never B_1301, whose T5_30 verdict is v3-A7's pre-registered gate.

1. **Arm A first.** A's strict reward gives about 1 active group in 32, so A's updates carry almost no reward signal. B and P are needed for v3's B-against-P reading.
2. **Within an arm, the replication seed 1302 before the primary seed 1301.**
3. **Tie-break:** the fewest completed updates. This loses the least completed work, and that run is the furthest from 30 updates.

**Result:** the rule selects **A_1302**, which had 5 of 30 updates completed at 11:08 PDT. As before, it is paused only at its own lease-wait boundary, with no running stage interrupted. Its completed updates stay in the full denominator, and the updates it does not run are reported as unmeasured.

## What this changes in V4-A3

- **Pause scope:** one designated run (A_1302) instead of five. The other five v3 runs continue under the v3 watchdog.
- **v4 gates:** they start once A_1302's pause is recorded. They compete fairly for idle authorized GPUs, through the same per-device locks as v3, and hold no standing reservation.
  - Six contenders (five v3 runs plus v4) then share skampere1 devices 0, 5 and 7, the same contention as today. B_1301's pace should therefore stay about where it is: T5_30 around 10-24 midday at the recent 5–9 hours per update.
  - The gate chain needs about 10–12 GPU-hours of work, run stage by stage, and each stage may queue.
- **v4 pilot:** it still needs 3 GPUs. It starts after B_1301's `T5_30.json` and only when idle authorized GPUs allow, or earlier only if GPUs free up for another reason. All v4 gates must pass first.
- **v3 after B_1301's T5_30:** V4-A3's rule that v3-A7 runs no extension to 60 and no main study stays as recorded. Any stop of a still-running v3 run at that point will first be confirmed with Brando, per his 11:13 message.

## Implementation

The admitted runner and pause tool hard-code the five-run pause. A Codex `gpt-6-astra` dispatch at ultra effort, per Brando's "when in doubt ask codex ultra max thinking", will:

- read the designated run from this record;
- release the gates when that one pause is recorded;
- re-admit, test and dry-run the change, without pausing anything or using a GPU.

The master then runs the pause tool for A_1302 and starts the gates. It sends the coordinator one line when A_1302 is paused and one when the first v4 gate starts.
