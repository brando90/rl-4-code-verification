# Experiment 13 v2-S2 service-name correction before judge admission

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2/COVERAGE_SERVICE_REGISTRATION_S2.md>

**TLDR:** The hosted registry rejected the uppercase service name before any judge run or rating. A successor infrastructure lock lowercases only the benchmark service registration name; all scientific settings and control cells retain their frozen hashes.

On 10-14-2026, after publication `f59b423`, the collect-only service passed authenticated local and tunnel health checks and rejected unauthenticated requests. Registration returned HTTP 422, `Invalid benchmark name`; one explicit administrative diagnostic reproduced the error. Neither command submitted a judge run, sent a model query, or computed a gate statistic. The deployment helper stopped its two child processes; their exit and the free port were verified, and only this deployment's unused authentication secret and port claim were removed. [Failure receipt](coverage_registration_0.json).

The original [control lock](../locks/COVERAGE_CONTROLS_S2.json) remains immutable. Its [successor](../locks/COVERAGE_CONTROLS_S2_REGISTRATION1.json) changes `veribench-rl4cv-e13v2-S2-controls` to `veribench-rl4cv-e13v2-s2-controls`. The private configuration and prepared-manifest hashes necessarily change; 327 of the 328 private dependency bindings remain identical. The control manifest, executable, tests, hosted agent, model selectors and efforts, request benchmark metadata, rubric, prompts, parser, thresholds, denominators, costs, and no-resubmission rule are unchanged. The unchanged deployment helper reads the newly published execution plan.

This is pre-admission service provisioning, not a repeated scientific gate or an extra candidate. Required integration checks and the successor lock must be published before provisioning resumes and before the first judge admission. The initial 50-rating control cohort is still entirely unmeasured.
