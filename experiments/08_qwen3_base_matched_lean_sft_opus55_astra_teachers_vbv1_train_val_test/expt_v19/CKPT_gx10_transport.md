# Experiment 19: GX10 artifact transport and Astra port checkpoint

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v19/CKPT_gx10_transport.md

**TLDR:** Two ordinary local watches are armed to launch one authorized Astra code port and transfer immutable training/evaluation artifacts after the existing Stanford Network Analysis Project (SNAP) Secure Shell (SSH) connection is authenticated. No model call, weight transfer or optimizer update has occurred through this deployment yet; full-model execution belongs to the training owner.

## Current state — 10-19-2026

- Owner: `unattended_and_gap_sources`; actual training, inference, scoring and host selection: `train_current_and_cleaned`.
- Source: this experiment's `arm_gx10_deploy.py`, `finish_gx10_deploy.py`, `run_astra_port.py`, `relay_artifacts.py`, `stream_artifacts.py`.
- Initial watch: local tmux `rl4cv-gx10-port-deploy-v19`.
- Completion/bundle watch: local tmux `rl4cv-gx10-finish-deploy-v19`.
- Status/log root: `/Users/lethan3/Documents/veribench-projects/tmp/rl4cv-gx10-transfer-v19/`.
- Current state: waiting for the existing authenticated control socket; no fresh gateway login attempts.
- Control socket: `/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control`.
- SNAP run: `/lfs/skampere1/0/eth127/rl4cv_tiny_training`; port root: `gx10_port_v19`.
- GX10 destination: `/home/lethan3/workspace/rl4cv-gx10/experiment-v19`.
- GX10 Python: `/home/lethan3/workspace/rl4cv-gx10/training-v14/.venv/bin/python`.
- Runtime: PyTorch 2.9.1+cu130, Transformers 4.55.4, ARM64 GB10 capability 12.1; different from the SNAP runtime.
- No initial weights or training-data files reached GX10 before the connection expired. Preserve any later partial files and receipts.

## Handoff contract

The initial watch launches exactly one `gpt-6-astra`, high-effort code-port CLI job in remote tmux `codex-rl4cv-astra-gx10-port-v19`. It uses the approved private lab-key path and the shared experiment 15 budget helper: adaptation purpose, reservation $40, observed-cost stop $3, timeout 900 seconds. The conservative maximum single-request exposure is $35.85; no other account/key fallback is authorized by this script. A configured local API-key payer was unverified and remains unused.

The worker sees only the frozen trainer, assembler, protocol and runtime facts. It produces `train_gx10.py` and `PORT_NOTES.md`. The completion watch transfers these exact bytes, checks hashes and syntax, then writes `code/port_ready.json` with `train_wrapper_sha256` and state `READY_FOR_SMOKE`. This marker establishes transport readiness; it does not replace the independent full-model control or establish optimizer equivalence.

The sole weight/data relay streams through two encrypted SSH connections without storing a local weight copy. Each received ordinary file is SHA-256 checked before atomic rename. Readiness is published only when the complete manifest matches. Bundle identities and SNAP manifest filenames are:

| Identity | Manifest | Purpose |
| --- | --- | --- |
| `initial` | `transfer_manifest_initial.json` | Exact version 6 mixed initialization, frozen trainer, immutable partial818 data used only for disposable smoke |
| `evaluation` | `transfer_evaluation.json` | Frozen validation instructions, prompt/extraction helpers, scorer, gold references and identities |
| `final` | `transfer_final.json` | Full experiment 18 accepted cohort, declared exclusions and every bound accepted proof receipt |

The completion watch copies `/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v19/production_host.json` byte for byte once it exists, preserving its hash. It never chooses a host. The training owner's cross-host phase grants and persistent chain govern all graphics processor use.

Invoke the wrapper for disposable smoke only after both the initial transfer and port-readiness markers exist:

```sh
/home/lethan3/workspace/rl4cv-gx10/training-v14/.venv/bin/python \
  /home/lethan3/workspace/rl4cv-gx10/experiment-v19/code/train_gx10.py \
  --root /home/lethan3/workspace/rl4cv-gx10/experiment-v19 \
  --condition partial818 \
  --frozen-source-dir /home/lethan3/workspace/rl4cv-gx10/experiment-v19/code/expt_v12_frozen \
  --smoke
```

## Recovery and limits

Both local watches use the control socket and `ProxyCommand=/usr/bin/false` for SNAP commands, preventing fallback to a new gateway connection. They poll every 15 seconds. Root owns the single pending human authentication step. Local watches and an unfinished relay require the Mac to remain available; no independent headless SNAP-to-GX10 authentication route has been established. After transfer, the training owner's native GX10 chain runs independently.

Inspect `deploy_launched.json`, `deploy_failure.json`, `finish_progress.json`, `finish_failure.json`, and each transfer completion before restarting a watch. Never launch a second Astra attempt or overwrite a different already-published wrapper or host decision. The receiver preserves incomplete `.transfer-partial` files; byte-range resumption is not implemented. Reconcile hashes and add a bounded missing-file recovery before repeating an interrupted large relay.

## Verification log

- 10-19-2026: Prepared single-writer relay, verified a 2.56 MB loopback transfer/hash/atomic-write control, and armed both local watches. Syntax checks pass. Added final-cohort and immutable host-decision handoff; no paid call or optimizer launched. The separate CPU-only Linux publication gate restored pinned external dependencies and passed the 40 previously affected tests; its final full-suite run is in progress.
- 10-19-2026: Full CPU-only Linux publication gate passed: 1,360 tests and 6 subtests passed, 30 skipped; all 9,587 tracked snapshot files and 469 pinned external assets verified. Full and compact receipts are in `results/linux_publication_gate.*`; failed-attempt logs remain preserved. Transport guards also passed actual local byte/hash/idempotence/rejection controls.
