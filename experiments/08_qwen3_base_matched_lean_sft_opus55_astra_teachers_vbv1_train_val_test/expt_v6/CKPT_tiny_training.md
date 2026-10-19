# Concise Lean curriculum training checkpoint

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v6/CKPT_tiny_training.md

**TLDR:** Three parallel continuations are authorized: 1.7B existing-data control, 1.7B augmented and 4B augmented, followed by complete validation. Preparation is active; no training has launched.

## State

- Created: 10-19-2026 00:47 PDT. Last updated: 10-19-2026 01:08:53 PDT.
- Coordinator checkout: `/Users/lethan3/Documents/veribench-projects/tmp/rl4cv-tiny-training-10-19-2026`, detached at `8bf1200a1c7861debf89a5f0161df800ba442993`; preserve the original main checkout's eight unrelated dirty files.
- Cluster account: eth127 on skampere1; reuse authenticated local tmux `ssh-skampere1-eth127` via `tmp/tiny_remote.py`. Never interleave uploads and commands through this terminal.
- Remote run root: `/lfs/skampere1/0/eth127/rl4cv_tiny_training`.
- Inputs: existing expanded corpus 2,585; tiny 500; start expansion 1.7B step 667. Exact hashes and recipe in [PROTOCOL.md](PROTOCOL.md).
- Latest inventory: devices 1, 2 and 6 idle; other jobs on 0, 3, 4, 5 and 7. Recheck ownership and leases immediately before launch. Training memory estimated 40–70 GB/device.
- Available runtime: `/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python` works and imports torch 2.7.1+cu128 / Transformers 4.55.4. Generation runtime's interpreter symlink is private, but its site-packages import through `/usr/bin/python3` successfully (torch 2.13.0+cu130, Transformers 5.18.0, vLLM 0.30.0). Prefer a pinned consistent route after checks.
- Original validation pack symlinks resolve into a private brando9 directory. Rebuild/copy readable validation-only instructions and require every recorded version-3 prompt hash to match before generation.
- Source archive and experiment code are being copied to owned cluster storage. Durable preparation, training, exit monitoring and validation still need launch and verification.
- Next: finish preparation, freeze its exact receipt, run longest-sequence disposable update, start both isolated GPU jobs in parallel, verify actual optimizer progress, then finish complete validation and publish measured comparison.
- No provider calls, messages to others, or student training have occurred under this experiment.
- Transport blocker: the original SSH process (local pid 15875) has stdout redirected to `/dev/null`, so RPC output/acknowledgements cannot be observed. Do not assume any remote upload/preparation succeeded. Fresh named tmux `ssh-tiny-training` waits for eth127 CS password at the official gateway; the user has been asked to complete that human-only login. The fresh connection enables an owned ControlMaster socket for reliable subsequent transfer/execution. Do not send more commands through the old pane.
- Latest scope: user corrected 8B to 4B; add only 4B augmented, with float32 CPU master weights/AdamW state and bfloat16 GPU parameters, contingent on longest-sequence memory check. No extra 4B control was requested.

## Event log

- 10-19-2026: User requested the two conditions in parallel after discussing the control's purpose and full-validation cost; parallel plan restored prospectively before updates.
- 10-19-2026: Added the user-requested 4B augmented condition, prospective CPU offload implementation, and three-system validation manifest; human-only SSH reauthentication pending.

- 10-19-2026 01:08:53 PDT: New authenticated SSH ControlMaster verified after user login; no further password entry required while it remains live. All corrected 500 examples passed full compilation/kernel/differential/format/admission checks. Both model-size token/checkpoint preparations passed; 135/135 exact validation prompts, three real scorer controls and numerical CPU optimizer control passed. Source/protocol frozen before updates. Full repository gate reruns in an owned dependency layout after provisioning missing pytest/ripgrep and optional-fixture paths; no test source changed. Next: commit the frozen source, launch all three isolated smoke/training/validation pipelines, and verify optimizer progress.

- 10-19-2026 01:11:11 PDT: Parallel GPU pipelines launched under remote tmux `rl4cv-tiny-training`. 1.7B control and mixed longest-sequence checks passed (about 38.36 GiB peak for control); both full training processes started. 4B longest-sequence check is active on device 6. Full Linux gate passed: 1,366 passed, 24 skipped, six subtests passed; optional experiment-13 private integration fixtures use their documented unavailable-prerequisite skip. Source/protocol local freeze commit: `ef92ac739dcc782040abfcd7a9bdff6af1d47718`. No other user jobs/registries changed.
