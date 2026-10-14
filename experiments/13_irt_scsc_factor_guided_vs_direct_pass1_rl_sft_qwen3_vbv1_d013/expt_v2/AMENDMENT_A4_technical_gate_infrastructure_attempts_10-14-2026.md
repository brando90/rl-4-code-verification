# Experiment 13 v2 amendment A4: technical-gate attempts that fail on infrastructure before measuring anything

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/AMENDMENT_A4_technical_gate_infrastructure_attempts_10-14-2026.md>

**TLDR:** LP-1 attempt 1 stopped during vLLM engine construction, after 52.5 seconds of device time. The launcher had put the GPU's UUID in `CUDA_VISIBLE_DEVICES`, where vLLM 0.10.0 expects an integer index. It produced 0/8 responses and computed none of LP-1's statistics ([RESULTS_LP1.md](RESULTS_LP1.md)).

A4 lets an attempt of a **technical** gate that stopped on a reproducible infrastructure defect, **before computing any admission statistic**, be rerun after a verified fix:

- at most 3 attempts per gate;
- every scientific setting byte-identical;
- every attempt published.

An attempt that computes its admission statistics is final, whether it passes or fails. The scientific gates keep the strict no-retry rule.

**Status:** ADOPTED 10-14-2026 16:16 PDT by the version 2 master (Claude Code `claude-opus-5-5`, session "Oct 9: IRT for eval metric decomposition"), as coordinator. A1 and A2 were adopted the same way.

**Disclosure:** A4 was written after LP-1 attempt 1 was published (`50cf118`, `10335d1`). That attempt measured no probe response, token, trainer probability or admission statistic. A rerun therefore cannot select on any LP-1 outcome.

## Why

The no-retry rule after L1v2 stops outcome-dependent retries, the forking paths that would inflate the chance of passing a gate. An attempt that measured nothing has no outcome to select on.

The frozen design already distinguishes the two cases. The L1v2 lock permits "one identical infrastructure retry" per cell, and A1 treated R0 and R1 as fix-and-rerun development tests. A UUID-for-index defect is deterministic, so an identical retry fails again; only a fixed launcher can measure LP-1. Ending the experiment on this defect would leave the hypothesis untested for a reason unrelated to it.

## Rules

1. **Scope.**
   - **Covered:** the technical admissions LP-1, LP and T1–T4 (PLAN §§ 5–6, PROTOCOL § 6).
   - **Not covered:** G1, H2, F2 and the other forecast checks, the T5 learning gate, L2, the pilot and main learning runs, and the test evaluation. These keep the no-retry rule unchanged.
2. **Which attempts are INCOMPLETE-INFRA.** An attempt that ends before computing any of its admission statistics because of a reproducible launcher, environment or infrastructure defect, recorded in its private logs. Examples:
   - engine construction or device-binding errors;
   - an out-of-memory error before the first scored response;
   - node loss;
   - a crashed dependency.

   For LP-1, the admission statistics are the unsupported-token count, the median and 99th-percentile absolute log-probability errors, and the importance-ratio truncation fraction.
3. **Fix before the rerun.**
   - The fix changes no scientific setting. The probe set and its seeds, sampler, token caps, thresholds, checkpoints and their hashes, scorer, and resource caps stay byte-identical, bound by hash.
   - A regression test reproduces the defect and passes with the fix.
   - A preflight check covers the defect's failure class.
   - The fix, its tests and a successor lock (for LP-1: `locks/LP1_A4.json`) are pushed before the rerun. The lock names each changed binding and why, and binds every unchanged binding at its previous hash.
4. **Rerun.**
   - The rerun is the next numbered attempt of the complete gate.
   - Failed attempts stay published. Their device-hours count against the gate's frozen per-attempt cap and cumulative allowance, which are unchanged.
   - Outputs of failed attempts never enter any statistic.
5. **Bound and finality.**
   - A gate gets at most 3 attempts, counting attempt 1.
   - A third INCOMPLETE-INFRA attempt stops the gate as INCOMPLETE, and that stop is published.
   - An attempt that computes its admission statistics is final, PASS or FAIL, and is never retried.
6. **Generation batches.** The anchor panel and batch 2 keep the frozen per-cell ledger rule from L1v2: one identical infrastructure retry per missing cell, and no completed cell is ever regenerated.

## Application to LP-1

- **Attempt 1** is INCOMPLETE-INFRA: 0/8 responses, 0 tokens, 0 trainer evaluations and every admission statistic unmeasured, after 0.014593276 device-hours.
- **Attempt 2** is admitted after rule 3. The preflight must:
  - map the leased UUID to its numeric index from `nvidia-smi`;
  - check that `CUDA_VISIBLE_DEVICES` holds that integer;
  - construct the engine on the claimed device with a non-probe prompt before the attempt counts.
- **Every later launch path** gets the same fix and test: the anchors, LP, T1–T4, the pilot and the main runs.
- **Device time.** Attempt 2 stays within the LP-1 lock's 0.5 device-hour per-attempt cap and its 0.6 device-hour cumulative allowance (0.014593276 already used).

G0 PASS, every frozen forecast, every later gate threshold and the original LP-1 record are unchanged.
