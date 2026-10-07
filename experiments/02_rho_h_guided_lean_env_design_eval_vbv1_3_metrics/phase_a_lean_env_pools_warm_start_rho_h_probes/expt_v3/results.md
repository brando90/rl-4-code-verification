# Experiment 02A v3 results — Lean warm-start data from frontier teachers

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v3/results.md>

**TLDR:** Live record of the Lean warm-start data run: how many screened, non-VeriBench Python tasks each frontier teacher turns into a kernel-verified VeriBench-format Lean file. The source build and screens are done (970 of 974 MBPP tasks declared, 0 contamination hits); no teacher call has been made. The design is in [README.md](README.md).

**Status:** BUILDING (worker on `skampere1`, 10-07-2026 16:15 PDT). Zero-model-call steps in progress; no teacher call has been made.

| Step | Status | Evidence |
|---|---|---|
| Protocol lock | pending | — |
| Source build and screens | done | MBPP `full` revision `4bb6404f`, 974 rows; 970 kept, 4 dropped (`harness_name_collision`, MBPP ids 56, 349, 899, 967); screens vs VeriBench `c11b99ba` (896 Python + 899 Lean files): 0 exact, 0 near (max word-5-gram Jaccard 0.103). [`results/mbpp_rewrite_manifest.json`](results/mbpp_rewrite_manifest.json), [`results/screen_report.json`](results/screen_report.json), [`results/declared_manifest.json`](results/declared_manifest.json) (970 task ids, list SHA-256 `ef51bae1…`, file SHA-256 `b85e5374…`) |
| Prompt pack and held-out check | done | 971 task dirs (970 declared + 1 preflight) from the agent-spec v6 adapter at VeriBench `85fd329c6`; [`results/pack_manifest.json`](results/pack_manifest.json); held-out prompt check PASS ([`results/heldout_prompt_check.json`](results/heldout_prompt_check.json)); service-loader round-trip 971/971 PASS ([`results/pack_roundtrip.json`](results/pack_roundtrip.json)) |
| Teacher runs | pending | D-014 approved the single-call exception (10-07-2026); waiting on the scorer adapter check, service, identity record and preflight |
| Scoring and verdict | pending | — |
