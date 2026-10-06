# Experiment 02A v2 — live external-pool preparation results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v2/results.md>

**TLDR:** Local exploratory preparation verified the FVAPPS source identity and a full curated-source contamination screen, then froze a 24-task candidate manifest. No task is an accepted fixed reference: FVAPPS supplies `sorry` stubs, so reference acceptance and the final remote preflight remain pending.

**Status:** PLANNED — no source probe, training run, repair run, or model evaluation has been launched from this version.

| Item | Observed local preparation | Remote requirement |
|---|---:|---|
| FVAPPS revision | `3552a173e74837dd0017d72431c6ede8fa903bb7` | Verify downloaded bytes again |
| `train.jsonl` SHA-256 | `e0874ed37ab4c0a1e727cc2e11fdc9d4add5f34316ddc726b1f3922d60146bc1` | Match exactly |
| Source rows | 4,715 | Recount |
| Curated source rows | 1,083 | Recount |
| Screened curated rows | 1,083 | Rerun against execution corpus |
| Exact / near (word-5-gram >= 0.70) | 0 / 0 | Rerun and preserve report |
| Candidate panel | 24 hash-ordered rows | Pending reference acceptance |

The selected task IDs and row hashes are in `results/fvapps_external24_candidate_manifest.json`. Their source field names are exactly `apps_id`, `apps_question`, `assurance_level`, `sorries`, `spec`, and `units`. No field contains an accepted Lean implementation or proof; the `spec` definitions and theorem bodies contain `sorry`.

**TLDR-end:** [rl4cv: experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics prospective external-pool setup] This phase prepares a contamination-screened external pool for prospective non-VeriBench work, while leaving all fixed-reference use blocked until accepted Lean references exist.

**Snapshot:**
```text
FVAPPS revision: 3552a173e74837dd0017d72431c6ede8fa903bb7
FVAPPS train SHA-256: e0874ed37ab4c0a1e727cc2e11fdc9d4add5f34316ddc726b1f3922d60146bc1
rows: 4715; guarded_and_plausible: 1083
screen: exact=0; word-5-gram Jaccard >=0.70=0
candidate panel: 24; reference status: pending acceptance
```
