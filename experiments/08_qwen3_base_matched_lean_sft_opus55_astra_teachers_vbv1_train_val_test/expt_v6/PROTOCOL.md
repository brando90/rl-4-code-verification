# Qwen3 1.7B continuation with a concise Lean curriculum

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v6/PROTOCOL.md

**TLDR:** Compare existing-data replay with existing data plus the verified 500-example curriculum, starting from the same 1.7B checkpoint, and also train an augmented-data 4B model. Run the three conditions in parallel on separate A100s and measure the full existing validation split. This is a new experiment; previous protocols remain frozen.

This prospective protocol and the preparation receipt must be recorded before the first optimizer update, including the disposable stress check. Preparation copies and tokenizes fixed inputs without updating any model. Later changes require a dated amendment retaining this original contract.

**Status:** LOCKED 10-19-2026 01:08:53 PDT; input admissions and exact schedules verified before optimizer updates.

## Scientific question

Does adding one exposure to each of the 500 concise Python-to-Lean examples improve the current 1.7B model beyond an equal additional assistant-token budget spent replaying existing training data? The primary comparison is mixed minus control validation binary success, with 10,000 paired task bootstrap draws, seed 0, carrying all eight attempts per task together. A positive difference with a 95% interval above zero supports improvement; an interval spanning zero is inconclusive. Report changes from the starting checkpoint separately when its prior complete validation receipts can be verified. This single training seed does not measure variation across training seeds.

## Inputs

- Starting weights: experiment 08 version 3 expansion 1.7B, full step 667, `/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/ckpt/v3_E_1p7b/hf/step_667`. Verify every file in its existing SHA256SUMS, copy to this run's owned `initial/`, verify the copy, and retain the manifest. The upstream Base revision is `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`.
- Existing pool: all 2,585 previously admitted examples, including the original 1,315, 685 cached responses and 585 MBPP responses. Source SHA-256 `7fa0255741a2b6046ceda0dfda43664334ca603a0aeca9fc2424af43c849726b`.
- Added pool: version 5 `dataset/training.jsonl`, exactly 500 verified examples, SHA-256 `8c493b9f1e1acf43b21d244b36f44647059b9de5dc8d1cb2785b7c3ba58ac5ad`. Reuse the recorded compilation, differential, output-format and protected-reference admission by exact file identity. No four coordinator prototypes enter training.
- D-013 split: train 539, validation 135, test 222. Training never loads validation/test task content or gold. Evaluation loads validation instructions; scoring remains outside model generation. Test evaluation is outside this experiment.

## Training conditions and fixed budgets

Both conditions start from the identical copied weights, use fresh AdamW moments, and target 5,752,936 additional assistant loss tokens. Train the full crossing minibatch and record overshoot. Equal loss tokens do not imply equal updates, processed tokens or device time.

Existing examples are permuted with `random.Random(20261019).shuffle`. Tiny examples use seed 20261020. Microbatch one, accumulated batch two, no packing or truncation; maximum combined sequence length 16,384. Control follows only the existing-data order. Mixed follows the same existing-data order and inserts one tiny-only pair after each two existing-data pairs until all 500 have appeared once, then continues existing data. Preparation must confirm all 500 fit before the token boundary. Tiny responses have their own minibatches to avoid being overwhelmed by long responses within token-normalized batches. No outcome-dependent resampling, extra epochs or silent restarts.

Both conditions use Transformers 4.55.4 / PyTorch 2.7.1+cu128 from the existing readable cluster environment, float32 parameters and optimizer states, bfloat16 autocast, PyTorch scaled dot-product attention, activation checkpointing, AdamW peak learning rate 2e-5, betas (0.9, 0.98), epsilon 1e-5, weight decay 0.1 and gradient clipping 1.0. The learning rate is a shared function of cumulative assistant tokens: warmup over the first 3% from 5% to full rate, then cosine decay to zero. This separately labelled Transformers implementation is not numerically equivalent to the earlier NeMo run.

Mask every system/user and padding token. The loss span is the inherited empty thinking block, the complete assistant response, the message terminator and the historical trailing end-of-text token. Verify token identities against the pinned Base tokenizer and recorded per-row counts. Record every consumed row, source, loss-token count, schedule hash and runtime identity. Save complete training state every 100 updates and at completion; export final Hugging Face weights with hashes.

## Validation and interpretation

Declare exactly two new systems, control and mixed, each with all 135 existing validation tasks and eight attempts: 2,160 cells. Reuse the exact frozen system prompt, addendum, task instructions and extractor, checking instruction/prompt hashes against the version 3 recorded validation hashes. Sampling: thinking on, seed `91 * 100003 + sample_idx`, temperature 0.6, top-p 0.95, top-k 20, maximum 12,288 output tokens, stop `<|im_end|>`, one vLLM engine per device. Generation batch size and vLLM cache configuration are operational parameters and may be adjusted before generation with provenance retained. No new task prompt or solver reminder is appended to the frozen benchmark prompt.

Use the pinned VeriBench scorer `59059a20d40adf3289869e58302169ad78102877` with `--skip-tc`, Lean 4.22.0 and the inherited non-vacuity checks. Strict binary success requires the existing compilation/executable-test, kernel-proof and non-vacuity gates. Preserve raw failures and capped outputs. No hosted formal-specification judge is called, and no aggregate requiring that judge is reported. Report extraction, caps, compilation, proof results, binary success, pass@8, per-task successes out of eight, and the count with 2–6 successes out of eight (the requested 25–75% range).

The full cell manifest is the Cartesian product of `{1.7B_control,1.7B_mixed,4B_mixed}`, the committed 135 validation task IDs in their recorded order, and sample indices 0–7: 3,240 cells total. Persist it before generation. Reject extra/duplicate cells and leave missing measurements explicit. Fixed scientific budgets are not reset by infrastructure failures. Deterministic scoring can be completed from preserved outputs; identical interrupted generation cells can be recovered at most once with original sampling identity, recording both attempts. Do not regenerate low-scoring completed cells.

## User-requested 4B augmented condition (added before launch)

The user explicitly corrected an initial 8B request to 4B and requested one additional A100. There is no 8B training condition. The 4B condition uses the same augmented pool, schedule rule, assistant-token target, optimizer hyperparameters and validation contract. Its start is the verified version 3 expansion 4B step-667 export, and its Base tokenizer revision is `906bfd4b4dc7f14ee4320094d8b41684abff8539`. Preparation directly verifies tokenizer prefix and response identities.

To fit one 80 GB A100 at the unshortened 16,384-token limit, 4B uses bfloat16 device parameters with full float32 master weights and AdamW state offloaded to CPU RAM. This trains every parameter; there is no low-rank adapter or quantized optimizer. Parameter precision and optimizer placement differ from the 1.7B GPU-only float32 implementation and are explicitly recorded. Expected device memory is approximately 30–65 GB, with roughly 60–100 GB host memory and additional parameter/gradient transfers each update. Actual memory and throughput must be measured by the longest-sequence disposable update before admission. This implementation may be transfer-bound, so no equal-runtime promise is made.

Compare 4B validation descriptively with the verified earlier 4B starting-checkpoint results; without a new 4B replay control, do not attribute a 4B gain specifically to the tiny examples. The primary matched comparison remains the two matched 1.7B conditions. Three devices are the maximum simultaneous GPU use. On each device, training precedes its own validation generation, after which GPU processes exit before CPU scoring.

## Compute, preconditions and stop rules

Execute as eth127 under `/lfs/skampere1/0/eth127/rl4cv_tiny_training`, in named persistent tmux sessions. Read the other experiments' lease registries and a fresh full GPU process inventory. Use two genuinely free 80 GB A100s, one per condition, explicitly isolating CUDA_VISIBLE_DEVICES. Preserve foreign jobs. Expected training memory 40–70 GB per device, compute-bound; estimate 1–2 hours training per condition in parallel, followed by approximately 1–3 hours generation and CPU scoring, with actual throughput replacing this estimate. Never hold a device just for CPU scoring. Maximum eight hours per training condition and eight hours per validation generation; stop an individual process only for the recorded resource/time boundary, nonfinite optimization, corrupt inputs, or actual infrastructure failure.

Before full training, one disposable update on the longest real sequence plus a tiny example must pass with finite nonzero gradients and fit one A100. Discard only those disposable updated weights. Failures retain receipts; an infrastructure amendment must precede another attempt. Use four CPU threads per trainer and up to eight Lean scoring workers in total. Local disk has approximately 2.2 TB available despite its low percentage-free reading; reserve at most 400 GB for this bounded experiment and verify absolute space before starting. Credentials and transcripts never enter training responses or Git.

**Authorization:** The user requested training with the new data, then explicitly requested the two runs in parallel and a third A100 for augmented 4B training. No provider spend, external messaging or dashboard publication is required.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## Evidence and continuation

Canonical [live results](results.md) and [checkpoint](CKPT_tiny_training.md) track preparation, running optimizer updates, exported weights, generated cells and scored cells separately. Model training alone is not evidence of improved correctness. Run source, exact input/schedule hashes, logs, full failures and terminal exit receipts survive coordinator disconnects. Bulky weights, tensors and raw generations remain on owned cluster storage; compact receipts and per-task results are mirrored into Git.

## Executable-example correction and validation provenance (before training)

The originally generated 500 answers contain named `test_` theorems but no anonymous Lean `example` declaration. The benchmark's executable-example gate requires an `example`; preserving only the message envelope would not teach this requirement. Keep version 5 pristine. Derive exactly 500 training answers by inserting one `example : <first existing concrete test statement> := <that named test>` immediately before `end Tiny`. No implementation, specification, named proof or input task changes. Run the complete original checker again on these exact new bytes: compilation, allowed kernel axioms, 32 differential cases, extractor round trip and pinned template/token cap. Repeat protected-reference screening. The derived training file and its admission receipt are immutable training inputs, with their new hashes recorded before the first update. No model calls are needed for this deterministic transformation.

The readable dataset checkout's current adapter generates agent-spec v7 instructions, whereas the historical validation pack used agent-spec v6. The original private pack is unreadable to eth127. The exact v6 adapter and completion contract from VeriBench commit `546b19fde50b06ec04f97c93798a98f37c539188` are included as source snapshots to reconstruct the validation-only pack. All 135 instruction, system, addendum and combined-prompt hashes must equal the original committed version-3 records. This is a byte-identical reconstruction, not a new prompt condition.

Scoring uses an owned grading directory and a small `lake env lean` adapter that invokes the identical pinned Lean 4.22.0 binary with the existing cached import directories and one compiler thread. Frozen scorer bytes remain unchanged. Before scoring models, positive, compilation-error and sorry-proof controls must produce the expected verdicts; preserve compiler/import-path and adapter hashes. No shared package directory is modified.

The 4B float32 CPU-master AdamW implementation must match native float32 AdamW on a deterministic three-update rounding/shadow-weight control before the real memory stress check.

## Frozen realized schedules and admission

The corrected training file has SHA-256 `2f50cd04757904b2ac703693c4520df813dd98e0f18881de92c515c7f87bb119`: 500/500 compiled, 16,000 differential comparisons, zero protected-reference hits and maximum assistant span 226 tokens (plus the inherited one-token training terminator). Control has 664 updates and 5,759,732 loss tokens; each augmented run has 904 updates and 5,753,602 loss tokens. Every augmented run consumes all 500 new examples and 1,308 existing examples. Control consumes 1,328 existing examples. Both sizes have byte-identical token tensors and augmented schedules. See `results/preflight/` for exact source mixture, per-step schedules and checkpoint-file hashes.

The existing 14B waiter has a fixed device plan but no active allocation on the selected idle devices; its last capacity check was waiting for H200 headroom. Use the existing E13/E08 admission locks through read-only descriptors, follow the authoritative live-lease parser (dead historical leases remain untouched), and hold the admission gates until production CUDA contexts are visible. The old waiter remains running and no foreign process or registry is modified.
