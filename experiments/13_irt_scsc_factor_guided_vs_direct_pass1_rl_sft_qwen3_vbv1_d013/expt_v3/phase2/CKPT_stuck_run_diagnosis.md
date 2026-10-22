# Experiment 13 stuck-run diagnosis checkpoint

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/e13v3-resume-missing-receipt-fix-10-22-2026/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/phase2/CKPT_stuck_run_diagnosis.md>

**TLDR:** Read-only diagnosis and a bounded missing-receipt resume fix are complete in the isolated branch; live runs and their state remain unchanged.

Created: 10-22-2026 12:24:52 PDT
Last updated: 10-22-2026 12:24:52 PDT

## Goal
- Diagnose `experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/` v3/v4 stalls, rank disk recovery and stage a resume fix without activation.
## What ran
- Read-only log/process/disk inspection; isolated CPU regression and repository tests. No training or model calls.
## Results
- Report: [DIAGNOSIS_stuck_runs_10-22-2026.md](DIAGNOSIS_stuck_runs_10-22-2026.md); 1,168.41 GB top-five candidates; 97 v3 and 1,405 root tests pass, 15 root skips.
- Stage exit 0 and UNMEASURED explain three v3 missing receipts; 3/3 v4 engine attempts fail function serialization.
## Stuck / blocked
- Deployment intentionally held; missing lake, cached scoring failures, device contention, disk and counter budget remain live concerns.
- v4 exhausted its frozen three-attempt cap; re-admission belongs to Brando.
## Next steps
- [p 10/10] Coordinator reads report: `cat /lfs/skampere1/0/brando9/rl4cv_e13v3/diag_10-22-2026/wt/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/phase2/DIAGNOSIS_stuck_runs_10-22-2026.md`.
- [p 9/10] Review staged code; coordinate scoring/environment recovery and v4 transport repair before any authorized deployment.
## Brando to-do
- Decide loss of older native checkpoint resume ability and whether to re-admit v4 after its technical fix.

## Log
- 10-22-2026 12:24:52 PDT -- Diagnosis and isolated fix verified; branch-only publication pending; no live activation. Worktree retained as requested, cleanup owner coordinator after explicit scope change permitting removal.
