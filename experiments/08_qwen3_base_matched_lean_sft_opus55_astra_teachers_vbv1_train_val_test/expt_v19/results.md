# V19: GX10 full-cleanup 1.7B training results

**Doc link:** [protocol](PROTOCOL.md)

**Status:** RUNNING — artifact transfer and host-port preparation,10-19-2026.

**Last updated:**10-19-2026.

| Phase | Status | Observed evidence |
|---|---|---|
| SNAP duplicate-run fence | DONE | Idle watcher2110195 stopped; zero cleaned optimizer updates/pipelines |
| Interim818-replacement data freeze | DONE |10,940 rows; control input only |
| Single artifact relay | IN PROGRESS | Owned by `/root/unattended_and_gap_sources`; preserve partial files if SSH expires |
| Astra training port | IN PROGRESS | Thin host/path wrapper; frozen V12 source remains unchanged |
| Full1.7B longest-sequence control | PENDING | Actual16,112-token optimizer update required |
| V18 final cleanup dataset | PENDING | Process all remaining1,540 rows; coverage/exclusions explicit |
| Final production first update | PENDING | No V19 production update yet |
| Full1,080-cell validation | PENDING | Frozen prompts/manifest, GPU Transformers fallback available in plan |
| Native Lean/kernel controls | DONE | Real nativeARM compile+kernel accepted symbolic proof/anonymousnative test, rejected sorry/axiom/namednative; exact frozenkernel hash |
| Full scorer /1,080-cell scoring | PENDING | Full source/prompt bundle pending relay; verifier unchanged |

V12 current-data validation finished at120/1,080 binary successes (11.11%,135-task bootstrap95%6.94–15.83%), below25%. Its [failure analysis](../expt_v12/RESULTS_current_failures.md) found no `exact?` in971 extracted outputs; type/proof/test/implementation failures dominate. This result motivates the declared full cleanup comparison and independent training-data improvements, not benchmark-specific teacher repairs.

**TLDR-end:** [rl-4-code-verification: GX10 final cleanup] Preparing the full1.7B hardware control and complete training/evaluation path. Production waits for the V18 final dataset; the interim818 snapshot is not presented as the final condition.
