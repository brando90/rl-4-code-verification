# Sherlock training completed results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4/results.md>

**TLDR:** Both fixed-seed training runs in `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4` completed 658/658 updates and exported checkpoints. All 1,316 step records passed verification; the collector hash-verified 36 files in persistent storage. Total allocation was 2.1203 of the eight permitted graphics processing unit (GPU) hours.

**Status:** COMPLETE — 2/2 declared trajectories, both training jobs and terminal collector COMPLETED 0:0.
**Last verified:** 10-18-2026 21:21 PDT

The frozen [protocol](PROTOCOL.md) execution criterion passed: each seed consumed all 1,315 admitted examples and 5,752,936 assistant loss tokens exactly once. Across the two runs that is 2,630 example exposures and 11,505,872 loss tokens, with finite metrics and nonzero gradients on every update. The corpus contains 476 VeriBench V1 training tasks. Validation remains unmeasured and test unopened; these execution measurements establish no held-out accuracy or formal-correctness result. Statistical intervals and significance are not estimated from two training trajectories (p-val=n/a).

- **Seed 20260830:** 658/658 updates; last-batch training loss 0.170871; training-loop time 3,703.60 seconds; GPU allocation 01:04:20 (3,860 seconds); peak allocated device memory 57.66 GiB. [Result](results/20260830/result.json), [all steps](results/20260830/steps.csv), [export hashes](results/20260830/weights_manifest.json).
- **Seed 20260831:** 658/658 updates; last-batch training loss 0.269843; training-loop time 3,610.89 seconds; GPU allocation 01:02:53 (3,773 seconds); peak allocated device memory 56.18 GiB. [Result](results/20260831/result.json), [all steps](results/20260831/steps.csv), [export hashes](results/20260831/weights_manifest.json).

The loss values describe different final training batches; they are not a held-out comparison or a basis for selecting a seed. [Machine-readable seed summary](results/seed_summary.csv). Both used one NVIDIA H100 80 GB at a time. Preparation 48377554, training 48378536/48378539 and collector 48378541 all finished successfully. The collector ended at 17:56:16 PDT on 10-18-2026. Total GPU allocation was 7,633 seconds, including startup/export; provider spend was $0. No training trajectory was repeated or substituted.

## Export and persistent storage evidence

The [terminal receipt](results/terminal_receipt.json) and [archive manifest](results/archive_manifest.json) record 36 scratch-to-persistent file hash matches, including both full training states and both 12-file Hugging Face exports. They reside under `/home/groups/sanmi/brando9/rl4cv_sherlock/expt_v4/runs/<seed>/`. The terminal receipt and manifest are also retained inside the persistent `results_bundle.tar.gz`.

[Independent persistent verification](results/persistent_verification.json) confirmed all 36 files exist with matching sizes, rehashed the 30 metadata/tokenizer files, and checked both checkpoint configurations against the pinned Base configuration. All four model shards have valid safetensors headers, contiguous tensor offsets, float32 storage, index correspondence and complete 28-layer coverage; each export contains 310 stored tensors representing 1,720,574,976 parameters. Full-weight hashes come from the collector's verified copy; no second full-model load or inference evaluation was performed.

The downloaded 6,422,908-byte results bundle matches both scratch and persistent storage: SHA-256 `6d1eadbe6417b48f15bb54cf5d27b9be95da5acc5e0b940c999d15e118fe8da2`. [Collection verification](results/final_collection_verification.json) checks exact corpus, source, token and order identities; both complete step tables; terminal scheduler outcomes; and absence of inspected failure markers. The final progress files retain their last pre-export RUNNING label; completed result and scheduler receipts establish the terminal outcome.

The exact frozen model revision, token admission and source hashes remain in [preparation](results/prepare_receipt.json) and the two result receipts. Prior unchanged-code verification: [full Linux log](results/make-test-linux.txt), 1,382 tests plus six subtests passed, three skipped; three terminal-state controls passed. Collection assertions passed on the completed artifacts. Initial [launch receipt](results/initial_training_receipt.json), [launch visual evidence](results/sherlock_training.png) and [first-seed monitor](results/first_seed_completion_monitor.json) remain as historical evidence.

## Reusable access and closeout

The existing private runner is online. An independent [workflow command](https://github.com/brando90/sherlock-agent-bridge/actions/runs/39198620248) returned `brando9` on `sh03-01n69.int` with exit code 0 and no Duo prompt; [verification receipt](results/agent_access_verification.json). Authorized agents can use `sherlockctl exec 'hostname; id -un'` and submit substantial work through its own Slurm allocation. [Shared access guide](https://github.com/brando90/agents-config/blob/main/machine/sherlock-agent-access.md). Other agents' access services and jobs were preserved.

[Google companion](https://docs.google.com/document/d/1S1FgSRRSzVmh4bF8XBtaNnYupBeaHsrjmP0dLwwL1eM/edit) still shows the earlier partial status: its update returned 403 PERMISSION_DENIED for connected account `brando@vals.ai`; [sync receipt](results/google_companion_sync.json). Editor access or reconnection as the owner is required. The single [completion email](results/done_email_receipt.json) was sent at 21:25:05 PDT on 10-18-2026, message ID `1a15267ee2fc1c9a`, with all four required blind-copy recipients verified. START message ID `1a15110b6da2f189` is retained for deduplication. The finished training [monitor is PAUSED](results/monitor_closeout_receipt.json); no further training checks or reruns are scheduled by it.

Collaborator update: Both Sherlock replications finished all 658 updates, and I’ve preserved the complete trajectories and hash-verified checkpoints in persistent storage. The run used 2.12 GPU-hours; held-out performance remains unmeasured.

**TLDR-end:** [rl4cv: Sherlock training] `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v4` completed both declared training trajectories and persistent checkpoint verification within the eight GPU-hour limit; the shared private command route is live.
