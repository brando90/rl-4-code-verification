# expt_v5 protocol: Night 5, Night 4 replicated on independent start checkpoints (frozen before any RL)

**TLDR:** Night 4's changed law (Eq. 7 plus the target-alignment term alpha) beat uniform random at n4, but rested on one start checkpoint per scale and three seeds, and the trivial rule "best environment on n3" did best. Night 5 reruns the identical pipeline on freshly pretrained start checkpoints to see whether that result survives a new draw of the start policy. Nothing about the law, rules, strength, seeds, budgets or decision rule changes.

Written 10-26-2026 11:00 PDT by ultimate_brando9, after pretraining was launched and before any probe, alpha or GRPO step of Night 5.

## What is new
- Start checkpoints: `E16_PRETRAIN_SEED=1` (default 0 reproduces Night 2/4 byte for byte): model init seed 1234+1, pretraining-document draw seed 7+1 (same concept bank, family_seed 1), pretraining batch-order generator seed 1. Steps per scale unchanged (2000/2500/3000/4000).
- RL strength S2 (Adam lr 3e-4, KL 0.1) is reused from Night 4's frozen receipt (`rl_setting.json` + sha256 copied unchanged); no new pilot, so no new tuning on the replicate.
- Environments e00-e11 and Night 2's frozen mixtures m00-m03 copied unchanged. Target, prompt pools, budgets (12,800 / 25,600 / 51,200 tokens), seeds 0/1/2, alpha definition, probes, rules (law, law+alpha, alpha alone, best-fixed-n3, uniform random), bootstrap (2,000 draws) and the POSITIVE / NOT ESTABLISHED / NO ADVANTAGE rule are exactly `expt_v4/PROTOCOL.md`. Code: `expt_v4/night4.py` with `--out`, driver `night5.sh`.
- Environment difference to disclose: Night 4 ran numpy/torch of the Night 4 machine state; Night 5 uses venv `mrmr` (numpy 1.26.4, torch 2.14.1 CPU). Versions are recorded in each `n*_meta.json`.

## Pre-registered predictions (written before any Night 5 RL)
- P1: law+alpha's n4 regret interval stays below random's (POSITIVE again). Night 4: 1.08 [0.55, 1.82] vs 2.22 [2.03, 2.63].
- P2: law+alpha is not better than the plain law (paired interval contains 0).
- P3: "best on n3" has the lowest point regret at n4 again.
- Reading: if P1 fails, Night 4's POSITIVE was a property of one start checkpoint. If P1 holds, the changed law's advantage over random replicates but, with P2/P3, it is avoiding disasters, not picking the best environment.
- Decisive outcome is the same frozen rule on law+alpha vs random; nothing else is decisive.

## Hygiene
CPU only, nice 10, one thread per process, at most 4 concurrent processes, $0, no hosted inference. No outcome-based reruns, dropped cells, extra seeds or changed budgets; stages resumable, immutable per-cell files. The n4 forecast is frozen (`freeze`) before any n4 trajectory.
