# Experiment 08 version 2 results — matched step-658 test evaluation at all four sizes

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/results.md>

**TLDR:** Version 2 evaluates 1.7B, 4B and 14B at step 658 once each on the VeriBench V1 test split (222 tasks × 8 samples), using version 1's exact sampling, scorer and judge. With version 1's 8B step-658 result, it then compares all four sizes after identical SFT: the same 1,315 examples, 658 updates and 5,752,936 loss tokens. No new test cells have been measured yet; the worker is verifying inputs and the baseline environment.

**Status:** RUNNING (dispatched 10-13-2026). The protocol is locked and the forecast was frozen before generation.

**Last updated:** 10-13-2026 17:29 PDT

| Phase | Status | Evidence |
|---|---|---|
| Preflight | DONE | Version 1 DONE; no live writer; full tests 338 passed, 4 skipped |
| Input verification | DONE | Three weight manifests, test list and forecast match; fresh judge bundle 3/3 match |
| Admission publication | DONE | Published main 25bbe01 before launch; six admission tests pass |
| Generation | IN PROGRESS | Startup compiler environment repaired; 0/5,328 cells yet |
| Judge controls | READY | 25 train controls reproduce prompt hashes; service health and authentication pass on port 9860 |
| Scoring and test judging | PENDING | No new scored cells or judge ratings |
| Reused-analysis regression | DONE | All six reused systems exactly reproduce original scopes; independent 108 factor/score checks pass |

## Declared cells

| System | Role | Declared cells | Known cells | Judge ratings known |
|---|---|---:|---:|---|
| `test_sft_1p7B_f1p0` | new | 1,776 | 0 | 0 |
| `test_sft_4B_f1p0` | new | 1,776 | 0 | 0 |
| `test_sft_14B_f1p0` | new | 1,776 | 0 | 0 |
| `test_sft_8B_f1p0` and the four Base systems | reused from version 1 | 8,880 | 8,880 | complete in version 1 |

## Validation context (version 1, already observed; validation split, 135 tasks × 8)

| Step-658 checkpoint | Extracted / 1,080 | Capped / 1,080 | Mixed tasks / 135 | `kernel_binary` mean pass | Validation gates |
|---|---:|---:|---:|---:|---|
| 1.7B | 897 | 184 | 20 | 0.0491 | fail (extraction, cap) |
| 4B | 946 | 134 | 32 | 0.0926 | fail (extraction, cap) |
| 8B | 974 | 106 | 32 | 0.0963 | PASS |
| 14B | 995 | 84 | 39 | 0.1204 | PASS |

TL;DR: Version 2 is running. No version 2 test number exists yet; this file is updated as each system is generated, scored and judged.

## Preflight receipt

The initial full suite had 328 passed, 4 skipped and four failures from inherited `CODEX_HOME`. Removing that variable only for the test process gives **338 passed, 4 skipped** in 292.21 seconds, including six new admission cases; no source repair was needed. Installed scipy/psutil into `.venv`. The watchdog harmless failure/fake-mail test passes (one relaunch, deduplicated notices). The start email was sent at 17:18 PDT. Input hashes: [inputs_check.json](results/inputs_check.json); route verification: [route_identity_v2.json](results/route_identity_v2.json).

## Execution launch and recovery

The manifest and admission guard were published at `25bbe01` before launching the three persistent drivers. The GPU lease guard rejected occupied device 0, so 1.7B uses device 4; 4B uses 1; 14B uses 2,3 with two shards. Other users on devices 0 and 7 were left alone. All initial generators failed before any output because inherited `CUDA_HOME=/usr/local/cuda-12.4` overrode the 12.8 compiler on PATH; resumes now explicitly use CUDA 12.8 and private compilation caches. Failed logs and driver identities are retained. Sampling and scoring are unchanged.

The host watchdog runs every 15 minutes and at reboot, checks child identities and progress, and resumes a dead driver once per incident. The fake-mail failure test and throwaway-session idle-nudge test pass. The canonical checkpoint is [CKPT_e08v2.md](CKPT_e08v2.md); the launch-named local resume copy is under `$WORK/v2/`. The worker learned after its start notification that the master had already sent one; no further start email is scheduled.

**TLDR-end:** [rl4cv: 08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2 matched step-658 test] The manifest is published and generation startup is recovering with the corrected compiler. No new test factor is reported yet; full tests pass (338 passed, 4 skipped).
