# Failure taxonomy of the step-658 validation outputs

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3/RESULTS_failure_taxonomy.md>

**TLDR:** At every size, about four of five validation attempts produce a Lean file that fails to compile, one in ten to one in six never finishes its file before the 12,288-token cap, and the rest are kernel successes; there is no middle ground because the frozen scorer only counts proofs in files that compile. The smaller models' format deficits are entirely unterminated long generations, not missing file markers. In a 48-file deterministic recheck of compile failures, the most common first error is an executable test that evaluates to false (14/48), followed by type or application mismatches (15/48), failed proof tactics (9/48) and unknown identifiers (7/48). Prepared for Lethan (1.7B/8B) and Rakshit (4B/14B) on 10-14-2026 with zero model calls; validation split only.

## Setup

- Systems: experiment 08 version 1, step 658 (5,752,936 loss tokens) at Qwen3 Base 1.7B, 4B, 8B and 14B (B = billion parameters). VeriBench V1 validation split (D-013): 135 tasks x 8 attempts = 1,080 declared cells per size, all 1,080 known at every size. Sampling as in the frozen ladder (temperature 0.6, top-p 0.95, top-k 20, 12,288 max tokens, seed 91). Test-split outputs were never opened.
- Inputs: the host scored rows `ladder/validation/scored/scored_sft_<size>_f1p0_g8.jsonl`, raw generations `ladder/validation/raw/gen_<label>.jsonl`, the per-shard scorer receipts (`kernel_theorems`, `agent_n_sorry`) and the committed per-cell CSVs `expt_v1/results/ladder/sft_<size>_f1p0_validation_cells.csv` (SHA-256 1.7B `3d8de2b4…`, 4B `6cc557f7…`, 8B `2487c550…`, 14B `fcd206e3…`; validation ids `666d6d6b…`). Every source hash is in [results/failure_taxonomy.json](results/failure_taxonomy.json) (`systems.<size>.sources`); the per-cell classification file (4,320 rows, no file contents) stays on the host at `/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/results/failure_taxonomy_cells.jsonl` (SHA-256 in the JSON).
- Code: [failure_taxonomy.py](failure_taxonomy.py). Primary category = first match of: not extracted; extracted but `compiles = false`; compiles with zero proved theorems; compiles with unproved, vacuous or unparseable theorems; `kernel_binary = 1`; otherwise compiles-all-proved-but-not-kernel-success. The token cap is an overlapping flag.

## Primary category per size (mutually exclusive; denominators 1,080 cells)

| Size | No Lean file extracted | Extracted, does not compile | Compiles, zero proved | Compiles, unproved or vacuous | Kernel success |
|---|---:|---:|---:|---:|---:|
| 1.7B | 183 (0.169 [0.129, 0.216]) | 844 (0.782 [0.735, 0.825]) | 0 | 0 | 53 (0.049 [0.027, 0.076]) |
| 4B | 134 (0.124 [0.086, 0.167]) | 846 (0.783 [0.735, 0.830]) | 0 | 0 | 100 (0.093 [0.060, 0.131]) |
| 8B | 106 (0.098 [0.066, 0.135]) | 870 (0.806 [0.760, 0.849]) | 0 | 0 | 104 (0.096 [0.063, 0.134]) |
| 14B | 85 (0.079 [0.048, 0.113]) | 865 (0.801 [0.755, 0.845]) | 0 | 0 | 130 (0.120 [0.083, 0.162]) |

Shares are cell shares with 95% percentile task-bootstrap intervals (10,000 draws, seed 0, unit = task with its 8 attempts); p-val=n/a (deterministic classification of complete manifests, no hypothesis test). The "compiles, all proved, not kernel success" category is also 0 at every size.

**Why the two middle columns are empty.** In all 4,320 cells, `compiles = true` holds exactly when `IC_tests = 1` and exactly when at least one theorem is counted proved; a file with any Lean error gets `n_theorems_proved = 0` from the frozen scorer. A failed proof tactic therefore appears as a compile error, and the receipts cannot separate "wrong definition" from "wrong proof" without rechecking the file (next section). `sorry` is rare: 0 / 4 / 4 / 1 compile-error cells (1.7B / 4B / 8B / 14B) contain it.

## Overlapping flags (same denominators)

| Size | Token cap (12,288) | No file extracted | Capped and still extracted | Not capped and no file | Unparseable theorem type | Kernel success |
|---|---:|---:|---:|---:|---:|---:|
| 1.7B | 184 | 183 | 1 | 0 | 0 | 53 |
| 4B | 134 | 134 | 0 | 0 | 0 | 100 |
| 8B | 106 | 106 | 0 | 0 | 0 | 104 |
| 14B | 84 | 85 | 0 | 1 (`cs_set__merge_sort` attempt 0, finish `stop`, 10,763 tokens) | 1 | 130 |

Every capped completion already contains the `FILE:` marker and an opening ```` ```lean ```` fence: the model started the file and never reached the closing fence, so the extractor finds no complete block. Mean generated tokens by category: kernel successes 1,947 / 2,215 / 2,189 / 2,129 (1.7B / 4B / 8B / 14B); compile errors 4,085 / 4,204 / 4,341 / 4,225; unextracted 12,288 (14B 12,270 because of the one `stop` cell). For 1.7B the frozen gate deficits of 75 extractions and 76 fewer capped outputs are the same 184 cells; for 4B the 26 and 26 are the same 134 cells.

Per task (135): mixed success 20 / 32 / 32 / 39; all eight attempts fail 115 / 102 / 103 / 96; all eight succeed 0 / 1 / 0 / 0.

## First error kinds in a deterministic sample of compile failures

24 compile-error cells per size (1.7B, 4B) were drawn by ascending `sha256("rl4cv-e08-v3-taxonomy-sample:" + task_id + "#" + sample_idx)` and recompiled with `lake env lean` in the private Lean v4.22.0 + Mathlib grading project (`sft_v3/results/lean_recheck_sample/`). The first `error:` line was bucketed by regex (order and patterns in the JSON):

| First error kind | 1.7B (n = 24) | 4B (n = 24) |
|---|---:|---:|
| Executable test false (`native_decide` evaluated that the proposition … is false) | 7 | 7 |
| Type or application mismatch, failed instance synthesis, non-definitional equality | 7 | 8 |
| Failed proof tactic (`unsolved goals`, `rfl`, `rewrite`, `introN`, `simp made no progress`) | 5 | 4 |
| Unknown identifier, constant or field | 5 | 2 |
| Syntax (`unexpected token`) | 0 | 1 |
| Other (`normal level must be rejected`) | 0 | 1 |
| No `error:` line in the recheck log (unresolved) | 0 | 1 |

Deterministic counts, p-val=n/a; 24 files per size give only a coarse picture (a Wilson 95% interval for 7/24 is [0.15, 0.49]). Roughly a third of sampled failures are wrong implementations caught by the model's own tests, another third are elaboration errors, and under a quarter are proof-only failures.

## Representative validation examples (task, attempt; first error line)

1.7B:

- Compile error: `security_set__security_6858__vulnerabilities__157_unsafesslfinishedmac` #1 (5,703 tokens, `stop`): `solution.lean:28:29: error: failed to synthesize`; `humaneval_set__humaneval_41_car_race_collision` #5 (1,784 tokens, `stop`): `solution.lean:66:0: error: Not a definitional equality: the left-hand side`.
- No file extracted: `cs_set__insertion_sort` #4 and `medical_oss_set_real__my_noisy_cgm_target_raise` #2, both 12,288 tokens, finish `length`, `FILE:` marker and opening fence present, no closing fence.

4B:

- Compile error: `security_set__security_6858__vulnerabilities__157_unsafesslfinishedmac` #1 (6,361 tokens, `stop`): `solution.lean:25:40: error: failed to synthesize`; `easy_set__11_myfirstchar` #2 (3,259 tokens, `stop`): `solution.lean:27:61: error: Application type mismatch: In the application`.
- No file extracted: `humaneval_set__humaneval_41_car_race_collision` #5 and `realcode_set__20_html_escape` #3, both 12,288 tokens, finish `length`, unterminated file.

Examples were chosen by the salted hash order in the JSON, not by hand; the "compiles but unproved" categories have no examples because they are empty. Full logs of the four rechecks are under `sft_v3/results/lean_recheck/` on the host.

## What this means for the continuation

1. The smaller models' gate failures are runaway generations: cut the tail of the length distribution (the median successful file is about 2k tokens) rather than teaching a new output format. Both conditions of the planned continuation should report the capped share at half and full budget as a primary diagnostic.
2. Compile failure is the dominant mass at every size (78-81%), and most sampled first errors are implementation or elaboration mistakes rather than proof failures. More exposure to correct files (replay) and more solution variants (expansion) both target this; the taxonomy cannot say which helps, which is exactly what the two-condition comparison measures.
3. Under the frozen scorer the "compiles but unproved" stage is unobservable; if the mentees want proof-level diagnostics they should add a Lean recheck like the sampled one to the evaluation, without changing the frozen scorer or gates.

**TLDR-end:** [rl4cv: 08 expt_v3 › failure taxonomy] Unterminated 12,288-token generations explain every missing extraction, compile errors are four of five cells at all sizes, and the frozen scorer leaves no "compiles but unproved" middle, so the continuation should be judged on capped share and compile rate as much as on kernel success.
