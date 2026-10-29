# Stage 2a dry run (Sherlock), Oct 29 2026

Agent: cc opus 5.5 xhigh (screen worker for AT-1791).

- Trainer: `train_e25ckpt.py` (Exp 24 fp16 trainer + dense checkpoints 16/32/48/64/96/128 never overwritten, `ckpt_record.json` per checkpoint, `steplog.jsonl` per update for rolling rho/H). Helper `steplog.py`, tests `tests/test_e25_stage2a_steplog.py` (7 pass).
- Dry run 1, job 50012468: FAILED exit 3 after 138 s. Not a trainer bug: the 1% log-prob gate fired because the Exp 20 start policy's `config.json` said float32 while the trainer ran fp16 (7.79% of tokens |delta|>0.05). Fix: `sherlock/stage2a_run.sbatch` now always rewrites the start dir's dtype to float16.
- Dry run 2, job 50104275 (e25_dryb, tiny: 2 updates x 2 groups x 1024 tokens, real strict Lean reward, fp16): COMPLETED exit 0 in 4m08 on sh04-07n11. Log-prob gate passed (share of tokens over tol 0.00128, mean abs delta 0.00134, max abs delta 0.081; 16384 of 16384 tokens in support). Checkpoints `ckpt_u001` and `ckpt_u002` written with `ckpt_record.json` and DONE markers; `steplog.jsonl` has 2 lines (one per update); `rollouts.jsonl`, `checkpoints_check.json`, `smoke_logprob_check.json` and `RUN_DONE` present.
- 8-update gate run, job 50104279 (e25_gate8, afterok on 50104275; 8 updates x 16 groups x 12288 tokens, checkpoint at 8): still PENDING in the Sherlock gpu queue (Oct 29 15:25).
- Stage 2b (pilot) is not started: it needs this gate run and 02A Stage D.
