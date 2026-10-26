# V19 GX10 training checkpoint

**Doc link:** [live results](results.md)

**TLDR:** SNAP's duplicate watcher is fenced. Artifact relay/Astra training port are separately owned; this worker owns actual controls, final training, inference and scoring.

## Current state

- Updated10-19-2026; owner `/root/train_current_and_cleaned`, root publishes.
- Local home: `experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v19` in `.worktrees/rl4cv-sol-repair-10-19-2026`.
- GX10 home: `/home/lethan3/workspace/rl4cv-gx10/experiment-v19`.
- Environment: `.../training-v14/.venv`, Torch2.9.1+cu130/Transformers4.55.4; full-model control pending.
- Starting weights: V6 mixed1.7B, initial manifest0acf7b913175e58d9bc3ead57bd0c0eb0a71669f494918cef404dec77dc9ee7b.
- Interim data:10,940 rows/818 replacements/13,420,616tokens, smoke only.
- Final production data: V18 full remaining1,540 cleanup; honest unresolved exclusions explicit, no mislabeled original fallbacks.
- SNAP idle watcher2110195 fenced at1792431426.449; no cleaned actual updates/pipelines existed.
- Relay and Astra port: `/root/unattended_and_gap_sources`, single writer; do not duplicate7GB transfer.
- SNAP SSH master dropped10:40; root is restoring human password session. No new SNAP probes until notified. Remote jobs persist; GX10 SSH is independent.
- This worker owns GPU Transformers fallback and frozen native-kernel scoring; exact small evaluation bundle manifest being prepared.
- Next: finish local portable evaluation code/protocol, receive relay/port paths, run real full1.7B longest-sequence disposable update, then wait for final V18 data.

## Event log

-10-19-2026: FirstV12 complete120/1,080; full851-output compiler diagnosis and971-output tactic audit documented.
-10-19-2026: GX10 migration explicitly authorized; SNAP idle second-run watcher fenced without touching foreign jobs.
-10-19-2026: Root selected hardware control now and finalV18 condition later; no interim818 production run. Prospective host/runtime/inference differences recorded.
