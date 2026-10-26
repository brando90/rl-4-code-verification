# V23: fresh-base training with500 repaired tiny examples

**Doc link:** [experiment home](README.md)

**TLDR:** The user confirmed a fresh run again, adding the completed500 tiny repairs. Start from original Qwen3-1.7B-Base with a fresh optimizer, independently of the completed V20 weights and its ongoing validation. Freeze this protocol and all data/source hashes before updates.

## Initialization and admitted sources

- Original official Qwen/Qwen3-1.7B-Base revision ea980cb0a6c2ae4b936e82123acc929f1cec04c1; model.safetensors SHA2566df85b39330e5a425ee36253d0f894e4387e4f0a15b9c53cb467d668e6b3a841. Recheck all7cached model/tokenizer/config files and frozen Qwen template/vocabulary. No previous fine-tuned checkpoint or optimizer state enters initialization.
- Take the immutable3,568-row V20 admitted dataset, plus all470 accepted V21 tiny examples and30 accepted V22 Sol-review repairs, retaining exact receipt/comment-insertion provenance. Add the125 already discovered explicit Workbook alternatives only if they pass all existing source/receipt/comment/scope/token gates, protected screens and final global deduplication. Record exact source counts and exclusions; do not silently treat proposed4193rows as the measured total.
- Require strict explicit proofs under the existing broad-automation inventory, actual proof-sketch header and meaningful English inline comments. Preserve task implementation, API, specifications, theorem statements and tests. Named theorem axiom cones remain restricted to propext, Classical.choice and Quot.sound; no sorry/admit/new axioms/native_decide in named proofs. Preserve the original predeclared anonymous concrete-test exception explicitly.
- No new teacher generation or fresh bulk compilation: reuse exact checked-source kernel receipts. Comment-annotated outputs must have exact raw checked source, receipt, insertion replay, matching non-comment tokens and lexical context, and separate source hashes. Validate each final row rather than assuming all predecessor rows pass a new format.
- Recheck frozen FILE extraction, actual Qwen training template,16,384 total-token cap without truncation; tiny assistant answers remain below1000tokens. Screen inputs/answers against764 protected references with frozen exact and near gates; deduplicate responses and canonical public statements. Save full per-row decisions and exposure/loss-token counts before first update. All222 test tasks remain sealed; validation task content or outputs never enters training.

## Training, allocation and monitoring

- Same frozen V20/V12 one-pass defaults: deterministic source-interleaved schedule, seed20261019, microbatch1, accumulation2, full-parameter float32 weights/AdamW moments, bfloat16 autocast, SDPA, gradient checkpointing. Assistant-only token-weighted loss with prompt masked, end-of-turn/end-of-sequence supervised. Each example is exposed once.
- AdamW beta=(0.9,0.98), epsilon1e-5, decay0.1, clip1.0, learning rate2e-5,3%token warmup and cosine decay. Fresh optimizer. Dataset changes are disclosed; no equal-token causal claim against V20.
- One genuinely empty80GB A100 on skampere1, respecting shared E08/E13/device leases and setting CUDA_VISIBLE_DEVICES explicitly. GPU4 was empty at the root preflight; perform fresh admission and choose another empty device only if needed. V20 validation on GPU1 and all foreign jobs remain untouched. Expected allocated memory40–70GB, mostly GPU compute; roughly40–60minutes training, revised from actual throughput.
- Run a discarded longest-plus-shortest control using this exact base and dataset, then reload original base with a fresh optimizer for production. Record first actual update, device/PID identity, progress, durable optimizer checkpoints and final weight hashes. Training deadline12hours, generation/scoring8hours each. Monitor death and stalls with an independent remote watcher; preserve failures and optimizer state, no silent restart from zero after updates.

## Evaluation and output

After training evaluate the same135 frozen VeriBench V1 validation tasks x8samples=1080cells. Keep frozen prompts/adapter/kernel/binary scorer, seed91,temp0.6,top-p0.95,top-k20,thinking on,max12288newtokens,im_end stop and original SNAP inference backend. Exact infrastructure retries only; preserve every failed/missing cell. Target25% is the pre-existing binary validation success definition. Do not run the222-task test split or a paid judge.

Use separate RUN/corpus_training_v23 data/model/execution/evaluation paths. Retain V20 and its evaluation unchanged. Root publishes compact source/admission/training/cell receipts; raw models and generations stay remote. Existing compatible dependency overlay and writable cache fixes may be reused with exact provenance, without mutating shared environments or changing scientific settings.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).
