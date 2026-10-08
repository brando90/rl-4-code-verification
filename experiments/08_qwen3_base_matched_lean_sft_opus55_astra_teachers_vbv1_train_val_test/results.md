# Experiment 08 results — matched Lean SFT warm start for Qwen3 Base from Valkyrie teachers on the VeriBench V1 train split

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/results.md>

**TLDR:** The VeriBench V1 train / validation / test split (539 / 135 / 222 tasks, D-013) and the zero-call baselines are done. On the new validation split, Qwen3 Base's `kernel_binary` mixed-group share at G = 8 is 0.000 (1.7B), 0.022 (4B) and 0.000 (8B), all below the 0.05 gate. The SNAP worker has finished every zero-call lock-1 check (served pack, scorer adapter, tokenizer template, service, route identity); lock 1 and the live teacher preflight are next.

**Status:** RUNNING (SNAP worker on `skampere1`; teacher data and S done; locking lock 2, then the dry run and matched SFT)

**Last updated:** 10-08-2026 02:43 PDT (worker, S assembled)

## Phases

| Phase | Status | Evidence |
|---|---|---|
| D-013 split | DONE (10-07-2026) | `expt_v1/results/split/` (manifest SHA-256 `157ce781…`), `tests/test_splits.py` |
| Base models on the splits (experiment 05 receipts) | DONE (10-07-2026) | `expt_v1/results/base_qwen3_e05_on_d013_splits.json` |
| Token-budget inputs | DONE (10-07-2026) | `expt_v1/results/token_budget_gold_lengths.json`, `token_budget_e103_teacher_yields.json` |
| Lock 1 preflight and lock | lock 1 LOCKED 2026-10-08T00:16 UTC at `6e6890f` (lock commit `cc86ec0`); live preflight (8 cells) IN PROGRESS since 10-07-2026 17:17 PDT | `expt_v1/results/pack_check.json`, `scorer_adapter_check.json`, `template_check.json`, `deployment_e08.json`, `route_identity_e08.json` |
| Teacher runs (4,312 cells) | DONE (10-08-2026): 4,312 / 4,312 terminal; measured 3,827; kept 2,004; charges 5,111.94 USD | `expt_v1/results/runs_state.json`, `results/receipts/preflight/` |
| Scoring, screen, SFT set S | DONE (10-08-2026): |S| = 1315 over 476 tasks, 5.75M assistant tokens | `expt_v1/results/scored_cells.jsonl`, `generated_lean_screen.json`, `sft_set_manifest.csv`, `sft_set_stats.json`, `teacher_analysis.json` |
| Lock 2 preflight and lock | IN PROGRESS: static checks PASS; lock and dry run next | `expt_v1/results/template_check_examples.json`, `sft_schedule.json`, `sft_config_diff.md` |
| Matched SFT, 4 sizes × 5 checkpoints | PENDING | — |
| Validation ladder and selection | IN PROGRESS: Base 14B DONE (passes all gates at the boundary, mixed 7 / 135); trained checkpoints pending SFT | `expt_v1/results/validation_ladder_base14b.json` |
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

## Live preflight (PROTOCOL § 12.7; 8 locked cells + 4 diagnostic cells)

| Teacher | Cells | Served | Finish | Lean collected | Scored | Independent samples | Charge (USD) |
|---|---:|---:|---|---:|---|---|---:|
| Astra (`openai/gpt-6-astra-max`, reasoning max) | 4 | 4 | `stop` ×4 (2.3–3.8k output, 17–33k reasoning tokens, 8–16 min) | 4 | 4 × `no_typecheck` (IC_tests 0; 6–9 theorems stated); prompt hashes = pack; extraction consistent 4 / 4 | yes (response hashes differ on both tasks) | 5.78 |
| Opus 5.5 (`anthropic/claude-opus-5-5-no-fallback`, compute max) | 4 | 4 | `model_error` / `MaxOutputTokensExceededError` ×4 after ~18 min | 0 | 4 × `no_lean` | not testable (no responses) | 0.00 recorded |
| Opus 5.5, compute **xhigh** (diagnostic, amendment A1) | 4 | 4 | `stop` ×4 (5.1–9.0k output, 22.8–43.3k reasoning tokens, 4–7 min) | 4 | 4 × **kept** (IC_tests = IC_proofs = 1, 10–20 theorems stated, none vacuous); extraction consistent 4 / 4 | yes (both tasks) | 3.51 |

- **Finding (10-07-2026, worker):** the gateway caps this model's output at 128,000 tokens (registry `properties.max_tokens`). Experiment 103's Opus 5 max run spent a median 76,840 reasoning tokens per cell and 117 / 895 cells hit the same error; experiment 02A v3's Fable 5.1 max preflight failed the same way. Opus 5.5 at max effort therefore cannot deliver files on most tasks under the locked settings, and the 2,156 main calls would be wasted.
- **Decision (agents-config Rule 57, flagged for Brando):** Opus main runs were not admitted at `max`. The tagged diagnostic preflight at `compute_effort xhigh` completed and passed end to end, so PROTOCOL § 3 was amended for `opus55` to `xhigh` (lock-1 amendment A1, version 1.1, `LOCKED 2026-10-08T00:55:51Z at bc27e1c`) before any Opus main call; the Opus main runs were then admitted. Astra's settings are unchanged; its 4 main runs (2,156 cells) were admitted at 17:44 PDT under the lock.
- **Harvest note:** `valk run results` answers "tracker returned a malformed response" on this tracker (as in 02A v3 and experiment 01); the run-output benchmark JSON carries the same per-task rows with the service-collected bytes, and the per-task `agent_output.tar.gz` carries `receipt.json` + `response.txt`.
- **NeMo RL infrastructure smoke (not scientific):** NeMo RL 0.4.0 at `c751f811` built with `uv` (worker venvs built at first launch); Qwen3-1.7B-Base, 4 synthetic examples, 2 steps on GPU 0 (21.7 GB): loss 2.73 → 2.15, `step_2` checkpoint saved with optimizer, scheduler and dataloader state, exported to Hugging Face format (`qwen3`). All four Base snapshots hash-verified against the hub (`expt_v1/results/model_weights_e08.json`).

## Base 14B on the validation split (generated here, PROTOCOL § 9; zero model calls)

Qwen3-14B-Base `0b0bd373…`, experiment 05's exact sampling, 135 tasks × 8 = 1,080 cells (frozen manifest `expt_v1/results/ladder_manifest_base14b.json`), all 1,080 known.

| Gate | Value | Threshold | Pass |
|---|---:|---|---|
| (a) extraction | 1,010 / 1,080 = 0.935 | ≥ 0.90 | yes |
| (b) capped at 12,288 tokens | 77 / 1,080 = 0.071 | ≤ 0.10 | yes |
| (c) `kernel_binary` mixed-group share | 7 / 135 = 0.052, Wilson 95% [0.025, 0.103] | ≥ 0.05 | yes (at the boundary) |

Diagnostics: pass@8 share 0.052, all-pass share 0, mean pass rate 9 / 1,080 = 0.0083, IC_tests rate 0.0083, mean generated tokens 2,001, within-task diversity (mean pairwise word-5-gram Jaccard) 0.144; 5 cells had a vacuous theorem and are not counted as passes. p-val=n/a (prespecified point-estimate gate). Note: Base 14B meets the readiness gate without any SFT, unlike Base 1.7B / 4B / 8B on experiment 05's receipts (0.000 / 0.022 / 0.000); the selection rule in PROTOCOL § 9 applies to the trained checkpoints and is unchanged. Evidence: `expt_v1/results/validation_ladder_base14b.json`, `expt_v1/results/ladder/base14b_validation_{per_task,cells}.csv`.

## Teacher runs, scoring, screen and the SFT set S (PROTOCOL §§ 3–7; 10-08-2026)

All 4,312 declared cells are terminal (8 Valkyrie runs of 539 cells, concurrency 24; one identical recovery re-send for 16 positively unserved cells, all measured). Every collected file was kernel-scored by the frozen scorer in the private grading project; `kernel_binary` includes the non-vacuity screen. Charges are the gateway's per-receipt reports (Vals-funded, D-108). Unmeasured = no model response (output cap, content filter, infrastructure); such cells stay in the denominator.

| Teacher / sample | Declared | Measured | Unmeasured | Kept | Kept / measured [Wilson 95%] | Truncated | Charge (USD) |
|---|---:|---:|---:|---:|---:|---:|---:|
| opus55/s1 | 539 | 539 | 0 | 303 | 0.5622 [0.52, 0.6034] | 97 | 447.75 |
| opus55/s2 | 539 | 539 | 0 | 287 | 0.5325 [0.4903, 0.5742] | 102 | 461.02 |
| opus55/s3 | 539 | 539 | 0 | 304 | 0.564 [0.5218, 0.6053] | 96 | 467.13 |
| opus55/s4 | 539 | 539 | 0 | 306 | 0.5677 [0.5256, 0.6089] | 101 | 460.19 |
| astra/s1 | 539 | 539 | 0 | 206 | 0.3822 [0.3421, 0.4239] | 0 | 840.9 |
| astra/s2 | 539 | 539 | 0 | 207 | 0.384 [0.3439, 0.4258] | 0 | 812.77 |
| astra/s3 | 539 | 539 | 0 | 193 | 0.3581 [0.3187, 0.3994] | 0 | 807.72 |
| astra/s4 | 539 | 539 | 0 | 198 | 0.3673 [0.3277, 0.4089] | 0 | 814.46 |

Union coverage: 479 / 539 train tasks have at least one kept file (share 0.8887, Wilson 95% [0.8593, 0.9125]); both teachers 277, opus55 only 159, astra only 43, neither 60. Total reported charge 5111.94 USD.

Failure taxonomy (cells): Opus 5.5 {"kept": 1200, "no_lean": 437, "no_typecheck": 515, "unproved_theorem": 2, "vacuous_theorem": 2}; Astra {"kept": 804, "no_lean": 34, "no_typecheck": 1316, "unparseable_theorem_type": 2}. `no_lean` cells are the unmeasured ones (Opus: 78 per run exceeded the 128,000-token output cap even at xhigh, 9–11 were content-filtered); `no_typecheck` is the dominant measured failure. Kept-file lengths (Qwen3 tokens): Opus mean 4908, median 4811, p90 6615 (n 1200); Astra mean 3055, median 2653, p90 4693 (n 804). Per-family union coverage: aerospace_set_real 2/2, aerospace_set_synthetic 10/10, compilers_set_real 3/3, compilers_set_synthetic 9/9, concurrent_set_real 3/3, concurrent_set_synthetic 9/9, critical_infra_set_real 4/4, critical_infra_set_synthetic 8/8, crypto_set_real 10/10, crypto_set_synthetic 2/2, cs_set 1/15, easy_set 20/25, finance_set_real 5/5, finance_set_synthetic 7/7, gov_cert_set_real 2/2, gov_cert_set_synthetic 10/10, hardware_set_real 3/3, hardware_set_synthetic 10/10, humaneval_set 30/34, hypervisor_set_real 3/3, hypervisor_set_synthetic 10/10, medical_oss_set_real 6/6, medical_oss_set_synthetic 6/6, memory_bugs_set_real 3/3, memory_bugs_set_synthetic 9/9, os_embedded_set_real 4/4, os_embedded_set_synthetic 8/8, realcode_set 3/19, regulated_set_real 3/3, regulated_set_synthetic 9/9, rfc_set_real 11/11, rfc_set_synthetic 1/1, security_set 255/276.

**Generated-Lean screen (§ 6):** 2004 kept, extraction-consistent cells → 6012 texts (file, full response, each fenced block) against the 714 validation + test Python programs and gold Lean references: 0 exact, 0 near hits (max word-5-gram Jaccard 0.0277); mean Jaccard to the task's own gold 0.0284 (max 0.1402), diagnostic only.

**S (§ 7):** |S| = 1315 examples over 476 distinct train tasks (Opus 798, Astra 517); exclusions {"over_length_cap": 4, "per_teacher_cap": 685} (the per-teacher cap of 2 distinct files is the rule, not a loss); per-task example counts {"0": 63, "1": 29, "2": 185, "3": 132, "4": 130}. Assistant tokens (template-inserted prefix + response + `<|im_end|>\n`): total 5,751,621, mean 4373.9, median 4296, p10 2213, p90 6623, max 12070; prompt tokens total 4,617,702 (mean 3511.6). Against the README estimate (1,100–1,600 examples, 4–6.5M assistant tokens): realized 1,315 examples and 5.75M assistant tokens, inside the upper scenario. Manifest (ids, hashes, token counts, no contents): `expt_v1/results/sft_set_manifest.csv`; stats `sft_set_stats.json`; the JSONL stays on the host.

**Lock-2 static checks (§ 12):** rendering prefix and mask on every example under all four tokenizers: 1315 / 1315 PASS (`template_check_examples.json`); NeMo RL's own formatter reproduces the evaluation prompt and the loss span (`<think>\n\n</think>\n\n` + response + `<|im_end|>\n` + `<|endoftext|>`) on every example with identical ids across sizes (`sft_schedule.json`, verdict PASS). Schedule: 658 steps of global batch 2 (|S| odd → one fully loss-masked padding slot in the last step), warmup W = 20 then cosine over 638; loss-token total 5,752,936; checkpoints at steps [82, 164, 334, 497, 658] (12.5 / 25 / 50 / 75 / 100 %, overshoot 1,658 / 4,315 / 8,240 / 4,079 / 0 tokens). Configs `expt_v1/configs/e08_sft_<size>.yaml` derive from Varun's with every difference listed in `sft_config_diff.md` (declared: `add_generation_prompt true` so the loss span excludes the generation prompt; openai_format adapter for the system message; SFT-time validation and Weights & Biases off; segment-and-resume checkpoints; GPU layout per size).

## Open questions for Brando

- None blocking. Varun's math/code rows and warm-start checkpoints (D-105) would allow a math + code + Lean arm in a later version; ask him first.

**TLDR-end:** [rl4cv: expt 08 matched Lean SFT warm start] The VeriBench V1 split (539 / 135 / 222) and zero-call baselines are done: Qwen3 Base falls below the chosen validation-signal gate at all three measured sizes (mixed share ≤ 0.022). Teacher data, SFT and evaluation are pending on SNAP.
