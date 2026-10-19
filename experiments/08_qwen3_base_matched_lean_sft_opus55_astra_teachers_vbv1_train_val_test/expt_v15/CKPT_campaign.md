# Adaptive1.7B campaign recovery checkpoint

**Doc link:** [live results](results.md)

**TLDR:** First run complete at11.11%; final cleanup and GX10 second-run preparation are ready. Cluster reauthentication is required before new cleanup calls and checkpoint transfer can begin.

## Current state
- Updated 10-19-2026 10:49 PDT. One local writer owns publication in `.worktrees/rl4cv-sol-repair-10-19-2026`; the automatic publisher is paused during source repair/publication.
- Remote RUN `/lfs/skampere1/0/eth127/rl4cv_tiny_training`; GX10 `/home/lethan3/workspace/rl4cv-gx10/experiment-v19`.
- V12 current COMPLETE: 5,470 updates, 120/1,080 validation successes; independent full recomputation PASS. Raw/scored outputs are immutable. Full 851-file compiler diagnosis is complete.
- V13 DONE_PARTIAL: 818 replacements +227 unchanged +1,540 flagged fallbacks, all2,585 accounted. This historical phase remains immutable.
- V12 partial-cleanup training prepared but received ZERO optimizer updates. Watcher2110195 fenced for GX10 migration; receipt in V12/results/gx10_migration_fence.json.
- V18 source/protocol/watch/finalizer ready; local filesystem-only deployment watcher waits for the existing SSH control socket. No V18 paid calls launched at last verified observation.
- V19 prospective final-cleanup training protocol and single streaming relay are ready. Real full1.7B longest-sequence GPU control has not run; earlier tiny-model GPU installation controls passed.
- All sufficiently large inspected SNAP GPUs were occupied by foreign jobs. GX10 reachable with about115GiB memory available. User explicitly authorized GX10 and Astra code porting.
- Global paid ceiling900, cleanup780/adaptation120 including prior charges and reservations; campaign_budget.py preserves all old ledger entries. Teacher model Terra/high; one Astra/high code-porting exception only.
- V14 admission provides678 eligible examples via latest_admission.json; retain separate source/format/exclusion evidence.
- SNAP authenticated master dropped around10:40PDT. One human login is pending in `tmux attach -t ssh-tiny-training`; press Enter then complete the CS password prompts. No automatic gateway login retries.
- Remote V15 recovery watch and waiting V17 adaptive process last verified before disconnection; current liveness is unknown until login returns. Do not report a waiting receipt-only trial as new training.
## Next commands
- After the control socket returns, notify all three owners; their local deployment watchers launch V18 cleanup and the single V19 Astra/relay route. Avoid duplicate deployment.
- Inspect V15 outer watch and V17 manifests/liveness; preserve healthy remote jobs and fence only this campaign's idle conflicting GPU dispatcher if necessary.
- Run V19 full-model disposable control, assemble accepted-only V18 final dataset, freeze inputs, launch actual second training and finish all1,080 validation cells and scoring.
- Publish compact task/cell tables, source, amendments and verification receipts. Deployment of the updated local V15 source waits for restored SSH and a safe owner restart.
## Log
-10-19-202606:14PDT -- Frozeninitialcampaigncontract; prior68repaircompletionpublished9f9f163; currenttrainingandcleanupremoteownerspreparing.
- 10-19-2026 10:30 PDT -- Recovered orchestration, verified actual120/1080recompute, froze partialcleanup and releasedsecondpreparation; newpublicdataadmission ready.
- 10-19-2026 10:49 PDT -- Recorded900authorization, final-cleanup/GX10 owners, fenced zero-update partial dispatcher, SSH outage and pending human login; preserve all historical outcomes.
- 10-19-2026 11:05 PDT -- Full GX10 Linux verification PASS:1360tests+6subtests,30skips; native kernel and six pipeline controls PASS. Full second-run watchers armed; publication prepares exact owned metadata. Cluster login remains the external prerequisite.
