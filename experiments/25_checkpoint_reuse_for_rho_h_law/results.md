# Experiment 25 (checkpoint reuse): Stage 0 results (0a inventory, 0b, 0c, 0d, 0e)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/25_checkpoint_reuse_for_rho_h_law/results.md>

**TLDR:** Stage 0 is done on committed data and the public-checkpoint audit; protocol frozen first ([PROTOCOL.md](PROTOCOL.md), commit 4d740dd5). (0b) P2 HOLDS on the toy: a 50%-prefix fit (steps 25, 50) forecasts step 100 at the held-out scale n4 as well as the full fit (RMSE ratio 0.975 on Night 4 and 0.970 on Night 5, rank accuracy gap ≤ 0.02, 10 of 10 seed resamples), but this is weak evidence because Eq. 7 has no skill on the toy at n4 (RMSE 3.07 pp against the observed SD 2.96 pp, rank accuracy 0.46 where chance is 0.5). The Night 4 to Night 5 retrospective check shows the law is not transferable across pretraining draws any better than the environment mean, while simply reusing Night 4's measured utilities (persistence) has RMSE 0.2 to 0.4 pp. (0c) P4: ρ and H of the 1.7B SFT rungs match fresh runs: ΔH = +0.002 [−0.024, +0.027] EQUIVALENT within ±0.073; Δlog ρ = +0.174 [−0.170, +0.480] EQUIVALENT only at the coarse ±0.49 margin (not within ±0.244). (0d) The power note held (half-widths 0.325 and 0.0255). (0e) Q1, Q2(a), Q2(b) and Q3 pass the audit; Q2(c) and Q4 fail the license rule (`license: other` with no text; RL endpoints have no license); GPU arms were not run in this step (see the status line). No result here is evidence about Lean code verification.

## Deviations from the frozen protocol (none silent)
1. 0e found the plan's Q4 recipe numbers wrong for the four D-endpoints (G = 8, 64 prompts per step, 100 steps, lr 1e-5; the plan's G = 16, batch 256, about 146 steps belong to other repos). Q4 is not run (license), so no measurement is affected.
2. The 0c adapter check "`unparseable` False on every ladder row used" is enforced for the two 1.7B rungs P4 uses (0 rows each); four other files each contain one unparseable row and are reported but not used in P4 (`ladder/base_8B_e05`, `ladder/sft_14B_f0p125`, `ladder/sft_14B_f1p0`, `fresh/v16_v4_20260831`; in the last, P4 uses it as a fresh seed with that row kept as scored by the original run).
3. The completion-mode generator and its smoke-checkpoint pass need a GPU and are not done in this step; they are the first item of the R5 follow-up (the audit itself ran).
4. 14B rung size: the plan quotes 177 GB per rung; live `du` on skampere1 shows 56 GB per rung (`pytorch_model.bin`, 5 rungs = 280 GB). The plan figure is stale or counted something else.

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

## Status
GPU arms (R5) were NOT RUN in this step: the first GPU task needs the completion-mode generator to pass the smoke checkpoint, the arms need a GPU host that does not need a Duo passcode (skampere1 A100s through the keytab, 98% full disk; Sherlock excluded by the no-Duo rule), and the combined time exceeds one sitting. Filed as a follow-up with the arm order Q1, Q2(b), Q2(a) (Q4 and Q2(c) dropped by the license rule), cap 20 GPU-hours.
