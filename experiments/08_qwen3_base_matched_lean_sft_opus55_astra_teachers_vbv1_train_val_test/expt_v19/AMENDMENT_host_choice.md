# V19: choose one execution host before production updates

**Doc link:** [protocol](PROTOCOL.md)

**TLDR:** Prefer the original SNAP A100 runtime if an adequate device is genuinely empty before production starts; otherwise use the validated GX10 fallback. This choice is frozen before the first final-condition update and does not depend on model scores.

The root coordinator clarified this choice on10-19-2026 while V18 cleanup and transport recovery were pending. GX10 setup and the discarded full-model control remain useful. The old V12 partial-condition watcher remains fenced permanently; it is not restarted to train the818 snapshot.

After the final dataset is ready, inspect real device contexts and admission leases. Select one host, record the hardware/runtime/source/data identity, and launch exactly one V19 final-condition trajectory. If SNAP is selected, preserve the original Torch2.7.1, frozen generation and scoring route; the GX10 runtime changes in the base protocol apply only if GX10 is selected. Once actual production updates exist, preserve that trajectory and handle infrastructure failures explicitly; do not start a duplicate or switch hardware based on validation scores.

All data coverage, unresolved exclusions, full1,080-cell validation and unchanged verifier requirements continue to apply.
