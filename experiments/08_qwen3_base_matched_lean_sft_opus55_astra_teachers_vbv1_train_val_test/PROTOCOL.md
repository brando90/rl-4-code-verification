# Experiment 08 protocol — matched Lean SFT warm start from Valkyrie teachers on the VeriBench V1 train split

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/PROTOCOL.md>

**TLDR:** This fixes, before the calls they govern, the D-013 split, the teacher prompt bytes, teachers and settings, the keep rule, the generated-Lean screen, the SFT set rule, Varun's matched SFT recipe at four Qwen3 Base sizes, the validation gates and checkpoint selection, and the single test evaluation. Lock 1 covers §§ 1–7 and the teacher preflight in § 12, before any teacher call including preflight; lock 2 covers §§ 8–11 and the training preflight in § 12, before any SFT step including the disposable dry run. After a lock, any change to a section it covers is a new version (`expt_v2`), except the already specified infrastructure changes and framework fallback.

**Lock 1 (§§ 1–7):** `LOCKED 2026-10-08T00:16:15Z at commit 6e6890fed68af71ac694adf4ff934934d84984bf` (SNAP worker, after zero-call checks 1–6 in § 12 passed; evidence in `expt_v1/results/{pack_check,scorer_adapter_check,template_check,deployment_e08,route_identity_e08}.json`). Confirmed selectors and settings: `opus55` = `anthropic/claude-opus-5-5-no-fallback` with `-k compute_effort max -k max_tokens 128000 -k addendum vbv1` (registry dump 10-07-2026: fallback list empty, the only Opus 5.5 selector without fallbacks); `astra` = `openai/gpt-6-astra-max` with `-k reasoning_effort max -k max_tokens 128000 -k addendum vbv1` (the highest served effort); temperature never passed. Manifests: main = the 539 train ids in `expt_v1/results/split/vbv1_train_task_ids.txt` (SHA-256 `03c4167cb086f37a86369e79115ff17035ac85bf6e3533e91a1a6c5c0e4b81c6`) × 2 teachers × r = 1…4 = 4,312 cells, labels `rl4cv-e08-v1-<short>-s<r>`, `-k benchmark rl4cv-e08-<short>-s<r>`; preflight = the first two train ids in task-id order (`aerospace_set_real__my_fprime_crc_match`, `aerospace_set_real__my_fprime_sequence_nonempty`) × labels `rl4cv-e08-preflight-<short>-p1/p2` × 2 teachers = 8 cells. Agent retry bound verified on the installed bundle (`single_call.py` `6e1a9b0d…`): at most 2 requests per cell, re-send only after HTTP 429/5xx with no response. Non-vacuity implementation and hashes: `scorer_adapter_check.json` → `vacuity`.
**Lock 2 (§§ 8–11):** `NOT LOCKED` — replaced with `LOCKED <UTC> at commit <hash>` after the static lock-2 checks in § 12 pass and before the disposable training dry run.

## 1. Split (D-013, frozen)

- `expt_v1/results/split/vbv1_split_manifest.csv` (relative to this experiment), built by `python -m rl4cv.splits` from VeriBench at the `veribench` pin `c11b99badfa386fd26810b208eef1eb8dc9f6806`; manifest SHA-256 `157ce781ed9e4ac93a1a1fe0c49f2ee2ae907be1260402485c8f6fa3d06e0e24`; parameters salt `rl4cv-d013-vbv1-split-v1`, fractions 0.60 / 0.15 / 0.25, word-5-gram Jaccard threshold 0.70.
- Train 539, validation 135, test 222 (core 369 / 93 / 152; IndustrySet 170 / 42 / 70). `tests/test_splits.py::test_committed_manifest_reproduces_from_pinned_dataset` must pass on the host before lock 1.
- **Use.** Train tasks: teacher prompts and the SFT set. Validation tasks: evaluation and selection in § 9 only. Test tasks: § 10 only, after the § 9 selection is committed. No validation or test task, reference or output enters teacher prompts or SFT data. Test outcomes never tune or select anything. The fixed contamination screen may read protected source/reference text only to exclude overlaps; it never sends that text to a teacher or adds it to S.

**Prior exposure:** experiment 05 Base scores and experiment 103 teacher scores, including their test subsets, were already inspected in the zero-call design work. This is not a previously unseen benchmark. The prospective holdout claim is one evaluation of each newly selected trained checkpoint after selection; historical test summaries must not change the split, data rule, gates or recipe. Version 2 must also freeze its design without using version 1 test outcomes.

## 2. Prompt bytes and served pack (zero model calls)

- **Source:** VeriBench experiment 103's VBV1 gated pack on `skampere1` (`/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/packs/vbv1_896`, agent-spec v6), the pack experiments 01 and 05 generated from.
- **Served pack:** for each of the 539 train ids, `instruction.md` copied byte for byte, plus whatever `tests/test.sh` the collect-only service needs, with a fixed placeholder canary. No `solution/`, gold file or reference text is served. Each instruction's SHA-256 must equal the `instruction_sha256` that experiment 05's raw generation rows record for the same task. Any mismatch blocks.
- **Teacher message:** exactly what `vb103_single_call` sends. The system message is `SYSTEM_PROMPT` (SHA-256 `dc051963de1199dd4f77c9f8f96218eb45be331c819b8e76693b063b206143cd`). The user message is `instruction.rstrip() + "\n\n---\n\n" + addendum_vbv1.md` (addendum SHA-256 `a7a0fc1b7be6b4ede41fd6b31e1e1dcae3d2fd320a6cddf9b311cf55855a18f5`). Every receipt's `system_prompt_sha256` and `addendum_sha256` must match. The `vb103_single_call` bundle in the bucket is downloaded and its file hashes recorded. If its VBV1 prompt or extraction differs from experiment 103's VBV1 run (`single_call.py` `6e1a9b0d…`), stop; never push a modified agent under that name.
- **Held-out check:** the system prompt, addendum and train instructions contain no validation or test task text. Screen each separately with `rl4cv.screens` against the validation and test Python and gold Lean, and record the result.

## 3. Teachers and route (D-015)

- **Route:** Valkyrie runs, `valk run start --agent vb103_single_call --benchmark <this experiment's collect-only service> --dataset default --model <selector> --task-ids-file <the 539 train ids> -k addendum vbv1 -k max_tokens 128000 -k benchmark <sample label> -k <effort>`. The service is experiment 103's single-call service in collect-only mode (`VB_NO_COMPILER=1`, `VB_COLLECT_ONLY=1`), deployed by this experiment on `skampere1` behind a bearer-protected tunnel in a claimed port block. Experiment 01's `deploy_rl4cv_e01_judge_service.py` is the deployment pattern. Vals funds it; the gateway key reaches the agent only through Valkyrie's secret mapping (`fellows/brandoModelGatewayApiKey`). Never use the key on the host.
- **Teachers** (selectors confirmed against a registry dump taken with zero calls before lock 1; the confirmed selector and settings are written here at lock 1):

  | Short name | Model | Selector | Settings |
  |---|---|---|---|
  | `opus55` | Claude Opus 5.5 | `anthropic/claude-opus-5-5-no-fallback` (the only Opus 5.5 selector without fallback models) | `-k compute_effort max`; temperature not passed (registry default 1.0) |
  | `astra` | GPT-6 Astra | the highest-effort GPT-6 Astra selector the registry serves (expected `openai/gpt-6-astra-max`) | `-k reasoning_effort` at that effort; temperature not passed |

- **Samples:** K = 4 per (task, teacher). There is one Valkyrie run per (teacher, r), r = 1…4, each over all 539 train tasks. Every run passes a distinct `-k benchmark rl4cv-e08-<short>-s<r>`, which makes the gateway `query_id` distinct per sample; labels are `rl4cv-e08-v1-<short>-s<r>`. That gives 8 runs and **4,312 declared cells**.
- **Calls:** at most two model requests per cell in total, counting the agent's own re-send after HTTP 429/5xx. A cell is re-sent once, as the identical cell, only when its receipts positively show that no model request was served. A served or possibly served call is never re-sent: that includes a client timeout, a hit on the 128,000-token output limit, and a collection failure after generation. It is recovered from the run output if possible, otherwise it stays `unmeasured`. No cell is re-sampled or dropped because of its content or score.
  - Verify the frozen agent enforces this bound before lock 1. HTTP 5xx or a timeout alone does not prove that no request was served. Both attempts share the same task, teacher, sample label and query identity. Apply the same accounting to preflight.

## 4. Scoring

- **Scorer bytes:** `score_scsc.py`, `run_real_eval.py` and `kernel_axioms.py` from the `veribench_scorer` pin `59059a20d40adf3289869e58302169ad78102877`. Check the commit against `external/deps.lock.json` and full file hashes against the pinned Git blobs (the lock file contains only hash prefixes). Run with `--skip-tc` in this experiment's private copy of the Lean v4.22.0 + Mathlib grading project on `skampere1`. These are VeriBench tasks, so the scorer's native gold mapping applies; no FSC is computed here.
- **Adapter check (before lock 1):** 3 train gold references score IC_tests = IC_proofs = 1, and 3 broken variants of train files fail. A compiling train control with a proved `True` or self-equality theorem must fail the keep rule despite perfect kernel factors. Five of experiment 103's Astra train-task files reproduce experiment 103's IC_tests and IC_proofs exactly.

## 5. Keep rule

- `rl4cv.rewards.reward_kernel_binary == 1`. The file typechecks under the frozen scorer, states at least one `example` and at least one theorem, every stated theorem is kernel-proved with axioms only in {`propext`, `Classical.choice`, `Quot.sound`}, and no theorem is vacuous. `sorry`, `admit`, declared axioms and `native_decide` in named theorems fail.
- **Non-vacuity:** populate `ScoredResponse.vacuous_theorems` from the stated theorem types using the pinned VeriBench non-vacuity check before calling `reward_kernel_binary`. `rl4cv.veribench.jobs.scored_response` defaults this field to zero and is insufficient alone. Record the implementation and hashes at lock 1; an unparseable theorem type makes the keep decision unmeasured, not accepted. This is the declared syntactic screen (literal `True` or self-equality), not a claim to decide semantic vacuity.
- **Consistency check:** extracting the teacher's full response text (`response.txt`) with `rl4cv.veribench.exp103`'s extraction must reproduce the scored file byte for byte. Otherwise the cell is excluded from the SFT set and listed. The student is evaluated with that extraction, so its training text must extract to the verified file.

## 6. Generated-Lean screen

Every kept extracted file, the full assistant response that will receive loss, and each fenced code block in that response are screened separately with `rl4cv.screens` (exact normalized hash; word-5-gram Jaccard ≥ 0.70) against the validation and test splits' Python programs and gold Lean references. A hit in any text excludes the whole example from the SFT set and is listed with its nearest file and score; its receipt and `kernel_binary` stay unchanged. The maximum Jaccard to the task's own gold reference is reported as a diagnostic.

## 7. SFT set S

- **Candidates:** kept, consistent, screen-clean cells from the 8 manifest runs that pass the rendered length cap below. Apply all eligibility filters before deduplication and the per-teacher cap; an overlength candidate never consumes a slot. Preflight cells are excluded.
- **Per task:** visit teachers in fixed order `opus55`, then `astra`; within each teacher visit r = 1…4. Drop a candidate whose extracted file has the same `rl4cv.screens.norm_hash` as an already-selected file for that task from either teacher. Keep the first 2 eligible distinct files from each teacher. A task contributes 0–4 examples. This priority is independent of arrival order, validation/test scores, quality beyond the keep rule, and length beyond the cap.
- **Example:** messages `[system: SYSTEM_PROMPT, user: instruction.rstrip() + "\n\n---\n\n" + addendum, assistant: the teacher's response text verbatim]`. The response is not edited, trimmed or re-wrapped; the teacher's hidden reasoning is not available and is not invented.
- **Rendering (every size):** the pinned Qwen3 Base tokenizer's chat template. `apply_chat_template([system, user], add_generation_prompt=True, enable_thinking=True)`, which is byte-identical to what `rl4cv.veribench.generate --thinking on` feeds vLLM, must be an exact prefix of `apply_chat_template([system, user, assistant])`. The remainder is the assistant span and the only span with loss. It includes whatever assistant prefix the pinned template inserts (expected empty `<think>\n\n</think>\n\n` block) and `<|im_end|>`; verify the actual bytes before lock 1 rather than assuming an Instruct template. The four sizes' tokenizers must give identical token ids on every example.
  - Require both the byte prefix and token-id prefix, with `enable_thinking=True` in both renders and `add_generation_prompt=False` for the full example. Freeze the mask boundaries and include the actual template-inserted tokens in assistant-token counts.
- **Length cap:** rendered total ≤ 16,384 tokens; longer examples are excluded and listed.
- **Order:** ascending `sha256("rl4cv-e08-sft-order-v1:" + task_id + "|" + teacher + "|" + r)`, identical at every size.
- **Recorded before lock 2:** |S|, distinct tasks, per family, per teacher, assistant tokens (total, mean, quantiles), prompt tokens, and exclusions by reason. The committed manifest holds ids, hashes and token counts, never file contents.

## 8. Matched SFT recipe (identical at every size)

- **Models:** Qwen3-1.7B-Base `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`, Qwen3-4B-Base `906bfd4b4dc7f14ee4320094d8b41684abff8539`, Qwen3-8B-Base `49e3418fbbbca6ecbdf9608b4d22e5a407081db4`, Qwen3-14B-Base `0b0bd3732e2c374d483664439ea334928b65f304`. Each revision is confirmed on the Hugging Face hub and weight hashes are recorded.
- **Framework:** NeMo RL 0.4.0 SFT (commit `c751f811`, DTensor v2), built in this experiment's own environment. Start from Varun's production SFT config (`/lfs/skampere3/0/vmadan/paper1_phase1c_sft_v1/phase1c_production_sft.yaml`), committed byte for byte with its launcher, run manifest and recipe as `expt_v1/configs/varun_*` (provenance and SHA-256 in `expt_v1/configs/README.md`), so no cross-host access is needed. The explicit hyperparameters below govern experiment 08. Commit all differences from the source config before lock 2, including rendering, masks, scheduler, seed and GPU layout; never silently inherit conflicting defaults. Resolve `c751f811` to its full commit and record the environment; a different revision blocks.
- **Hyperparameters:** full-parameter bf16; AdamW lr 2×10⁻⁵, betas (0.9, 0.98), eps 1×10⁻⁵, weight decay 0.1; gradient clip 1.0; Varun's schedule form: `LinearLR(start_factor = 1/W, end_factor = 1, total_iters = W)` with W = ⌈0.03 × total steps⌉, then `CosineAnnealingLR(T_max = total steps − W, eta_min = 0)` (his run: W = 31 of 1,024); global batch 2 sequences; maximum sequence length 16,384; assistant-only loss, normalized over the global batch's assistant tokens; no sequence packing; seed 20260830 (Varun's `sft.seed`) for model and trainer randomness, with data order fixed by § 7; **one epoch** over S in the § 7 order (steps = ⌈|S| / 2⌉).
- **Batch boundaries:** step j consumes consecutive examples 2j−1 and 2j, without reshuffling or distributed-sampler duplication. For odd |S|, use one real example and one fully loss-masked padding slot in the last step. Normalize the summed assistant-token loss by real assistant tokens across all ranks, excluding padding. Require identical cumulative loss-token logs across sizes. Empty S gives NOT READY without training or new test generation.
- **Checkpoints:** the first step whose cumulative assistant tokens, in the fixed order, reach 12.5%, 25%, 50%, 75% and 100% of S's total. Compute these identical step indices before training and report actual cumulative tokens, including step overshoot. Coincident rung steps share one checkpoint/evaluation. Each checkpoint is exported to Hugging Face format and must load in vLLM.
- **Logging and in-training validation:** SFT-time validation is off (`val_period` 0; selection is the § 9 ladder) and Weights & Biases is off; TensorBoard plus per-step CSV logs (step, loss, learning rate, cumulative assistant tokens) are on. Varun's run had both on; these are recorded differences.
- **Only the GPU layout may differ by size** (GPU count, sharding, micro-batching, activation checkpointing). It never changes the global batch, order, steps, schedule or loss.
- **Fallback:** if NeMo RL 0.4.0 cannot be built and pass the § 12 dry run within 6 working hours, use TRL's `SFTTrainer` with the same hyperparameters, order, batch, mask and checkpoints at every size. Freeze both candidate environments' exact versions and configs at lock 2; this declared fallback is the only framework exception. Commit the dry-run receipt and chosen framework before production SFT. Restart every production size from its pinned Base weights; never continue a dry-run checkpoint or mix frameworks across sizes.

## 9. Validation ladder and selection (validation split only)

- **Systems:** the 5 checkpoints × 4 sizes, plus Base 14B, generated here. Base 1.7B, 4B and 8B use experiment 05's receipts restricted to the 135 validation tasks; their sampling is identical. Recompute only their `kernel_binary` non-vacuity screen from preserved files using the same adapter as the trained policies, writing new experiment 08 receipts; preserve experiment 05's kernel factors and historical summaries.
- **Sampling** (experiment 05 exactly): `rl4cv.veribench.generate --thinking on --seed 91 --stop-token '<|im_end|>' --max-tokens 12288 --temperature 0.6 --top-p 0.95 --top-k 20 --samples 8`, 135 tasks, 1,080 cells per system, kernel-scored as in § 4.
- **Completeness:** freeze the full task × sample × system manifest before generation. Join all receipts to it, rejecting duplicates/extras and listing missing cells. Clean empty responses are measured failures; length-capped responses are scored as they stand and count in the truncation gate, as in experiment 05 (their transport `measured` flag is false). Missing generation or failed scoring is unknown, never zero. A checkpoint with any unknown gate input is INCOMPLETE and cannot pass. Recover identical infrastructure-failed cells only; finish all declared rungs even if an earlier one passes.
- **Gates per checkpoint:** (a) extraction succeeds using experiment 103's rule in ≥ 90% of cells; (b) ≤ 10% end at the 12,288-token cap; (c) `kernel_binary` mixed-group share ≥ 0.05 over 135 tasks. These require ≥ 972 extracted cells, ≤ 108 capped cells and ≥ 7 mixed tasks, with all 1,080 cells known. The 0.05 readiness gate is experiment 08's choice at experiment 01 G1's failure boundary, not G1's 0.20 strong-pass threshold. Report the mixed-share point estimate and Wilson 95% interval; p-val=n/a (a prespecified point-estimate gate).
- **Also reported (no gate):** pass@8 share, all-pass share, mean pass rate, IC_tests rate, mean proof fraction, mean generated tokens, and within-task diversity (mean pairwise word-5-gram Jaccard of a task's 8 extracted files), each per size and fraction.
- **Selection:** f* is the smallest fraction at which all four sizes pass (a)–(c), and π₀(N) is each size's checkpoint at f*. The answer to "how many SFT tokens" is actual cumulative assistant tokens at that step. If all gate inputs are complete but no common fraction exists, report PARTIAL if any size passes any rung, otherwise NOT READY. Incomplete inputs give BLOCKED with no test generation until resolved. PARTIAL checkpoints are unmatched diagnostics, not matched warm starts for cross-size RL. Commit `expt_v1/results/selection.json` (verdict, f*, actual step/tokens, checkpoint paths/hashes, complete gate table, selected systems and frozen test manifest) **before any test-split generation**.

## 10. Test evaluation (once, after the selection commit)

- **Systems:** π₀(N) at every size (under PARTIAL, each passing size's earliest passing checkpoint, labelled as such), Base 14B (generated), and Base 1.7B / 4B / 8B (experiment 05 receipts restricted to the 222 test tasks).
- **Sampling:** as § 9, 222 tasks × 8. NOT READY stops without new test evaluation. The RL-READY comparison has 8 systems (4 selected + 4 Base), 14,208 declared cells: 8,880 new and 5,328 reused. Test outcomes never trigger new training, selection or samples.
- **Factors:**
  - IC_tests and IC_proofs from the kernel.
  - FSC from `vb103_judge` (D-102; experiment 100 H2: GPT-6 Sol high + Claude Opus 5.5 max, median of three ratings each, mean of the medians divided by five), under a new suite `rl4cv-e08:<system>`. Preserve `(system, task_id, sample_idx, rating_idx)` identities throughout; task_id alone cannot key an eight-sample run. Judge every cell with IC_tests = 1, including IC_proofs = 0: these cells contribute to the D-009 factor mean even when their per-file SCSC is zero.
  - Keep D-102's 60-file audit per system: 12 cells per core family, ranked by `sha256("rl4cv-e08-audit-v1:" + task_id + "|" + sample_idx)` over the frozen test manifest, identical across systems. Judge overlap once; list missing audit files without replacements. Audit FSC on IC_tests = 0 is diagnostic only.
  - `fsc_compiled` = FSC when IC_tests = 1, else 0 (D-003, including compiling files without an `example`). Unknown kernel factors stay unknown. Do not additionally gate the official factor on proof success or vacuity; reward helpers do not define the D-009 dataset aggregate.
  - Before test judging, freeze its manifest/settings and pass bounded positive/negative route controls on train files, checking delivered models, efforts, rubric, inputs and aggregation against the validated bundle (D-108). Six ratings per file are declared calls, not retries; preserve completed ratings and apply § 3's two-request/no-possibly-served-resend limit to each rating. Do not divide an already normalized FSC score again.
- **Aggregate:** SCSC = (mean IC_tests · mean IC_proofs · mean `fsc_compiled`)^(1/3) (D-009). Use the same cohort with all three factors known for all means, report measured/declared cell and task counts, and list every unknown cell. If incomplete, label the measured-cohort score and bound the full-manifest aggregate by assigning unknown factors 0 or 1; bounds are not observed scores. Never multiply means from different cohorts or use `summarize`'s mean per-file SCSC as the official aggregate. Report all 222 tasks (1,776 cells), core 152 (1,216) and IndustrySet 70 (560) separately per system. Use 10,000 task-bootstrap resamples with seed 0, carrying all eight samples together; intervals describe this single run, not training-seed variation. Paired differences use shared resampled task indices and a common known cohort across systems, with missing-pair counts and full-manifest bounds when needed; p-val=n/a (interval estimation only).
- **Primary comparison:** per size, π₀(N) minus Base, on the `kernel_binary` mean pass rate and on SCSC, with a paired task-bootstrap 95% interval.

## 11. RL

Not part of version 1. On RL-READY, version 2 locks its own protocol before any RL step: GRPO from π₀(N) on train-split prompts, `kernel_binary` reward first, validation monitoring, and one test evaluation.

## 12. Preflight

**Before lock 1 (zero model calls):**

1. `make test` passes on the host, including the split reproduction test against the pinned VeriBench files.
2. The served pack is built: 539 instructions with hashes matching experiment 05's, and no gold anywhere in the pack.
3. The service answers 200 with the bearer and 401 without, both locally and through the tunnel. The per-task time limit read back is ≥ 2 × the agent's client timeout + 600 s.
4. A registry dump (zero calls) confirms both selectors, their settings and that the Opus 5.5 selector has no fallbacks. The bucket's `vb103_single_call` bytes are recorded and checked against § 2.
5. Identity and payer are recorded with non-secret evidence: host, Valkyrie environment and organization, the secret mapping by name, and the payer.
6. The scorer adapter check (§ 4) is recorded.

Commit lock 1 after checks 1–6, with exact selectors/settings and teacher manifests, including the first two train ids in task-id order for preflight. The lock line names the immediately preceding code/artifact commit; record the resulting lock commit separately in the checkpoint to avoid a self-referential hash.

**After lock 1, before the main teacher manifest:**

7. **Live preflight:** 2 train tasks × 2 sample labels (`rl4cv-e08-preflight-<short>-p1/p2`) × 2 teachers = 8 calls. Each is scored end to end, with status, finish reason, delivered settings, charge and response SHA-256 recorded. **Independence:** for each teacher, the two samples' response hashes differ on at least one of the two tasks. Otherwise sampling is suspected to be cached; record BLOCKED and investigate before any main-manifest call.

**Before lock 2 (static checks, no training):**

1. S is assembled and its § 7 statistics are recorded, with every one of the 4,312 teacher cells terminal (kept, excluded with reason, or unmeasured). Do not train while a teacher run can still add candidates.
2. The rendering prefix check and the tokenizer identity check across all four sizes pass on every example.
3. Exact trainer versions/configs, seed, step/token schedule, model revisions and GPU plans are recorded (Trigger Rule 9 estimate). S must be nonempty.
4. Commit lock 2 using the code-commit/lock-commit convention above.

**After lock 2, before production SFT:**

5. **Disposable NeMo RL dry run on Qwen3-1.7B-Base:** first 16 examples in S's order, 8 steps (if |S| < 16, use all S for ⌈|S| / 2⌉ steps). Prompt/padding tokens get zero loss; counted loss tokens equal rendered assistant spans. Mean loss on this fixed set, evaluated without dropout before/after, decreases. A checkpoint exports to Hugging Face format, loads in vLLM, and generates on the two preflight train tasks with extraction working. Keep receipts; exclude outputs from S/evaluation and restart production from Base. Use only § 8's frozen fallback; other failed controls block execution.

## 13. What is committed

- **Committed:** this protocol with its lock lines; the scripts and configs, with no secrets; manifests and hashes; per-cell receipts without content; scored summaries; the S manifest (ids, hashes, token counts); training-loss CSVs; checkpoint hashes; per-task evaluation CSVs (counts and factors, no file contents); `selection.json`; and `results.md`.
- **Host only** (`/lfs/skampere1/0/brando9/rl4cv_e08/`): raw teacher responses, Lean files, the SFT JSONL, checkpoints, raw generations and the private Valkyrie configuration.

## 14. Allowed infrastructure changes

The following may change without a new version, and each change is recorded: ports, tunnel, concurrency, GPU layout, re-sends under § 3, scorer parallelism, and the vLLM tensor-parallel degree. The following change only by a new version: models, revisions, selectors, efforts, K, prompts, the keep rule, the screen, the S rule, the recipe, sampling, gates, the selection rule and the test procedure.
