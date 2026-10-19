# Concise Lean curriculum training checkpoint

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v6/CKPT_tiny_training.md

**TLDR:** Three parallel continuations are authorized: 1.7B existing-data control, 1.7B augmented and 4B augmented, followed by complete validation. All three trainers are making updates. The 1.7B comparison publishes independently of the longer 4B run.

## State

- Updated: 10-19-2026 02:16:25 PDT. Fused CPU AdamW is deployed and verified on the existing 4B trajectory; update 102 has completed.
- Owned checkout: `/Users/lethan3/Documents/veribench-projects/tmp/rl4cv-tiny-training-10-19-2026`; preserve original checkout's eight unrelated edits.
- Remote root: `/lfs/skampere1/0/eth127/rl4cv_tiny_training`, eth127 on skampere1.
- SSH ControlMaster: `/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control`, held by local tmux `ssh-tiny-training`. Do not use the old stdout-broken SSH session.
- Effective 4B owner: remote tmux `rl4cv-tiny-4b-fused`, controller PID 849764/start ticks 63914009. Fused trainer PID 976411; exact identity in execution/4b_mixed/training_fused.json. GPU 6 remains the only 4B device.
- Original checkpoint 100 and all 100 metrics rows retained exactly. Checkpoint inspection verified all 4,022,468,096 parameters and Adam steps; restore verified float32 masters/moments, bf16 shadows and CPU/CUDA random-number states. Source, batch order, token schedule and optimizer hyperparameters are preserved; only CPU kernel changed to fused=True.
- Latest verification: results/fused_handoff/deployment_verified.json. Early timing samples are sparse and sequence lengths differ; no overall speedup or validation-improvement claim yet. CSV elapsed joins model loops and excludes handoff/startup; wall-clock receipts retain all time.
- Both original 1.7B runs finished training: control 664 updates, augmented 904. Validation generation runs on GPUs 1 and 2. Full conditions remain 1,080 validation cells each, 3,240 total; test evaluation is unopened.
- Remote tmux `rl4cv-tiny-training` keeps the original augmented 1.7B generation/scoring pipeline. Its deliberate 4B -15 termination and zero-output control import failure remain in original receipts.
- Remote tmux `rl4cv-tiny-primary-recovery` runs the control's identical generation after owned dependency repair (SciPy 1.16.2, PyOpenSSL 26.4.0); both failed startup attempts retained. See AMENDMENT_generation_environment.md. Shared runtimes are unchanged.
- Remote `rl4cv-tiny-primary-results` independently publishes the primary comparison after all 16 primary scoring jobs finish. The recovery's scoring waits for the original supervisor; 4B scoring then waits for primary recovery, keeping at most eight scoring jobs at once.
- The fused controller owns final full analysis, explicitly reconciles only the planned/recovered original failures and retains unexpected failures. The original 12-hour total 4B training deadline is unchanged. The old process-specific wall-clock guard is retired.
- Local `rl4cv-tiny-training-watch --watch --publish` mirrors progress every minute and commits milestones when main has not advanced. One Git writer at a time; stop only this local observer before manual commits.
- Gate: repeated full Linux suite passed 1,366 tests, 24 skips, six subtests. Optimizer save/restore and real-process fencing/rejection controls passed. Exact prompts and scorer controls passed before training.
- Next: finish the three unchanged validation manifests, inspect primary/full summaries and publish the measured comparison. No provider calls or messages to others are used.

## Event log

- 10-19-2026: User requested the two conditions in parallel after discussing the control's purpose and full-validation cost; parallel plan restored prospectively before updates.
- 10-19-2026: Added the user-requested 4B augmented condition, prospective CPU offload implementation, and three-system validation manifest; human-only SSH reauthentication pending.

- 10-19-2026 01:08:53 PDT: New authenticated SSH ControlMaster verified after user login; no further password entry required while it remains live. All corrected 500 examples passed full compilation/kernel/differential/format/admission checks. Both model-size token/checkpoint preparations passed; 135/135 exact validation prompts, three real scorer controls and numerical CPU optimizer control passed. Source/protocol frozen before updates. Full repository gate reruns in an owned dependency layout after provisioning missing pytest/ripgrep and optional-fixture paths; no test source changed. Next: commit the frozen source, launch all three isolated smoke/training/validation pipelines, and verify optimizer progress.

- 10-19-2026 01:11:11 PDT: Parallel GPU pipelines launched under remote tmux `rl4cv-tiny-training`. 1.7B control and mixed longest-sequence checks passed (about 38.36 GiB peak for control); both full training processes started. 4B longest-sequence check is active on device 6. Full Linux gate passed: 1,366 passed, 24 skipped, six subtests passed; optional experiment-13 private integration fixtures use their documented unavailable-prerequisite skip. Source/protocol local freeze commit: `ef92ac739dcc782040abfcd7a9bdff6af1d47718`. No other user jobs/registries changed.

- 10-19-2026 01:18:55 PDT: All three real trainers verified making updates. Early 1.7B throughput predicts about 45–60 minutes training; 4B CPU-offload updates take 30–44 seconds and predict roughly 9–11 hours. Added prospective wall-clock-only 4B extension to 12 hours with a tested independent guard; healthy trainer, tokens, optimizer and RNG remain untouched. Guard publishes the primary 1.7B comparison before waiting for 4B. Wait/reap control passed; exact identities and all pause/resume events recorded remotely. Local watcher mirrors live results every 60 seconds.

- 10-19-2026 01:30:12 PDT: Added independent primary-results watcher and serialized analysis publication; verified milestone publisher against a temporary Git remote, including unrelated concurrent main advancement. CPU fused optimizer kernel investigation leaves healthy trainers unchanged. Updated the durable state to the actual working SSH transport and running pipelines.

- 10-19-2026 01:55:33 PDT: User explicitly authorized fused CPU optimizer deployment. Exact master/moment save/restore, five post-restore numerical updates and real-process checkpoint fencing/rejection controls passed. Source and operational amendment locked before handoff. Deploying persistent checkpoint-100 handoff on GPU 6; both original 1.7B pipelines continue under their original supervisor.

- 10-19-2026 01:55:38 PDT: Remote tmux `rl4cv-tiny-4b-fused` verified live, controller PID 328548/start ticks 63872417, state WAITING_FOR_CHECKPOINT, target 100. Source lock verified remotely before waiting. Original trainer 2941031 remains active; no original updates discarded. Both controls passed; full deterministic repository gate is rerunning before publication.

- 10-19-2026 01:58:40 PDT: Repeated full deterministic Linux gate passed before fused deployment publication: 1,366 passed, 24 skipped, six subtests passed, one warning, 187.47 seconds. Source, original trainer and original 1.7B pipelines unchanged.

- 10-19-2026 01:59:25 PDT: Refreshed only the waiting CPU handoff controller to include explicit CUDA-context-release and bounded startup checks; active controller PID 812018/start ticks 63894818. Initial waiter/source receipts retained remotely. No trainer restarted and no updates lost; target remains checkpoint 100.

- 10-19-2026 02:05:42 PDT: Fused handoff controller refreshed while still waiting, PID 849764/start ticks 63914009, to reconcile the control's generation startup recovery. All original completed updates preserved. Original control generation and first retry both failed on incompatible OS dependency fallbacks before any output; original receipts retained. Owned SciPy 1.16.2/PyOpenSSL 26.4.0 restore full model import and subprocess inspection. One extra startup attempt declared prospectively in AMENDMENT_generation_environment.md; exact same sampling/model/data. Remote tmux rl4cv-tiny-primary-recovery now starts the control's engine. All CPU scoring pools remain serialized. CSV records preserve original CRLF bytes through a scoped Git whitespace attribute.

- 10-19-2026 02:16:25 PDT: Deployed fused CPU optimizer successfully from verified checkpoint 100. Original completed metrics prefix is byte-identical, full-state/RNG restore passed and actual updates 101–102 completed with finite losses/nonzero gradients. Active trainer PID 976411 on GPU 6. Both 1.7B trained checkpoints are now in validation; owned dependency recovery preserved zero-output startup failures. Permanent verification receipts mirrored into results/fused_handoff.
