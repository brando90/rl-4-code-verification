# Experiment 10 results: promotion-policy replay on SWE-bench Verified factor matrices

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/results.md>

**TLDR:** Phase A's primary replay ran on the real data on 10-14-2026 (`skampere1`, zero model calls, 1,000 splits × 1,000 dyadic bootstrap draws over 164 systems × 424 tasks) under the LOCKED protocol revision 3 (commit `55d1c53`, forecast `e4eccd8b…3c23`), and **`expt_v2` completed on 10-15-2026** ([`expt_v2/results.md`](expt_v2/results.md)). Scored as frozen in `expt_v1`: **H1** the scalar rule (`candidate.score > incumbent.score`) makes a harmful promotion in 25.8% [24.1%, 28.2%] of small-validation-gain pairs; **H2a** supported, 0.1265 [0.0840, 0.1675], descriptive only; **H3 (`expt_v1` factor/binary gates) no recommendation** (`interval_includes_zero`): the factor matrix beats the scalar rule at equal validation gain (C_fac0 = 0.0210 [0.0017, 0.0403]) but not binary per-item pass/fail (C_fac = 0.0046 [−0.0027, 0.0117]), and "just be stricter" (S0+) is safer than uncalibrated per-item rules (−0.0652 [−0.0838, −0.0443] versus R3). **In `expt_v2` ([`expt_v2/results.md`](expt_v2/results.md)):** (1) fixing the `matched_test_lists` shape check to `164 × 421` ran all 1,000 splits (`0` degenerate) and reproduced every primary `164 × 424` finding within `0.002`; and (2) out-of-fold **2PL IRT (`R_irt2pl`) and 3-category GRM (`R_grm3`) promotion gates** cut within-stratum HPR from `0.2581` (`R0`) to **`0.2046` `[0.1848, 0.2297]`** ($\Delta\text{HPR} = +0.0535$ `[+0.0322, +0.0722]`, **20.7% relative cut**) and **`0.2000` `[0.1815, 0.2251]`** ($\Delta\text{HPR} = +0.0581$ `[+0.0374, +0.0764]`, **22.5% relative cut**, beating both `R2` by `+0.0418` `[+0.0227, +0.0603]` and `R3` by `+0.0372` `[+0.0182, +0.0537]`) while raising held-out $\Delta\text{pass@1}_E$ from `+0.0243` to `+0.0309` (`+0.0315` for `R_grm3_z`), and unstratified `S_grm3` achieves the lowest point-estimate HPR overall (`0.1659` `[0.1477, 0.1926]` vs `S0+` `0.1720`).

**Status:** PHASE A PRIMARY + `expt_v2` (421-TASK DRIFT SENSITIVITY + 2PL IRT / GRM3 GATES) DONE; PHASE B WAITING (10-15-2026).

**Last updated:** 10-15-2026.

| Stage | State | Evidence |
|---|---|---|
| Design and protocol revision 1 | DONE | commit `769ade0` |
| GPT-6 Astra (effort ultra) design review of revision 1 | DONE (15 findings, applied in revision 2) | [reviews/design_review_gpt6_astra_ultra_10-09-2026.md](reviews/design_review_gpt6_astra_ultra_10-09-2026.md) |
| GPT-6 Astra (effort ultra) protocol-and-code review of revision 2 | DONE: 3 blocking, 5 major, 1 minor; all fixed in revision 3, with counterexamples as regression tests | [reviews/review_gpt6_astra_ultra_protocol_r2_and_code_10-09-2026.md](reviews/review_gpt6_astra_ultra_protocol_r2_and_code_10-09-2026.md) |
| Claude Fable 5.1 review | NOT AVAILABLE: personal account out of usage credits (attempt 1 died 10:18 PDT, no file); Stanford account "Usage credits are required for this model"; Vals account "individual spend limit" (preflight probes, 10-09-2026). No credits bought | — |
| Protocol revision 3 | DONE (locked) | [PROTOCOL.md](PROTOCOL.md) |
| Analysis code and unit tests | DONE (15/15 pass in `v1`; 2/2 pass in `v2`) | `expt_v1/analyze_e10.py`, `expt_v2/analyze_e10_v2.py` |
| Synthetic checks | DONE | `expt_v1/results/synthetic/` |
| Lock and frozen forecast | DONE: commit `55d1c53` (10-09-2026 16:43 PDT); forecast `expt_v1/forecasts/e10_forecast.json`, SHA-256 `e4eccd8b84fa427fa9d5839980df6c08293f6a628f93cfc0c01f78cf2f163c23` (`verify_forecast` True on 10-14-2026); pins `analyze_e10.py` `a1278349…`, `tests/test_e10_replay.py` `dc1ba2e1…`, `per_cell_e07.jsonl.gz` `f064c395…`, drift list `e1d34185…` all re-verified | `expt_v1/forecasts/forecast_ledger.jsonl` |
| Phase A primary replay (`--sensitivity none`) | DONE: launched 10-14-2026 13:02 PDT on skampere1 (clone at `57c3bb6`, venv numpy 2.5.4, 15/15 tests pass there) in tmux `rl4cv-e10-phase-a-10-14`; 1,000 splits × 1,000 draws, 32 workers, one BLAS thread each; exit 0 at 13:04:56 PDT; output [`e10_primary.json`](expt_v1/results/e10_primary.json) SHA-256 `0005a03e455ae22a92edfee1d2632a4a3d1246ddfc8159d7c738b47f60ed20b1`, scored by [`expt_v1/score_e10.py`](expt_v1/score_e10.py) into [`e10_primary_verdicts.json`](expt_v1/results/e10_primary_verdicts.json) | [`expt_v1/results/run_e10_primary.log`](expt_v1/results/run_e10_primary.log) |
| Phase A sensitivity (`--sensitivity matched_test_lists`) | BLOCKED under `v1` lock (`(164, 420)` vs `(164, 421)`); **DONE in `expt_v2`** (10-15-2026 on `skampere1`, 1,000 splits × 1,000 draws over `164 × 421`, 0 degenerate splits, reproduces all primary metrics within `0.002`) | [`expt_v2/results.md`](expt_v2/results.md), [`e10_v2_matched_test_lists.json`](expt_v2/results/e10_v2_matched_test_lists.json) |
| `expt_v2` out-of-fold 2PL IRT and 3-category GRM promotion gates (`S_irt2pl`, `S_grm3`, `R_irt2pl`, `R_grm3`) | **DONE** (10-15-2026 on `skampere1`): `R_irt2pl` and `R_grm3` cut within-stratum HPR by `20.7%` and `22.5%` relative to `R0` and significantly outperform both `R2` and `R3` while increasing held-out $\Delta\text{pass@1}_E$ | [`expt_v2/results.md`](expt_v2/results.md), [`e10_v2_main.json`](expt_v2/results/e10_v2_main.json) |
| Phase B (real AlphaHebe records) | WAITING on the AlphaHebe team's export | [`PROMPT_dispatch_e11_hebe_factor_feedback.md`](../11_hebe_gepa_factor_feedback_and_nonregression_gate_2x2_swebench_verified/PROMPT_dispatch_e11_hebe_factor_feedback.md) |

## Phase A verdicts (primary run, population P_near, q = 0.5)

**How to read every number.** `x [lo, hi] p-val=n/a`: x is the mean over the 1,000 admitted task splits of the split-level statistic; [lo, hi] is the 2.5–97.5 percentile interval of that split average over 1,000 dyadic system-bootstrap draws (resampling unit: the 164 systems, pair weight m_I·m_C; seed `20261010`); no null-hypothesis test is run, so p-val=n/a. Split 5–95% ranges in the tables below are ranges, not intervals. Denominators: 164 systems × 424 tasks (reproduced; stop rule passed); 1,000 splits (seed `20261009`), 0 degenerate; median 2,382 P_near pairs per split (ordered pairs with 1 ≤ net_V ≤ 10, i.e. `near_max_net_gain` = 10 of 212 validation tasks). Every family had full support: 1,000/1,000 splits admitted and 1,000/1,000 draws valid, except the deployable rule's conditional HPR (430/1,000 valid draws, reported inconclusive). Thresholds (interval excluding 0, utility-guard lower bound −0.01, practical target 0.20) are the agent-suggested values frozen in `e10_forecast.json` before any real-data statistic existed. Verdicts were produced mechanically by `python3 expt_v1/score_e10.py --result expt_v1/results/e10_primary.json --out expt_v1/results/e10_primary_verdicts.json --tables`.

| Prediction (frozen) | Statistic | Value | Verdict |
|---|---|---|---|
| H1 (descriptive) | HPR of the scalar rule: share of P_near promotions with Δpass1_E < 0 | 0.2580 [0.2410, 0.2821] p-val=n/a | reported |
| H1 | share with losses_E ≥ 1 | 0.9991 [0.9961, 1.0000] p-val=n/a | reported |
| H1 | mean losses_E / \|E\| | 0.0754 [0.0690, 0.0820] p-val=n/a | reported |
| H1 | mean Δpass1_E (regression-to-the-mean check) | 0.0245 [0.0223, 0.0262] p-val=n/a | reported: positive on average |
| H2a: partial Spearman(HRM_V, losses_E/\|E\| \| losses_V, gains_V, pass1_V(I)) > 0 with interval excluding 0 | ρ_partial | 0.1265 [0.0840, 0.1675] p-val=n/a | **SUPPORTED**, descriptive only (see caveat) |
| H3 factor gate: C_fac = HPR(R2) − HPR(R3) > 0, interval excluding 0 | C_fac | 0.0046 [−0.0027, 0.0117] p-val=n/a | **not met** (interval includes 0) |
| H3 factor gate: C_fac0 = HPR(R0) − HPR(R3) > 0, interval excluding 0 | C_fac0 | 0.0210 [0.0017, 0.0403] p-val=n/a | met |
| H3 utility guard for R3 versus R2 and R0: lower bound of Δ mean Δpass1_E > −0.01 | R3 − R2; R3 − R0 | 0.0007 [−0.0000, 0.0014]; 0.0003 [−0.0014, 0.0023] p-val=n/a | met, met |
| H3 binary gate: C_bin = HPR(R0) − HPR(R2) > 0, interval excluding 0 | C_bin | 0.0163 [−0.0014, 0.0355] p-val=n/a | **not met** (interval includes 0) |
| H3 utility guard for R2 versus R0 | R2 − R0 | −0.0004 [−0.0020, 0.0014] p-val=n/a | met |
| **H3 decision** | | | **No recommendation: superiority or retained utility not established. Reason code: `interval_includes_zero`.** |
| Practical target: relative HPR reduction ≥ 0.20 versus S0+ (reported, not a rule) | S0+ − R3; S0+ − R2 | −0.0652 [−0.0838, −0.0443] (relative −0.379); −0.0698 [−0.0865, −0.0507] (relative −0.406) p-val=n/a | **not met**: S0+ is safer than both |

**What is and is not concluded.** Per the protocol, "no recommendation" is not evidence that per-item information has no value: the point estimates of all per-item policies are safer than R0 (R2 0.2418, R3 0.2372, R3h 0.2346 versus R0 0.2581), and C_fac0 and C_hid (0.0235 [0.0039, 0.0416]) do exclude zero. The factor-feedback question moves to experiment 11 without a gate claim. Power was never established (the synthetic signal set also crossed zero), and the whole study conditions on public system pairs, which omit candidate generation and search.

### Policies at q = 0.5 (P_near; family support 1,000/1,000 splits, 1,000/1,000 draws)

| Policy (information used) | HPR | mean Δpass1_E (benefit kept) | mean losses_E/\|E\| | recall of Δpass1_E > 0 pairs | achieved rate |
|---|---|---|---|---|---|
| S0+ (unstratified: largest net_V, "just be stricter") | 0.1720 [0.1549, 0.1991] | 0.0358 [0.0330, 0.0379] | 0.0706 [0.0643, 0.0769] | 0.5660 [0.5587, 0.5748] | 0.500 |
| S1 (unstratified: largest ΔSCS_V) | 0.1932 [0.1726, 0.2198] | 0.0334 [0.0303, 0.0358] | 0.0746 [0.0676, 0.0813] | 0.5503 [0.5411, 0.5616] | 0.500 |
| S2 (unstratified: fewest losses_V) | 0.2261 [0.2081, 0.2536] | 0.0261 [0.0237, 0.0280] | 0.0581 [0.0543, 0.0637] | 0.5222 [0.5115, 0.5359] | 0.500 |
| S3 (unstratified: smallest TRM_V) | 0.2283 [0.2083, 0.2578] | 0.0258 [0.0231, 0.0280] | 0.0578 [0.0541, 0.0633] | 0.5202 [0.5075, 0.5346] | 0.500 |
| R0 (gain-stratified, hash order: scalar only) | 0.2581 [0.2365, 0.2867] | 0.0243 [0.0218, 0.0262] | 0.0750 [0.0687, 0.0819] | 0.4986 [0.4879, 0.5089] | 0.499 |
| R1 (stratified, largest ΔSCS_V: smooth aggregate) | 0.2349 [0.2153, 0.2606] | 0.0286 [0.0258, 0.0308] | 0.0771 [0.0701, 0.0837] | 0.5171 [0.5097, 0.5252] | 0.499 |
| R2 (stratified, fewest losses_V: binary per-item) | 0.2418 [0.2248, 0.2668] | 0.0239 [0.0217, 0.0257] | 0.0586 [0.0550, 0.0642] | 0.5091 [0.4983, 0.5207] | 0.499 |
| R3 (stratified, smallest TRM_V: factor matrix) | 0.2372 [0.2179, 0.2637] | 0.0246 [0.0222, 0.0269] | 0.0582 [0.0548, 0.0640] | 0.5124 [0.5016, 0.5259] | 0.499 |
| R3h (stratified, smallest HRM_V: hidden regressions) | 0.2346 [0.2163, 0.2619] | 0.0254 [0.0227, 0.0274] | 0.0609 [0.0574, 0.0670] | 0.5147 [0.5041, 0.5262] | 0.499 |

All entries are `x [lo, hi] p-val=n/a`. Achieved rates are 0.499 for stratified policies because floor(q × stratum weight) drops the odd pair in each of the 10 strata.

### Paired contrasts (HPR(first) − HPR(second); positive = second safer), P_near

| Contrast | q = 0.25 | **q = 0.5 (primary)** | q = 0.75 | Utility guard at q = 0.5 (Δpass1_E of second − first) |
|---|---|---|---|---|
| C_bin = R0 − R2 | 0.0246 [−0.0075, 0.0584] | **0.0163 [−0.0014, 0.0355]** | 0.0072 [−0.0038, 0.0207] | −0.0004 [−0.0020, 0.0014] |
| C_fac = R2 − R3 | 0.0048 [−0.0086, 0.0176] | **0.0046 [−0.0027, 0.0117]** | 0.0060 [−0.0002, 0.0117] | 0.0007 [−0.0000, 0.0014] |
| C_fac0 = R0 − R3 | 0.0295 [−0.0030, 0.0620] | **0.0210 [0.0017, 0.0403]** | 0.0132 [0.0013, 0.0261] | 0.0003 [−0.0014, 0.0023] |
| C_hid = R0 − R3h | 0.0304 [−0.0025, 0.0635] | **0.0235 [0.0039, 0.0416]** | 0.0136 [0.0025, 0.0259] | 0.0011 [−0.0006, 0.0029] |
| C_agg = R0 − R1 | 0.0335 [0.0016, 0.0663] | **0.0232 [0.0042, 0.0405]** | 0.0140 [0.0044, 0.0243] | 0.0043 [0.0027, 0.0059] |
| C_strict = S0+ − R3 | −0.0922 [−0.1186, −0.0686] | **−0.0652 [−0.0838, −0.0443]** | −0.0303 [−0.0408, −0.0191] | −0.0112 [−0.0124, −0.0093] |
| C_strict = S0+ − R2 | −0.0970 [−0.1219, −0.0738] | **−0.0698 [−0.0865, −0.0507]** | −0.0363 [−0.0463, −0.0250] | −0.0119 [−0.0131, −0.0101] |
| S2 − S3 (risk-only rankings) | −0.0063 [−0.0208, 0.0066] | **−0.0022 [−0.0113, 0.0048]** | 0.0023 [−0.0045, 0.0086] | −0.0003 [−0.0011, 0.0005] |

All entries are `x [lo, hi] p-val=n/a`; p-val=n/a throughout. **q sensitivities:** the frozen decision is the same at q = 0.25 and q = 0.75 (no gate: C_fac includes 0 at all three q; C_bin includes 0 at all three; C_fac0 excludes 0 at q = 0.5 and 0.75 but not at 0.25). Every utility guard passes at every q (all lower bounds > −0.01; smallest −0.0037 for R2 − R0 at q = 0.25). Full per-q policy tables are in [`e10_primary.json`](expt_v1/results/e10_primary.json) and are printed by `score_e10.py --tables`.

### H2 sensitivities and the predictive comparison (P_near)

| Specification | Value | Reading |
|---|---|---|
| H2(a) HRM_V given losses_V, gains_V, pass1_V(I) | 0.1265 [0.0840, 0.1675] p-val=n/a | frozen prediction met |
| KRM_V in place of HRM_V | 0.0868 [0.0414, 0.1307] p-val=n/a | positive |
| HRM_V with the six marginal gate/factor means added | 0.0970 [0.0643, 0.1272] p-val=n/a | positive |
| TRM_V given gains_V and pass1_V(I) | 0.3146 [0.2492, 0.3756] p-val=n/a | positive (TRM_V also counts items that flipped, so this is partly losses_V itself) |
| H2(c) median out-of-sample R² for losses_E/\|E\|, endpoint-disjoint system halves (median 589 fitting and 591.5 evaluation pairs; 1,000/1,000 splits defined) | M0 (binary) 0.4313 (split 5–95%: 0.3165 to 0.5269); M1 (+marginals) 0.4030; M2 (+HRM, KRM, TRM, GLM) 0.3980 | adding the matrix features does not help prediction: median ΔR²(M2 − M1) = −0.0017 (5–95%: −0.0728 to 0.0379), share > 0 = 0.475 |

**Caveat, as frozen:** before the lock, H2(a) was 0.112 [0.056, 0.148] on a synthetic null set with no system-specific breakage trait, because factor values on hard, jointly unresolved tasks also sharpen the estimate of a candidate's ability. The real value, 0.1265, is of that size, so H2(a) is **not** evidence of a regression-specific mechanism. The endpoint-disjoint predictive comparison agrees: the matrix adds nothing out of sample beyond binary features and marginal means.

### Deployable rule and the secondary population

- **Deployable rule (net_V ≥ 1 and losses_V = 0, natural acceptance rate), P_near:** acceptance 0.0008 [0.0000, 0.0038] p-val=n/a (median 2 accepted pairs per split of 2,382; 1,000/1,000 splits and draws); HPR given accepted 0.0003 [0.0000, 0.0008] but **inconclusive (insufficient support)**: only 430/1,000 draws defined it. Between public systems, a strict "no validation loss" rule accepts almost nothing, so its safety cannot be estimated here.
- **P_pos (all ordered pairs with net_V ≥ 1; point estimates and split 5–95% ranges only, no bootstrap by protocol):** median 13,243 pairs per split, 0 degenerate splits. H1 HPR 0.0538 (0.0467 to 0.0609); share with losses_E ≥ 1 0.9820; mean losses_E/\|E\| 0.0449; mean Δpass1_E 0.1878. At q = 0.5: HPR R0 0.0541, R1 0.0491, R2 0.0493, R3 0.0481, R3h 0.0478, S0+ 0.0000 (0.0000 to 0.0002); C_fac0 0.0060 (−0.0011 to 0.0135), C_fac 0.0012 (−0.0026 to 0.0052), C_bin 0.0048 (−0.0017 to 0.0112). H2(a) 0.1106 (0.0207 to 0.1995). Deployable zero-loss rule: acceptance 0.0174 (0.0074 to 0.0312; median 215.5 accepted pairs per split), HPR given accepted 0.0000 (0.0000 to 0.0000). H2(c): M0 0.6353, M1 0.6225, M2 0.6298; ΔR²(M2 − M1) median +0.0081 (−0.0177 to 0.0264), share > 0 = 0.789 (median 3,291 fitting pairs). Large validation gains are rarely harmful, selecting the largest-gain half removes harm almost entirely, and in this larger population the matrix features do add a little out-of-sample predictive value.

### Cost

Wall clock 2 min 52.95 s (`runtime_s` 172.5) for 1,000 splits × 1,000 draws × 2 populations with 32 worker processes on skampere1 (user CPU 4,681 s, 3,048% CPU). Memory: GNU time's maximum resident set size 2.36 GB (the largest single process); the summed resident set of the 34 processes sampled at 13:03 PDT was 21 GB. Output 106 KB.

## Plain-English reading for Brando (what this means for AlphaHebe's promotion gate)

1. **The current gate is harmful often.** When a candidate beats the incumbent by a small margin on the promotion envelope (1–10 of 212 tasks), about one promotion in four (25.8% [24.1%, 28.2%]) lowers pass@1 on held-out tasks, and 99.9% of such promotions break at least one previously solved held-out task (7.5% of held-out tasks on average). The average promotion is still a small net gain (+2.45 points), so the gate is not useless, only noisy.
2. **Per-item information helps a little, and the factor matrix is not shown to beat plain per-item pass/fail.** At equal validation gain, ranking by the factor-regression mass (R3) cuts harmful promotions from 25.8% to 23.7% (C_fac0 = 0.0210 [0.0017, 0.0403], an 8% relative cut) without costing held-out gain, but the extra cut beyond binary per-item losses (C_fac = 0.0046 [−0.0027, 0.0117]) is not separated from zero, and neither is the binary gate's own cut (C_bin = 0.0163 [−0.0014, 0.0355]). Under the rules frozen before the data were read, that is **no recommendation**; a fixed-threshold candidate gate is not built from this.
3. **Demanding a larger gain beats screening on items.** At the same promotion budget, "promote only the larger validation gains" (S0+) has 17.2% harmful promotions versus 23.7% for R3 and 24.2% for R2, and it also keeps more held-out gain (+3.6 versus +2.5 points). The 20% relative-reduction target is met by S0+ over the per-item rules, not the other way round. If AlphaHebe needs a cheap safety change today, raise the promotion margin.
4. **"Hidden" factor regressions correlate with later losses, but not for the reason hoped.** The correlation is real (0.1265 [0.0840, 0.1675]) yet of the size produced by a synthetic null with no breakage mechanism, and the matrix features add no out-of-sample predictive value over binary features plus marginals (ΔR² median −0.0017). The factor matrix mostly sharpens the estimate of how good the candidate is, which pass/fail counts already carry.
5. **A strict monotone rule ("never promote a candidate that loses any validation item") is almost never satisfied** between public systems (2 of 2,382 pairs per split), so this replay cannot say how safe it would be; phase B on real AlphaHebe candidates is the only way to test it.
6. **Exploratory, not frozen:** the smooth aggregate ΔSCS_V at equal gain (R1) was both safer than R0 (C_agg = 0.0232 [0.0042, 0.0405]) and kept more gain (+0.0043 [0.0027, 0.0059]); it is reported for experiment 11's design, not as a finding of this experiment.

## Synthetic checks before the lock (no real data)

Data comes from `expt_v1/synthetic_e10.py`: 164 systems × 424 tasks, 20 splits × 100 draws.

- **Signal set:** systems differ in ability and in a propensity to break PASS_TO_PASS tests.
- **Null set:** no system-specific breakage.

| Check | Signal | Null | Consequence for the protocol |
|---|---:|---:|---|
| H2(a) partial Spearman (3 binary covariates) | 0.096 [0.059, 0.130] | 0.112 [0.056, 0.148] | Positive even under the null: factor values also sharpen the ability estimate, so H2 is descriptive, not a mechanism test |
| H2 with marginal factor means | 0.052 [0.008, 0.087] | 0.037 [0.007, 0.081] | Same caveat |
| Unstratified "fewest regressions" (S3) versus "largest gain" (S0+), HPR | 0.304 versus 0.260 | 0.305 versus 0.266 | Ranking by risk alone confounds gain size, so primary policies are stratified by validation net gain |
| Stratified R0 − R3 HPR (factor versus scalar at equal gain) | +0.015 [−0.008, +0.034] | +0.014 [−0.012, +0.036] | Small effects; intervals are wide at this size |

**Bootstrap coverage** (`coverage_check.json`): 400-system population, 100 samples of 60 systems, 200 tasks, 10 splits, 200 draws. The nominal 95% dyadic-bootstrap intervals covered the population value in 100% (H1 HPR), 100% (R0 − R2), 100% (R2 − R3), 99% (R0 − R3) and 99% (H2) of replications. The intervals are conservative in this simulation, partly because 60 of 400 systems are sampled without replacement. This is a sanity check, not a proof of calibration.

**Full-pipeline check (revision 3).** On the synthetic signal set, 40 splits × 1,000 draws with 8 worker processes (`signal_r3_40splits_1000draws.json`):

- **Cost:** 42.4 s wall time, 2.7 GB peak resident memory. The real run (1,000 splits) is estimated at about 18 minutes.
- **Matching:** matched rates R0 0.499 versus R3 0.499. Every family had full support (40/40 splits, 1,000/1,000 valid draws).
- **Undefined stays undefined:** the deployable zero-loss rule accepted no pair, so its conditional harmful promotion rate is reported as undefined, not 0.

## Deviations and open questions

- **10-14-2026, matched-test-lists sensitivity blocked by its own stop rule.** PROTOCOL.md declares that dropping the 4 drift tasks gives 164 × 420 and that any other shape stops the analysis. On the real cohort the drop gives 164 × 421 because `django__django-10097` (1 drift cell) lies outside the 424-task common cohort; within the cohort the drift is 65 cells in 3 tasks. The pinned code stopped before computing any statistic (exit 1, 1.4 s). Re-admitting the sensitivity requires changing `EXPECTED_SHAPE` in `analyze_e10.py` or the protocol's declared drop, which is a dated amendment or a new `expt_v2` with its own lock; it was not done in this round. The primary analysis never reads the drift list and is unaffected. The check that found the cause read only cohort membership flags, no outcome.
- **10-14-2026, worker count.** The run used 32 worker processes (the dispatch note suggested 16). Results do not depend on the worker count: splits are independent, every seed is per split or rebuilt identically in each process, and `settings.workers` is recorded in the output.
- **10-14-2026, scoring script.** `expt_v1/score_e10.py` (new, not pinned) only reads the output JSON and applies the frozen rules; it recomputes no statistic. Its `--tables` output is the source of the tables above.
- **10-09-2026, review worktree removal:** removing the GPT-6 reviewer's worktree with `--force` discarded its checkpoint file (`CKPT_codex-rl4cv-e10-e11-design-review.md`) and an edit it had made to that worktree's copy of this ledger. The review file itself had been copied first and is unchanged.
