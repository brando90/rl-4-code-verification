# Idea: choose the GRPO group size G from the start policy's pass@1 distribution

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/ideas/grpo_group_size_vs_start_pass1/README.md>

**TLDR:** Brando (10-20-2026) noticed that rl4cv inherits G=8 from Varun's ICLR RL-environment paper. When the start policy's pass@1 is low (Lean SFT gives roughly 10%), a larger G may give GRPO more learning signal at the same rollouts per update. This is an idea to validate, **not** a rule. Keep it out of the repository's agent instruction files until the pass@1 ranges where each G works are validated.

## Why it might help

GRPO learns only from mixed groups. A group of G samples on a task with per-sample success p is mixed with probability 1 − p^G − (1 − p)^G. A larger G helps exactly the tasks with low but nonzero p, which is the low-pass@1 regime.

## First estimate (existing data, no new calls, 10-20-2026)

The data is experiment 13's A6 pipeline diagnostic: start policy `sft_4B_f1p0`, historical sampler (temperature 0.6, top-p 0.95, top-k 20), 64 train tasks × 8 samples.

| Strict successes out of 8 | 0 | 1 | 2 | 3 | 5 | 6 | 7 | 8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Tasks | 51 | 2 | 3 | 3 | 2 | 1 | 1 | 1 |

These are expected nonzero-advantage samples per update, all at the same 256 rollouts per update:

| Assumed p for the 51 tasks at 0/8 | G=8 × 32 groups | G=16 × 16 groups | G=32 × 8 groups |
|---|---:|---:|---:|
| 0 (pessimistic) | 42 | 46 | 48 |
| 0.02 | 72 | 103 | 145 |
| 0.056 (Jeffreys posterior mean) | 117 | 169 | 219 |

**Takeaways.**
- The gain depends entirely on whether the 0/8 tasks have a small nonzero p, which 8 samples cannot resolve.
- G=16 is never worse here and is up to about 1.4× better.
- G=16 halves the distinct prompts per update. In the pessimistic case it also raises the chance of an update with no signal from about 0.6% to about 4%.

## How to validate

1. **Estimate the per-task p distribution.** Draw 32 or more samples per task on about 32 train tasks from the start policy, at the actual rollout sampler.
2. **Choose G by a rule fixed in advance.** At fixed rollouts per update, choose G to maximize expected nonzero-advantage samples, with a floor on distinct prompts per update.
3. **Test it.** Run a small matched pilot (G=8 vs the chosen G, same tokens) on train reward and validation pass@1.
4. **Map across regimes.** Repeat across start policies with different pass@1, to build the G-by-pass@1 map Varun described before any instruction-file rule.

Candidate first use: experiment 13 v4, as a pre-declared G-selection stage. This is awaiting Brando's OK.
