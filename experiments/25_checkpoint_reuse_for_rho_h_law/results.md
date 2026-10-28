# Experiment 25 (checkpoint reuse): Stage 0 results (0a to 0e) and R5 arms Q1 and Q3

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/25_checkpoint_reuse_for_rho_h_law/results.md>

**TLDR:** Stage 0 and the first R5 arms (Q1, Q3) are done on committed data, public checkpoints and public logs, protocol frozen first ([PROTOCOL.md](PROTOCOL.md), addenda A and A.1 committed before any R5 generation). Verdicts, one line each:
- **P2 (prefix fit vs full fit, toy): HOLDS, weakly.** RMSE ratio at held-out n4 0.975 (Night 4) and 0.970 (Night 5); Eq. 7 has no skill on the toy there (RMSE 3.07 pp vs observed SD 2.96 pp), so two equally poor fits agree.
- **P4 (1.7B SFT rungs vs fresh runs): EQUIVALENT.** ΔH +0.002 [−0.024, +0.027] inside ±0.073; Δlog ρ +0.174 [−0.170, +0.480] inside ±0.49 only (coarse margin), not ±0.244.
- **P6 (Q1, Delphi replicas): NOT TESTABLE as frozen.** Only 2 (3.4B) and 3 (9.7B) environments are measurable (q_mixed ≥ 0.2) in all three replicas; the protocol needs ≥ 4. Descriptive only: at 9.7B on the 3 common environments the pooled seed SD is 0.16 of the between-environment SD for log ρ and 0.31 for H; the lowest pairwise Spearman of the environment ranking is 1.0 (log ρ) and 0.5 (H), with 3 environments. Not a pass.
- **P8 (Q3, sigmoid vs Eq. 7 on public RL reward curves): worked example, not tested (3 blend curves + 4 logs ≤ 7). Neither form beats a flat baseline.** Sigmoid MAE/range on the Snowball blend: 0.244 (5.7T), 0.132 (async), 0.381 (sync), all above the 0.10 bar; Eq. 7 gives 0.249, 0.134, 0.382; the flat "last 5 fit-window steps" baseline gives 0.265, 0.131, 0.373. Delphi D1 to D4 logs: sigmoid 0.121, 0.078, 0.212, 0.079 (2 of 4 under 0.10).
- **Q4 and Q2(c): blocked by license** (`license: other` with no text; RL endpoints have no license). **Decision for Brando (not taken):** ask laion for a license, or relax the unclear-license rule.
- **Smoke and generator:** completion-mode generator in `expt_v2/` passed the 0e smoke on a free skampere1 A100 (Delphi 3.4B, 400 of 400 samples, extraction non-empty 100%).
- Q2(a) and Q2(b) were not run in this task (about 2 of the 20 GPU-hours used); no result here is evidence about Lean code verification.

## Deviations from the frozen protocol (none silent)
0. Freeze timing: PROTOCOL.md was committed locally (before any 0b, 0c outcome was computed or read) but pushed to main together with the results, because a full `make test` had to pass before any push and the suite takes 20 minutes. The commit order, not the push order, is the evidence of the freeze. `make test`: 1,397 passed, 7 failed, 58 skipped; the 7 failures are in unrelated experiment 08 and 13 tests (missing cluster files and modules in a fresh clone), none in `tests/test_e25_stage0.py` (6 passed).
1. 0e found the plan's Q4 recipe numbers wrong for the four D-endpoints (G = 8, 64 prompts per step, 100 steps, lr 1e-5; the plan's G = 16, batch 256, about 146 steps belong to other repos). Q4 is not run (license), so no measurement is affected.
2. The 0c adapter check "`unparseable` False on every ladder row used" is enforced for the two 1.7B rungs P4 uses (0 rows each); four other files each contain one unparseable row and are reported but not used in P4 (`ladder/base_8B_e05`, `ladder/sft_14B_f0p125`, `ladder/sft_14B_f1p0`, `fresh/v16_v4_20260831`; in the last, P4 uses it as a fresh seed with that row kept as scored by the original run).
3. The completion-mode generator and its smoke pass were first reported as not done; a later run did them (smoke PASS, Q1 generated and scored, Q3 run on CPU). Q2(a) and Q2(b) remain not run (time; follow-up AT-1796).
4. 14B rung size: the plan quotes 177 GB per rung; live `du` on skampere1 shows 56 GB per rung (`pytorch_model.bin`, 5 rungs = 280 GB). The plan figure is stale or counted something else.
5. P6 precondition: the protocol asks for ≥ 4 measurable environments per scale; at 3.4B only 2 and at 9.7B only 3 are measurable in all three replicas, so P6 is reported as NOT TESTABLE and the SD and Spearman figures are descriptive. `rg/leg_counting/L0` has 103 distinct test questions (n recorded, per addendum A.1) and `coin_flip` L0 and L1 were NOT BUILT (0 and 2 distinct questions). The 9.7B base replica's GSM8K cell has q_mixed 0.196, just under the 0.2 bar.
6. Q3 detail not in the frozen text: the Delphi D1 to D4 logs hold raw rewards in [−1, 1], so each D curve was shifted to its observed minimum before the sigmoid fit (the frozen A in [0, 1.5 × max] assumes non-negative rewards); the Snowball curves were not shifted. The blend average uses the domains present at each step (17.2 of 18 on average for sync and 5.7T, 12.8 for async). The flat last-5-steps baseline is an addition, reported beside the two frozen forms.
7. Measurement note: the 8-shot direct-answer format makes the models answer in 5 to 60 tokens, so accuracies on GSM8K and MATH are low (0.02 to 0.08); this is the protocol, not a generator fault, and is the reason few environments clear the bar.
8. Tests: after the R5 code, `tests/test_e25_stage0.py`, `tests/test_e25_completion.py` and `tests/test_e25_q3.py` give 15 passed, 1 skipped; the full `make test` was not rerun after the R5 code, so the 7 pre-existing experiment 08 and 13 failures in deviation 0 stand as last measured.

## 0a Inventory (what exists that could feed the law)
Checked live on skampere1 (read-only, Kerberos keytab; Sherlock not checked: it needs a Duo passcode and the rule is no Duo pushes).
| Item | Location | Size | Count / labels | Retention risk | Feeds |
|---|---|---|---|---|---|
| SFT ladder (exp 08, 4 sizes × 5 rungs) | skampere1 `/lfs/skampere1/0/brando9/rl4cv_e08/ckpt/{1.7B,4B,8B,14B}/hf/step_{82,164,334,497,658}` (Oct 8 to 11) | 7.6 GB (1.7B), 17 GB (4B), 31 GB (8B), 56 GB (14B) per rung; 20 rungs about 0.56 TB | 5 rungs per size, steps 82 / 164 / 334 / 497 / 658 (12.5 / 25 / 50 / 75 / 100% of data) | `/lfs/skampere1/0` is 98% full (1.1 TB free of 56 TB); the 14B steps 82 / 164 / 497 were proposed for deletion (not done by this task; hold request in the plan §7) | R4 (rungs as start policies), a real probe at rungs (0c uses the saved per-sample scores, not the weights) |
| Ladder per-sample scores | repo `experiments/08_*/expt_v1/results/ladder/*_validation_cells.csv` | 32 files × 1,080 rows | 20 rungs + 4 Base + v27 / v16 fresh | none (committed) | 0c |
| v27 fresh 1.7B runs (12.5 / 25 / 50% × 2 seeds) and v16 100% seeds | scores in repo `expt_v27_data_size_seeds/results/analysis/`; step logs and checkpoints on Sherlock `$SCRATCH` | NOT CHECKED (Sherlock) | 6 + 2 runs | `$SCRATCH` purge after 90 days; v4 archive reported durable under `/home/groups/sanmi` (from notes, not re-verified) | R4, per-step curves |
| NeMo RL exp 13 v3 (4B) | skampere1 `/lfs/skampere1/0/brando9/rl4cv_e13v2` | 170 GB (whole tree) | latest checkpoint only (stalled at 6 to 22 of 30 updates) | SNAP disk pressure | none usable for a trajectory |
| Toy cells (Nights 4, 5) | repo `experiments/16_*/expt_v{4,5}/results/night{4,5}/` | 576 cells each | 16 env × 4 scales × 3 seeds × steps 25 / 50 / 100; `start_n1..4.pt` kept for Night 5 | none | 0b |
| Complete Lean RL trajectory | none | n/a | no run has finished | n/a | the gap this plan addresses |
Not found (stated, not guessed): any mid-run ρ or H measurement; any per-step rollout log of an RL run with Lean scoring.

## 0b R2 prefix extrapolation (toy), `expt_v1/results/0b_prefix_night{4,5}.json`
Setup as frozen: Eq. 7 fit on steps {25, 50, 100} (FULL), {25, 50} (PREFIX50), {25} (PREFIX25, fixed-median C0), scale n1 to n3, 16 environments, 3-seed mean; target = step 100 at the held-out scale. Ranges are over the 10 distinct resamples of the seeds {0, 1, 2}; with 3 seeds there is no finer interval. 16 cells per target, 3 trajectories per cell.
**Night 4, held-out n4 (primary):**
| Fit | RMSE pp [seed-resample range] | Rank accuracy | RMSE of "predict 0" | SD of observed U | RMSE on cells with U < 0 / n cells |
|---|---|---|---|---|---|
| FULL | 3.07 [2.98, 3.30] | 0.463 [0.43, 0.48] | 3.83 | 2.96 | 3.18 / 14 |
| PREFIX50 | 3.00 [2.92, 3.17] | 0.479 [0.45, 0.49] | 3.83 | 2.96 | 3.01 / 14 |
| PREFIX25 | 3.17 [3.03, 3.48] | 0.487 [0.42, 0.50] | 3.83 | 2.96 | 3.33 / 14 |
**Night 4, held-out n3 (secondary, fits on n1 to n2):** FULL 2.69 / 0.492; PREFIX50 2.65 / 0.492; PREFIX25 2.85 / 0.492 (RMSE pp / rank accuracy).
**Night 5, held-out n4:** FULL 3.14 [2.92, 3.44] / 0.417; PREFIX50 3.05 [2.82, 3.32] / 0.417; PREFIX25 3.30 / 0.433; predict-0 RMSE 4.07, SD 3.01. **n3:** FULL 2.65 / 0.479; PREFIX50 2.62 / 0.454; PREFIX25 2.72 / 0.446.
**P2 verdict (frozen criteria): HOLDS, both nights, primary and secondary.** RMSE ratio PREFIX50/FULL at n4: 0.975 (Night 4), 0.970 (Night 5); rank-accuracy gap (FULL − PREFIX50): −0.017 and 0.000; at n3: ratio 0.984 and 0.990, gap 0.000 and 0.025. It holds in 10 of 10 seed resamples in each case (largest ratio 0.986, largest gap 0.008 on the resamples). The sensitivity (fixed-median C0 instead of the grid) changes RMSE by at most 0.1 pp. In-scale step-100 forecasts from the prefix (n1, n2, n3) are within 0.00 to 0.12 pp of the full fit (ratios 1.00 to 1.10; the worst is n1 on Night 4, 1.09 → 1.21 pp). The sigmoid per-cell arm is NOT FITTABLE on this data (a 50% prefix has 2 budget points; the toy has only 3 budgets per trajectory) and is deferred to Night 6.
**How much weight this carries.** Weak. On the toy, Eq. 7 at the held-out scale is no better than predicting the environment mean (RMSE about 3.0 to 3.1 pp against an observed SD of 3.0 pp; pairwise rank accuracy 0.42 to 0.49 against 0.5 for chance), so "the prefix fit is as good as the full fit" means two fits with no skill agree. It does show that the budget-axis information in steps 25 and 50 is not the bottleneck; the bottleneck is the environment term at a new scale (forgetting regime at n4: 14 of 16 cells have U < 0). P2 is untested in a regime where the law has skill (the in-scale n1 target, RMSE 1.1 pp, is the closest).
**Retrospective Night 4 → Night 5 (labeled RETROSPECTIVE; Night 5 outcomes were committed; not a forecast),** `0b_cross_start_night4_to_night5.json`: law fit on Night 4 (n1 to n3), scored on Night 5 (new start checkpoints, same environments and seeds), RMSE pp (rank accuracy):
| Scale / step | Law | Persistence (Night 4's measured U) | Night 4 environment mean |
|---|---|---|---|
| n1 / 100 | 1.04 (0.68) | 0.33 (0.91) | 1.23 |
| n2 / 100 | 2.21 (0.52) | 0.41 (0.90) | 2.37 |
| n3 / 100 | 2.60 (0.47) | 0.21 (0.93) | 2.74 |
| n4 / 100 | 3.14 (0.47) | 0.39 (0.97) | 3.02 |
Steps 25 and 50 are in the JSON and show the same pattern. Reading: Night 4's own measured utilities predict Night 5 almost perfectly, so what varies across the pretraining draws is small compared with what varies across environments (consistent with the log ρ and H seed differences quoted in the plan), but Eq. 7 itself does not capture that environment ordering on the toy (the same near-chance rank accuracy). That supports reuse of probes across starts (the Q1 question) and says nothing in favor of the law's coefficients.

## 0c R4 on real data, `expt_v1/results/0c_real_rho_h.json`
135 VeriBench validation tasks × 8 samples per cell; ρ, H by `measure_environment` with `admitted = not capped`; task-level bootstrap, 10,000 draws (seed 20261028), the same resampled tasks for every arm. Task order is identical across all 32 files. Selected rows (point estimate, 95% interval): 
| Run | ρ | H | mixed tasks | admission | mean tokens |
|---|---|---|---|---|---|
| 1.7B SFT rung 50% | 4.8 [2.1, 8.0] | 0.074 [0.035, 0.119] | 11 | 0.77 | 5,984 |
| 1.7B fresh 50%, seed 20260830 | 3.3 [1.3, 5.8] | 0.062 [0.028, 0.104] | 9 | 0.74 | 6,142 |
| 1.7B fresh 50%, seed 20260831 | 3.4 [1.4, 6.0] | 0.062 [0.028, 0.104] | 9 | 0.79 | 5,874 |
| 1.7B SFT rung 100% | 10.9 [6.2, 16.6] | 0.132 [0.083, 0.188] | 20 | 0.83 | 5,370 |
| 1.7B fresh 100%, seed 20260830 (v16) | 9.5 [5.3, 14.7] | 0.121 [0.073, 0.176] | 18 | 0.83 | 5,541 |
| 1.7B fresh 100%, seed 20260831 (v16) | 12.4 [7.5, 18.2] | 0.159 [0.105, 0.218] | 24 | 0.82 | 5,493 |
The full table (20 rungs, 4 Base models, 8 fresh runs) is in the JSON. The 12.5% and 25% 1.7B rungs and fresh runs have 1 to 3 mixed tasks (ρ 0.2 to 0.8, H 0.007 to 0.021) and were declared uninformative before P4 was read. Training-noise yardstick (two fresh seeds): 50%: |Δlog ρ| = 0.04, |ΔH| = 0.0002; 100%: |Δlog ρ| = 0.26, |ΔH| = 0.037.
**P4 verdict (frozen: pooled 50% and 100%, rung minus mean of the two fresh seeds, paired bootstrap):**
| Metric | Pooled Δ [95%] | Half-width | Margin | Verdict |
|---|---|---|---|---|
| H | +0.002 [−0.024, +0.027] | 0.0255 | ±0.073 | EQUIVALENT |
| log ρ | +0.174 [−0.170, +0.480] (9,997 valid draws) | 0.325 | ±0.49 (coarse); ±0.244 (fine) | EQUIVALENT at the coarse margin only (not inside ±0.244) |
Per fraction: 50%: Δlog ρ +0.347 [−0.320, +0.951], ΔH +0.012 [−0.026, +0.049]; 100%: Δlog ρ +0.000 [−0.268, +0.243], ΔH −0.008 [−0.045, +0.031]. Caveats: 1.7B only, 2 fresh seeds per fraction (training-seed variability is represented only by those two points, not by the bootstrap), the rung and fresh runs used different trainers (NeMo on A100 versus a custom loop on a Sherlock GPU), and 9 to 24 mixed groups per cell. The fresh 100% seeds already differ by 0.26 in log ρ, which is about as large as the rung-versus-fresh gap.
**0d power note.** The frozen figures were 0.33 (log ρ) and 0.025 (H); measured 0.325 and 0.0255. The 0.25-SD margin for log ρ cannot be demonstrated with this data, as stated.

## 0e External-checkpoint audit (Hugging Face API and public pages; no weights downloaded), `expt_v1/audit_0e/`
All 25 Marin and laion ids in the plan exist and are ungated; every repo has only `main` (no intermediate-step branches, no tags, despite the README). Marin Delphi: Qwen3ForCausalLM, vocab 128,256, fp32 on disk (13.5 GB at 3.4B, 38.9 GB at 9.7B, 99.9 GB at 25B), `apache-2.0` with a `research-only` tag and no LICENSE file. The nine laion SFT-from-base repos and the Q4 start repo are bf16 with `license: other` and no license name, link or text anywhere (the SFT data `nyu-dice-lab/wildchat50m-rewild-sft-385700` is also `license: other`); the four RL endpoints have no README and no license field. Default rule (unclear → not used) applies.
- **Q4 start repo confirmed** from the training logs (`MODEL_PATH=laion/delphi-1e22-p33m67-32p07b-lr0_67-54770ae7-wc386k_lr1e5-sft` in all four); `rl_run_script.sh` is a template reading `MODEL_PATH` from the environment. `chat_template.jinja` is byte-identical across the four. D-endpoint recipe: lr 1e-5 constant, G = 8, 64 prompts per step, 100 steps, T 0.7, max 3,584 tokens, GRPO, no KL, entropy coefficient 0.01, 500-prompt sets: D1 `rlvr_math`, D2 `rlvr_ifeval`, D3 `dapo_math`, D4 `math500` (train on test). The training logs show D1 reward about 0 for steps 10 to 90 and −1.00 (cap) at step 100, D3 at −1.00 from step 30 (entropy collapse, as issue 6279 says for 5 of 6 math cells), D2 rising 0.31 → 0.75, D4 near 0. The published per-endpoint MATH-500 gains P9 needs sit in `main_rl_evals/SCORES.md` inside a 231 MB tarball that was not downloaded.
- **Seed semantics:** documented only as "training seeds"; Marin PR #10555 (lower-budget repeats) passes `seed` with `data_seed=None`, so in Levanter one seed drives both init and data order; the 1e21 and 1e22 replicas' recipe is not shown (inference). Final loss across the 3 replicas at 1e22: 2.5308, 2.5342, 2.5311. Only 5 seed-suffixed repos exist on HF (the PR says 20 will be published).
- **W&B** `dogml/delphi_rl_scaling_6279`: the page returns HTTP 200 (single-page app) but the anonymous GraphQL query returns `project: null`, the same answer as for a nonexistent project; not publicly readable. **Snowball artifacts** (`open-athena/Snowball-67B-A2B-Mixed-RLVR-Experiment-Artifacts`, card license `null`): numeric per-step data exist (`rlvr1-domain-reward-series.json`: 4,114 rows, 18 domains, sync and async 110 steps each, 5.7T 46; `all-step-generation-telemetry.csv`: per-step reward and pass@16; curves are stitched from resume lineages and not monotone). The four D-endpoint RL training logs hold 100 numeric steps each, so Q3 does not need W&B.
- **Disk (bf16-in-memory, on-disk bytes):** Q1 157.2 GB, Q2(a) 152.2 GB (the 25B repo alone is 99.85 GB: do not stage on this machine's 107 to 114 GB free; use cluster scratch or convert shard by shard), Q2(b) 67.7 GB, Q2(c) 43.6 GB (bf16; the plan's 90 GB assumed fp32), Q4 97.1 GB; union of Q1 + Q2(a) + Q2(b) 311.2 GB (matches the plan).
- **Smoke checkpoint recommended:** `marin-community/delphi-1e21-3.4Bparams-46.3Btokens` (Apache-2.0, 13.5 GB, shared by Q1, Q2(a), Q2(b)). The authors' log shows vLLM 0.11.0 loading Qwen3ForCausalLM for the Q4 start repo; not run by us. Pass `dtype=bfloat16` (config dtype is null).
- **Measurability risk (new):** published base-model GSM8K-flex pass@1 / pass@8 is 2.0 / 12.4 (3.4B) and 2.4 / 15.0 (9.7B), MATH500 pass@1 0.1; q_mixed ≥ 0.2 may fail on GSM8K and MATH at G = 8, so Reasoning Gym is the main hope; those numbers were measured with a raw-completion format whose shot count was not confirmed.
**Feasibility decision per arm (stop condition of plan §1b):**
| Arm | Verdict | Reason |
|---|---|---|
| Q1 | PASS on license and disk; measurability unknown | Apache-2.0, 3 replicas each at 3.4B and 9.7B |
| Q2(a) | PASS on license and disk; measurability unknown | 25B needs cluster scratch |
| Q2(b) | PASS on license and disk; smaller-D models likely at the floor | 5 repos exist |
| Q2(c) | FAIL | `license: other`, no text |
| Q3 | PASS | Snowball numeric curves (card license null: aggregates only, cite the source); Delphi D1 to D4 logs available but those repos fail the license rule, so only the logs' numbers (not the weights) are used and that is flagged |
| Q4 | FAIL | start repo `license: other`; endpoints no license; D1 and D3 collapsed |
To unblock Q2(c) and Q4: ask laion (the repo owner) to state a license, or the owner relaxes the default rule explicitly (a decision for Brando, not taken here).


## R5 smoke, Q1 and Q3 (CPU scoring; GPU generation on skampere1 A100s, `expt_v2/`)
**Smoke (0e, `expt_v2/results/0e_smoke_delphi_3p4b.json`): PASS.** `delphi-1e21-3.4Bparams-46.3Btokens`, bf16, vLLM 0.17.1, one A100, `rg/basic_arithmetic/L0` and `gsm8k/train500` × first 50 ids × G = 8: 400 of 400 samples returned in each environment, extraction non-empty 100%, correct samples present in both (accuracy 0.121 and 0.015), finite ρ and H, token counts well under the cap. Smoke numbers are not used in P6.
**Q1 (P6): environments and measurability per replica.** 8 environments built (500 ids each except `math/prealgebra_L1L2_int` 334 and `leg_counting/L0` 103 distinct, `coin_flip` NOT BUILT), 8-shot direct-answer completion, T 1.0, G = 8, max 512 tokens, per-environment measures in `expt_v2/results/q1_*_measure.json`, raw samples in `expt_v2/results/raw_samples/`, ρ and H by `measure_environment`. Each cell: q_mixed / ρ / H; "·" marks a cell below the q_mixed ≥ 0.2 bar (listed, excluded from P6, never dropped). Replicas: the base repo and the `-seed42` and `-seed62746` repos. Measurable environments per replica: 3.4B 2 / 3 / 3; 9.7B 3 / 4 / 4; in all three replicas: 3.4B 2 (`rg/basic_arithmetic/L0`, `rg/leg_counting/L0`), 9.7B 3 (`math/prealgebra_L1L2_int`, the same two).


**3.4B**

| Environment | n | base | seed42 | seed62746 |
|---|---|---|---|---|
| gsm8k/train500 | 500 | 0.13 / 3550 / 0.125 · | 0.11 / 1873 / 0.101 · | 0.16 / 4788 / 0.153 · |
| math/prealgebra_L1L2_int | 334 | 0.19 / 5901 / 0.177 · | 0.20 / 6281 / 0.181 | 0.22 / 5569 / 0.197 |
| rg/basic_arithmetic/L0 | 500 | 0.63 / 5655 / 0.521 | 0.57 / 1823 / 0.462 | 0.61 / 3590 / 0.500 |
| rg/basic_arithmetic/L1 | 500 | 0.09 / 1730 / 0.065 · | 0.08 / 224 / 0.049 · | 0.08 / 722 / 0.060 · |
| rg/leg_counting/L0 | 103 | 0.70 / 9528 / 0.633 | 0.50 / 3804 / 0.440 | 0.54 / 32702 / 0.481 |
| rg/leg_counting/L1 | 500 | 0.16 / 987 / 0.150 · | 0.13 / 407 / 0.126 · | 0.19 / 8539 / 0.172 · |
| rg/simple_equations/L0 | 500 | 0.14 / 5555 / 0.114 · | 0.14 / 1064 / 0.116 · | 0.15 / 5645 / 0.116 · |
| rg/simple_equations/L1 | 500 | 0.00 / 7 / 0.002 · | 0.01 / 61 / 0.005 · | 0.00 / 39 / 0.003 · |

**9.7B**

| Environment | n | base | seed42 | seed62746 |
|---|---|---|---|---|
| gsm8k/train500 | 500 | 0.20 / 9786 / 0.180 · | 0.23 / 8551 / 0.206 | 0.23 / 6812 / 0.213 |
| math/prealgebra_L1L2_int | 334 | 0.31 / 19709 / 0.277 | 0.30 / 13796 / 0.266 | 0.31 / 19102 / 0.276 |
| rg/basic_arithmetic/L0 | 500 | 0.57 / 2928 / 0.484 | 0.71 / 4072 / 0.592 | 0.68 / 3908 / 0.565 |
| rg/basic_arithmetic/L1 | 500 | 0.09 / 946 / 0.060 · | 0.10 / 3482 / 0.076 · | 0.08 / 2230 / 0.054 · |
| rg/leg_counting/L0 | 103 | 0.60 / 28451 / 0.520 | 0.53 / 35465 / 0.474 | 0.66 / 38696 / 0.593 |
| rg/leg_counting/L1 | 500 | 0.15 / 1983 / 0.142 · | 0.17 / 2710 / 0.162 · | 0.16 / 5301 / 0.145 · |
| rg/simple_equations/L0 | 500 | 0.13 / 1045 / 0.119 · | 0.16 / 730 / 0.112 · | 0.13 / 906 / 0.117 · |
| rg/simple_equations/L1 | 500 | 0.00 / 0 / 0.000 · | 0.01 / 30 / 0.004 · | 0.01 / 62 / 0.005 · |

**P6 verdict: NOT TESTABLE as frozen (needs ≥ 4 measurable environments in the comparison at each scale; there are 2 and 3).** Descriptive figures (`expt_v2/results/p6_q1.json`, not a verdict): at 9.7B on the 3 common measurable environments, pooled seed SD of log ρ 0.18 vs between-environment SD 1.15 (ratio 0.16, bar 0.25) and of H 0.048 vs 0.153 (ratio 0.31, bar 0.25); lowest pairwise Spearman of the environment ranking 1.0 (log ρ) and 0.5 (H), with only 3 environments. On the 7 environments with any mixed groups in all replicas (not protocol; includes cells below the bar): 3.4B log ρ ratio 1.04 and H ratio 0.22, lowest Spearman 0.29 and 0.93; 9.7B log ρ ratio 0.27 and H ratio 0.17, lowest Spearman 0.89 and 0.96. Reading: environment ordering by H is stable across the three pretraining replicas at both scales; log ρ is noisy at 3.4B (a single cell, `leg_counting/L0`, goes from ρ 3,804 to 32,702 between replicas) and steadier at 9.7B; with 2 degrees of freedom and a bar that is not met, this does not decide whether 02B needs a second warm start. The `max_tokens` cap is almost never hit (mean 5 to 61 tokens), so admission is 0.94 to 1.00 and ρ is driven by the short answers.
**Why so few measurable environments.** GSM8K and MATH accuracy under direct-answer 8-shot is 0.02 to 0.08, q_mixed 0.11 to 0.31; Reasoning Gym L1 sets and `simple_equations` are at the floor. GSM8K clears the bar only at 9.7B (2 of 3 replicas); MATH prealgebra clears it in 3 of 3 replicas at 9.7B and 2 of 3 at 3.4B. This is the measurability risk flagged in 0e, confirmed.

**Q3 (P8), `expt_v2/q3_p8.py`, `expt_v2/results/q3_p8.json`.** Sigmoid in log step (A ∈ [0, 1.5 max], log t_mid ∈ [0, log 2T], B ∈ [0.1, 5], multi-start least squares) and Eq. 7's saturating form a·t/(t + t0) fitted on 10% to 50% of the steps; MAE on 50% to 100% divided by the curve's observed range; bar 0.10. Snowball card license is `null` (aggregates only, source cited); the D1 to D4 repos fail the license rule, so only their training logs' numbers are used (flagged).
| Curve | steps | range | Sigmoid MAE/range | Eq. 7 MAE/range | Flat last-5 baseline |
|---|---|---|---|---|---|
| Snowball blend, 5.7T start | 46 | 0.348 | 0.244 | 0.249 | 0.265 |
| Snowball blend, Sept 11 async | 110 | 0.691 | 0.132 | 0.134 | 0.131 |
| Snowball blend, Sept 11 sync | 110 | 0.351 | 0.381 | 0.382 | 0.373 |
| Delphi D1 (rlvr_math) | 100 | 1.305 | 0.121 | 0.117 | 0.118 |
| Delphi D2 (ifeval) | 100 | 0.529 | 0.078 | 0.070 | 0.074 |
| Delphi D3 (dapo_math, collapsed) | 100 | 0.180 | 0.212 | 0.213 | 0.000 |
| Delphi D4 (math500) | 100 | 1.047 | 0.079 | 0.082 | 0.082 |
Per-domain Snowball curves with ≥ 40 steps: 52 curves, 49 evaluable; the sigmoid is under 0.10 on 12, median MAE/range 0.158; it beats Eq. 7 on 22 and the flat baseline on 14 of the 49. **P8 verdict: worked example, not tested (7 or fewer main curves).** The sigmoid does not meet the 0.10 bar on any of the 3 blend curves and does not beat a flat extrapolation; the two forms are indistinguishable, because the stitched and noisy curves are mostly flat after 50% of the steps (blend mean 0.24 to 0.27 in the fit window vs 0.19 to 0.28 after). This says the 50%-prefix fit has no demonstrated advantage on these public curves; it does not say the law fails on a Lean run.

## Status
Done in this task: 0a to 0e, the smoke pass, Q1 at 3.4B and 9.7B (P6 not testable), Q3 (worked example). Not run: Q2(b) and Q2(a) (follow-up AT-1796 keeps them; cap 20 GPU-hours, about 2 used), Q2(c) and Q4 (license). The downloaded Delphi weights on skampere1 `~/e25/hf` were removed after generation; raw samples (6 tarballs) and per-environment measures are committed in `expt_v2/results/`.

