# Experiment 02A v2 — live external-pool preparation results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v2/results.md>

**TLDR:** Execution revalidated FVAPPS and pinned VERINA source screening, froze outcome-blind candidate panels and disjoint candidate partitions, and found the external endpoint inadmissible. No candidate has entered training, checkpoint selection, repair, or judge scoring.

**Status:** EXTERNAL-SOURCE STUDY COMPLETE; TRAINING/REPAIR BLOCKED.

| Item | Observed local preparation | Remote requirement |
|---|---:|---|
| FVAPPS revision | `3552a173e74837dd0017d72431c6ede8fa903bb7` | Verify downloaded bytes again |
| `train.jsonl` SHA-256 | `e0874ed37ab4c0a1e727cc2e11fdc9d4add5f34316ddc726b1f3922d60146bc1` | Match exactly |
| Source rows | 4,715 | Recount |
| Curated source rows | 1,083 | Recount |
| Screened curated rows | 1,083 | Rerun against execution corpus |
| Exact / near (word-5-gram >= 0.70) | 0 / 0 | Rerun and preserve report |
| Candidate panel | 24 hash-ordered rows | Pending reference acceptance |

## 10-05-2026 execution update

| Receipt | Observed count | Verdict |
|---|---:|---|
| FVAPPS rerun | 4,715 rows; 1,083 curated; 24 candidates; exact / near contamination 0 / 0 | Candidate-only: released stubs contain `sorry` |
| VERINA source | 189 Apache-2.0 records at `66b3ce5…7249f`; exact / near contamination 0 / 0 | 24 source-hash-selected candidates frozen before outcomes |
| VERINA Lean 4.22 original bytes | 22 compile pass / 24; 2 compile fail | Compatibility is incomplete without changing source |
| VERINA original reference theorem | 6 kernel-honest / 24; 16 forbidden `sorryAx`; 2 unknown | Source references cannot be promoted to endpoint certification |
| Independent endpoint applicability | 0 / 24; required minimum 20 / 24 | FAIL: no audited generic Lean candidate adapter preserving fixed requirement identities and candidate hashes |
| Candidate allocation | 141 train / 24 validation / 24 test | Frozen outcome-blind; NOT ADMITTED for training |

The receipts are `results/fvapps_external24_snap_manifest.json`, `results/verina_external24_candidate_manifest_2026-10-06.json`, `results/verina_external24_lean422_2026-10-06T0600Z/results.json`, and `../../../../04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v3/results/verina_external24_applicability_2026-10-06T0610Z/results.json`. The split receipt is `results/verina_candidate_train_validation_test_2026-10-06.json`.

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
