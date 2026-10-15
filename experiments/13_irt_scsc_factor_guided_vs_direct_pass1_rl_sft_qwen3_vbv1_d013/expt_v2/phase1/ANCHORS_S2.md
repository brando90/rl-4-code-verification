# Experiment 13 v2-S2 anchor generation and resource plan

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1/ANCHORS_S2.md>

**TLDR:** Generate the complete connected train panel under the admitted float16 condition: Base, half-schedule and full-schedule batch 1, each 539 tasks × 8 samples. Freeze calibration, item parameters and F2 before the separate full-schedule batch 2. Completed cells are immutable; each missing cell has at most one identical infrastructure retry. This prospective plan is published before any anchor generation.

Created: 10-14-2026. Condition: **v2-S2**. S1's measured LP-1 FAIL remains final. S2's original-probe confirmation PASS was published at `2b2f8b5`, after its lock at `f8ecbfa`. A5 is closed at 0.207209183243/3.0 device-hours; this later allocation does not reopen or reset that allowance.

## Scientific settings

The existing full manifests remain byte-identical: 4,312 cells per batch, train only, fixed task/sample seeds, thinking enabled, temperature 1, top-p 1, top-k disabled, 8,192 generated-token cap, no prompt truncation, maximum context 15,945, terminal token IDs 151643 and 151645, and batch size 32. Length-capped outputs remain eligible for the frozen strict scorer. No output is selected or regenerated using its score.

Models are the pinned Qwen3-4B-Base revision `906bfd4b4dc7f14ee4320094d8b41684abff8539`, the experiment-08 half-schedule export `step_334`, and full-schedule export `step_658`. Weight files and every export metadata file are hashed. Generation uses installed vLLM 0.10.0, float16 and the exact S2 engine/sampling constructor. The shared full-export tokenizer is passed explicitly for all three policies, preserving the already-rendered prompt tokens and decoding. The base and trained tokenizers have identical core vocabulary and normalized merges; the full export adds four special-token entries. All models have vocabulary size 151,936; the tokenizer's largest added-token ID is 151668, and the manifests' maximum prompt token ID is 151645. This avoids silently changing tokenization between anchors. No model weights or tokenizer vocabulary are resized.

Each claimed device first constructs the actual engine and produces one token for the same non-probe health prompt admitted under A4. This health output never enters calibration or a gate. Numeric `CUDA_VISIBLE_DEVICES` is resolved from the leased physical UUID at each launch and rechecked at each stage. The S2 frozen runtime and LP-1 code are preserved; new modules implement anchor-only orchestration.

## Prospective allocation

Use idle, unreserved devices on skampere1, skampere2 or skampere3 through the canonical experiment-13 registry. At most three devices serve independent policies concurrently; at least 40,000 MiB device memory, 64 GiB available host memory per simultaneous owned launch and 25 GiB free local storage are required. Check all compute processes, foreign registries and master reservations before each claim and repeat the hardware check immediately afterward. Historical leases and their accounting are retained.

The anchor-only ceiling is **144 device-hours for all four batches and their permitted recovery**, with each lease at most 2 hours. This is a prospective runaway ceiling, not a measured runtime prediction. The original PLAN estimate was 4–6 hours. The S2 development probe generated eight long responses in approximately 180 seconds after engine startup. Conservatively extrapolating that eight-response rate without assuming any benefit from batch 32 gives 26.95 hours per 4,312-cell batch, 107.8 hours for four batches and 134.75 hours with 25% reserve; rounding upward gives 144. Actual batch-32 throughput will be reported after the first fixed segment. The allowance includes preflight, model startup and cleanup. No external model-provider charge is incurred by this self-hosted generation. SNAP pre-approval authorizes this recorded allocation.

A segment handles at most 256 eligible cells, preserving batch size 32. It starts no new batch with 900 seconds or less left in its lease; the supervisor reserves 90 seconds for cleanup. Active lease reservations count against the phase ceiling. Different policies may occupy different devices, but the same policy cannot have two active leases. Missing or uncertain cleanup quarantines the lease. A depleted allocation is recorded honestly; no silent budget reset occurs.

## Durability and continuation

An exclusive durable attempt receipt is written before each call. Valid responses are individually retained even if another batch member is invalid. Completed cells are validated against their frozen identity and never called again. Missing cells may consume only their second identical attempt, with both receipts preserved; exhausted cells remain explicitly missing in the declared denominator. An interrupted controller must reconcile its prior lease and child identities before continuing. It cannot launch afresh on another host while a prior ledger may survive. Host selection is sticky after the first attempt.

Source, input, installed-version and model hashes are checked before execution. Every controller verifies that its exact lock is already published on main. A separate 15-minute poller supervises the three independent controllers under the existing owner watchdog; a busy device is a wait condition. Cron additions preserve every installed line and have a reboot entry. Raw generations, task identities and cell ledgers remain private. Public receipts contain counts and hashes only.

The first three batch locks admit generation only. Each completed batch needs a separate published scoring lock. Calibration and item parameters are then frozen, including F2=0.75 and the already-published G1 method lock. Full batch 2 requires those published prerequisites; no initial launch plan admits it. No actual-data fit, hypothesis statistic or optimizer update is part of this generation freeze.
