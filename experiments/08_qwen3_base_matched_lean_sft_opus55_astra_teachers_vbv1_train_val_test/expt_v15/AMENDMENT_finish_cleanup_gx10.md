# Finish proof cleanup and run the second 1.7B condition

**Doc link:** [campaign protocol](PROTOCOL.md)

**TLDR:** The user authorized another conditional $300, bringing the campaign maximum to $900, and explicitly permitted GX10 execution and an Astra code-porting worker. Historical partial cleanup and training records remain immutable; version18 completes the remaining cleanup and version19 owns the requested final second run.

Recorded 10-19-2026 before any version18 paid call or version19 production optimizer update.

## Authorization and accounting

The shared ledger remains `RUN/adaptive_1p7b_campaign/budget.json`, where `RUN=/lfs/skampere1/0/eth127/rl4cv_tiny_training`. The additional authorization raises the total ceiling from $600 to $900, including conservative charges and active reservations. Internal maximum allocations are $780 cleanup and $120 adaptation, including all historical charges. Activate the third tranche only when needed for remaining work and bounded in-flight exposure; record the reason. No old charge is discarded or reduced merely to free allowance.

New work uses [campaign_budget.py](campaign_budget.py), with atomic reservations, model-specific estimates and bounded CLI calls. Preserve the old version13 helper and phase limits as historical evidence. Terra/high remains the teacher and adaptation model. The user authorized `gpt-6-astra`/high for code porting only; it may use at most one bounded worker, charged to adaptation, with a $40 worst-case reservation and a $3 observed conservative stop. Estimates are not invoices. Approved lab credentials stay outside Git and are supplied only to the approved command-line client.

## Execution and evidence

Version13 ended with 818 verified replacement answers, 227 unchanged originals and 1,540 flagged original fallbacks. Its completion is not rewritten. [Version18](../expt_v18/README.md) processes those remaining rows using focused prompts, reuses valid partial proofs, and admits only explicit proofs with unchanged statements and actual pinned-kernel, template, token and protected-source checks. Unresolved rows remain visible; they are never silently labeled cleaned.

The prepared 818-replacement dataset received no production optimizer update. Its idle SNAP dispatcher was fenced before migration. [Version19](../expt_v19/README.md) may use that dataset for a discarded full-model hardware control, then assembles the final cleaned cohort and trains the requested second condition from the same original mixed checkpoint. Exclusions and changed row/token counts are disclosed. Existing non-original data keeps its previously recorded fallback policy.

All sufficiently large SNAP GPUs were occupied at the migration check. The user explicitly offered the GX10; use its installed user environment and record the changed host, CUDA/PyTorch runtime and actual generation backend. Keep the fixed 135-task ×eight-sample validation manifest, prompts, scorer, kernel and binary-success definition. Finish all 1,080 cells and scoring; the sealed test split stays sealed.

The authenticated cluster connection dropped at approximately 10:40 PDT. Remote jobs survive independently; fresh access needs the user's CS password. One replacement interactive login is provided in local `tmux attach -t ssh-tiny-training`, with no automatic gateway retry loop. Preparation and deterministic checks continue locally and on the reachable GX10 while that login is pending. Deployment status is recorded separately from local source readiness.
