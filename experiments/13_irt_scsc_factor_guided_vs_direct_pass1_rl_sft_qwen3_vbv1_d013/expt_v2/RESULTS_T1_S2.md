# Experiment 13 v2-S2 T1: attempt 1 INCOMPLETE-INFRA

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/RESULTS_T1_S2.md>

**TLDR:** T1 attempt 1 ended on a reproducible Ray Unix-socket path defect before any trainer probability or admission statistic. This is INCOMPLETE-INFRA under A4, not a T1 scientific FAIL or a version-2 stop. Attempt 2 requires the path repair, regression test, preflight and published successor lock first.

The [learning-pilot freeze](phase2/LP_A6_S2_FREEZE.md) was published at `970d274` before execution. Its actual non-probe vLLM engine preflight passed on leased idle skampere1 device 0. Generation completed all 8/8 frozen train responses, 44,844 output tokens, with three cap-limited responses. These attempt-1 outputs are retained and excluded from every future gate statistic.

The trainer failed in `ray.init`, before model construction or any trainer probability, with `validate_socket_filename failed: AF_UNIX path length cannot exceed 107 bytes`. The exact configured socket pathname is 148 bytes. The generation and training configuration, masks, sampler and all thresholds remain unchanged. [Saved attempt receipt and evidence hashes](phase2/T1_A6_attempt1_result.json) record zero trainer-probability responses, no evaluation-attempt marker and no admission statistic. All probability errors and the unsupported/truncation statistics remain unmeasured; no value is inferred from the earlier S2 admission.

All three leases are RELEASED with verified cleanup. Cumulative T1 usage is **0.168878405 device-hours**, inside the unchanged **1.5-hour per-attempt and 2.0-hour cumulative** caps. The complete technical allocation stays 23.75 device-hours. A4 admits the next numbered complete-gate attempt only after a verified infrastructure repair; at most three attempts, and any computed gate statistic is final. No optimizer update, mutation-audit measurement or new held-out response occurred.

Required Lean integration: **1,121 passed, 3 skipped, zero failures in 497.20 seconds**, direct exit 0 ([receipt](phase2/T1_A6_publication_test.json)). This verifies the published implementation; it does not turn the observed infrastructure defect into a gate PASS. The repair is pending at this publication.
