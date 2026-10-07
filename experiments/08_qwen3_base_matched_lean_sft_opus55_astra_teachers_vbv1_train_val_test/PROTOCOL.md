# Experiment 08 protocol — matched Lean SFT warm start from Valkyrie teachers on the VeriBench V1 train split

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/PROTOCOL.md>

**TLDR:** This fixes, before the calls they govern, the D-013 split, the teacher prompt bytes, teachers and settings, the keep rule, the generated-Lean screen, the SFT set rule, Varun's matched SFT recipe at four Qwen3 Base sizes, the validation gates and checkpoint selection, and the single test evaluation. Lock 1 covers §§ 1–7 and happens before the first teacher call; lock 2 covers §§ 8–11 and happens before the first SFT step. After a lock, any change to a section it covers is a new version (`expt_v2`).

**Lock 1 (§§ 1–7):** `NOT LOCKED` — the SNAP worker replaces this with `LOCKED <UTC> at commit <hash>` after the § 12 lock-1 preflight passes and before the first manifest call.
**Lock 2 (§§ 8–11):** `NOT LOCKED` — replaced with `LOCKED <UTC> at commit <hash>` after the § 12 lock-2 preflight passes and before the first SFT step.

## 1. Split (D-013, frozen)

- `experiments/08_…/expt_v1/results/split/vbv1_split_manifest.csv`, built by `python -m rl4cv.splits` from VeriBench at the `veribench` pin `c11b99badfa386fd26810b208eef1eb8dc9f6806`; manifest SHA-256 `157ce781ed9e4ac93a1a1fe0c49f2ee2ae907be1260402485c8f6fa3d06e0e24`; parameters salt `rl4cv-d013-vbv1-split-v1`, fractions 0.60 / 0.15 / 0.25, word-5-gram Jaccard threshold 0.70.
- Train 539, validation 135, test 222 (core 369 / 93 / 152; IndustrySet 170 / 42 / 70). `tests/test_splits.py::test_committed_manifest_reproduces_from_pinned_dataset` must pass on the host before lock 1.
- **Use.** Train tasks: teacher prompts and the SFT set. Validation tasks: § 9 only. Test tasks: § 10 only, after the § 9 selection is committed. No validation or test task, reference or output enters any training data, prompt, tuning or selection step.

## 2. Prompt bytes and served pack (zero model calls)

- **Source:** VeriBench experiment 103's VBV1 gated pack on `skampere1` (`/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/packs/vbv1_896`, agent-spec v6), the pack experiments 01 and 05 generated from.
- **Served pack:** for each of the 539 train ids, `instruction.md` copied byte for byte, plus whatever `tests/test.sh` the collect-only service needs, with a fixed placeholder canary. No `solution/`, gold file or reference text is served. Each instruction's SHA-256 must equal the `instruction_sha256` that experiment 05's raw generation rows record for the same task. Any mismatch blocks.
- **Teacher message:** exactly what `vb103_single_call` sends. The system message is `SYSTEM_PROMPT` (SHA-256 `dc051963de1199dd4f77c9f8f96218eb45be331c819b8e76693b063b206143cd`). The user message is `instruction.rstrip() + "\n\n---\n\n" + addendum_vbv1.md` (addendum SHA-256 `a7a0fc1b7be6b4ede41fd6b31e1e1dcae3d2fd320a6cddf9b311cf55855a18f5`). Every receipt's `system_prompt_sha256` and `addendum_sha256` must match. The `vb103_single_call` bundle in the bucket is downloaded and its file hashes recorded. If its VBV1 prompt or extraction differs from experiment 103's VBV1 run (`single_call.py` `6e1a9b0d…`), stop; never push a modified agent under that name.
- **Held-out check:** the system prompt and addendum contain no validation or test task text. They are screened with `rl4cv.screens` against the validation and test Python and gold Lean, and the result is recorded.

## 3. Teachers and route (D-015)

- **Route:** Valkyrie runs, `valk run start --agent vb103_single_call --benchmark <this experiment's collect-only service> --dataset default --model <selector> --task-ids-file <the 539 train ids> -k addendum vbv1 -k max_tokens 128000 -k benchmark <sample label> -k <effort>`. The service is experiment 103's single-call service in collect-only mode (`VB_NO_COMPILER=1`, `VB_COLLECT_ONLY=1`), deployed by this experiment on `skampere1` behind a bearer-protected tunnel in a claimed port block. Experiment 01's `deploy_rl4cv_e01_judge_service.py` is the deployment pattern. Vals funds it; the gateway key reaches the agent only through Valkyrie's secret mapping (`fellows/brandoModelGatewayApiKey`). Never use the key on the host.
- **Teachers** (selectors confirmed against a registry dump taken with zero calls before lock 1; the confirmed selector and settings are written here at lock 1):

  | Short name | Model | Selector | Settings |
  |---|---|---|---|
  | `opus55` | Claude Opus 5.5 | `anthropic/claude-opus-5-5-no-fallback` (the only Opus 5.5 selector without fallback models) | `-k compute_effort max`; temperature not passed (registry default 1.0) |
  | `astra` | GPT-6 Astra | the highest-effort GPT-6 Astra selector the registry serves (expected `openai/gpt-6-astra-max`) | `-k reasoning_effort` at that effort; temperature not passed |

- **Samples:** K = 4 per (task, teacher). There is one Valkyrie run per (teacher, r), r = 1…4, each over all 539 train tasks. Every run passes a distinct `-k benchmark rl4cv-e08-<short>-s<r>`, which makes the gateway `query_id` distinct per sample; labels are `rl4cv-e08-v1-<short>-s<r>`. That gives 8 runs and **4,312 declared cells**.
- **Calls:** at most two model requests per cell in total, counting the agent's own re-send after HTTP 429/5xx. A cell is re-sent once, as the identical cell, only when its receipts positively show that no model request was served. A served or possibly served call is never re-sent: that includes a client timeout, a hit on the 128,000-token output limit, and a collection failure after generation. It is recovered from the run output if possible, otherwise it stays `unmeasured`. No cell is re-sampled or dropped because of its content or score.

## 4. Scoring

- **Scorer bytes:** `score_scsc.py`, `run_real_eval.py` and `kernel_axioms.py` from the `veribench_scorer` pin `59059a20d40adf3289869e58302169ad78102877`, hashes checked against `external/deps.lock.json`. Run with `--skip-tc` in experiments 01 and 05's Lean v4.22.0 + Mathlib grading project on `skampere1`. These are VeriBench tasks, so the scorer's native gold mapping applies; no FSC is computed here.
- **Adapter check (before lock 1):** 3 gold references score IC_tests = IC_proofs = 1, and 3 deliberately broken files fail. Five of experiment 103's Astra train-task files reproduce experiment 103's IC_tests and IC_proofs exactly.

## 5. Keep rule

- `rl4cv.rewards.reward_kernel_binary == 1`. The file typechecks under the frozen scorer, states at least one `example` and at least one theorem, every stated theorem is kernel-proved with axioms only in {`propext`, `Classical.choice`, `Quot.sound`}, and no theorem is vacuous. `sorry`, `admit`, declared axioms and `native_decide` in named theorems fail.
- **Consistency check:** extracting the teacher's full response text (`response.txt`) with `rl4cv.veribench.exp103`'s extraction must reproduce the scored file byte for byte. Otherwise the cell is excluded from the SFT set and listed. The student is evaluated with that extraction, so its training text must extract to the verified file.

## 6. Generated-Lean screen

Every kept file is screened with `rl4cv.screens` (exact normalized hash; word-5-gram Jaccard ≥ 0.70) against the validation and test splits' Python programs and gold Lean references. A hit is excluded from the SFT set and listed with its nearest file and score; its receipt and `kernel_binary` stay unchanged. The maximum Jaccard to the task's own gold reference is reported as a diagnostic.

## 7. SFT set S

- **Candidates:** kept, consistent, screen-clean cells from the 8 manifest runs. Preflight cells are excluded.
- **Per (task, teacher):** candidates in sample order r = 1…4. Drop a candidate whose extracted file has the same `rl4cv.screens.norm_hash` as an already-selected file for that task from either teacher. Keep the first 2. A task contributes 0–4 examples.
- **Example:** messages `[system: SYSTEM_PROMPT, user: instruction.rstrip() + "\n\n---\n\n" + addendum, assistant: the teacher's response text verbatim]`. The response is not edited, trimmed or re-wrapped; the teacher's hidden reasoning is not available and is not invented.
- **Rendering (every size):** the pinned Qwen3 Base tokenizer's chat template. `apply_chat_template([system, user], add_generation_prompt=True, enable_thinking=True)`, which is byte-identical to what `rl4cv.veribench.generate --thinking on` feeds vLLM, must be an exact prefix of `apply_chat_template([system, user, assistant])`. The remainder is the assistant span and the only span with loss. It includes the template's empty `<think>\n\n</think>\n\n` block and `<|im_end|>`. The four sizes' tokenizers must give identical token ids on every example.
- **Length cap:** rendered total ≤ 16,384 tokens; longer examples are excluded and listed.
- **Order:** ascending `sha256("rl4cv-e08-sft-order-v1:" + task_id + "|" + teacher + "|" + r)`, identical at every size.
- **Recorded before lock 2:** |S|, distinct tasks, per family, per teacher, assistant tokens (total, mean, quantiles), prompt tokens, and exclusions by reason. The committed manifest holds ids, hashes and token counts, never file contents.

## 8. Matched SFT recipe (identical at every size)

- **Models:** Qwen3-1.7B-Base `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`, Qwen3-4B-Base `906bfd4b4dc7f14ee4320094d8b41684abff8539`, Qwen3-8B-Base `49e3418fbbbca6ecbdf9608b4d22e5a407081db4`, Qwen3-14B-Base `0b0bd3732e2c374d483664439ea334928b65f304`. Each revision is confirmed on the Hugging Face hub and weight hashes are recorded.
- **Framework:** NeMo RL 0.4.0 SFT (commit `c751f811`, DTensor v2), built in this experiment's own environment. The config is Varun's production SFT config (`/lfs/skampere3/0/vmadan/paper1_phase1c_sft_v1/phase1c_production_sft.yaml`), copied with provenance into `expt_v1/configs/`. It changes only the model and revision, data paths, output and checkpoint directories, total steps, checkpoint steps and logging, and the committed diff shows exactly that.
- **Hyperparameters** (the config's values where it states them; the frozen recipe JSON otherwise; both recorded): full-parameter bf16; AdamW lr 2×10⁻⁵, betas (0.9, 0.98), eps 1×10⁻⁵, weight decay 0.1; gradient clip 1.0; linear warmup over 3% of steps then cosine decay; global batch 2 sequences; maximum sequence length 16,384; assistant-only loss, normalized over the global batch's assistant tokens; no sequence packing; one fixed seed; **one epoch** over S in the § 7 order (steps = ⌈|S| / 2⌉).
- **Checkpoints:** the first step whose cumulative assistant tokens, in the fixed order, reach 12.5%, 25%, 50%, 75% and 100% of S's total. These step indices are computed from the rendered set before training, so they are identical at every size. Each checkpoint is exported to Hugging Face format and must load in vLLM.
- **Only the GPU layout may differ by size** (GPU count, sharding, micro-batching, activation checkpointing). It never changes the global batch, order, steps, schedule or loss.
- **Fallback:** if NeMo RL 0.4.0 cannot be built and pass the § 12 dry run within 6 working hours, use TRL's `SFTTrainer` with the same hyperparameters, order, batch, mask and checkpoints at every size, recorded as a deviation. Frameworks are never mixed across sizes.

## 9. Validation ladder and selection (validation split only)

- **Systems:** the 5 checkpoints × 4 sizes, plus Base 14B, generated here. Base 1.7B, 4B and 8B use experiment 05's receipts restricted to the 135 validation tasks; their sampling is identical.
- **Sampling** (experiment 05 exactly): `rl4cv.veribench.generate --thinking on --seed 91 --stop-token '<|im_end|>' --max-tokens 12288 --temperature 0.6 --top-p 0.95 --top-k 20 --samples 8`, 135 tasks, 1,080 cells per system, kernel-scored as in § 4.
- **Gates per checkpoint:** (a) a Lean block is extracted in ≥ 90% of cells; (b) ≤ 10% of cells end at the 12,288-token cap; (c) `kernel_binary` mixed-group share ≥ 0.05 over the 135 tasks (gate G1 of experiment 01; point estimate, Wilson 95% interval reported).
- **Also reported (no gate):** pass@8 share, all-pass share, mean pass rate, IC_tests rate, mean proof fraction, mean generated tokens, and within-task diversity (mean pairwise word-5-gram Jaccard of a task's 8 extracted files), each per size and fraction.
- **Selection:** f* is the smallest fraction at which all four sizes pass (a)–(c), and π₀(N) is each size's checkpoint at f*. The answer to "how many SFT tokens" is S's assistant tokens up to f*. If there is no common fraction, the verdict is PARTIAL (each size's earliest passing fraction is reported) or NOT READY. `expt_v1/results/selection.json` (f*, checkpoint paths and hashes, gate table) is committed **before any test-split generation**.

## 10. Test evaluation (once, after the selection commit)

- **Systems:** π₀(N) at every size (under PARTIAL, each passing size's earliest passing checkpoint, labelled as such), Base 14B (generated), and Base 1.7B / 4B / 8B (experiment 05 receipts restricted to the 222 test tasks).
- **Sampling:** as § 9, 222 tasks × 8.
- **Factors:**
  - IC_tests and IC_proofs from the kernel.
  - FSC from `vb103_judge` (D-102; experiment 100's H2 ensemble), run as a new labelled suite `rl4cv-e08:<system>`, for every cell with IC_tests · IC_proofs > 0.
  - `fsc_compiled` = that FSC, and 0 for cells that do not compile (D-003).
- **Aggregate:** SCSC = (mean IC_tests · mean IC_proofs · mean `fsc_compiled`)^(1/3) over all cells (D-009), always with the three factor means and n. Reported for all 222, core 152 and IndustrySet 70 separately. 95% intervals come from a task bootstrap with 10,000 resamples. Judge failures are `unmeasured`: listed and bounded (all 0 / all 1), never counted as 0.
- **Primary comparison:** per size, π₀(N) minus Base, on the `kernel_binary` mean pass rate and on SCSC, with a paired task-bootstrap 95% interval.

## 11. RL

Not part of version 1. On RL-READY, version 2 locks its own protocol before any RL step: GRPO from π₀(N) on train-split prompts, `kernel_binary` reward first, validation monitoring, and one test evaluation.

## 12. Preflight

**Before lock 1 (zero model calls except the last item):**

1. `make test` passes on the host, including the split reproduction test against the pinned VeriBench files.
2. The served pack is built: 539 instructions with hashes matching experiment 05's, and no gold anywhere in the pack.
3. The service answers 200 with the bearer and 401 without, both locally and through the tunnel. The per-task time limit read back is ≥ 2 × the agent's client timeout + 600 s.
4. A registry dump (zero calls) confirms both selectors, their settings and that the Opus 5.5 selector has no fallbacks. The bucket's `vb103_single_call` bytes are recorded and checked against § 2.
5. Identity and payer are recorded with non-secret evidence: host, Valkyrie environment and organization, the secret mapping by name, and the payer.
6. The scorer adapter check (§ 4) is recorded.
7. **Live preflight:** 2 train tasks × 2 sample labels (`rl4cv-e08-preflight-<short>-p1/p2`) × 2 teachers = 8 calls. Each is scored end to end, with status, finish reason, delivered settings, charge and response SHA-256 recorded. **Independence:** for each teacher, the two samples' response hashes differ on at least one of the two tasks. Otherwise sampling is suspected to be cached; record BLOCKED and investigate before any manifest call.

**Before lock 2:**

1. S is assembled and its § 7 statistics are recorded.
2. The rendering prefix check and the tokenizer identity check across all four sizes pass on every example.
3. **NeMo RL dry run on Qwen3-1.7B-Base:** 16 examples, 8 steps. Prompt tokens get zero loss, and the counted loss tokens equal the rendered assistant spans. The loss decreases. A checkpoint exports to Hugging Face format, loads in vLLM, and generates on 2 validation tasks with extraction working. The outputs are discarded and never selected.
4. The GPU plan per size is recorded (Trigger Rule 9 estimate).

## 13. What is committed

- **Committed:** this protocol with its lock lines; the scripts and configs, with no secrets; manifests and hashes; per-cell receipts without content; scored summaries; the S manifest (ids, hashes, token counts); training-loss CSVs; checkpoint hashes; per-task evaluation CSVs (counts and factors, no file contents); `selection.json`; and `results.md`.
- **Host only** (`/lfs/skampere1/0/brando9/rl4cv_e08/`): raw teacher responses, Lean files, the SFT JSONL, checkpoints, raw generations and the private Valkyrie configuration.

## 14. Allowed infrastructure changes

The following may change without a new version, and each change is recorded: ports, tunnel, concurrency, GPU layout, re-sends under § 3, scorer parallelism, and the vLLM tensor-parallel degree. The following change only by a new version: models, revisions, selectors, efforts, K, prompts, the keep rule, the screen, the S rule, the recipe, sampling, gates, the selection rule and the test procedure.
