# V19: fully processed proof-cleanup 1.7B continuation on GX10

**Doc link:** [protocol](PROTOCOL.md)

**Status (QA 11-25-2026): SUPERSEDED by expt_v20 (user stopped the full cleanup; V19 saw zero production updates).** **TLDR (earlier):** Prepare the complete 1.7B training and evaluation pipeline on GX10, verify its longest sequence with a discarded optimizer update, and train the requested final cleanup condition after V18 finishes processing the remaining original-pool proofs.

**Status:** Preparing on 10-19-2026. The SNAP second-run watcher is fenced; no V19 production optimizer update has occurred.

The V13 dataset with 818 replacements is a control input for memory and runtime verification. It is not the final fully processed comparison dataset. The final original-pool data comes from V18; unresolved exclusions and actual proof-cleanup coverage will be stated explicitly. The 500 tiny examples, 7,794 admitted Workbook statements and 61 repaired Workbook examples retain their previously admitted policy.

This continues the completed V12 current-data run (120/1,080 validation successes) from the same V6 mixed starting weights. Hardware and PyTorch change, so the comparison does not isolate a causal effect of proof cleanup. The end-to-end deliverable includes all 135 validation tasks × eight samples, frozen extraction/scoring and the existing non-vacuity rule; weights alone do not complete this experiment.

See [live results](results.md), the [checkpoint](CKPT_gx10_training.md), and the unchanged [V12 failure analysis](../expt_v12/RESULTS_current_failures.md).
