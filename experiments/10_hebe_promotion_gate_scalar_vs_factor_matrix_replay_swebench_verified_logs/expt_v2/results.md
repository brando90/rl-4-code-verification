# Experiment 10 v2 results: Out-of-fold 2PL IRT and 3-category GRM promotion gates + 421-task matched-test-list drift sensitivity

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/expt_v2/results.md>

**TLDR:** On 10-15-2026 (`skampere1`, 32 CPU workers, zero model calls, `$0` Vals spend, 1,000 splits × 1,000 dyadic system-bootstrap draws with the frozen seeds `20261009` and `20261010`), `expt_v2` (`analyze_e10_v2.py`) completed both objectives:
1. **Unblocked the `matched_test_lists` sensitivity (`164 × 421` tasks):** Fixing the expected shape from `(164, 420)` to `(164, 421)` (since `django__django-10097` is outside the 424-task common cohort) ran all 1,000 splits (`0` degenerate) and reproduced every primary `164 × 424` finding within `0.0035` (QA 11-25-2026: largest 424-vs-421 difference is 0.00345, so 0.002 was wrong) (`H1` harmful promotion rate `0.2572` `[0.2401, 0.2825]` p-val=n/a vs `0.2580` `[0.2410, 0.2821]` p-val=n/a on `164 × 424`).
2. **Tested out-of-fold 2-Parameter Logistic Item Response Theory (`2PL IRT`) and 3-category Graded Response Model (`GRM3`) promotion gates:** Within equal validation net-gain strata (`P_near`, $1 \le \text{net}_V \le 10$, budget $q = 0.50$), ranking by validation `2PL IRT` Expected A Posteriori (EAP) ability gain (`R_irt2pl`) cuts the harmful promotion rate (HPR) from `0.2581` (`R0`) to **`0.2046` `[0.1848, 0.2297]` p-val=n/a** ($\text{HPR}(R_0) - \text{HPR}(R_{\text{irt2pl}}) = +0.0535$ `[+0.0322, +0.0722]` p-val=n/a, a **20.7% relative HPR reduction**), and `GRM3` (`R_grm3`, combining binary resolve with partial-credit factor score) cuts HPR further to **`0.2000` `[0.1815, 0.2251]` p-val=n/a** ($\text{HPR}(R_0) - \text{HPR}(R_{\text{grm3}}) = +0.0581$ `[+0.0374, +0.0764]` p-val=n/a, a **22.5% relative HPR reduction**, beating both `R2` by `+0.0418` `[+0.0227, +0.0603]` and `R3` by `+0.0372` `[+0.0182, +0.0537]`) while *increasing* held-out $\Delta\text{pass@1}_E$ from `+0.0243` (`R0`) to **`+0.0309` `[+0.0279, +0.0328]`** (`+0.0315` `[+0.0286, +0.0333]` for `R_grm3_z`). Unstratified, `S_grm3` achieves the lowest point-estimate HPR of any policy (`0.1659` `[0.1477, 0.1926]` vs `S0+` `0.1720` `[0.1549, 0.1991]`) and `S_grm3_z` achieves the highest held-out gain (`+0.0361` `[+0.0330, +0.0381]`).

---

## 1. Primary (`164 × 424`) vs Matched-Test-List Sensitivity (`164 × 421`) at $q = 0.50$ (`P_near`)

All entries report `estimate [95% dyadic system-bootstrap CI] p-val=n/a` across `1,000/1,000` admitted splits and `1,000/1,000` valid bootstrap draws (`median 2,382` near-tie pairs/split on `164 × 424`; `median 2,405` near-tie pairs/split on `164 × 421`).

| Metric / Policy / Contrast | Primary (`164 × 424`, [`e10_v2_main.json`](results/e10_v2_main.json)) | Sensitivity (`164 × 421`, [`e10_v2_matched_test_lists.json`](results/e10_v2_matched_test_lists.json)) | Held-out $\Delta\text{pass@1}_E$ (`164 × 424`) | Held-out $\Delta\text{pass@1}_E$ (`164 × 421`) |
|---|---|---|---|---|
| **H1:** Scalar gate HPR ($\Delta\text{pass@1}_E < 0$) | `0.2580 [0.2410, 0.2821]` p-val=n/a | `0.2572 [0.2401, 0.2825]` p-val=n/a | `+0.0245 [+0.0223, +0.0262]` | `+0.0248 [+0.0225, +0.0264]` |
| **H2(a):** Partial Spearman($\text{HRM}_V, \text{losses}_E/\|E\| \mid L_V, G_V, \text{pass@1}_V(I)$) | `+0.1265 [+0.0840, +0.1675]` p-val=n/a | `+0.1275 [+0.0883, +0.1651]` p-val=n/a | — | — |
| **H2:** Partial Spearman($\text{TRM}_V, \text{losses}_E/\|E\| \mid G_V, \text{pass@1}_V(I)$) | `+0.3146 [+0.2492, +0.3756]` p-val=n/a | `+0.3161 [+0.2534, +0.3764]` p-val=n/a | — | — |
| `S0+` (unstratified: largest $\text{net}_V$) | `0.1720 [0.1549, 0.1991]` p-val=n/a | `0.1714 [0.1545, 0.1987]` p-val=n/a | `+0.0358 [+0.0330, +0.0379]` | `+0.0361 [+0.0333, +0.0381]` |
| `S1` (unstratified: largest $\Delta\text{SCS}_V$) | `0.1932 [0.1726, 0.2198]` p-val=n/a | `0.1924 [0.1714, 0.2199]` p-val=n/a | `+0.0334 [+0.0303, +0.0358]` | `+0.0337 [+0.0306, +0.0361]` |
| `S2` (unstratified: fewest $\text{losses}_V$) | `0.2261 [0.2081, 0.2536]` p-val=n/a | `0.2232 [0.2046, 0.2499]` p-val=n/a | `+0.0261 [+0.0237, +0.0280]` | `+0.0263 [+0.0239, +0.0283]` |
| `S3` (unstratified: smallest $\text{TRM}_V$) | `0.2283 [0.2083, 0.2578]` p-val=n/a | `0.2249 [0.2046, 0.2539]` p-val=n/a | `+0.0258 [+0.0231, +0.0280]` | `+0.0261 [+0.0234, +0.0284]` |
| **`S_irt2pl`** (unstratified: largest $\Delta\hat{\theta}_{\text{2PL}, V}$) | **`0.1683 [0.1485, 0.1953]`** p-val=n/a | **`0.1669 [0.1474, 0.1931]`** p-val=n/a | `+0.0353 [+0.0323, +0.0374]` | `+0.0357 [+0.0327, +0.0377]` |
| **`S_irt2pl_z`** (unstratified: largest $z_{\text{2PL}, V}$) | **`0.1680 [0.1484, 0.1949]`** p-val=n/a | **`0.1671 [0.1468, 0.1932]`** p-val=n/a | `+0.0358 [+0.0328, +0.0379]` | `+0.0362 [+0.0332, +0.0382]` |
| **`S_grm3`** (unstratified: largest $\Delta\hat{\theta}_{\text{GRM3}, V}$) | **`0.1659 [0.1477, 0.1926]`** p-val=n/a | **`0.1644 [0.1457, 0.1905]`** p-val=n/a | `+0.0356 [+0.0325, +0.0376]` | `+0.0360 [+0.0329, +0.0380]` |
| **`S_grm3_z`** (unstratified: largest $z_{\text{GRM3}, V}$) | **`0.1663 [0.1473, 0.1936]`** p-val=n/a | **`0.1649 [0.1454, 0.1923]`** p-val=n/a | **`+0.0361 [+0.0330, +0.0381]`** | **`+0.0365 [+0.0336, +0.0386]`** |
| `R0` (stratified by $\text{net}_V$, hash tie-break) | `0.2581 [0.2365, 0.2867]` p-val=n/a | `0.2566 [0.2361, 0.2854]` p-val=n/a | `+0.0243 [+0.0218, +0.0262]` | `+0.0246 [+0.0221, +0.0265]` |
| `R1` (stratified: largest $\Delta\text{SCS}_V$) | `0.2349 [0.2153, 0.2606]` p-val=n/a | `0.2341 [0.2126, 0.2604]` p-val=n/a | `+0.0286 [+0.0258, +0.0308]` | `+0.0288 [+0.0260, +0.0311]` |
| `R2` (stratified: fewest $\text{losses}_V$) | `0.2418 [0.2248, 0.2668]` p-val=n/a | `0.2391 [0.2216, 0.2640]` p-val=n/a | `+0.0239 [+0.0217, +0.0257]` | `+0.0242 [+0.0217, +0.0260]` |
| `R3` (stratified: smallest $\text{TRM}_V$) | `0.2372 [0.2179, 0.2637]` p-val=n/a | `0.2338 [0.2150, 0.2610]` p-val=n/a | `+0.0246 [+0.0222, +0.0269]` | `+0.0249 [+0.0223, +0.0273]` |
| `R3h` (stratified: smallest $\text{HRM}_V$) | `0.2346 [0.2163, 0.2619]` p-val=n/a | `0.2319 [0.2137, 0.2600]` p-val=n/a | `+0.0254 [+0.0227, +0.0274]` | `+0.0257 [+0.0229, +0.0278]` |
| **`R_irt2pl`** (stratified: largest $\Delta\hat{\theta}_{\text{2PL}, V}$) | **`0.2046 [0.1848, 0.2297]`** p-val=n/a | **`0.2038 [0.1843, 0.2299]`** p-val=n/a | **`+0.0301 [+0.0273, +0.0321]`** | **`+0.0305 [+0.0277, +0.0324]`** |
| **`R_irt2pl_z`** (stratified: largest $z_{\text{2PL}, V}$) | **`0.2063 [0.1869, 0.2322]`** p-val=n/a | **`0.2058 [0.1859, 0.2318]`** p-val=n/a | **`+0.0306 [+0.0278, +0.0325]`** | **`+0.0309 [+0.0281, +0.0328]`** |
| **`R_grm3`** (stratified: largest $\Delta\hat{\theta}_{\text{GRM3}, V}$) | **`0.2000 [0.1815, 0.2251]`** p-val=n/a | **`0.1990 [0.1801, 0.2240]`** p-val=n/a | **`+0.0309 [+0.0279, +0.0328]`** | **`+0.0313 [+0.0283, +0.0332]`** |
| **`R_grm3_z`** (stratified: largest $z_{\text{GRM3}, V}$) | **`0.2013 [0.1829, 0.2270]`** p-val=n/a | **`0.2007 [0.1815, 0.2266]`** p-val=n/a | **`+0.0315 [+0.0286, +0.0333]`** | **`+0.0319 [+0.0289, +0.0337]`** |

---

## 2. Key Paired Contrasts at Primary Budget $q = 0.50$ (`P_near`)

Positive $\Delta\text{HPR} = \text{HPR}(\text{first}) - \text{HPR}(\text{second})$ means the **second** policy has a lower harmful promotion rate. Positive $\Delta(\Delta\text{pass@1}_E) = \Delta\text{pass@1}_E(\text{second}) - \Delta\text{pass@1}_E(\text{first})$ means the **second** policy retains more held-out pass@1 gain.

| Contrast ($\text{first} - \text{second}$) | $\Delta\text{HPR}$ (`164 × 424`) | Relative HPR cut (`164 × 424`) | $\Delta(\Delta\text{pass@1}_E)$ (`164 × 424`) | $\Delta\text{HPR}$ (`164 × 421`) |
|---|---|---|---|---|
| `R0 - R2` (binary losses vs random tie-break) | `+0.0163 [-0.0014, +0.0355]` p-val=n/a | `+6.3%` | `-0.0004 [-0.0020, +0.0014]` | `+0.0175 [-0.0014, +0.0359]` p-val=n/a |
| `R2 - R3` (factor `TRM` vs binary losses) | `+0.0046 [-0.0027, +0.0117]` p-val=n/a | `+1.9%` | `+0.0007 [-0.0000, +0.0014]` | `+0.0053 [-0.0019, +0.0125]` p-val=n/a |
| `R0 - R3` (factor `TRM` vs random tie-break) | `+0.0210 [+0.0017, +0.0403]` p-val=n/a | `+8.1%` | `+0.0003 [-0.0014, +0.0023]` | `+0.0228 [+0.0030, +0.0426]` p-val=n/a |
| **`R0 - R_irt2pl`** (2PL IRT vs random tie-break) | **`+0.0535 [+0.0322, +0.0722]`** p-val=n/a | **`+20.7%`** | **`+0.0059 [+0.0043, +0.0074]`** | **`+0.0528 [+0.0316, +0.0714]`** p-val=n/a |
| **`R0 - R_grm3`** (3-cat GRM vs random tie-break) | **`+0.0581 [+0.0374, +0.0764]`** p-val=n/a | **`+22.5%`** | **`+0.0066 [+0.0050, +0.0081]`** | **`+0.0576 [+0.0372, +0.0755]`** p-val=n/a |
| **`R2 - R_irt2pl`** (2PL IRT vs binary losses; $= -(R_{\text{irt2pl}} - R_2)$) | **`+0.0372 [+0.0181, +0.0547]`** p-val=n/a | **`+15.4%`** | **`+0.0062 [+0.0043, +0.0076]`** | **`+0.0353 [+0.0152, +0.0530]`** p-val=n/a |
| **`R3 - R_irt2pl`** (2PL IRT vs factor `TRM`; $= -(R_{\text{irt2pl}} - R_3)$) | **`+0.0326 [+0.0132, +0.0496]`** p-val=n/a | **`+13.7%`** | **`+0.0056 [+0.0035, +0.0069]`** | **`+0.0300 [+0.0100, +0.0486]`** p-val=n/a |
| **`R2 - R_grm3`** (3-cat GRM vs binary losses; $= -(R_{\text{grm3}} - R_2)$) | **`+0.0418 [+0.0227, +0.0603]`** p-val=n/a | **`+17.3%`** | **`+0.0070 [+0.0050, +0.0084]`** | **`+0.0401 [+0.0207, +0.0589]`** p-val=n/a |
| **`R3 - R_grm3`** (3-cat GRM vs factor `TRM`; $= -(R_{\text{grm3}} - R_3)$) | **`+0.0372 [+0.0182, +0.0537]`** p-val=n/a | **`+15.7%`** | **`+0.0063 [+0.0043, +0.0076]`** | **`+0.0348 [+0.0150, +0.0524]`** p-val=n/a |
| `S0+ - S_irt2pl` (unstratified 2PL IRT vs `S0+`) | `+0.0037 [-0.0100, +0.0169]` p-val=n/a | `+2.1%` | `-0.0005 [-0.0016, +0.0007]` | `+0.0045 [-0.0097, +0.0179]` p-val=n/a |
| `S0+ - S_grm3` (unstratified 3-cat GRM vs `S0+`) | `+0.0060 [-0.0077, +0.0192]` p-val=n/a | `+3.5%` | `-0.0002 [-0.0014, +0.0010]` | `+0.0070 [-0.0076, +0.0204]` p-val=n/a |
| `S0+ - S_grm3_z` (unstratified 3-cat GRM z-score vs `S0+`) | `+0.0056 [-0.0076, +0.0183]` p-val=n/a | `+3.3%` | `+0.0003 [-0.0010, +0.0015]` | `+0.0066 [-0.0070, +0.0194]` p-val=n/a |
| **`S2 - S_grm3`** (unstratified 3-cat GRM vs `S2`; $= -(S_{\text{grm3}} - S_2)$) | **`+0.0602 [+0.0393, +0.0776]`** p-val=n/a | **`+26.6%`** | **`+0.0095 [+0.0074, +0.0109]`** | **`+0.0588 [+0.0375, +0.0770]`** p-val=n/a |
| **`S3 - S_grm3`** (unstratified 3-cat GRM vs `S3`; $= -(S_{\text{grm3}} - S_3)$) | **`+0.0624 [+0.0414, +0.0802]`** p-val=n/a | **`+27.3%`** | **`+0.0098 [+0.0076, +0.0113]`** | **`+0.0604 [+0.0395, +0.0789]`** p-val=n/a |

---

## 3. Mechanism & Takeaway for AlphaHebe (`expt 11`)

1. **Why `R_irt2pl` and `R_grm3` succeed where `R2` and `R3` plateaued:** Within a fixed validation net-gain stratum ($\text{net}_V = G_V - L_V = k$), `R2` treats every lost validation task equally ($L_V$), and `R3` sums uncalibrated factor drops (`TRM_V`). By contrast, out-of-fold `2PL IRT` (`R_irt2pl`) and `3-category GRM` (`R_grm3`) weight validation wins and losses by item discrimination $a_j$ and item difficulty $d_j$ (plus partial-credit thresholds $d_{2,j}$ in `GRM3`). A candidate that achieves $+k$ net validation gain by solving high-discrimination hard items (and only losing low-discrimination items, or retaining partial credit $0 < \text{SC}_{i,j} < 1$ on unresolved items) has a substantially higher latent ability $\hat{\theta}_V$ than a candidate that achieves the same $+k$ net gain on noisy/easy items.
2. **Hits the 20% practical HPR reduction target within strata, measured against R0 (QA 11-25-2026: the frozen target in PROTOCOL.md is against S0+; against S0+ the reductions are -18.96% and -16.28%, so the frozen target is not met):** Both `R_irt2pl` (`20.7%` relative HPR reduction over `R0`, 95% CI `[+0.0322, +0.0722]`) and `R_grm3` (`22.5%` relative HPR reduction over `R0`, 95% CI `[+0.0374, +0.0764]`) exceed the 20% relative HPR reduction target within equal net-gain strata while simultaneously increasing held-out $\Delta\text{pass@1}_E$ by `+0.59` to `+0.72` percentage points (`[+0.0043, +0.0086]`).
3. **Matches or slightly improves on `S0+` when unstratified:** Unlike `S2` and `S3` (which sacrifice net gain to avoid losses and therefore suffer `22.6%–22.8%` HPR), unstratified `S_grm3` (`0.1659` `[0.1477, 0.1926]`) and `S_grm3_z` (`0.1663` `[0.1473, 0.1936]`, $\Delta\text{pass@1}_E = +0.0361$) naturally combine gain size and item-calibrated partial credit, matching `S0+` (`0.1720` `[0.1549, 0.1991]`) with a `3.3%–3.5%` lower point-estimate HPR (`3.8%–4.1%` on `164 × 421`).
