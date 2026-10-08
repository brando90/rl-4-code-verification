# Experiment 08 results — matched Lean SFT warm start for Qwen3 Base from Valkyrie teachers on the VeriBench V1 train split

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/results.md>

**TLDR:** The VeriBench V1 train / validation / test split (539 / 135 / 222 tasks, D-013) and the zero-call baselines are done. On the new validation split, Qwen3 Base's `kernel_binary` mixed-group share at G = 8 is 0.000 (1.7B), 0.022 (4B) and 0.000 (8B), all below the 0.05 gate. The SNAP worker has finished every zero-call lock-1 check (served pack, scorer adapter, tokenizer template, service, route identity); lock 1 and the live teacher preflight are next.

**Status:** RUNNING (SNAP worker on `skampere1`, tmux `rl4cv-e08-worker`; zero-call lock-1 checks done, lock 1 pending)

**Last updated:** 10-07-2026 17:12 PDT (worker, lock-1 zero-call checks)

## Phases

| Phase | Status | Evidence |
|---|---|---|
| D-013 split | DONE (10-07-2026) | `expt_v1/results/split/` (manifest SHA-256 `157ce781…`), `tests/test_splits.py` |
| Base models on the splits (experiment 05 receipts) | DONE (10-07-2026) | `expt_v1/results/base_qwen3_e05_on_d013_splits.json` |
| Token-budget inputs | DONE (10-07-2026) | `expt_v1/results/token_budget_gold_lengths.json`, `token_budget_e103_teacher_yields.json` |
| Lock 1 preflight and lock | IN PROGRESS (zero-call checks DONE 10-07-2026; lock and live preflight pending) | `expt_v1/results/pack_check.json`, `scorer_adapter_check.json`, `template_check.json`, `deployment_e08.json`, `route_identity_e08.json` |
| Teacher runs (4,312 cells) | PENDING | — |
| Scoring, screen, SFT set S | PENDING | — |
| Lock 2 preflight and lock | PENDING | — |
| Matched SFT, 4 sizes × 5 checkpoints | PENDING | — |
| Validation ladder and selection | PENDING | — |
| Test evaluation | PENDING | — |

## D-013 split

| Split | All | Core | IndustrySet |
|---|---:|---:|---:|
| train | 539 | 369 | 170 |
| validation | 135 | 93 | 42 |
| test | 222 | 152 | 70 |
| total | 896 | 614 | 282 |

- **Groups:** 664 groups (434 single tasks, 229 pairs, 1 group of 4). They were linked by 230 security safe/vulnerable pairs, 2 exact Python copies, 4 exact gold-Lean copies, 1 near Python copy and 1 near gold-Lean copy.
- **Gold mapping:** all 896 Python tasks map to exactly one gold Lean file. The task ids are identical to experiment 05's 896.
- **Leakage check:** the largest Jaccard between tasks in different splits is 0.640 for Python (`realcode_set__1_insort_right` train vs `realcode_set__3_insort_left` validation) and 0.610 for gold Lean, both below the 0.70 grouping threshold.

## Baseline: Qwen3 Base on the D-013 splits (experiment 05 receipts, G = 8, zero new calls)

`kernel_binary` per task over 8 samples; mixed = between 1 and 7 passes. The 95% interval is Wilson's, with the task as the unit.

| Model | Split | Tasks | Mixed share [95%] | pass@8 share | IC_tests mean pass rate |
|---|---|---:|---:|---:|---:|
| Qwen3-1.7B-Base | validation | 135 | 0.000 [0.000, 0.028] | 0.000 | 0.0009 |
| Qwen3-4B-Base | validation | 135 | 0.022 [0.008, 0.063] | 0.022 | 0.0046 |
| Qwen3-8B-Base | validation | 135 | 0.000 [0.000, 0.028] | 0.000 | 0.0000 |
| Qwen3-1.7B-Base | test | 222 | 0.000 [0.000, 0.017] | 0.000 | 0.0000 |
| Qwen3-4B-Base | test | 222 | 0.005 [0.001, 0.025] | 0.005 | 0.0011 |
| Qwen3-8B-Base | test | 222 | 0.000 [0.000, 0.017] | 0.000 | 0.0000 |

Every mixed-share point estimate is below experiment 08's 0.05 readiness gate (experiment 01 G1's failure boundary, not its 0.20 strong-pass boundary); the 4B validation interval crosses 0.05, so this is not an uncertainty-adjusted rejection. p-val=n/a (no hypothesis test). Qwen3-14B-Base is not measured yet; PROTOCOL § 9 generates it.

## Token-budget inputs (zero calls, Qwen3 tokenizer)

| Quantity | Train | Validation | Test |
|---|---:|---:|---:|
| Gold Lean tokens, mean (median) | 2,312 (1,657) | 1,918 (1,718) | 1,995 (1,648) |
| Experiment 103 Opus 5 max single call, tasks passing the kernel proxy | 251 / 539 | 62 / 135 | 99 / 222 |
| … mean tokens of its passing files | 5,104 | 4,998 | 5,042 |
| Experiment 103 Astra high single call, tasks passing | 261 / 539 | 68 / 135 | 118 / 222 |
| … mean tokens of its passing files | 2,731 | 2,602 | 2,809 |

These historical validation/test summaries were inspected before the prospective protocol locks; the holdout claim concerns newly selected trained checkpoints, not unseen historical outcomes. Token `median` fields use the upper middle observation for even counts.

The kernel proxy is IC_tests = IC_proofs = 1 with at least one theorem and one `example`, without the vacuity check. Either teacher passes 362 of 539 train tasks; both pass 150. The estimate in [README.md](README.md#how-many-sft-tokens-estimate-before-any-call) is about 1,100–1,300 SFT examples, or about 4–5M assistant tokens per model.

## Light QA before dispatch (requested by Brando, one round)

- **Reviewer:** Codex CLI 0.161.0, model `gpt-6-astra`, reasoning effort `ultra`. This was a cross-company review of a Claude-built change, with role `acceptance` for the design.
- **Scope:** `ab650c3..4b66ca1` (commits `a17b899` and `4b66ca1`), meaning the split code, tests and artifacts, the D-013 / D-015 rule edits, and this experiment's design, protocol and runbook. Zero model calls, no Valkyrie runs, no GPUs.
- **Verdict block:**

  ```
  VERDICT: FIXED
  CRITICAL_ISSUES: 0
  MAJOR_ISSUES: 10
  FIXES_APPLIED: 14
  STRUCTURAL: IMPROVED
  SUMMARY: Corrected experiment 08's protocol, runbook and artifact validation while preserving the split and earlier experiment protections. Deterministic checks pass.
  ```

- **Major findings fixed (by the reviewer):**
  1. FSC judging covers every IC_tests = 1 cell on one common cohort (D-009), with D-102's 60-file audit and route controls.
  2. Screens cover full assistant text.
  3. The SFT-set priority and filter order are deterministic.
  4. An actual non-vacuity check is required (the stock adapter defaults it to zero).
  5. Locks precede live preflight and the dry run.
  6. Seed, scheduler, odd final batch and loss normalization are explicit.
  7. Incomplete gate inputs block selection.
  8. Worker paths are isolated under the experiment's work root.
  9. The input readers reject duplicate or incomplete rows.
  10. The split reproduction test fails, instead of skipping, on a dataset mismatch, and checks all seven artifacts.
- **Split unchanged:** all seven split artifacts reproduce byte for byte, and the manifest SHA-256 is still `157ce781…`.
- **Builder follow-ups after review (master, 10-07-2026 16:42 PDT):**
  - Reverted an out-of-scope title header the reviewer added above `CLAUDE.md`'s agents-config bootstrap lines.
  - Aligned PROTOCOL § 8 with Varun's committed config: his `LinearLR`-then-cosine schedule form, seed 20260830, SFT-time validation and Weights & Biases off.
  - Committed Varun's config files with provenance (`expt_v1/configs/`), so the worker needs no access to `skampere3`.
  - Added an upper scenario to the token estimate: about 1,200–1,600 examples and 4.5–6.5M assistant tokens.

## Worker setup and lock-1 zero-call checks (SNAP worker, 10-07-2026)

Host `skampere1`, work root `/lfs/skampere1/0/brando9/rl4cv_e08`, own clone on `main`. Zero model calls in this section.

| Check (PROTOCOL § 12, before lock 1) | Result | Evidence |
|---|---|---|
| `make test` with the pinned VeriBench root | 112 passed, 1 skipped (the skip is experiment 07's `scipy` test); all 13 split tests ran, including the reproduction test | `.venv`, `external/` at the three pins |
| Served pack (539 train tasks) | PASS: 539 / 539 instruction hashes equal experiment 05's receipts; no `.lean`, `solution/`, gold or theorem text outside `instruction.md`; system prompt `dc051963…`, addendum `a7a0fc1b…` | `expt_v1/results/pack_check.json` |
| Held-out screen of system prompt, addendum and 539 instructions vs validation + test Python and gold Lean (714 files) | 0 exact, 0 near hits; max word-5-gram Jaccard 0.177 (an instruction vs a validation Python program) | same file |
| Tokenizer template (control task, 4 sizes) | PASS: evaluation prompt is a byte and token-id prefix of the full render; loss span = `<think>\n\n</think>\n\n` + response verbatim + `<|im_end|>\n`; 1.7B / 4B / 8B / 14B tokenizer files and chat template byte-identical; 3,630 prompt tokens, 87 assistant tokens on the control | `expt_v1/results/template_check.json` |
| Scorer adapter (frozen scorer `59059a20`, private grading project, Lean v4.22.0 + Mathlib `79e94a09`) | PASS on 14 files: 3 train gold kept (IC_tests = IC_proofs = 1, `kernel_binary` 1); empty → `no_lean`, non-compiling → `no_typecheck`, `sorry` → `unproved_theorem`; the compiling `True` control → `vacuous_theorem` despite perfect kernel factors; 5 experiment-103 Astra train files reproduce experiment 103's IC_tests / IC_proofs / theorem and axiom counts exactly | `expt_v1/results/scorer_adapter_check.json` |
| Service | `rl4cv-e08-vbv1-train` on `127.0.0.1:9740` (claimed block 9740–9759) behind a bearer-protected cloudflared tunnel; health 200 with the bearer and 401 without, locally and through the tunnel; per-task limit read back 6,600 s = 2 × 3,000 + 600 | `expt_v1/results/deployment_e08.json` (URL and bearer only under `$WORK/private/`) |
| Route identity (D-108) | PASS: Valkyrie environment `bench`, log group `fellows/brando-miranda`, bucket `fellow-brando-miranda` (organization BrandoMiranda-fellow); the gateway key never reached the host (secret mapping `fellows/brandoModelGatewayApiKey` by name); installed `vb103_single_call` bundle = experiment 103's frozen hashes (`single_call.py` `6e1a9b0d…`); retry bound verified: at most 2 requests per cell, re-send only after HTTP 429/5xx, timeouts never replayed; payer Vals; 0 prior runs on this benchmark | `expt_v1/results/route_identity_e08.json` |
| Registry dump (10-07-2026, 454 models, SHA-256 `572c742f…`) | `anthropic/claude-opus-5-5-no-fallback`: fallback list empty (the only Opus 5.5 selector without fallbacks), default compute effort `max`, max_tokens 128,000; `openai/gpt-6-astra-max`: the highest served effort (max > xhigh > high > medium > low) | same file |

**Finding (gold references and the keep rule):** 403 of the 896 pinned gold references use `native_decide`, mostly in `example`s but sometimes inside named theorems, where the frozen scorer counts the theorem as not kernel-proved (IC_proofs 0.5 on the two aerospace diagnostics). The adapter check therefore picks its 3 gold files among references that never use `native_decide` and scores the first 2 that do as diagnostics (`forbidden_axiom`, `kernel_binary` 0). The keep rule for teacher files is unchanged.

## Open questions for Brando

- None blocking. Varun's math/code rows and warm-start checkpoints (D-105) would allow a math + code + Lean arm in a later version; ask him first.

**TLDR-end:** [rl4cv: expt 08 matched Lean SFT warm start] The VeriBench V1 split (539 / 135 / 222) and zero-call baselines are done: Qwen3 Base falls below the chosen validation-signal gate at all three measured sizes (mixed share ≤ 0.022). Teacher data, SFT and evaluation are pending on SNAP.
