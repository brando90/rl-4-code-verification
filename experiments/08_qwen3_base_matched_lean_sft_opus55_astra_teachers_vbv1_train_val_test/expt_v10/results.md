# Workbook verification running; initial unresolved recovery complete

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v10/results.md

**TLDR:** RUNNING, 10-19-2026 05:52 PDT. Cluster: 10,233/10,995 checked, 9,192 PASS with48slots. GX10: 1,600/1,600 checked, 487 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.

## Execution

- `rl4cv-workbook-verify-v10` on skampere1:48parallel single-threaded Lean checks; no graphics processor allocated. Positive, sorry and declared-axiom controls passed before the queue. An initial control collided with an existing Mathlib declaration name; that preflight receipt is preserved and the control was renamed before any dataset cell ran.
- `rl4cv-workbook-unresolved-v10` on skampere1:4parallel recovery slots, now finished. All74cases accounted for:6recovered,61checked but still unresolved,7requiring proof/library repairs not attempted by this mechanical pass.
- `rl4cv-gx10-verify-v10` on cactushacks-gx10:16native ARM Lean4.22.0 slots, Mathlib79e94a093aff4a60fb1b1f92d9681e407124c2ca. Mathlib import and positive/sorry/declared-axiom controls passed. Total active capacity is64slots across both hosts.

All previous exclusions, statements and proof scripts are preserved. The6recovered cases have actual kernel PASS under the documented legacy-notation/resource amendment; they still require matching explanatory comments, format checks and protected screens before training admission. Compiler success alone does not reverse the1,082prior semantic rejections.

[Current per-item check table](results/cluster_row_results.csv) contains completed cells; the [frozen manifest receipt](results/freeze.json) retains the full declared count and input hash. [Progress snapshot](results/cluster_progress.json) and [all74unresolved diagnoses](results/unresolved_audit.json) preserve exact counts and reasons. [Recovery outcomes](results/unresolved_progress.json) preserve each of74decisions. Categories overlap;57cases had parser compatibility failures,10resource failures,5unknown identifiers,7unsolved-goal diagnostics and1other diagnostic.

48was an initial resource choice, not a quota. skampere1has128logical CPUs, and52Lean processes used about185GBresident memory during the combined passes. Other jobs share the node; the sampled overall load was about90–97, with42.7%CPU idle in a later one-second sample. The two measures cover different intervals. The GX10 has20ARM CPU cores and about120GBavailable memory; its native environment will be verified before adding work.

## Pending

Finish the10,995-cell original-source check; retain every failure. TheGX10checks the frozen last1,600-source shard; a local orchestration relay imports validated native successes into cells the cluster has not started, while retaining host-specific evidence. Both node jobs finish independently if that relay disconnects. Broader compatibility/proof repairs and incorporation of other audited sources remain separate from this original-source compilation pass. No training has started on the new pool.

## Latest automatic snapshot

RUNNING, 10-19-2026 05:52 PDT. Cluster: 10,233/10,995 checked, 9,192 PASS with48slots. GX10: 1,600/1,600 checked, 487 PASS with16slots; setup DONE. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training.

TheGX10shard is a subset of the10,995original cells. Successful exact-source ARM receipts can be reused by unstarted cluster cells; host totals must not be added as distinct statements. Raw evidence remains on its execution host.
