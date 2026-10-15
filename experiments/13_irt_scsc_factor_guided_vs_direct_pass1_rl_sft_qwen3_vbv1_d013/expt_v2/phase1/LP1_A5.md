# Experiment 13 v2-S2: frozen numerical candidates and development admission

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1/LP1_A5.md>

**TLDR:** Under adopted A5, measure two numerical candidates in this fixed order: C1 float16, then C2 float32 only if C1 does not qualify. Both use the same dtype in vLLM 0.10.0 and NeMo RL 0.4.0. Select the first clearing all four development margins, freeze it, and confirm once on the original LP-1 probe. S1's measured FAIL remains final: 99th-percentile absolute log-probability error 0.124769325 > 0.10 over 40,035 tokens in 8/8 responses.

## Frozen list and evidence chronology

[Candidate declaration](LP1_A5_candidates.json) contains the exact order, private configuration hashes, eight-task identifier hash and manifest hash. This declaration and the [C1 development lock](../locks/LP1_A5_C1.json) must be pushed before any development measurement. All candidate implementation and input preparation is CPU-only. The lock records every replacement relative to S1's A4 lock and retains previous hashes for every unchanged binding.

| Order | Shared numerical change | Expected Phase 2 cost (unmeasured) |
|---|---|---|
| C1 | Generator weight/activation dtype `float16`; trainer `precision=float16`; trainer's generation config `precision=float16` | Lower: same two-byte tensor storage class and supported low-precision tensor-core path as S1 |
| C2 | The same three settings become `float32` | Higher: four-byte tensors, larger memory traffic and the installed libraries' dtype-compatible fallback kernels |

The installed trainer chooses attention automatically because sequence packing is disabled; it does not force FlashAttention 2 in this configuration. The installed vLLM CUDA platform selects its dtype-compatible backend (including FlexAttention for float32 on its V1 engine). No library is replaced or patched. Existing float32 log-softmax, eager inference, batch sizes and automatic kernel selection stay fixed. These source checks establish available configuration paths, not successful device execution; each run still requires the claimed-device non-probe engine preflight. Float16 training stability and actual cost remain subject to the unchanged later technical gates.

## Probe and decision rule

Draw eight tasks with Python `random.Random(1302151).sample(sorted(train minus original LP1 tasks), 8)`. The 539-task train allowlist is unchanged; overlap with the original probe is zero. Keep the original per-task sampling seed rule `cell_seed('lp1', task, 0)`, rendered prompt tokens, model export, thinking setting, temperature 1, top-p 1, top-k -1, 8,192-token cap and terminal-token mask. No validation or test prompt is used. Both candidates receive byte-identical development manifests and seeds. Hash the UTF-8 task IDs in draw order, one newline per ID; publish only that hash and counts.

A candidate qualifies exactly when its complete eight-response measurement has unsupported count 0, median absolute error ≤0.008, 99th-percentile absolute error ≤0.08, and importance-ratio truncation fraction ≤0.008 at cap 2. The unchanged probability evaluator also reports the original admission verdict; an original-threshold PASS alone is insufficient for development selection. The list cannot be extended after measurement. A measured candidate is final and never repeated; no candidate after the first qualifier is measured. Infrastructure failures retain their evidence and obey A4's verified-fix/publication/three-attempt rules.

Freeze the first qualifier in `locks/LP1_A5_S2.json` and publish after required tests before one confirmation on the original probe. Confirmation uses the unchanged thresholds 0, 0.01, 0.10 and 0.01. No qualifier, or a failed confirmation, stops version 2. Every new result is labeled v2-S2 with S1's final failure disclosed. No outcome here is evidence of learning.

## Resources and supervision

All A5 runs share at most 3.0 new device-hours, at most 0.5 per run including preflight and cleanup. The canonical experiment-13 registry keeps its historical S1 hours; its cumulative ceiling is the frozen pre-A5 registry total plus 3.0, not a reset. CPU-bound preparation and source hashes do not consume device time. An idle device on skampere1/2/3 requires the existing minimum 40,000 MiB device memory, 64 GiB host memory and 8 GiB free storage, no compute processes and no foreign lease/reservation. Recheck immediately after claim; release only after marked-process cleanup. Busy devices remain a wait condition.

The fresh A5 watchdog registers the same single writer; its two cron lines append to all twelve existing lines. Six fake-mailer checks pass. The existing 15-minute device poller dispatches only a published, bound plan. The original S1 terminal receipts and sent notifications remain historical; no completion notice is sent for preparation or ordinary waiting. Phase 1 and Phase 2 proceed only after confirmed S2 admission, with S2 applied to every subsequent numerical generation/training path and the published G1 method lock verified before any fit.
