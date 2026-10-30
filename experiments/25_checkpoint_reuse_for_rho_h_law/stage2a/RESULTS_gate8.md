# Stage 2a gate8b (Sherlock job 50104279, e25_gate8), Oct 29-30

Result: the run finished. Slurm labelled the job OUT_OF_MEMORY (exit code 0) because the memory cgroup killed a process after the run had ended.

- Updates 1-8 all in steplog.jsonl (8 lines), 1024 rollouts generated, ckpt_u008 saved with ckpt_record.json, checkpoints_check.json: present [8], missing [], incomplete [].
- Log-prob gate (smoke_logprob_check.json): share |delta|>0.05 = 0.00061, pass true.
- RUN_DONE written 01:56:51, checkpoint saved 01:56:08; Slurm logged "Detected 1 oom_kill event in StepId=50104279.batch" at 01:57:07, i.e. in teardown, 16 s after RUN_DONE. Peak 92.18 of 96 GB (96%), job wall 3:52:10, 13752 GPU-seconds.
- Seconds per update (update_seconds): 1989, 1893, 1417, 999, 1451, 1569, 3273, 1161 (mean about 1720).
- Strict successes per update: 12, 6, 3, 12, 4, 3, 10, 5.
- No rerun needed: outputs are complete and checked. For stage 2b the sbatch now requests --mem=128G (was 96G) so Slurm does not label a finished run as failed.

Agent: cc opus 5.5 xhigh
