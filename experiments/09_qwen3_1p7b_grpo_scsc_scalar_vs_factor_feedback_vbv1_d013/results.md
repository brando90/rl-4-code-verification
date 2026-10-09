# Live results: Qwen3 1.7B factored-score policy training

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/results.md>

**TLDR:** The overnight run is active under its provisioned 16-hour deadline. Immutable inputs, a one-GPU Qwen/feedback preflight, and both live judge-control configurations have passed; two-turn calibration, training, and held-out efficacy remain unmeasured.

**Status:** RUNNING (started 10-08-2026 19:13 PDT / 2026-10-09T02:13:36Z).

**Last updated:** 10-08-2026 19:45 PDT / 2026-10-09T02:45:00Z.

| Phase | Status | Evidence |
|---|---|---|
| Runtime and ownership | DONE | Run `0c84fdc2-d5cf-4a04-9137-e214edbd8c36`; sanitized receipt `expt_v1/results/runtime_receipt.json`; deadline 2026-10-09T18:13:36Z. |
| Immutable input audit | DONE | NeMo RL `c751f811217db7df0d4c94abdeaada6626cfc150`; Qwen3 1.7B step-658 config/tokenizer checksums recorded privately. |
| Shared GPU admission | DONE | Experiment-08 owner acknowledgment permits only a live lease. GPU 3 was leased for a bounded preflight and released at 2026-10-09T02:42:44Z. |
| Qwen feedback preflight | PASS | Owned receipt `../../receipts/gpu_preflight_e09.json`: A100, Qwen3 1.7B, 32,768-token bound, and raw feedback rendering passed. |
| Frozen scorer adapter control | PASS | One bounded CPU scorer completed 14 files in about five minutes; it accepted expected gold/historical files and rejected empty, non-compiling, `sorry`, vacuous, and forbidden-native-decision controls. Owned receipt: `../../receipts/scorer_adapter_e09.json`. |
| Two-turn adapter and loss/reward controls | IN PROGRESS | Terminal-only reward, feedback boundaries, action-mask rejection, exact-input cache, and frozen-scorer control have passed. No optimizer update or disposable checkpoint has been used. |
| Validated judge route and live controls | PASS | Both H2 Sol high and H2 Opus 5.5 max completed 25/25 control cells and passed oracle/vacuous/blank/shuffled/half-deletion checks; 50 measured cells total. |
| Judge-control cleanup | DONE | The collect-only service and tunnel were torn down after harvest; its claimed port is free. |
| Isolated trainer runtime | IN PROGRESS | An experiment09-owned NeMo checkout at the frozen commit and pinned submodules is provisioning its separate vLLM actor environment. No GPU lease is held and it is not yet a usable trainer. |
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
