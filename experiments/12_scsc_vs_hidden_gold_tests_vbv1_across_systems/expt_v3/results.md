# Experiment 12 v3: Factor Decomposition & Silent-Bug Escape Analysis on VeriBench V1

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v3/results.md>

**Status:** DONE (`10-16-2026`, `$0` API spend, zero model calls).

**TLDR:** Across all `3,210` primary, fully applicable, compiling VeriBench V1 (`VBV1`) cells (`11` systems $\times$ `896` tasks; `3,174` hidden-gold passes vs `36` silent semantic bugs from [`expt_v2`](../expt_v2/results.md)), **mechanical self-verification alone ($\text{IC}_{\text{tests}}, \text{IC}_{\text{proofs}}$) has chance-level discrimination (`P2` ROC AUC `0.4997 [0.3644, 0.5821]`)**: `36/36 (100.0%)` of compiling solutions that fail hidden gold reference tests pass 100% of their own self-generated unit tests (`IC_tests = 1.0`), and `33/36 (91.7%)` also pass 100% of their own self-generated proofs (`IC_proofs = 1.0`). Adding **Formal Specification Coverage (`FSC`)** raises `P2` ROC AUC by **`+0.2451 [+0.1049, +0.3596] p-val < 0.0005`** to **`0.7448 [0.5784, 0.8654]`** (`SCSCv-3`) and **`0.7792 [0.6387, 0.8867]`** with Leave-One-System-Out (`LOSO`) task `FSC` calibration, catching **`23/33 (69.7%)`** of silent semantic bugs that escaped mechanical self-verification (`6.10×` risk ratio, Fisher exact `p-val = 4.39e-07`).

---

## 1. Factor Ablation on Compiling VBV1 Cells (`P2` System-Stratified ROC AUC)

In [`expt_v2`](../expt_v2/results.md), `SCSCv-3` achieved `P1` system-level Spearman `0.8909 [0.7818, 0.9000]` across all `896` tasks (driven by compilation and `IC_tests` across non-compiling vs compiling cells) and `P2` cell-level ROC AUC `0.7448 [0.5768, 0.8659]` across the `3,210` compiling, fully applicable common-measured cells (`3,174` hidden-gold passes vs `36` hidden-gold failures). Here we decompose `P2` by factor using 2,000-draw paired task-cluster bootstrap (`seed = 20261016`, all `896` tasks in the resampling frame):

| Predictor on Compiling Primary Cells (`n = 3,210`, `36` silent bugs) | Passing Mean (`n = 3,174`) | Failing Mean (`n = 36`) | `P2` System-Stratified ROC AUC `[95% CI]` | $\Delta$ AUC vs Mechanical $\sqrt{\text{IC}_{\text{tests}} \cdot \text{IC}_{\text{proofs}}}$ `[95% CI]` | Bootstrap `p-val` |
|---|---:|---:|---:|---:|---:|
| **`IC_tests` only** (self-generated unit tests) | `0.9836` | `1.0000` | `0.4661 [0.3945, 0.5218]` | `-0.0336 [-0.1123, +0.0852]` | `0.51` |
| **`IC_proofs` only** (self-generated theorem compilation) | `0.9918` | `0.9755` | `0.5141 [0.3776, 0.5974]` | `+0.0145 [+0.0105, +0.0184]` | `< 0.0005` |
| **Mechanical only** $\sqrt{\text{IC}_{\text{tests}} \cdot \text{IC}_{\text{proofs}}}$ | `0.9876` | `0.9873` | `0.4997 [0.3644, 0.5821]` | baseline | `n/a` |
| **`FSC` only** (Formal Specification Coverage judge) | `0.9271` | `0.7861` | **`0.7484 [0.5868, 0.8657]`** | **`+0.2487 [+0.1126, +0.3617]`** | **`< 0.0005`** |
| **`SCSCv-3`** $(\text{IC}_{\text{tests}} \cdot \text{IC}_{\text{proofs}} \cdot \text{FSC})^{1/3}$ | `0.9519` | `0.9107` | **`0.7448 [0.5784, 0.8654]`** | **`+0.2451 [+0.1049, +0.3596]`** | **`< 0.0005`** |
| **`FSC` + Leave-One-System-Out (`LOSO`) Task `FSC`** | `0.8194` | `0.6928` | **`0.7792 [0.6387, 0.8867]`** | **`+0.2796 [+0.1569, +0.3853]`** | **`< 0.0005`** |

---

## 2. Silent-Bug Escape Rate Under Mechanical vs Specification-Guarded Promotion Gates

Why do mechanical self-checks fail to discriminate once code compiles? Because when a model implements a slightly wrong function, it writes unit tests and theorems that match its own implementation:
- **`36 / 36` (`100.0%`)** of compiling solutions that fail hidden gold reference tests have **`IC_tests = 1.0000`** (`36 / 3,158 = 1.14%` silent bug escape rate).
- **`33 / 36` (`91.7%`)** of compiling solutions that fail hidden gold reference tests have **both `IC_tests = 1.0000` and `IC_proofs = 1.0000`** (`33 / 3,116 = 1.06%` silent bug escape rate).

Restricting to the **`3,116` mechanically self-verified solutions (`IC_tests = 1.0` and `IC_proofs = 1.0`)**, the `FSC` factor separates silent semantic bugs from true reference implementations:

| Stratum Within `IC_tests = 1.0 ∧ IC_proofs = 1.0` (`n = 3,116`) | Cells in Stratum | Hidden-Gold Failures (Silent Bugs) | Silent-Bug Failure Rate | Share of Mechanically Unflagged Silent Bugs (`/33`) | Risk Ratio (`FSC < 1` vs `FSC = 1`) | Two-Sided Fisher Exact `p-val` |
|---|---:|---:|---:|---:|---:|---:|
| **`FSC < 1.0`** (judge flags spec gap) | `853` | **`23`** | **`2.70%`** (`23/853`) | **`69.7%`** (`23/33` caught) | **`6.10×`** (`OR = 6.24`) | **`4.39e-07`** |
| **`FSC = 1.0`** (`SCSCv-3 = 1.0` promoted) | `2,263` | **`10`** | **`0.44%`** (`10/2,263`) | **`30.3%`** (`10/33` escape) | reference (`1.00×`) | `n/a` |

---

## 3. Synthesis with Experiment 13: The Two Complementary Roles of SCSC Factors

Combining [`Expt 12 v2/v3`](results.md) with [`Expt 13 v2/v3`](../../13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v3/PROTOCOL.md) establishes why every factor of `SCSC` is necessary across the RL + evaluation lifecycle:
1. **Before compilation / strict verification succeeds (RL Training — Expt 13):** Direct binary `pass@1` (`strict`) suffers **100% GRPO gradient starvation** (`0/31` active groups, `grad_norm = 0.0` on `Qwen3-4B` `step_658`), whereas guarded mechanical + structural factors (`factored_reward`) activate **`14/31` (`45.16%`, `+45.16 pp`, `p-val = 0.000122`)** of GRPO groups on the exact same 256 rollouts.
2. **After compilation & mechanical self-checks succeed (Evaluation / Promotion Gating — Expt 12 v3):** Mechanical self-checks (`IC_tests = 1 ∧ IC_proofs = 1`) saturate (`AUC = 0.4997`, missing `33/36 = 91.7%` of silent bugs), whereas **`FSC`** increases discrimination to **`AUC = 0.7448` (`SCSCv-3`) / `0.7792` (`FSC + LOSO task FSC`)** and catches **`69.7%` (`23/33`)** of mechanically unflagged silent bugs (`6.10×` risk ratio, `p-val = 4.39e-07`).

**TLDR-end:** [rl4cv: Expt 12 v3 factor ablation] Completed the zero-call `Expt 12 v3` factor decomposition (`results.md`, `results/factor_ablation_v3.json`), showing mechanical self-verification (`IC_tests`, `IC_proofs`) has `0.4997` AUC on compiling cells (`33/36` silent bugs pass both), while `FSC` raises AUC to `0.7448` (`0.7792` with LOSO task calibration) and cuts silent-bug escapes by `6.10×` (`p-val = 4.39e-07`).
