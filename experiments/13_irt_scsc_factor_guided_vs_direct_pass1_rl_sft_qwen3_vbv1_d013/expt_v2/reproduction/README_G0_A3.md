# G0 under Amendment A3: exclusion verification and prospective implementation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/reproduction/README_G0_A3.md>

**TLDR:** The admitted 217-cell exclusion set is verified. The separate wrapper imports the frozen evaluator and computes full-manifest completion bounds; its code, tests and lock must be published before its single run.

## Verified exclusion set

Secure Hash Algorithm 256-bit (SHA-256) digest: `c00b35abaecda874820d4b1b29015655e248c19f319fa574fefa3d0804124128`. Exactly 217 unique cells belong to the 33,456-cell ordinary manifest, all train or validation; none belongs to test. All four publicly named class-(c) cells are included. No identifiers or per-cell measurements are published in this report.

The two equivalent compositions are 167 originally typed limits + 3 class (a) + 4 class (c) + 43 class (d), or 168 typed limits + 2 class (a) + 4 class (c) + 43 class (d). The supplemental A2 timeout has both typed status and class (a); it is counted once. Here class (a) means timing/resource dependent, (c) historical-record irreproducibility, and (d) unknown.

| Policy (cell-ID prefix) | Train | Validation | Total exclusions |
|---|---:|---:|---:|
| qwen3-1.7b-base | 5 | 1 | 6 |
| qwen3-4b-base | 6 | 0 | 6 |
| qwen3-8b-base | 2 | 1 | 3 |
| sft_1p7B_f0p125 | 0 | 1 | 1 |
| sft_1p7B_f0p25 | 0 | 1 | 1 |
| sft_1p7B_f0p5 | 0 | 16 | 16 |
| sft_1p7B_f0p75 | 0 | 17 | 17 |
| sft_1p7B_f1p0 | 0 | 22 | 22 |
| sft_4B_f0p25 | 0 | 17 | 17 |
| sft_4B_f0p5 | 0 | 17 | 17 |
| sft_4B_f0p75 | 0 | 14 | 14 |
| sft_4B_f1p0 | 0 | 17 | 17 |
| sft_8B_f0p125 | 0 | 14 | 14 |
| sft_8B_f0p25 | 0 | 18 | 18 |
| sft_8B_f0p5 | 0 | 19 | 19 |
| sft_8B_f0p75 | 0 | 10 | 10 |
| sft_8B_f1p0 | 0 | 19 | 19 |
| **Total** | **13** | **204** | **217** |

These are deterministic metadata counts (p-val=n/a), not G0 outcomes. The full denominator remains unchanged.

## Completion algorithm fixed before measurement

`g0_a3.py` imports `g0.py`'s unchanged `evaluate`; it never invokes its `main`. Before importing that evaluator or parsing validation rows, all nine lock bindings must match, including the original ordinary result ledger, manifest, frozen evaluation dependency, and opaque public receipt. Runtime also verifies that the lock and implementation occur in the specified commit on fetched `origin/main`. A canonical exclusive-create `G0_A3/attempt.json` admits one execution only. Hash/publication preflight failure happens before reservation or data parsing.

Excluded receipts are discarded before their measurement fields are inspected. The ordinary manifest supplies the complete 135-task, eight-sample arrays and the exclusion masks. Any other missing required cell makes its stratum INCOMPLETE; an INCOMPLETE 4B stratum fails G0. The original measured values in excluded receipts never constrain completions. New strict values are zero or one; a strict success requires reward B exactly one, otherwise B ranges over [0,1].

Dense-only counts separate across tasks. For each task the wrapper considers endpoint fills, constant fills matching each retained reward, all strict successes, and a single unequal reward. These cover both possibilities for the Boolean dense-only predicate: strict must be constant and B nonconstant. The per-task extrema sum to exact cohort bounds. Witnesses preserve every retained cell.

For area under the receiver operating characteristic curve (AUC), each task contributes an allowed earlier-zero-success subset membership and later-positive label. Labels outside the subset are irrelevant and collapsed. Once states are fixed, maximize AUC by setting excluded earlier rewards to one for positives and zero for negatives; minimize by reversing those endpoints. This is exact by pairwise ranking monotonicity, including average-rank ties. Enumerate the Cartesian product of task states up to 2^20 configurations. An undefined completion exists if either outcome class is not forced to remain represented in the subset.

If that product exceeds 2^20, use the valid outer bound [0,1] for AUC and disclose it explicitly. The displayed feasible AUC witnesses then are **not certified extrema**, and the outer endpoints have no claimed attaining completion. This fallback can make the gate INCONCLUSIVE; it cannot manufacture PASS or FAIL. Dense-only bounds remain exact. If every exact completion has undefined AUC, admission fails. Otherwise an undefined possible completion prevents PASS, as required by the admission record.

Every attained extremum is passed to the frozen `evaluate`, including its 10,000 paired task-group bootstrap draws and unchanged seed 1302051. The public result contains full evaluator outputs for dense minima/maxima, defined AUC minima/maxima, and an undefined witness when present. Completed arrays remain private with a published digest. Completion bounds are identification bounds; bootstrap intervals are conditional on the displayed fixed completion and are not confidence bounds over all missingness assignments.

## Execution and supervision

Owner: `codex-rl4cv-e13v2-owner-g0`, process 1243923, verified full access and approvals `never`, Codex `gpt-6-astra`, effort `high` per the owner launch record. Previous owner is idle at its prompt; its only children are tool services, with no measurement/training child. It receives no input.

The watchdog uses the existing shared recovery lock and persistent ledger under `/lfs/skampere1/0/brando9/rl4cv_e13v2/watchdog`, run `e13v2_g0_owner_10-14-2026`. The seven existing cron lines were backed up and exactly preserved; two lines were appended (15-minute cadence and reboot). Owner process/start/boot identity is verified. All six existing watchdog self-tests passed, including fake-mail deduplication, concurrent recovery, orphan adoption and owned-session cleanup. Automatic executor replacement is not configured; the active owner handles continuation. No start email is sent under PLAN §7's completion/human-event-only rule.

This gate uses central processors and existing data only, with no model calls or graphics processor lease. skampere1 health preflight reaches the host and finds about 5,236 GiB local free space. Shared-filesystem percentage headroom fails its generic threshold (about 2,904 GiB free), but gate outputs/caches stay on the owned local filesystem and this bounded computation does not depend on shared bulk storage.

## Tests and freeze

The authored controls compare exact bounds with exhaustive synthetic completions, test one-class/empty eligibility and AUC monotonicity with ties, poison every excluded receipt including all four public class-(c) identities, retain unlisted missing cells as INCOMPLETE, and reject each hash mismatch before validation parsing. Required publication check: `E13_REQUIRE_LEAN_INTEGRATION=1 make test`. Result: 433 passed, 23 skipped, zero failed in 260.05 seconds; Lean integration required. The 22 wrapper controls passed within that suite. Log: `$WR/state/G0_A3_prepublication_test.log`, SHA-256 `7df2a638a81035cc0a7e5ec50192d42eedc4828e071e43a21e004cec973d49d1`.

The lock is [G0_A3.json](../locks/G0_A3.json). No G0 statistic has been computed at this freeze.
