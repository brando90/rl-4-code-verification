# Experiment 25, expt_v1: stage 1 and stage 2 run record (AT-1787), 10-28-2026 to 10-29-2026

**TLDR:** The fp16 GRPO trainer with real strict (arm A) and smooth (arm B) reward, a per-update mismatch gate and CPU gradient accumulation is in `code/`. Stage 1 passes: it fits one 16 GB A4000 at the full 12,288-token length, and the in-loop gate passes for fp16 (0.104%) and aborts bf16 (4.09%). Stage 2 passes: the 2-update smokes of both arms ran with gate at most 0.07% and no NaN or inf. Update-0 validation of step_658 through the new scorer reproduces 53/1080 strict. Pilot and full run were not started.

Raw logs and gate reports: `results/stage1_2_at1787/`. Trainer: `code/train_e25.py` (sha256 49f239d8cdd57697d771e12b6a1893ad327e4da642261317ca7deb1c7c677917). Start checkpoint: Experiment 08 v1 step_658 converted to fp16 (`step_658_float16`).

## Evidence against the acceptance list
(a) **A4000 memory and time (mercury1, RTX A4000 16 GB, real vLLM, fp16, vLLM memory 0.5, logit chunk 1024, CPU gradient accumulation).**
- Real rollouts, 2 groups x 8 rollouts x 3,072 tokens (49,152 tokens, 16 trained sequences): update 165.7 s (generation 109 s at about 450 tokens/s, training 56 s). Real scoring was not exercised there (all 16 rollouts truncated, score 0).
- Full 12,288-token training length on the A4000: fits. nvidia-smi peak 12,411 of 16,376 MiB (`results/stage1_2_at1787/a4000_mercury1/runs_p1_mem.txt`), training 79.4 s for 8 sequences of 12,288 tokens (about 10 s per sequence), no NaN, parameter step applied. **This probe used synthetic rollouts of full length (`--debug-synthetic-len`, a debugging flag), so its gate share of 1.0 in `runs/p1` is meaningless and is not evidence.** torch peak statistics include the vLLM sleep pool and over-read (16 to 17 GiB), so nvidia-smi is the number to use.
- Extrapolation, not measured: a full update (16 groups, up to 128 sequences) is about 20 min of training plus 20+ min of generation on one A4000, so more than 40 min per update; a 48-update run on one A4000 is days per arm. The A100 is the practical trainer; the A4000s are for validation fan-out.
- Recorded deviation from the 16 GB-unmodified trainer: fp32 gradient buffer replaced by GPU fp16 micro-batch gradients flushed to CPU fp32; vLLM memory 0.5.

(b) **Precision gate inside the trainer loop (A4000, mercury1, same 49,152-token setup).**
- fp16, loss scale 16384: share of tokens with abs logprob delta above tolerance 0.104% (51 tokens), max abs delta 0.115, no non-finite values, pass. Full-softmax share 2.53% (diagnostic only; the gate follows the Experiment 20 truncated-support definition).
- bf16, loss scale 1: gate 4.09% (1,985 tokens), above 1%, run aborts with rc=3 and no optimizer step (`ABORT.json`). Stage 0 separate-process probe gave fp16 0.111%.
- Decision: fp16 with fp32 master weights.

(c) **2-update smoke, both arms (skampere1 A100 80 GB, job-7ccb1561, fp16, real local scorer, 12,288 tokens, 4 groups x 8 rollouts per update).** Both exit rc=0 and `RUN_DONE`.
- Arm A (strict), GPU 0, 1915 s wall: update 1 had 1 of 4 groups active (3 strict successes of 32), 8 trained sequences, gate 0.039% (full softmax 0.85%), IS min 0.841 and max 1.054, grad norm scaled 55, no non-finite. Update 2 had 0 active groups (0 successes), so no trained sequences, gate 0.065%. Max gate 0.0652%, pass.
- Arm B (smooth, adapter-strict), GPU 2, 2218 s wall: update 1 identical rollouts to arm A (242,770 tokens, 3 strict successes), mean smooth 0.109, 16 trained sequences, gate 0.039%, IS 0.838 to 1.055. Update 2: mean smooth 0.0070, 0 strict, 16 trained sequences, IS 0.820 to 1.113, gate 0.053%. Max gate 0.0529%, pass. No NaN or inf in either arm. Arm A update 2 not training is the expected strict-reward behaviour when every sample fails.
- Per update on the A100 (shared GPU, another user's job was on GPU 0): 365 to 1746 s depending on how many samples reach Lean; scoring dominates (up to 1508 s for 32 rollouts).
- Recorded deviation: 4 groups per update instead of 16, GPUs 0 and 2 with vLLM memory 0.35. GPU 0 was shared with another user's process (about 41 GB), nothing of theirs was touched.
- Note for the pilot: full-softmax mismatch is 0.85% to 0.95% on the 12,288-token A100 runs, close to 1%. The gate (truncated support, Experiment 20 definition) is far below. Decide in the pilot whether to also watch the full-softmax share.

(d) **Update-0 validation through the new pipeline.**
- Saved step_658 validation generations (8 job dirs) rescored through the local scorer: **53/1080 strict, pass@1 0.0491, 20 of 135 tasks pass@8: exact match to Experiment 08's 53/1080 (QA item 9).**
- Fresh fp16 generation of step_658 (A100, 3,571 s) scored locally: 46/1080 strict (0.0426, 21 of 135 tasks pass@8). The 7-cell difference is generation noise from fp16 sampling, since the scorer is the same; it is one sample of 8, not a bias estimate. The update-0 baseline for the experiment should use the fp16 pipeline number.

## Findings about the setup
- A job launched with `ssh_launch` on skampere1 has no Kerberos or AFS ticket, so it cannot ssh to mercury; mercury work ran in foreground commands of at most 280 s, and long mercury runs need a launch on mercury itself.
- A real training run is not started anywhere.
