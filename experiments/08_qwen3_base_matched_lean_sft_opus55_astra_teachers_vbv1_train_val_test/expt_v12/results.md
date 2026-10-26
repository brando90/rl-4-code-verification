# Current-corpus1.7B run completed:120/1,080validation successes

**Doc link:** [protocol](PROTOCOL.md)

**TLDR:** Complete first-run training and evaluation:120/1,080binarysuccesses (11.11%), with task-bootstrap95%interval6.94–15.83%. The partial-cleanup dataset was prepared with818verified replacements and zero production updates; its SNAP dispatcher was then fenced. The final second condition waits for version18 cleanup and executes under version19.

**Last updated:** 10-19-2026 12:56 PDT.

| Measurement | Result |
|---|---:|
| Training examples consumed | 10,940 |
| Optimizer updates | 5,470 |
| Assistantloss tokens | 13,168,888 |
| Training time | 7,889seconds |
| Peak allocatedGPUmemory | 57.60GiB |
| Declared/scored validation cells | 1,080/1,080 |
| Binarysuccesses / compilingoutputs | 120/120 |
| Extractedoutputs | 971 |
| Length-cappedoutputs | 110 |
| Tasks with at least one success out of eight | 28/135 |
| Tasks with two–six successes out of eight | 16/135 |

The primarysuccessrate interval resamples135tasks, retaining their eightattempts,10,000draws,seed0; one trainingseed; p-value not computed. The25%validationtarget is unmet. Frozenprompt/scorer/kernelsettings and test-split isolation are preserved. Independent ordinary-code recomputation matched all1,080cells and the120successes.

The same 1,080 validation cells have nonzero reinforcement-learning reward signal: admitted signal density ρ is 15.37 [9.37, 22.76] advantage mass per million generated tokens, and effective coverage H is 0.164 [0.107, 0.228]. Twenty-four of 135 tasks are mixed (1–7 successes out of 8), and 4 of 135 are perfect, which accounts for the published 28/135 with at least one success. Intervals resample whole validation tasks, 10,000 draws, seed 0; p-val=n/a. Sherlock job 48510183 reproduced the measurement. Details: [signal audit](rl_signal_audit/results.md). This is necessary reward variation, not a measured reinforcement-learning improvement.

Compared descriptively on the samevalidationcohort, current minus previous replay is+1.94percentagepoints, pairedtask-bootstrap95%interval[−0.09,+4.17]; current minus previoustiny-mixed is+4.26points,[+2.13,+6.67]. Those are differentdata/token/continuationregimes; no single-component causalclaim follows. DetailedCPU-onlyfailureanalysis is separate and doesnotchange scores.

[Summary](results/analysis_v12_current_summary.json) · [All1,080cells](results/analysis_v12_current_cells.csv) · [135taskresults](results/analysis_v12_current_tasks.csv) · [Frozenadmission](results/current_prepare_receipt.json).

The frozenpoolcontains2,585originalPython-to-Lean,500tiny,7,794Workbookand61repairedWorkbookexamples. DatasetSHA256 `6b0cce0608a11b2aa7d31e1343c6db0ba8ade08fdbd62ec68914884064a9df3e`; source/protocolhashesandstartingweightsunchanged. TrainingandrawvalidationoutputsremainonSNAP behindtheartifactmanifest.

## Second-condition continuation

The prepared partial dataset remains frozen evidence, not a completed second training run. See [the migration fence](results/gx10_migration_fence.json), [full-cleanup continuation](../expt_v18/README.md) and [GX10 production protocol](../expt_v19/PROTOCOL.md). No clean-data improvement is claimed before that full run and its validation finish.
