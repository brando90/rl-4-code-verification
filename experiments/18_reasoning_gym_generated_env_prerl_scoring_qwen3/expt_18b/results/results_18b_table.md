Envs with outcomes: 16 (16 with both seeds). Mean gain +0.106; best env rg/leg_counting/L3.

Noise ceiling: seed-seed Spearman +0.488, 2-seed reliability +0.656, max forecast Spearman about +0.810.

| forecast | Spearman [95% CI] | Kendall [95% CI] | regret top-1 [CI] | regret top-3 | pick |
|---|---|---|---|---|---|
| rho_h | +0.476 [+0.04, +0.74] | +0.283 [-0.02, +0.56] | +0.382 [+0.00, +0.38] | +0.146 | rg/mini_sudoku/L2 |
| law_alpha | +0.368 [-0.23, +0.78] | +0.250 [-0.19, +0.62] | +0.040 [+0.00, +0.36] | +0.119 | rg/leg_counting/L2 |
| alpha | -0.391 [-0.72, +0.08] | -0.283 [-0.56, +0.02] | +0.452 [+0.19, +0.47] | +0.288 | rg/family_relationships/L0 |
| difficulty | -0.193 [-0.73, +0.41] | -0.159 [-0.62, +0.34] | +0.302 [+0.05, +0.48] | +0.281 | rg/simple_equations/L0 |
| smaller_model | -0.326 [-0.81, +0.32] | -0.217 [-0.64, +0.27] | +0.469 [+0.42, +0.53] | +0.469 | rg/letter_counting/L1 |
| random | -0.235 [-0.60, +0.25] | -0.133 [-0.43, +0.18] | +0.250 [+0.01, +0.50] | +0.248 | rg/family_relationships/L2 |
| rho_only | -0.268 [-0.70, +0.29] | -0.167 [-0.51, +0.21] | +0.469 [+0.19, +0.47] | +0.294 | rg/basic_arithmetic/L0 |
| H_only | +0.579 [+0.03, +0.89] | +0.450 [+0.04, +0.77] | +0.024 [+0.00, +0.47] | +0.156 | rg/simple_equations/L0 |
| pass_band | +0.156 [-0.42, +0.63] | +0.100 [-0.33, +0.48] | +0.469 [+0.00, +0.47] | +0.232 | rg/basic_arithmetic/L0 |

Random pick expected regret: top-1 +0.232, top-3 +0.210.

| env | seeds | gain | GSM8K gain | RG-5 gain | tag-rate change | in-env gain |
|---|---|---|---|---|---|---|
| rg/simple_equations/L0 | 2 | +0.313 | +0.159 | +0.344 | -0.098 | +0.295 |
| rg/mini_sudoku/L2 | 2 | -0.044 | -0.169 | -0.019 | -0.149 | +0.136 |
| rg/family_relationships/L0 | 2 | -0.115 | -0.286 | -0.080 | +0.033 | -0.217 |
| rg/basic_arithmetic/L0 | 2 | -0.132 | -0.551 | -0.048 | +0.035 | +0.385 |
| rg/family_relationships/L1 | 2 | +0.110 | -0.125 | +0.157 | +0.044 | +0.322 |
| rg/basic_arithmetic/L2 | 2 | +0.242 | +0.135 | +0.264 | -0.089 | +0.331 |
| rg/letter_counting/L3 | 2 | -0.196 | -0.594 | -0.116 | +0.048 | +0.111 |
| rg/leg_counting/L2 | 2 | +0.298 | +0.120 | +0.333 | +0.012 | +0.501 |
| rg/basic_arithmetic/L3 | 2 | +0.285 | +0.138 | +0.314 | +0.012 | +0.337 |
| rg/mini_sudoku/L0 | 2 | +0.277 | +0.035 | +0.325 | -0.032 | +0.665 |
| rg/leg_counting/L3 | 2 | +0.338 | +0.170 | +0.371 | -0.041 | +0.588 |
| rg/leg_counting/L1 | 2 | +0.288 | +0.144 | +0.317 | -0.057 | +0.826 |
| rg/word_sorting/L0 | 2 | -0.167 | -0.544 | -0.091 | -0.415 | +0.166 |
| rg/letter_counting/L1 | 2 | -0.132 | -0.577 | -0.042 | +0.046 | +0.088 |
| rg/mini_sudoku/L1 | 2 | +0.244 | +0.093 | +0.275 | +0.013 | +0.321 |
| rg/family_relationships/L2 | 2 | +0.088 | -0.213 | +0.148 | +0.047 | +0.170 |
