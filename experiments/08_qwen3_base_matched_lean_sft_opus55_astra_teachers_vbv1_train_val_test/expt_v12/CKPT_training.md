# V12 training checkpoint

**Doc link:** [live results](results.md)

**TLDR:** Production current-data training is running; all later phases are owned by remote ordinary-code dispatchers.

## Current state

- Updated: 10-19-2026 06:11 PDT.
- Source owner: `/root/train_current_and_cleaned`; root owns publication.
- Remote root: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v12`.
- Frozen10,940 unique rows;13,168,888 loss tokens;5,470 updates; zero764-reference overlaps.
- Dataset SHA2566b0cce0608a11b2aa7d31e1343c6db0ba8ade08fdbd62ec68914884064a9df3e.
- Actual production trainee PID2075643, pipeline PID2073223, A100 GPU1; first actual update passed.
- Disposable longest16,112-token control passed peak38.36GiB, weights discarded before production reload.
- Sessions `rl4cv-corpus-current-v12` and `rl4cv-corpus-cleaned-v12`; second waits forV13completion without leasingGPU2.
- Starting checkpoint remains completedV6mixed; both branches fresh optimizer/same seed, order and one-pass rule; loss tokens can differ.
- Next commands: read current/run/progress.json, dispatcher.json and cleaned_dispatcher.json; pipeline automatically generates1080validationcells then CPU scores.
- Preserve other jobs, including4B onGPU6. Protocol/source/runtimehashes are frozen; amendments/newtrials required for changes.

## Event log

- 10-19-2026: user authorized current-data training plus parallel cleaned-data continuation; initial protocol recorded before updates.
- 10-19-2026 06:11 PDT: Data freeze, longest-sequence control and first production update verified; pipeline and cleaned watcher live.
