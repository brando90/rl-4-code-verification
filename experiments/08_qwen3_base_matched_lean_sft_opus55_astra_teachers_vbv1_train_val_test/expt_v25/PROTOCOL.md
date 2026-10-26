# V25: matched automation-proof comparison with V20

**Doc link:** [experiment home](README.md); [reference fresh-run protocol](../expt_v20/PROTOCOL.md)

**TLDR:** User requested a matched run against the fresh1.85% V20 condition using automation-based proof versions while keeping comments. Keep exactly the same3,568 training examples, prompts, batches, initialization and optimization exposure; change only eligible proof versions and the proof-specific comments needed to describe them truthfully. Freeze exact pairing counts/hashes before updates.

## Matched reference

- ReferenceV20:3,568rows=684Python-to-Lean+2,145Workbook+61Workbookrepairs+678public proofs; onepass/1,784updates. Its full135task×8sample validation score is20/1080. Preserve its data/model/evaluation artifacts unchanged.
- Start again from official Qwen/Qwen3-1.7B-Base revisionea980cb0a6c2ae4b936e82123acc929f1cec04c1, same seven-file manifest and original pretrained weights, fresh optimizer. No V20/V23 trained weights or optimizer state.
- Preserve V20 UID/task/prompt identities, pool memberships, training row order and batch-index schedule exactly. No added500tiny examples, no125late alternatives, no source rebalancing, no dropping/replacing unpaired tasks. Every selected example appears once under the same seed20261019.

## Proof-version intervention

- Recover source-bound pre-cleanup proof counterparts from retained original Python examples and the same-statement public proof collections. Restore verified simp/omega/search-based proof bodies, preserving implementations, APIs, specifications, theorem statements, tests, FILE format and original system/user messages. Record each changed proof/source hash and exact predecessor provenance.
- User explicitly chose “Keep comments; restore simp/omega proofs.” Retain proof-sketch headers and meaningful inline-comment requirements. Keep existing comments where accurate; mechanically adapt only proof-specific descriptions that become false after restoring a different strategy. Record changed comments separately. Do not insert misleading explicit-proof descriptions over automation proofs.
- This condition relaxes the training-data tactic ban as its intended treatment. It does not relax Lean compilation, theorem honesty, statement preservation or scoring. No sorry/admit/new axioms or native_decide in named proofs. Preserve the original anonymous concrete-test exception. Reuse exact valid proof receipts; compile changed reconstructed sources only where needed to establish validity.
- Restore only predecessor proof spans containing the targeted automation; a different but also-explicit predecessor is not an intervention. Valid original automation spans may be composed with unchanged V20 proof spans where an original slot was unsafe (for example native_decide in a named numeric-test theorem); verify the exact resulting source and record per-proof partial restoration.
- If no valid same-task automation predecessor exists, retain the exact V20 row unchanged and report the pairing gap. Never choose a different statement or failed proof to force an automation example. Public examples that were already explicit remain unchanged. Publish exact changed/unchanged counts by source and retained tactic inventory before training; interpret the result as the documented paired subset, not a claim that all3,568 rows acquired automation.
- Recheck frozen FILE/Qwen template,16,384token cap without truncation and protected exact/near screens against764references. A format/cap/screen/validity issue in a predecessor falls back visibly to the V20 row, preserving the full matched cohort. No teacher generation or validation-derived proof repair.

## Training and resources

- Preserve V20 microbatch1, accumulation2, assistant-only token-weighted loss and supervised end tokens; float32 parameters/AdamW moments, bfloat16 autocast, SDPA, gradient checkpointing; beta=(0.9,0.98),epsilon1e-5,decay0.1,clip1.0. Use the exact V20 learning-rate sequence per optimizer update via its recorded reference token clock so shorter/longer proof versions do not shift warmup/decay. Record the reference schedule/source hashes and actual treatment loss-token totals.
- Proof lengths and compute necessarily differ; disclose both, without claiming equal-token training. Same example order, step count and learning rates permit a clearer comparison than changing dataset size or initialization. Comment wording may change when needed for truthful descriptions, so this does not isolate literal token substitutions from explanation content.
- Use one freshly admitted empty80GB A100 on skampere1 under the shared E08/E13/device locks, CUDA_VISIBLE_DEVICES explicit. GPU3/4 were empty at initial inventory; select only a currently empty/unleased device. Estimated40–70GB allocated, mostly GPUcompute; estimated30–60minutes training, revised from observed throughput. Preserve foreign jobs.
- Run discarded exact-base longest-plus-shortest control, then reload original weights and fresh optimizer for actual production. Persist first update, realPID/device/source identities, full steps/loss, durable checkpoints and final HF hashes. Remote death/stall monitor covers the full pipeline. No silent optimizer reset after updates. Training deadline12hours; generation/scoring8hours each.

## Evaluation and retained logs

Evaluate the same frozen135VeriBenchV1 validation tasks×8samples=1080cells, same prompts/adapter/kernel/binary scorer, seed91,temperature0.6,top-p0.95,top-k20,thinkingon,max12288newtokens andim_end stop. Preserve the full manifest, exact infrastructure retries and every failed/missing cell. Test222 remains sealed. No paid judging/model calls.

Use the v24 future_logging/parallel_scoring_logged.py default entry with32sharedCPUslots, durable compiler/kernel stdout/stderr, source/compiler identities and timeout/exit receipts. Apply the already verified compatible SciPy overlay and writable cache settings prospectively. New RUN/corpus_training_v25 namespace keeps every reference/result immutable. Report paired task-bootstrap comparison and complete diagnostic categories after full scoring, one seed per condition; no isolated effect claim about comments, which are retained in both conditions.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).
