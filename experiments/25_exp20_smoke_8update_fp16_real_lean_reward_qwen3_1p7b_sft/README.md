# Experiment 25: 8-update fp16 smoke with the real Lean reward (Qwen3-1.7B SFT)

Status: finished 2026-10-30 (ultimate_brando9 for Brando). Sherlock job 49639114 (gpu, 1 H100 SXM5): COMPLETED, exit 0, 1:45:05 wall, started 2026-10-30 06:49 UTC-7, 8 of 8 updates. Diagnostic smoke; touches no frozen gate (Exp 20's gate stays: <=1% of completion tokens with |logp_trainer - logp_vLLM| > 0.05 or outside the recomputed sampling support).

## Question
Exp 24 ran 8 updates of the fp16/fp16 lane with a stand-in reward (1 if the extracted Lean file has a theorem/lemma and no `sorry`). With the real frozen Lean strict reward instead: (1) does the gate (share of completion tokens with |logp_trainer - logp_vLLM| > 0.05 or outside the recomputed sampling support) stay <= 1% in every update; (2) is training finite; (3) how does the real reward differ from the stand-in, rollout by rollout?

## Setup
Exp 24's recipe unchanged: Exp 20 trainer, TRL 1.16.0 colocated vLLM 0.30.0 (Apptainer image vllm-openai_v0.30.0.sif), arm A, seed 0, 16 groups x 8 = 128 rollouts per update, thinking on, T=0.6, top-p 0.95, top-k 20, max 12288 new tokens, `--smoke`, 8 updates. Start policy: Qwen3-1.7B SFT (expt_v4 seed 20260831 hf checkpoint), `config.json` dtype set to float16 (weights symlinked; `code/setup.sh`); trainer float16, fp32 master weights and AdamW, lr 1e-6, grad clip 1.0, static loss scale 16384. Reward: the frozen Lean scorer (`score_e20.sh` / `score_scsc.py --skip-tc`, strict kernel-binary) run on Sherlock CPUs inside the job, no `--reward-proxy`. `code/train_e25.py` = Exp 24's `train_e24.py` plus one field `proxy_e23` in each rollouts row (the stand-in value computed from the same extracted Lean file), so the reward-vs-stand-in difference is measured on the same rollouts. Diff: `code/train_e25_vs_e24.diff`. Job script: `code/e25.sbatch`. Full state saved every 4 updates; the script resumes from `state_latest` if a second job is needed.

Hardware differs from Exp 24 (A100-SXM4-80GB on skampere1): H100 SXM5 80 GB on Sherlock, so generations are not bitwise comparable to Exp 24.

## Results
Summary: gate passes in all 8 updates (max 0.0573%, 17.5x under 1%); training is finite throughout; the real Lean reward is far stricter than the stand-in: 50 of 1,024 rollouts (4.9%) pass strict, against 809 of 1,024 (79.0%) for the stand-in, so with real reward only 19 of 128 groups carried a learning signal (0 unresolved measurements).

### Gate (truncated support), per update, vs 1%
share = (in-support tokens with |delta| > 0.05 + sampled tokens outside the recomputed support) / generated tokens. Computed from `results/log.jsonl` (`train_mismatch_truncated_support`) by `code/analyze_e25.py`; the job's own check (`results/smoke_logprob_check.json`) gives the same max, 0.0573%, pass.

| update | tokens | outside support | abs delta > 0.05 | gate share | mean abs delta | max abs delta | gate |
|---|---|---|---|---|---|---|---|
| 1 | 802,641 | 21 | 438 | 0.0572% | 0.00055 | 0.175 | pass |
| 2 | 884,734 | 18 | 389 | 0.0460% | 0.00048 | 0.247 | pass |
| 3 | 693,436 | 17 | 375 | 0.0565% | 0.00057 | 0.313 | pass |
| 4 | 698,324 | 10 | 314 | 0.0464% | 0.00051 | 0.230 | pass |
| 5 | 621,759 | 12 | 343 | 0.0571% | 0.00063 | 1.026 | pass |
| 6 | 760,664 | 21 | 387 | 0.0536% | 0.00056 | 0.940 | pass |
| 7 | 665,189 | 17 | 353 | 0.0556% | 0.00057 | 0.278 | pass |
| 8 | 685,807 | 12 | 381 | 0.0573% | 0.00058 | 0.396 | pass |

Gate value (max over updates) 0.0573%, 17.5x under 1%. Exp 24 (stand-in reward, A100): max 0.0783%; here 0.0460-0.0573%, no upward trend over 8 updates. Largest single |delta| 1.026 (update 5); 0.940 at update 6.

### Finiteness and drift (fp16 training)
| update | seqs backprop | nonfinite seqs | nonfinite params | grad norm | max scaled grad | IS min/max/mean | loss | max abs (fp16 - master) |
|---|---|---|---|---|---|---|---|---|
| 1 | 24 | 0 | 0 | 0.0356 | 20.0 | 0.805 / 1.066 / 0.9969 | 0.009 | 1.0e-06 |
| 2 | 8 | 0 | 0 | 0.0160 | 15.6 | 0.809 / 1.045 / 0.9960 | 0.000 | 2.0e-06 |
| 3 | 8 | 0 | 0 | 0.0243 | 13.5 | 0.865 / 1.063 / 0.9963 | -0.000 | 3.0e-06 |
| 4 | 32 | 0 | 0 | 0.0442 | 27.1 | 0.716 / 1.096 / 0.9965 | 0.006 | 4.0e-06 |
| 5 | 24 | 0 | 0 | 0.0469 | 22.3 | 0.849 / 1.088 / 0.9973 | 0.022 | 5.0e-06 |
| 6 | 8 | 0 | 0 | 0.0186 | 14.4 | 0.855 / 1.052 / 0.9959 | 0.001 | 6.0e-06 |
| 7 | 32 | 0 | 0 | 0.0505 | 34.1 | 0.784 / 1.103 / 0.9976 | 0.028 | 6.9e-06 |
| 8 | 16 | 0 | 0 | 0.0333 | 13.9 | 0.778 / 1.100 / 0.9961 | 0.002 | 7.9e-06 |

- No non-finite sequences or parameters in any update, no skipped step. Largest scaled gradient 34.1 against the fp16 maximum 65,504 (about 1,900x headroom at loss scale 16384).
- Fewer sequences are back-propagated than in Exp 24 (8-32 vs 24-80 per update; 152 in total): a group has nonzero advantage only if its 8 rollouts differ in reward, and with strict reward most groups are all-zero. Grad norms are 0.016-0.050 (Exp 24: 0.07-0.13), loss near zero.
- Drift: last column grows by about 1e-6 per update (7.9e-6 at update 8), as in Exp 24; importance ratios stay within 0.716-1.103, mean 0.996-0.998.

### Real reward vs stand-in (same rollouts, `results/rollouts.jsonl`)
All 1,024 rollouts have status `measured`; `unresolved_measurement`: **0** (none hidden). `proxy_e23` is the Exp 23/24 stand-in (1 if the extracted Lean file has a theorem/lemma and no `sorry`) computed from the same extracted file.

| | strict = 1 | strict = 0 | total |
|---|---|---|---|
| stand-in = 1 | 49 | 760 | 809 |
| stand-in = 0 | 1 | 214 | 215 |
| total | 50 | 974 | 1,024 |

- Agreement 263 of 1,024 (25.7%); disagreements 761: 760 where the stand-in says 1 and strict says 0, 1 the other way (update 3, task `security_set__security_6858__vulnerabilities__88_unsafebgproute`, 1,842 tokens, `lean_sha256` 31643cb9...; the extracted Lean text is not saved, so why the stand-in said 0 is not determined).
- Extraction: 810 rollouts have a Lean file (`file_blocks`), 214 have none (`no_lean_block`); the 214 are exactly the truncated-at-12,288-token rollouts. Of the 810 files, 50 pass strict (6.2%), 760 are scored and do not compile (`agent_compiles` false in the per-task scores); the 50 passes have no sorry, native_decide or phantom axioms. The stand-in marks 809 of the 810 files as 1 (it never compiles).
- Per update (strict / stand-in / both / stand-in only): 1: 8 / 100 / 8 / 92; 2: 2 / 83 / 2 / 81; 3: 6 / 102 / 5 / 97; 4: 11 / 99 / 11 / 88; 5: 7 / 111 / 7 / 104; 6: 2 / 102 / 2 / 100; 7: 8 / 107 / 8 / 99; 8: 6 / 105 / 6 / 99. Mean strict reward 0.0156-0.0859 per update (Exp 24 stand-in: 0.70-0.88).
- Learning signal: groups with nonzero advantage 3, 1, 1, 4, 3, 1, 4, 2 of 16 (19 of 128 groups, 14.8%). The 50 strict successes sit on 19 of the 128 distinct tasks (each update used 16 new tasks). `mean_smooth` is null in the log (smooth is not computed on this route; smooth is 0.0 only on the 214 no-file rollouts).

### Runtime and tokens
| update | active groups | strict succ | mean strict | gen tokens | truncated | no_lean | unresolved | gen s | score s | update s |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 3/16 | 8 | 0.0625 | 802,641 | 28 | 28 | 0 | 223 | 763 | 1042 |
| 2 | 1/16 | 2 | 0.0156 | 884,734 | 45 | 45 | 0 | 257 | 206 | 506 |
| 3 | 1/16 | 6 | 0.0469 | 693,436 | 25 | 25 | 0 | 192 | 686 | 909 |
| 4 | 4/16 | 11 | 0.0859 | 698,324 | 29 | 29 | 0 | 192 | 128 | 359 |
| 5 | 3/16 | 7 | 0.0547 | 621,759 | 17 | 17 | 0 | 172 | 686 | 893 |
| 6 | 1/16 | 2 | 0.0156 | 760,664 | 26 | 26 | 0 | 206 | 268 | 507 |
| 7 | 4/16 | 8 | 0.0625 | 665,189 | 21 | 21 | 0 | 182 | 700 | 921 |
| 8 | 2/16 | 6 | 0.0469 | 685,807 | 23 | 23 | 0 | 192 | 688 | 911 |

Totals over 8 updates: 5,812,554 generated tokens (mean 5,676 per rollout; 214 of 1,024 hit the 12,288 cap, 20.9%), 1,615 s generation, 4,125 s Lean scoring (CPU, inside the job; 128-763 s per update), 6,048 s summed update wall (generation + scoring + training; manifest `gpu_seconds` 6,047.6). Job wall 1:45:05 (train wall 6,274 s, incl. startup and checkpoint writes): about 1.75 H100 GPU-h. Scoring takes 1.3-4.0x the generation time in 6 of 8 updates (update 1: 223 s generation, 763 s scoring) and shorter in updates 2 and 4.

## Caveats
Eight updates, one seed, one start checkpoint (expt_v4 seed 20260831), lr 1e-6, so this is a numerics and reward-wiring smoke, not learning evidence: strict reward is 0.016-0.086 per update with no trend. H100 on Sherlock, not the A100 of Exp 24, so generations are not comparable bitwise. One strict/stand-in disagreement (strict 1, stand-in 0) is unexplained because the Lean text was not saved. Scoring time per update varies 128-763 s; the cause is not broken down. No bf16 lane. The Sherlock per-task score CSVs (64 cells, 34,496 rows, mostly `missing_output` rows for pack tasks not submitted) and the checkpoints stay on Sherlock. No gate changed; Exp 20 not resumed.

## Files
`code/` (train_e25.py, train_e25_vs_e24.diff, e25.sbatch, setup.sh, analyze_e25.py: `python3 code/analyze_e25.py results` regenerates the tables), `results/` (log.jsonl per-update log, rollouts.jsonl 1,024 rows, smoke_logprob_check.json, run_manifest.json, RUN_DONE; the Slurm job log job_49639114.log stays on Sherlock, not in this folder). Run dir on Sherlock: /scratch/users/brando9/rl4cv_sherlock/e20/e25/runs/A_s0 (checkpoints ckpt_u004, ckpt_u008, per-token e24_tokens_u00N.pt ~75 MB, scores/, jobs/).
