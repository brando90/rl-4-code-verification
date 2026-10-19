# Concise Lean curriculum training checkpoint

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v6/CKPT_tiny_training.md

**TLDR:** Three parallel continuations are authorized: 1.7B existing-data control, 1.7B augmented and 4B augmented, followed by complete validation. All three trainers are making updates. The 1.7B comparison publishes independently of the longer 4B run.

## State

- Updated: 10-19-2026 01:30:12 PDT. All three training processes are alive; no trainers have been restarted.
- Owned checkout: `/Users/lethan3/Documents/veribench-projects/tmp/rl4cv-tiny-training-10-19-2026`; leave the original checkout's eight unrelated edits alone.
- Remote root: `/lfs/skampere1/0/eth127/rl4cv_tiny_training` on skampere1, user eth127.
- SSH: use ControlMaster `/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control`, held by local tmux `ssh-tiny-training`. The old `ssh-skampere1-eth127` transport has unusable stdout; do not use it.
- Execution: remote tmux `rl4cv-tiny-training`; supervisor PID 2922150; GPUs 1/2/6 run 1.7B control/1.7B augmented/4B augmented. Other owners' jobs and registries are unchanged.
- Trainers: 2927715 / 2927618 / 2941031, respectively. Verify PID start times against execution receipts before any process action.
- Data: corrected 500 examples passed compilation, kernel, format, differential and contamination checks; original V5 remains pristine. Existing pool 2,585. Exact frozen identities are in PROTOCOL.md and results/protocol_lock.json.
- Gate: 1,366 tests passed, 24 skipped and six subtests passed; no shared environment or test source modified. Exact 135 validation prompts and positive/negative scoring controls passed.
- Remote `rl4cv-tiny-primary-results` independently publishes the 2,160-cell 1.7B comparison when all 16 scoring jobs finish. Full analysis remains 3,240 cells; test evaluation is unopened.
- Remote `rl4cv-tiny-4b-extended-wait` enforces the prospective 12-hour 4B allowance. It can intentionally pause only the idle supervisor after primary scoring while the 4B trainer continues. See AMENDMENT_4b_wallclock.md.
- Local `rl4cv-tiny-training-watch` mirrors progress every minute; `--publish` permits milestone commits of explicitly owned evidence and defers if another owner advances main. Never run concurrent Git writers.
- 4B currently uses CPU float32 master weights and unfused CPU AdamW. A separate CPU-only fused-kernel benchmark is recorded; it has not changed training, its optimizer or its state. Do not silently change frozen source experiment.py.
- Next: complete training, generation and all validation scoring, inspect summaries and publish the measured comparison. Any 4B kernel change needs a checkpoint-preserving continuation, explicit runtime amendment and reconciled process/watch identities.
- No provider calls or messages to others are used. All model computations use the three authorized A100s.

## Event log

- 10-19-2026: User requested the two conditions in parallel after discussing the control's purpose and full-validation cost; parallel plan restored prospectively before updates.
- 10-19-2026: Added the user-requested 4B augmented condition, prospective CPU offload implementation, and three-system validation manifest; human-only SSH reauthentication pending.

- 10-19-2026 01:08:53 PDT: New authenticated SSH ControlMaster verified after user login; no further password entry required while it remains live. All corrected 500 examples passed full compilation/kernel/differential/format/admission checks. Both model-size token/checkpoint preparations passed; 135/135 exact validation prompts, three real scorer controls and numerical CPU optimizer control passed. Source/protocol frozen before updates. Full repository gate reruns in an owned dependency layout after provisioning missing pytest/ripgrep and optional-fixture paths; no test source changed. Next: commit the frozen source, launch all three isolated smoke/training/validation pipelines, and verify optimizer progress.

- 10-19-2026 01:11:11 PDT: Parallel GPU pipelines launched under remote tmux `rl4cv-tiny-training`. 1.7B control and mixed longest-sequence checks passed (about 38.36 GiB peak for control); both full training processes started. 4B longest-sequence check is active on device 6. Full Linux gate passed: 1,366 passed, 24 skipped, six subtests passed; optional experiment-13 private integration fixtures use their documented unavailable-prerequisite skip. Source/protocol local freeze commit: `ef92ac739dcc782040abfcd7a9bdff6af1d47718`. No other user jobs/registries changed.

- 10-19-2026 01:18:55 PDT: All three real trainers verified making updates. Early 1.7B throughput predicts about 45–60 minutes training; 4B CPU-offload updates take 30–44 seconds and predict roughly 9–11 hours. Added prospective wall-clock-only 4B extension to 12 hours with a tested independent guard; healthy trainer, tokens, optimizer and RNG remain untouched. Guard publishes the primary 1.7B comparison before waiting for 4B. Wait/reap control passed; exact identities and all pause/resume events recorded remotely. Local watcher mirrors live results every 60 seconds.

- 10-19-2026 01:30:12 PDT: Added independent primary-results watcher and serialized analysis publication; verified milestone publisher against a temporary Git remote, including unrelated concurrent main advancement. CPU fused optimizer kernel investigation leaves healthy trainers unchanged. Updated the durable state to the actual working SSH transport and running pipelines.
