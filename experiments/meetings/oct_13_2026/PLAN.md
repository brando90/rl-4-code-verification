# Matched warm starts for Lethan and Rakshit

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/meetings/oct_13_2026/PLAN.md>

**TLDR:** Lethan owns Qwen3 Base 1.7B and 8B; Rakshit owns 4B and 14B. First diagnose the smaller models’ output failures, then compare additional exposure to the original data against a screened expansion at the same training-token budget across all four sizes. Reuse the existing training, recorded matched evaluation and cached teacher outputs; select future training choices on validation only.

## What the meeting decided

Source: Brando’s supplied `transcript.md` in this folder, meeting 10-13-2026. Its byte hash and source handling are recorded in [provenance.json](provenance.json). The transcript remains unchanged in the original folder. Its automatic transcript has inconsistent names and numbers; the executable records below settle checkpoint sizes and counts. Lethan is `@lethan3` (called Ethan in the meeting; surname differs between the roster and newer access record). Rakshit is Rakshit Kaushik, `@rakshit-kaushik`.

- Start from **Base** models and use the same supervised fine-tuning (SFT) examples, order and loss-token budget at every size. A billion parameters is abbreviated B in model sizes.
- The immediate goal is a reliable warm start for reinforcement learning (RL). Environment selection and whether factored feedback improves downstream success remain the research goals after this dependency.
- Each owner should bring measured results and a short presentation to the next meeting. Rakshit expected to resume after his midterm; the transcript’s “tomorrow”/“Friday” wording is not an exact agreed deadline.
- Lean training targets must compile and contain genuinely proved theorems; benchmark evaluation data are not training data.

The current Stanford weekly notes were checked on 10-13-2026. Their newest dated section is 10-09-2026 and still concerns downstream prediction using item response theory; they do not supersede this meeting’s warm-start assignment. The notes were not edited.

## The starting point is further along than the meeting suggested

Canonical experiment: [08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test](../../08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/README.md).

All four sizes already completed **658 updates / 5,752,936 loss tokens**, using the same **1,315 examples from 476 of 539 train tasks**. The smaller models were evaluated on validation; they failed output extraction and length gates. They do not need their original training repeated simply to fill a missing record.

The earlier test comparison used 8B at step 658 but 14B at step 334. It cannot establish that the larger model is worse after matched training. Version 2 attempted to evaluate 1.7B, 4B and 14B at step 658 and reuse the existing 8B result. At 10-13-2026 17:33 PDT, the existing owner `codexv-rl4cv-e08v2-matched-test` and its generators were verified live on `skampere1` after a compiler-environment repair. **Superseding status, 17:49 PDT:** the owner closed this attempt PARTIAL under its route-controls gate. The Vals organization lacks managed execution access and its existing provider mapping; 0/5,328 new generations persisted before closeout, and all new test scores remain unknown. Owned jobs were stopped and resources released. Resume requires restoration of the existing Vals route and revalidation of payer, judge bundle and controls. Follow [the owner’s results](../../08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/results.md) for subsequent counts.

The closed evaluation retains its recorded owner and recovery contract. Our new material is in `expt_v3`; its preparation and later training outputs must not overwrite version 1 or 2.

## Define the target before trying to reach it

**Smooth Conjunctive Score for Code verification (SCSC)** is the geometric mean of three factor means on the same measured cohort: test correctness, proved-theorem fraction and compile-gated formal specification coverage. A score of 0.25 is not a 25% probability of success.

Varun described **25–75% success with eight attempts**, then the meeting shifted to “25% accuracy or SCSC.” Keep both objectives visible:

1. **User’s performance milestone:** SCSC ≥0.25, assessed prospectively on validation for development, with all three factors, counts and task-bootstrap intervals. This has not been measured on the existing validation ladder; its binary pass rate is not a substitute.
2. **RL learning signal:** report binary successes out of eight, the fraction of tasks with both successes and failures, and the observed 2–6/8 band. Eight attempts give a noisy estimate of task difficulty. Neither a pooled mean nor the smooth score establishes that most tasks fall in the useful band.
3. **Existing frozen gates:** at least 972/1,080 extracted files, no more than 108/1,080 capped responses, and at least 7/135 mixed-success tasks, with all inputs known. Keep these historical verdicts intact. A common passing checkpoint across all four sizes is still absent.

The [completed audit](../../08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/RESULTS_continuation_audit.md) recomputes current validation measurements. At the shared full budget, binary success is 0.0963 [0.0630, 0.1343] for 8B and 0.1204 [0.0833, 0.1620] for 14B. Each has 135 tasks ×8 attempts; 95% task-bootstrap intervals, 10,000 draws, one training seed, p-val=n/a (no hypothesis test). These measurements support investigating improvement, not a promise that a little more data reaches 0.25 SCSC.

## Work assignments and order

Priorities are proposed next-work importance, not effort estimates or agreed deadlines. Both owners consume the **same frozen corpus and recipe**; model ownership does not authorize separate training recipes.

| Priority | Owner | Work | Completion evidence |
|---|---|---|---|
| [p 10/10] | Existing matched-evaluation owner after Vals route restoration; Lethan/Rakshit read their sizes | Resume and finish `08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2`; avoids duplicate training and test calls | Full 5,328 new-cell accounting, exact checkpoint hashes, all factors and separate core/IndustrySet rows |
| [p 9/10] | Lethan: 1.7B; Rakshit: 4B | Diagnose smaller-model failures using validation outputs; these are the immediate common-checkpoint blocker | Counts for missing extraction, length cap, compile error, unproved theorem and vacuity, plus representative validation examples; distinguish overlapping flags |
| [p 9/10] | Rakshit prepares cached responses; Lethan prepares the earlier Python-to-Lean pool | Build one expansion candidate pool; reuse paid-for outputs before generating more | Admitted/rejected manifest, rejection reasons, hashes, exact loss tokens, per-source/family/task coverage |
| [p 8/10] | Both, assigned sizes | Prepare and then run the same two-condition continuation after its protocol is frozen; separates more exposure from the expanded-pool intervention | Identical within-condition loss budgets across sizes, validation results for every declared checkpoint, one common selection decision |
| [p 8/10] | Both | Prepare one concise results page each before the next meeting; makes the meeting about findings | Baseline → change → measured result with uncertainty → next decision, plus one failed example and one successful example |

### Lethan can start here

1. Read the audit for 1.7B/8B. For 1.7B, the separate deficits are **75 more extracted outputs** and **76 fewer capped outputs** to meet the frozen gates; these need not be different files. Inspect tokenizer/template/stop handling and token-cap failures before attributing everything to insufficient model capacity. The harness extracts Lean files from text; “malformed JSON” in the meeting is a hypothesis, not an established failure cause.
2. Retrieve and verify the existing **Mostly Basic Python Problems (MBPP)** data using the command below. Access was reported resolved after the meeting; there is no need to recreate the canceled email attachment or release. Successful retrieval on Lethan’s machine remains unverified.
3. Convert the earlier `system/user/lean` rows into the new version’s explicit assistant format, preserving exact Lean bytes and provenance. Freeze the encoding, check extraction round trips and masked loss spans, screen the full rendered content, and report accepted counts and tokens. Do not directly concatenate unlike schemas.
4. Train/evaluate 1.7B and 8B under the shared version-3 manifest once preparation is complete. Pair with Rakshit on the manifest before either starts.

### Rakshit can start here

1. Read the audit for 4B/14B. For 4B, the separate deficits are **26 extractions** and **26 fewer capped outputs**. Reconcile failure modes with Lethan using the same categories.
2. Use [cached_train_candidates.csv](../../08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/results/cached_train_candidates.csv): **685 responses** excluded only by the historical per-teacher cap. The audit checked their train membership and recorded success/screen receipts. Fetch by the listed paths and verify hashes, then redo normalized deduplication jointly with the selected data and MBPP conversion.
3. Publish the shared accepted corpus, order and token schedule. Those 685 candidates span 360 **already-covered** train tasks; 389 are security examples. They add solution variants rather than new source-task coverage, so report family balance and unique task coverage separately from tokens.
4. Train/evaluate 4B and 14B under that same manifest. The earlier 14B test used half as many loss tokens as 8B; use the matched evaluation once its route blocker is resolved for the size comparison.

## The next comparison

Continue in [08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3](../../08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/README.md). The central uncertainty is whether failures improve with **additional exposure** or with an **expanded source/solution pool**.

- **Replay control:** continue each size from its frozen step-658 checkpoint on the original selected data.
- **Expanded pool:** continue the identical checkpoint on the original data plus admitted cached responses and admitted MBPP pairs.
- **Proposed bound:** one additional original-budget equivalent, **5,752,936 loss tokens per size and condition**; measure at half and all of that additional budget. All four sizes run both conditions; eight training continuations and 17,280 validation generations (2 conditions ×4 sizes ×2 checkpoints ×135 tasks ×8 attempts). This is a proposed study, not a launched run.
- **Keep it interpretable:** pin seed, template, masks, full-parameter optimization, sampling and verifier. Reset the additional-phase learning-rate schedule explicitly—the original cosine schedule ended at zero. Freeze how token budgets, last-batch masking, optimizer state, checkpoints and learning-rate progress work before training. Match those rules across conditions; log updates, processed tokens and wall time as well as loss tokens. Equal tokens need not mean equal updates or compute.
- **Prospective decision:** first seek a common checkpoint satisfying the existing format/signal gates. If both conditions qualify, prefer the expanded pool only if the minimum success rate across sizes improves and no size has a paired validation difference whose 95% interval lies wholly below zero; otherwise prefer replay or call the choice inconclusive. If neither qualifies, use the failure taxonomy to design a new version rather than silently adding epochs. Freeze this agent-proposed decision rule before measurement.
- **SCSC milestone:** evaluate the frozen candidate checkpoints on the declared validation set using the validated coverage judge and the official factor aggregation; report whether ≥0.25 is attained. Preserve judge/model pins and record judge calibration limits on these student outputs. Only then freeze the checkpoint/forecast for its single test evaluation. This is distinct from the version-2 test report, which is currently partial because its judge route failed admission. New judged evaluation also requires that route to work.

This initial comparison tests the expanded pool as one intervention; it does not isolate the effects of capped-response reuse versus MBPP, or diversity versus teacher/style changes. If it helps, a later ablation can separate those. More teacher generation, larger models and mathematics-only OpenR1 data are lower-priority alternatives after this inexpensive reuse path; they are not required dependencies.

## Data and execution contract

For new training, VeriBench V1 has **train 539 / validation 135 / test 222**. Training uses train tasks only; validation supports development; test never chooses the recipe. The older `02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v3` held out all 896 VeriBench V1 tasks and retains that historical rule. Newly mixing its outputs still requires a joint screen against the protected validation/test data and a source/duplicate-group check.

Exclude external HumanEval-derived data. Existing `humaneval_set` tasks assigned to VeriBench V1 train by the frozen split are a different case and remain governed by that split. VeriBench-Infinity is not automatically a training pool: identify source tasks and all variants, assign protected groups, and prove disjointness before admitting any material. Use only existing approved sources in the first comparison.

Training and model evaluation execute on the Stanford Network Analysis Project (SNAP) cluster under named persistent owners with full access, frozen manifests, progress records and a verified watchdog. Recheck the current allocation; preserve the closed version-2 evidence and its recovery contract. Teacher generation and coverage judging by Brando’s accounts use the project’s Vals-funded Valkyrie route; the transcript’s generic suggestion to use lab keys does not override current funding rules. Raw data and weights remain on the execution host; publish manifests and summaries in this private repository.

### Dataset retrieval and verification

Access update: [assistant’s superseding record](https://github.com/brando90/agents-config/issues/68#issuecomment-6157904333). The earlier release request was canceled. Use the recipient’s own working cluster login, not Brando’s username or credentials:

```bash
scp <your-cluster-login>@skampere1.stanford.edu:/lfs/skampere1/0/brando9/rl4cv_e02a_v3/sft/lean_warmstart_v3.jsonl .
shasum -a 256 lean_warmstart_v3.jsonl
```

Expected full hash: `2a3380227dedcb53aa449d50e2823e4a34bfb25ecdcf5b0c1c618b280d6b3c8a`; expected **587 rows / 455 distinct task identifiers**. If direct-node connectivity fails, check the official `whale.stanford.edu` gateway before concluding that a virtual private network is required. File readability by Lethan is not proven by an account-access announcement.

The matching original SFT dataset is `/lfs/skampere1/0/brando9/rl4cv_e08/sft/s_v1.jsonl`, hash `885d4ae2d6cf193bddc43df6ad6274cacfa8c98a5e5ecd63bd2519472f5e7354`. The original assembler defaults overwrite version-1 outputs: create a version-3 assembly path and explicit output paths first.

## Already completed for the team

- Reconciled the transcript with the actual training, validation and evaluation records, including the concurrent partial closeout.
- Recomputed the four complete validation success distributions and task-bootstrap intervals without model calls.
- Produced the 685-row cached-candidate manifest with train-membership, kernel/screen checks and source hashes, and verified all 685 response files on the cluster.
- Identified the existing 587-pair dataset, verified its full file hash and all 587 Lean hashes on the cluster, and documented the conversion requirement and superseded access blocker.
- Prepared the next controlled comparison and divided implementation and model ownership.

No new training, teacher generation or coverage judging was launched by this follow-through. The outstanding work is corpus admission, failure diagnosis and the frozen comparison. The separate matched evaluation needs Vals to restore the recorded managed route; this is an infrastructure dependency, not a new permission gate for corpus preparation.

**TLDR-end:** [rl4cv: matched warm starts for Lethan and Rakshit] Lethan owns 1.7B/8B and Rakshit 4B/14B, with one shared recipe. Recover the matched evaluation after its route repair, diagnose formatting, then test additional exposure against a screened expansion before buying more teacher data.
