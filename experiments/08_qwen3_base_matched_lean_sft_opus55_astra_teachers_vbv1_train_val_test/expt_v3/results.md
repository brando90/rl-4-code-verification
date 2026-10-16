# Cached data continuation preparation status

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/results.md>

**Status:** RUNNING: disposable dry run. **Last updated:** 10-15-2026 20:36 PDT.

| Phase | State | Evidence |
|---|---|---|
| Existing validation analysis | DONE | 4 sizes x 135 tasks x 8 known samples; [report](RESULTS_continuation_audit.md) |
| Failure taxonomy of the step-658 validation outputs | DONE (10-14-2026, zero model calls) | per size: no file 183 / 134 / 106 / 85, compile error 844 / 846 / 870 / 865, kernel success 53 / 100 / 104 / 130 of 1,080; [report](RESULTS_failure_taxonomy.md), [JSON](results/failure_taxonomy.json) |
| Cached train candidate inventory | DONE | 685 candidates / 360 already-covered train tasks; [manifest](results/cached_train_candidates.csv) |
| Earlier external pool inventory | DONE | 587 pairs / 455 tasks before conversion and joint screening |
| Source availability and hashes | DONE | 685/685 cached responses and 587/587 earlier Lean files verified; [receipt](results/host_data_verification.json) |
| Corpus conversion and admission | DONE (10-14-2026, host) | 2,585 / 2,587 admitted: 1,315 originals, 685 cached, 585 / 587 MBPP (2 `over_length_cap`); 0 duplicates, 0 held-out hits over 7,761 texts; new loss tokens 5,429,531 rendered; [manifest](results/admitted_corpus_manifest.csv), [stats](results/admitted_corpus_stats.json), [MBPP encoding](mbpp_conversion_spec.md) |
| Prospective training protocol | LOCKED | [PROTOCOL.md](PROTOCOL.md): two conditions, 5,752,936 additional loss tokens each, half/full validation, frozen gates, meeting decision rule |
| Deterministic verification | DONE | Linux 323 passed / 24 skipped on 10-13 ([receipt](results/verification.json)); macOS 10-14: 320 passed, 36 skipped, the 4 known macOS-only failures |
| Disposable expansion dry run | IN PROGRESS | Named session `rl4cv-e08-v3-dry`, GPU 1, actual NeMo training steps observed; production and validation pending |
| Deterministic continuation inputs | DONE | Replay steps 334/658 (2,880,477/5,752,936 loss tokens); expansion 335/667 (2,878,589/5,757,776); [schedules](results/sft_schedule_v3_E.json) |
| Prospective forecast and validation cells | DONE | [forecast](forecasts/e08_v3_forecast.json), 16 systems × 135 tasks × 8 samples = 17,280 unique cells |
| Four-size formatter and start weights | DONE | 2,585 examples match all four tokenizers and NeMo loss spans; all four step-658 weight exports pass full SHA-256 verification |
| Current full test suite | DONE | 1,183 passed, 17 skipped, 0 failed in 286.81 seconds; pinned dependency restored |

The preparation is deterministic reuse of existing data, not a new model experiment. Host files live under `/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/` (candidate corpus SHA-256 `7fa02557…`); version-1 and version-2 host files are untouched. Execution checkpoint: [CKPT_e08_v3.md](CKPT_e08_v3.md); historical preparation: [CKPT_continuation.md](CKPT_continuation.md).

**TLDR-end:** [rl4cv: 08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test] The taxonomy, the admitted 2,585-example candidate corpus and the locked two-condition protocol are ready; gains from more exposure or more data remain unmeasured until training and validation finish.
