# Experiment 08 version 3 protocol — matched replay versus admitted expansion (DRAFT, NOT LOCKED: lock before any training)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/PROTOCOL.md>

**TLDR:** Continue each frozen step-658 checkpoint (1.7B, 4B, 8B, 14B) under two conditions at the same additional budget of 5,752,936 loss tokens: replay of the original 1,315-example corpus, or the original corpus plus the admitted expansion. Evaluate on the 135 x 8 validation manifest at half and full budget with the frozen format/signal gates, apply the meeting's prospective decision rule, and only then judge the SCSC >= 0.25 milestone. Defaults resolved under Brando’s 10-15-2026 dispatch; lock publication precedes every version-3 supervised fine-tuning (SFT) step, including the disposable dry run.

**Status:** DRAFT, NOT LOCKED. Recommended defaults resolved; static verification is in progress. Version 1 (`../PROTOCOL.md`) and version 2 stay frozen; this version changes only what is listed here.

## 1. Question and conditions

Does more exposure to the same data, or a broader screened pool at the same loss-token budget, move the four sizes toward a common checkpoint that passes the frozen warm-start gates?

| Condition | Training pool | Start | Additional budget |
|---|---|---|---|
| **R** (replay) | the frozen version-1 corpus S: 1,315 examples, 476 train tasks, host `sft/s_v1.jsonl` SHA-256 `885d4ae2…` | step-658 export of each size | 5,752,936 loss tokens |
| **E** (expansion) | S plus every example admitted by `admit_corpus_v3.py` (`results/admitted_corpus_manifest.csv`, `admitted = 1`; host `sft_v3/s_v3_candidates.jsonl`, hash in `results/admitted_corpus_stats.json`) | the same exports | 5,752,936 loss tokens |

Eight continuations (2 conditions x 4 sizes), 16 validation ladders (2 checkpoints each), 17,280 validation generations. Both owners use the same corpus files, order rule and recipe; model ownership does not authorize separate recipes.

## 2. Data (frozen inputs)

- Split: D-013 (`../expt_v1/results/split/vbv1_split_manifest.csv`, SHA-256 `157ce781…`): train 539, validation 135, test 222. Training uses train-split VeriBench tasks and the MBPP (Mostly Basic Python Problems) pairs only; validation selects; test is not touched by this version.
- Admission (already run, zero model calls): hash verification of S, the 685 cached teacher responses and the 587 MBPP rows; MBPP conversion per [mbpp_conversion_spec.md](mbpp_conversion_spec.md); joint deduplication by `rl4cv.screens.norm_hash` and word-5-gram Jaccard >= 0.70 with S always kept; held-out screen of file, full assistant text and each fenced block against the 714 validation/test Python and gold Lean texts at VeriBench pin `c11b99ba`; tokenizer byte/token prefix, loss-span and 16,384-token checks. Rejections are listed by reason and never repaired.
- Admitted on 10-14-2026 (`results/admitted_corpus_stats.json`, host corpus SHA-256 `7fa02557…`, manifest SHA-256 `3ed7cb7a…`): 2,585 of 2,587 candidates — all 1,315 originals (5,751,621 rendered loss tokens; version 1's 5,752,936 adds the pipeline's one `<|endoftext|>` per example), all 685 cached responses (2,924,523 tokens, 360 train tasks, 389 security-set) and 585 of 587 MBPP pairs (2,505,008 tokens, 453 tasks; 2 rejected `over_length_cap`). Joint deduplication found 0 exact and 0 near duplicates; the held-out screen found 0 exact and 0 near hits over 7,761 texts. New loss tokens: 5,429,531 rendered (5,430,801 with the per-example end-of-text token), so the whole E pool holds 11,181,152 rendered loss tokens over 929 unique tasks. Confirmed against the committed manifest and host bytes on 10-15-2026. Full corpus SHA-256: `7fa0255741a2b6046ceda0dfda43664334ca603a0aeca9fc2424af43c849726b`; manifest SHA-256: `3ed7cb7a0844a56d9072498651a2b7b38e15e017d781847d6fcd7825b2f2980e`.

## 3. Example order and budget accounting (identical rule in both conditions)

- Order: ascending `sha256("rl4cv-e08-v3-sft-order-v1:" + source + "|" + task_id + "|" + teacher + "|" + sample)` over the condition's pool (`order_key` in the corpus file). In R this is a fresh deterministic permutation of S (not the version-1 order, so batches do not repeat the first epoch exactly); in E it interleaves original and admitted examples uniformly, so the half-budget checkpoint has seen a representative mix. The order is identical at every size.
- Batching as version 1 § 8: global batch 2 sequences, step j consumes examples 2j-1 and 2j, no packing, no reshuffling; if the pool count is odd the last step pairs one real example with one fully loss-masked padding slot.
- Budget boundary: precompute the cumulative-loss-token schedule from the manifest's `n_assistant_tokens` (the rendered loss span, including the template's `<think>\n\n</think>\n\n` prefix and `<|im_end|>\n`, plus the trailing `<|endoftext|>` counted at lock as in version 1). The half and full checkpoints are the first steps whose cumulative additional loss tokens reach 2,876,468 and 5,752,936; a crossing step is trained in full and its overshoot is reported. Training stops after the full-budget step. R therefore makes exactly 658 updates; E makes however many updates its schedule needs (fewer if its mean loss span is longer), and the realized counts are reported. Equal loss tokens do not mean equal updates, processed tokens or compute.
- In E a single pass in the fixed order will not reach the end of the pool if the pool holds more than 5,752,936 loss tokens; the realized per-source mix of what was actually consumed is reported from the schedule, not assumed.

## 4. Recipe (identical at every size and in both conditions)

- Start weights: each size's step-658 Hugging Face export (`ckpt/<size>/hf/step_658`), hash-verified against `weights_sha256_manifest` in `../expt_v1/results/ladder_manifest.json`; these are the weights the validation ladder measured.
- Optimizer: AdamW lr 2e-5, betas (0.9, 0.98), eps 1e-5, weight decay 0.1, gradient clip 1.0, full-parameter bf16, assistant-only loss normalized over the global batch's real assistant tokens, seed 20260830 — version 1 § 8 unchanged.
- **Learning-rate reset (explicit):** the version-1 cosine schedule ended at zero, so the continuation does not inherit it. New schedule per condition: `LinearLR(start_factor = 1/W, end_factor = 1, total_iters = W)` with W = ceil(0.03 x planned steps), then `CosineAnnealingLR(T_max = planned steps - W, eta_min = 0)`, where planned steps is the precomputed step of the full-budget checkpoint for that condition. Peak `2e-5` is selected, with fresh AdamW state. Replay: 658 planned steps, W=20, cosine 638; expansion: 667 planned steps, W=21, cosine 646.
- **Optimizer state:** fresh AdamW moments and fresh scheduler and dataloader state in both conditions (weights only are loaded). Resuming the saved step-658 moments is not chosen: the schedule is reset anyway and the native checkpoint's state loader would also restore the finished scheduler.
- **Masking:** prompt and padding tokens get zero loss; the only loss span is the rendered assistant span; the odd-count padding slot contributes zero loss tokens (checked as in the version-1 smoke: logged `global_valid_toks` equals the schedule).
- Framework and layout: NeMo RL 0.4.0 at `c751f811` in the existing `$WORK/nemo_rl` environment, version-1 configs with only `max_num_steps`, data path, scheduler totals and checkpoint steps changed (commit the diff); GPU layout per size as version 1 (1.7B 1 GPU, 4B 2, 8B 4, 14B 8 with tensor parallel 8); only the layout may differ by size. Checkpoints are produced by the segment-and-resume chain at the two rung steps and exported to Hugging Face format with `SHA256SUMS`.
- Logged per step: loss, learning rate, loss tokens, cumulative loss tokens, processed (prompt + assistant) tokens, wall-clock time per step and per segment; summarized as updates, loss tokens, processed tokens and wall time per condition and size.

## 5. Validation (validation split only)

- Manifest: 135 validation tasks x 8 attempts per system, systems `v3_<R|E>_<size>_f0p5` and `v3_<R|E>_<size>_f1p0` (16 systems, 17,280 cells), frozen as `expt_v3/results/ladder_manifest_v3.json` before any generation. Sampling exactly as version 1 § 9 (`rl4cv.veribench.generate --thinking on --seed 91 --stop-token '<|im_end|>' --max-tokens 12288 --temperature 0.6 --top-p 0.95 --top-k 20 --samples 8`), kernel scoring with the frozen scorer and the version-1 adapter including the non-vacuity screen.
- Completeness as version 1: every cell joined to the manifest, duplicates and extras rejected, missing cells listed as unknown; a checkpoint with any unknown gate input is INCOMPLETE.
- Gates per checkpoint (frozen, unchanged): (a) >= 972 / 1,080 extracted, (b) <= 108 / 1,080 capped, (c) >= 7 / 135 mixed-success tasks, all 1,080 cells known. Report the mixed share with its Wilson 95% interval, p-val=n/a.
- Also reported, per system: the failure taxonomy of [RESULTS_failure_taxonomy.md](RESULTS_failure_taxonomy.md) (primary categories and the token-cap flag), mean pass rate, pass@8, mean generated tokens, within-task diversity, and per-size paired differences E minus R at matched budget with 10,000 task-bootstrap draws (seed 0, eight attempts carried together), p-val=n/a.

## 6. Prospective decision rule (from the 10-13-2026 meeting plan; freeze before the first validation read)

1. Seek a **common checkpoint**: a budget fraction (half or full) at which all four sizes pass gates (a)-(c) within one condition.
2. If both conditions have a common checkpoint, prefer **E** only if the minimum validation success rate across the four sizes improves over R at the same fraction **and** no size has a paired E-minus-R difference whose 95% task-bootstrap interval lies wholly below zero; otherwise prefer **R**, or call the choice inconclusive when neither dominates.
3. If only one condition has a common checkpoint, that condition is selected and the other is reported as failing the gates with its taxonomy.
4. If neither has a common checkpoint, do not add epochs silently: use the taxonomy (capped share, compile-error share, first-error kinds) to design a new version.
5. Forecast: before reading any version-3 validation outcome, the owners freeze with `rl4cv.forecast.freeze_forecast` their prediction of which condition (R, E, neither) yields a common checkpoint, and at which fraction; failed forecasts are reported like successful ones.

6. **Pre-registered sensitivity:** independently repeat rules 1–4 using the common checkpoint across 4B, 8B and 14B, treating 1.7B as a capacity floor. Report this separately; it never replaces the primary four-size verdict. Compare E and R at the same fraction; prefer the earliest qualifying fraction within a condition, and report both fractions explicitly when comparisons disagree.
7. **Zero-call namespace diagnostic:** after preserving primary raw outputs and frozen scores, escape digit-leading Lean namespace identifiers with `«…»`, including corresponding `end` identifiers and qualified references, then recompile affected files under the same Lean/scorer/non-vacuity rules. Retain original and transformed hashes, changed-cell identities and diagnostic score deltas. No generation or hosted judge calls; diagnostic repairs never alter primary gates or selection.

## 7. SCSC >= 0.25 milestone (judge route required; deferred)

For the selected common checkpoint (or, under PARTIAL, each size's earliest passing checkpoint, labelled as such), compute the Smooth Conjunctive Score for Code verification on the declared validation manifest: IC_tests and IC_proofs from the kernel, formal specification coverage from the validated `vb103_judge` H2 ensemble (D-102, D-108) with bounded positive and negative controls before the first rating, `fsc_compiled` gated by IC_tests, and the D-009 aggregate (geometric mean of the three factor means on one common measured cohort) with all three factors, counts and task-bootstrap intervals. Report whether the aggregate is >= 0.25. This dispatch authorizes $0 paid model/judge spend. This section is DEFERRED until validation gates (a)–(c) are evaluated; no hosted calls are launched by this continuation. Historical route failures are not a current access test. Any single test evaluation is a later, separately frozen step.

## 8. Compute estimate (measured version-1 throughput, `ckpt/driver_<size>.log`)

Version 1 trained 658 updates / 5,752,936 loss tokens (about 10.4 M processed tokens) per size; exports are 5 per size there and 2 per continuation here.

| Size | GPUs (A100-80GB) | Version-1 training wall time | Per update | One continuation (training + 2 exports) | Both conditions | GPU-hours |
|---|---|---:|---:|---:|---:|---:|
| 1.7B | 1 | 62.5 min | 5.7 s | about 66 min | about 2.2 h | about 2.2 |
| 4B | 2 (TP 2) | 100.5 min | 9.2 s | about 107 min | about 3.6 h | about 7.1 |
| 8B | 4 (TP 4) | 111.9 min | 10.2 s | about 123 min | about 4.1 h | about 16.4 |
| 14B | 8 (TP 8) | 99.6 min | 9.1 s | about 115 min | about 3.8 h | about 30.6 |

E's update count differs from 658 by its mean loss span, so its training time scales accordingly; the host was shared during version 1, so these are upper-range estimates. Validation generation ran about 30-45 min per 1,080-cell rung on one GPU in version 1 (longer with tensor parallelism for 8B/14B) plus 1-3 h of CPU scoring per rung; 16 rungs are parallelizable across idle devices. Launch under the existing GPU lease discipline (Trigger Rule 9) and never on a device another user holds.

## 9. Owners, order of work and what is committed

- Execution owner: this named SNAP session `codex-rl4cv-e08v3-run`, under Brando’s 10-15-2026 dispatch. One writer for version 3; original mentee assignments are historical. Priority: 4B and 1.7B, then 8B and 14B; preserve at least one idle skampere1 device for the existing owner.
- Before lock: resolve recommended defaults, precompute both conditions' step schedules (`sft_schedule_v3_<R|E>.json`) and the two checkpoint steps, commit the config diffs and the frozen validation manifest, then after lock run the version-1 § 12.5-style disposable dry run on 1.7B (16 examples, 8 steps) for the E data path, starting from its step-658 export. Delete only disposable dry-run weights after verifying receipts.
- Committed: this protocol with its lock line, schedules, manifests, per-step training logs, checkpoint hashes, per-task validation CSVs, the taxonomy per system, the forecast, and `results.md`. Host only (`/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/`): corpus files, checkpoints, raw generations.
- Allowed without a new version: ports, concurrency, GPU layout, scorer parallelism, identical re-runs of infrastructure-failed cells. Everything in §§ 1-7 changes only by a new version or a dated, disclosed amendment file.

**TLDR-end:** [rl4cv: 08 expt_v3 › two-condition continuation protocol] Replay versus admitted expansion from the same step-658 weights at 5,752,936 additional loss tokens each, fresh optimizer with an explicit warmup-plus-cosine reset, 135 x 8 validation at half and full budget under the frozen gates and the meeting's decision rule; draft only, lock before training.
