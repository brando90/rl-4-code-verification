# V28: model-family replicate: the v4 Lean SFT recipe at Llama-3.2-1B and 3B (Gemma-3 prepared)

**TLDR:** Train Llama-3.2-1B and Llama-3.2-3B (public unsloth mirrors, pinned revisions) with expt_v4's recipe and corpus, three seeds each, then generate 135 validation tasks x 8 samples with the frozen v12 sampling settings and Lean-score them on Sherlock (free hardware, no paid API). Question: does the Qwen3 result (SFT lifts validation pass@1 from ~0 to 5% at 1.7B and 9% at 4B, seed SD about 0.3 pts) hold in a second model family? All metrics are no DT (Lean kernel check plus the non-vacuity gate, no differential testing). Validation split only; test unopened.

**Status:** DRAFT until the smoke chain passes; LOCKED when the full chain is first submitted (the locking commit and time go in an addendum below). After that, changes go in dated addenda; nothing above is edited.

## Question

1. **Family transfer.** At matched recipe and data, how do Llama-3.2-1B and 3B compare with Qwen3-1.7B and 4B on validation pass@1 and pass@8 (no DT)?
2. **Seed noise.** Is Llama's seed-to-seed spread inside the Qwen3 noise bar (SD 0.30 pts pass@1, 2.2 pts pass@8 at 1.7B)?

## Arms

| Arm | Model (public mirror, revision) | Seeds | Run names |
|---|---|---|---|
| A: Llama-3.2-1B | `unsloth/Llama-3.2-1B` (`9535bd9b1d1dea6acafbdc4813b728796aeb28da`), base weights, 1.24B parameters | 20260830, 20260831, 20260832 | `llama1b_s<seed>` |
| B: Llama-3.2-3B | `unsloth/Llama-3.2-3B` (`d4446454d87d51aa42e1fb174f25acc5f8762331`), base weights, 3.21B parameters | 20260830, 20260831, 20260832 | `llama3b_s<seed>` |

The official `meta-llama/Llama-3.2-*` repositories are gated; the unsloth repositories are public re-uploads of the same base weights. Every weight and tokenizer file is checked against the Hub's LFS SHA-256 pinned in `train_v28.py`. The same three seeds as the Qwen3 runs (20260830 to 20260832) are used.

## Inputs and what changes from expt_v4 (and why)

- **Corpus:** the same 1,315 examples, `s_v1.jsonl`, SHA-256 `885d4ae2d6cf193bddc43df6ad6274cacfa8c98a5e5ecd63bd2519472f5e7354`, one epoch, same shuffle `random.Random(seed).shuffle`.
- **Prompt format (the one deviation, forced by the tokenizer).** Qwen3's chat markers and its `<think>` block do not exist for Llama, and Llama-3.2 base ships no chat template. Both families use the corpus' system, user and assistant texts unchanged; Llama sees the Llama-3 header format: `<|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n`, then `{assistant}<|eot_id|><|end_of_text|>`; BOS is added once by the tokenizer. No empty think block (Llama has no thinking mode). Loss is on the assistant tokens only, as before. The header tokens are barely trained in the base model; all parameters, including the tied embeddings, are fine-tuned in float32, so the model can learn them, and the smoke test checks that generation stops on `<|eot_id|>`.
- **Token gate.** expt_v4's `token_manifest.jsonl` hashes Qwen token ids and cannot apply. `prepare` instead tokenizes every example with the family's tokenizer, asserts no sequence is longer than 16,384 tokens (the same bound) and at least one loss token each, asserts the 1B and 3B tokens are identical, and writes `token_manifest_llama3.jsonl` with per-example id hashes and counts, so training reads exactly what was gated. A failure of the 16,384 bound stops everything; changing it is an addendum, not a silent edit.
- **Recipe, unchanged:** one GPU, global batch 2 as two microbatches of 1, token-normalized assistant-only loss, AdamW lr 2e-5, betas (0.9, 0.98), eps 1e-5, weight decay 0.1, clip 1.0, 20-step linear warmup from 5% then 638-step cosine to 0, 658 updates, activation checkpointing, float32 parameters, bfloat16 autocast, SDPA, TF32 off; Sherlock modules python/3.14.2, py-pytorch/2.9.1_py314, py-transformers/4.57.3_py314; checkpoint every 100 updates and at 658.
- **3B memory.** float32 parameters + gradients + AdamW moments are about 51 GB, and the 128k-token vocabulary makes the loss activations large; the 3B arm therefore uses V26's `HostAdamW` (the same `torch.optim.AdamW` on float32 host copies; only CPU-vs-CUDA last-bit rounding can differ; `tests/test_offload_equivalence.py`). The smoke chain also tries the 3B optimizer on the GPU at the longest sequences; if it fits an 80 GB card with margin, that is recorded, but the full chain keeps the host optimizer (decided before the smoke, to stay comparable with Qwen3-4B). The 1B arm keeps the optimizer on the GPU as in expt_v4.
- **Generation (frozen v12 settings):** 135 validation tasks x 8 samples, seed 91, temperature 0.6, top-p 0.95, top-k 20, 12,288-token cap, vLLM 0.30.0 Apptainer image as in V26. Differences: stop tokens `<|eot_id|>` and `<|end_of_text|>`; the prompt format comes from the chat template saved with each checkpoint's tokenizer; `--thinking model-default` (no thinking switch); `--max-model-len 32768` (as the Qwen3 models' context).
- **Scoring:** unchanged (AT-477 `score_one.sh`, veribench `score_scsc.py --skip-tc` at 59059a2, Lean 4.22, Mathlib 79e94a09).

## Pipeline

1. `bash submit.sh smoke` (on Sherlock, in `$SCRATCH/rl4cv_sherlock/expt_v28`): prepare (downloads, hashes, token gate) + 4-update trainings on the four longest examples (1B; 3B host optimizer; 3B GPU optimizer on another seed) + one smoke generation from the 1B smoke checkpoint (3 tasks x 2 samples). **Smoke passes when:** prepare PASS; every smoke run finishes with finite loss, a loss that falls over the four updates, the peak GPU memory recorded and an export that loads; the smoke generation finishes cells with `finish_reason` `stop` for at least some samples and writes the extraction fields.
2. `bash submit.sh full`: 6 trainings (`gpu`, one 80 GB card each), 6 generations, 6 x 8 Lean score arrays, one collector -> `$SCRATCH/rl4cv_sherlock/expt_v28_results.tgz`. Mail BEGIN/END/FAIL to both of Brando's addresses; job ids in `jobs_v28.tsv`. A failed step cancels its dependents; no automatic retry, seed substitution or data resampling.
3. `analyze_v28.py` locally on the fetched tarball.

## Metrics (all no DT)

Per-attempt success = `kernel_binary` with the inherited non-vacuity gate (`expt_v6/analyze.evaluate`), exactly as V26. pass@1 = mean over 1,080 cells; pass@8 = share of the 135 tasks solved by at least one of 8 samples; 95% task bootstrap, 10,000 draws, numpy seed 0. Seed spread (mean, SD, range) per size over three seeds; paired differences between seeds and 3B pooled vs 1B pooled. The Qwen3 rows from V26 are shown in the same columns for the cross-family table; no cross-family significance claim is made without paired task-level data for both families (V26's cell tables are in its tarball; if used, they are paired on the same 135 tasks).

## Predictions (written before any job)

- Llama-3.2-1B: pass@1 between 0.3% and 3%; pass@8 between 2% and 14%.
- Llama-3.2-3B: pass@1 between 1% and 7%; pass@8 between 6% and 22%; 3B pooled minus 1B pooled positive with a CI excluding 0.
- Llama stays below Qwen3 at matched or larger size (Qwen3-1.7B 5.0%, Qwen3-4B 8.8% pass@1), because Llama-3.2 has weaker code and formal-math pretraining.
- Seed SD at each size under 1 pt pass@1 and under 4 pts pass@8, i.e. inside the order of the Qwen3 noise bar.
- If the Llama 1B result is near zero (below 0.5%), the family comparison at that size is uninformative and is reported as a floor, not a null.

## Scope, resources, stopping

Validation split only; the test split is not loaded. No paid API ($0 provider spend); Sherlock `gpu` and `normal` partitions with the sanmi account, other people's jobs never touched. GPU-hours estimate: train 3 x ~1 h (1B) + 3 x ~4 h (3B); generation 3 x ~0.5 h + 3 x ~1.5 h; about 25 GPU-hours. Smoke ~1 GPU-hour.

## Gemma-3 addendum (prepared, not launched)

`train_v28.py` carries `gemma1b` (`unsloth/gemma-3-1b-pt` @ `34a98bf3eaecc08c699516f625eb5e56e4c5d99d`) and `gemma4b` (`unsloth/gemma-3-4b-pt` @ `52aba93981c6ad7712b030eb6dd496ece1d279d6`) with `enabled: False`, LFS hashes pinned, and the Gemma turn format (`<start_of_turn>user\n{system}\n\n{user}<end_of_turn>\n<start_of_turn>model\n` ... `{assistant}<end_of_turn>\n<eos>`; Gemma has no system role, so the system text opens the first user turn). The format passes `tests/test_formats.py`. Open items to settle in a Gemma smoke before enabling: `gemma-3-4b-pt` is the multimodal checkpoint (the text weights load through `AutoModelForCausalLM` in transformers 4.57 and export for vLLM must be checked), attention backend (SDPA vs eager), and the 1B/4B memory plan (4B with the host optimizer). Gemma runs are a separate chain started only after the Llama result is in.

## Lock addendum: full chain submitted (no DT)

Submitted Sat 2026-10-31 09:37:14 PDT on Sherlock (account sanmi) with `bash submit.sh full`, once, from `$SCRATCH/rl4cv_sherlock/expt_v28`. The package on Sherlock has the same `PROTOCOL.md` (sha256 prefix `dc543ce1a6ae88ac`) as this file before this addendum; code commit on main: `33a6a37f` (merge of PR #32). From this point the protocol above, the predictions and the stopping rule are frozen: nothing in them changes after seeing results.

Smoke before the full chain (Sherlock): prepare passed (1315 examples, tokenizer hashes matched, longest sequence 16003 tokens under the 16,384 limit); Llama-1B and Llama-3B (host optimizer) trained with finite, falling loss and exported 7 files; one smoke generation stopped on the stop token. The 3B run with the optimizer on the GPU ran out of memory at step 2, as expected, so the 3B uses the host optimizer.

Jobs: 6 trainings, 6 generations, 6 score arrays and 1 collector, ids in `jobs_v28.tsv`. Mail flags BEGIN, END and FAIL go to the owner's two Gmail accounts. The collector job (50508663) runs after all others end, whatever their exit state.

**TLDR-end:** [rl4cv: model families] `08_.../expt_v28_llama32_family` replicates the Qwen3 v4 recipe at Llama-3.2-1B and 3B (3 seeds each, Sherlock, no DT), with the Gemma-3 config prepared.

## Results addendum (2026-11-02, no DT)

Chain finished: 60 of 60 jobs COMPLETED, results and the check against the predictions above in [results.md](results.md). Result in one line: Llama-3.2-1B 2.96% and Llama-3.2-3B 7.35% pooled validation pass@1, 3B minus 1B +4.38 pts [2.62, 6.42]; the 3B pass@1 prediction (1% to 7%) was missed by 0.35 pts, every other prediction held. The protocol, predictions and stopping rule above were not edited.

## Gemma-3 smoke addendum (2026-11-02, prepared, not submitted)

The Llama result is in, so the Gemma chain may start; this addendum fixes its smoke. Nothing is submitted by writing it.

- **Package.** A separate copy of this folder on Sherlock, `$SCRATCH/rl4cv_sherlock/expt_v28_gemma_smoke`, with `bash submit.sh gemma-smoke`. `V28_ARMS=gemma1b,gemma4b` enables only the two Gemma models (the `enabled` flags in the table stay as committed), and `V28_ATTN` selects `sdpa` or `eager` and is recorded in each `result.json` as `backend`. Because `train_v28.py` changed (two env switches, Llama paths unchanged), its sha256 differs from the one pinned in the Llama chain's receipt; the Gemma package has its own receipt.
- **Jobs (prepare + 6).** prepare (downloads `unsloth/gemma-3-1b-pt` and `gemma-3-4b-pt` at the pinned revisions, LFS hashes, token gate with the Gemma format); four 4-update smoke trainings on the four longest examples: gemma1b sdpa (seed 20260830), gemma1b eager (20260831), gemma4b sdpa and gemma4b eager (host optimizer, `auto`); two smoke generations (3 tasks x 2 samples) from the gemma1b and gemma4b sdpa exports. About 6 GPU-hours, `sanmi` account, mail to both of Brando's addresses, no paid API.
- **Open items the smoke settles:** (1) whether the 4B multimodal checkpoint loads with `AutoModelForCausalLM` in transformers 4.57.3 and exports text weights that vLLM 0.30.0 loads; (2) SDPA against eager attention (finite, falling loss, peak memory); (3) the 4B memory plan with the host optimizer on an 80 GB card; (4) generation stops on `<end_of_turn>` or `<eos>`.
- **Smoke passes when** prepare is PASS, every smoke run ends with finite loss that falls over the four updates, records peak GPU memory and exports files that load, and each smoke generation finishes samples with `finish_reason` `stop` for at least some samples and writes the extraction fields. A failed model is diagnosed and fixed before any full Gemma chain; the full chain (seeds 20260830 to 20260832, same recipe, same 135 validation tasks, same predictions-before-results rule with its own dated protocol) is a separate decision.

