# Live results: Qwen3 1.7B factored-score policy training

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/results.md>

**TLDR:** The overnight run is active under its provisioned 16-hour deadline. Immutable inputs, a one-GPU Qwen/feedback preflight, and both live judge-control configurations have passed; two-turn calibration, training, and held-out efficacy remain unmeasured.

**Status:** RUNNING (started 10-08-2026 19:13 PDT / 2026-10-09T02:13:36Z).

**Last updated:** 10-08-2026 21:11 PDT / 2026-10-09T04:11:00Z.

Recovery attempt 2 is active in the original run, using verified native `gpt-6-astra` / `ultra`, full filesystem access and approval policy `never`. The first coordinator's dependency children had exited; neither was duplicated. The owned pinned runtime imports both real NeMo actor classes. Exact native top-k/top-p probability, gradient, missing-rating, reward, schedule and Qwen rollout tests passed **28/28**; the latest repository check passed **146 tests, 4 skipped**. These are technical checks, not learned-weight results.

At 21:11 PDT, the native suite passes **29/29**, including a negative test ensuring a warmup flag cannot bypass real-request probability checks. Actual engine initialization now passes. A scheduler setup error was corrected, and the next bounded disposable control is active. No optimizer/save-reload gate or scientific admission is claimed.

The real optimizer control remains **unpassed**. One engine initialization exposed an unverified CUDA-device enumeration; the adapter now fixes PCI ordering and verifies physical GPU UUIDs. On the verified device, another user's engine started after lease admission. Initialization and its one identical contention retry stopped at the memory guard, before generation or an optimizer update. Healthy foreign processes were preserved and leases released. A new prospective occupancy guard and bounded admission wait are active; no resident GPU sharing is authorized.

All 539 training prompts were tokenized without reading held-out source. Including the protocol-required completion reminder, the maximum prompt is **7,893 tokens**. Two 8,192-token responses plus a conservative **8,236-token** feedback bound require **32,513 tokens**, so the candidate runtime context is now **32,768**, not the insufficient 24,576 starting candidate. Full-context optimizer memory is still unverified. The exact-six-rating batch queue has blocking/missingness tests; an offline three-task prompt-pack round trip passed with zero model calls. Existing control charges are **$3.0558** for 50 measured constituent ratings, not 50/50 expected-label accuracy.

| Phase | Status | Evidence |
|---|---|---|
| Runtime and ownership | DONE | Run `0c84fdc2-d5cf-4a04-9137-e214edbd8c36`; sanitized receipt `expt_v1/results/runtime_receipt.json`; deadline 2026-10-09T18:13:36Z. |
| Immutable input audit | DONE | NeMo RL `c751f811217db7df0d4c94abdeaada6626cfc150`; Qwen3 1.7B step-658 config/tokenizer checksums recorded privately. |
| Shared GPU admission | DONE | Experiment-08 owner acknowledgment permits only a live lease. GPU 3 was leased for a bounded preflight and released at 2026-10-09T02:42:44Z. |
| Qwen feedback preflight | PASS | Owned receipt `../../receipts/gpu_preflight_e09.json`: A100, Qwen3 1.7B, 32,768-token bound, and raw feedback rendering passed. |
| Frozen scorer adapter control | PASS | One bounded CPU scorer completed 14 files in about five minutes; it accepted expected gold/historical files and rejected empty, non-compiling, `sorry`, vacuous, and forbidden-native-decision controls. Owned receipt: `../../receipts/scorer_adapter_e09.json`. |
| Two-turn adapter and loss/reward controls | IN PROGRESS | Actual pinned rollout code with deterministic transport doubles and Qwen tokenizer passes boundaries/final-metadata/terminal-reward controls. Filtered-policy numerical tests pass. Real optimizer/save-reload, weight refit and full-context memory remain unpassed. |
| Validated judge route and live controls | PASS | Both H2 Sol high and H2 Opus 5.5 max completed 25/25 control cells and passed oracle/vacuous/blank/shuffled/half-deletion checks; 50 measured cells total. |
| Judge-control cleanup | DONE | The collect-only service and tunnel were torn down after harvest; its claimed port is free. |
| Isolated trainer runtime | IN PROGRESS | Owned actor imports pass. Real engine attempts stopped before generation; current occupancy admission is bounded. No healthy compiler child remains to adopt. |
| 256-rollout train calibration | PENDING | 0/256 rollouts, 0/512 assistant responses measured. |
| Frozen six-trajectory manifest | PENDING | Horizon not chosen. |
| Training | PENDING | 0/6 trajectories; 0 optimizer updates. |
| Common held-out evaluation | PENDING | Validation 0/945 cells; test 0/1,554 cells. |

- Declared comparisons: strict conjunction versus smooth geometric mean; scalar versus named-factor feedback at identical smooth reward.
- Six training trajectories planned; zero completed. Throughput-only horizon selection is specified before main training.
- Maximum evaluation declaration: 945 validation and 1,554 test cells; zero measured in this version.
- Existing audit: kernel-only factors did not differentiate the inspected 1.7B/4B 75% validation outputs. These prior outcomes motivate using full FSC, not relabeling the kernel proxy as smooth.
- The 256-rollout calibration remains the next scientific gate. Its fixed requirement is positive within-group scalar variance and at least one scalar reward unequal to the strict conjunction; no training or held-out test may precede it.
- Resource, optimizer, and complete two-turn integration controls remain prerequisites. No efficacy conclusion exists.

**TLDR-end:** [rl-4-code-verification: 09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013] The three-arm factored-score learning study has passed live judge controls and the bounded Qwen preflight; calibration, training, and held-out outcomes remain unmeasured.
