# Failure-guided curriculum and GX10 fallback preparation results

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v14/results.md

**TLDR:** The GX10 now passes real CUDA and tiny Qwen3 attention/backward/optimizer controls in an isolated user environment. Prepared 217 Mathlib and 512 DeepSeek candidates remain outside training; three Mathlib source controls passed the unchanged kernel inspector. No API calls, pretrained-model downloads or experiment training were launched here.

## Unattended readiness, observed 10-19-2026

| Item | Measured status |
| --- | --- |
| Primary cluster | Existing eth127 SSH master to skampere1 works; Codex CLI installed; authorized AFS key readable, mode 0600 |
| Ticket lifetime | Current Kerberos/AFS tickets expire 10-20-2026 00:53:33 UTC (10-19-2026 17:53:33 PDT); coordinator owns private local credential staging |
| GX10 | GB10 GPU idle at preflight; 20 ARM CPU cores, approximately 119 GiB RAM, 813 GiB disk available |
| User package installation | PASS, no sudo or Docker required |
| BF16 matrix CUDA backward + AdamW | PASS, 0.861 seconds, 22,546,432 bytes peak allocated |
| Tiny random Qwen3 SDPA attention backward + AdamW | PASS, 328,448 parameters, 0.640 seconds, 20,406,784 bytes peak allocated |
| Full 1.7B training throughput and peak memory | Not measured; no pretrained model downloaded |
| Automatic SNAP → GX10 fallback | Not configured independently of Mac. SNAP can reach the public Brev port but lacks its authenticated CLI/SSH route; GX10 direct SNAP SSH times out. No SSH private keys were copied. |

Installed environment: `/home/lethan3/workspace/rl4cv-gx10/training-v14/.venv`, PyTorch `2.9.1+cu130`, Transformers `4.55.4`, datasets `5.0.1`, accelerate `1.15.0`. The CUDA binary warns that its listed architecture range ends at 12.0; the GB10 is 12.1 and both actual controls passed. Preserve this warning. SNAP uses PyTorch `2.7.1+cu128`, so GX10 is a different runtime phase, not a claim of identical numerical execution. A fallback experiment still needs its ordinary one-batch model preflight and resource declaration.

No human Docker group/sudo change is needed for the working user environment. Detached local GX10 sessions can run after an initiating SSH disconnect, but future dynamic dispatch from the SNAP coordinator currently needs the Mac Brev route or a separately established authenticated route. This does not block queued work on the primary cluster. [Host receipt](results/unattended_preflight.json), [GPU control](results/gpu_control.json), [Qwen control](results/qwen_gpu_control.json), [package lock](results/requirements.lock.txt).

## Public source preparation

| Source | Prepared candidates | Current-kernel controls | Admitted training rows |
| --- | ---: | ---: | ---: |
| Mathlib at pinned Lean 4.22 revision | 217 | 3/3 passed | 0 |
| DeepSeek-Prover-V1 pinned public train artifact | 512, selected from first 3,271 rows | Not run | 0 |

Mathlib scanned all 6,726 modules. The conservative preparer kept short complete original files, their imports, all declaration context and the last named theorem, skipping broad automation. It is source discovery, not a Lean parser certificate. The Nat/Int/List controls compiled the exact original modules and passed the frozen source-hash-bound kernel inspector. All candidates still need comment/sketch policy checks, actual template/token checks, protected screens and global deduplication. Most of the 217 Mathlib modules concern advanced subjects; prefer relevant Data/Nat, Data/Int, Data/List and Logic examples when a corresponding gap appears rather than adding all 217 automatically.

DeepSeek source SHA256 matches its pinned artifact, with all selected rows labeled train. The historical source toolchain is older. Its dataset license is unresolved; the user explicitly authorized provisional use while checking with a mentor. Manifests record that fact; they do not claim license clearance. No whole-corpus proof rewrite was launched.

Public candidates and the DeepSeek source artifact are available to a SNAP-only coordinator at `/lfs/skampere1/0/eth127/rl4cv_tiny_training/public_gap_sources_v14/`; no Mac is needed to read those copies. The corresponding original preparation directory is `/home/lethan3/workspace/rl4cv-gx10/training-v14/`. [Artifact manifest](results/public_artifacts_manifest.json), [Mathlib preparation](results/mathlib_preparation.json), [DeepSeek preparation](results/deepseek_preparation.json), [kernel controls](results/mathlib_controls.json).

### Full 729-candidate formal validation extension

Under a [prospective amendment](AMENDMENT_bulk_validation.md), the complete prepared cohort is now undergoing CPU-only pinned kernel verification on SNAP: 217 Mathlib plus 512 DeepSeek rows, eight Lean workers, 60 seconds per compiler operation. All exact upstream source/context comparisons and original prefix-message checks passed before the frozen manifest was written. No source, statement, proof or training pool was changed. [Freeze](results/bulk_freeze.json).

The initial positive control exposed a driver artifact-path bug after the proof itself compiled and passed kernel inspection. The driver treated the Lean module identifier `_stdin` as a file path; it now hashes `evidence_dir/original.olean`. The failed preflight and initial freeze are preserved remotely, and the identical 729-source manifest was re-frozen with the corrected driver. No cohort cell had been compiled before this correction. The watcher correctly recorded and stopped that preflight failure.

Persistent session: `rl4cv-public-source-verify-v14`. Remote batch directory: `/lfs/skampere1/0/eth127/rl4cv_tiny_training/public_gap_sources_v14/bulk_validation/`. The ordinary watcher records heartbeat, driver exit and completion independently of the laptop. Run `python3 expt_v14/sync_bulk.py` from the experiment's parent directory to refresh compact local receipts and the full 729-row table. A formal pass will not mean training admission or English-to-formal semantic verification; comments, actual template/token checks, protected overlap screens, global deduplication and further source checks remain pending.

## Existing training evidence and next regime choices

The version 6 full 135-task, eight-attempt validation comparison gave control 99/1,080 (9.17%) and tiny-augmented 74/1,080 (6.85%). The paired task-bootstrap difference was −2.31 percentage points, 95% interval [−3.89, −0.83], 10,000 draws, seed 0; p-value not computed. There was one training seed. More data alone did not improve that matched run. Preserve a substantial Python-to-Lean assistant-loss-token share and record it separately from theorem-only proof tokens. The new all-current-data run provides its own prospective comparison.

The existing 100-task tiny diagnostic had 60 compilation failures and 40 compiling outputs. Generic category matches across the 60 failing files were: unsolved goals 26, tactic failures 11, type mismatches 10, missing instances 9, parser errors 5, invalid fields/projections 2, unknown identifier/constant 1, and 15 unclassified. Categories overlap and are pattern matches to stored diagnostics, not independent root-cause labels. No task statements, model answers or concrete failing expressions were exported by this aggregation. [Category counts](results/existing_diagnostic_failure_categories.json).

These counts favor concise explicit proof steps, typed examples, and targeted induction/rewriting examples. Correct wrappers already occurred on all 100 short diagnostic tasks, so comments and FILE formatting alone are not a demonstrated remedy for the main proof failures. Long validation generations still require separate truncation/EOS tracking. Use generic public/train-only examples, never solutions derived from a protected validation task. [Decision rules and admission protocol](PROTOCOL.md).
