Envs with outcomes: 16 (16 with both seeds). Mean gain +0.123; best env rg/leg_counting/L3.

Noise ceiling: seed-seed Spearman +0.388, 2-seed reliability +0.559, max forecast Spearman about +0.748.

| forecast | Spearman [95% CI] | Kendall [95% CI] | regret top-1 [CI] | regret top-3 | pick |
|---|---|---|---|---|---|
| rho_h | +0.482 [-0.04, +0.80] | +0.333 [-0.05, +0.66] | +0.209 [+0.00, +0.21] | +0.089 | rg/mini_sudoku/L2 |
| law_alpha | +0.100 [-0.41, +0.61] | +0.100 [-0.27, +0.49] | +0.081 [+0.00, +0.19] | +0.084 | rg/leg_counting/L2 |
| alpha | -0.494 [-0.80, -0.02] | -0.367 [-0.67, -0.04] | +0.183 [+0.15, +0.51] | +0.337 | rg/family_relationships/L0 |
| difficulty | -0.143 [-0.68, +0.48] | -0.103 [-0.54, +0.40] | +0.185 [+0.06, +0.33] | +0.172 | rg/simple_equations/L0 |
| smaller_model | -0.015 [-0.52, +0.53] | +0.000 [-0.41, +0.42] | +0.319 [+0.02, +0.47] | +0.265 | rg/letter_counting/L1 |
| random | -0.126 [-0.63, +0.47] | -0.050 [-0.47, +0.39] | +0.506 [+0.00, +0.51] | +0.315 | rg/family_relationships/L2 |
| rho_only | -0.250 [-0.74, +0.33] | -0.183 [-0.59, +0.24] | +0.040 [+0.00, +0.51] | +0.290 | rg/basic_arithmetic/L0 |
| H_only | +0.544 [+0.09, +0.83] | +0.367 [+0.05, +0.66] | +0.081 [+0.02, +0.08] | +0.055 | rg/simple_equations/L0 |
| pass_band | +0.147 [-0.37, +0.67] | +0.150 [-0.25, +0.56] | +0.040 [+0.00, +0.51] | +0.196 | rg/basic_arithmetic/L0 |

Random pick expected regret: top-1 +0.197, top-3 +0.184.

| env | seeds | gain | GSM8K gain | RG-5 gain | tag-rate change | in-env gain |
|---|---|---|---|---|---|---|
| rg/simple_equations/L0 | 3 | +0.239 | +0.107 | +0.265 | -0.004 | +0.182 |
| rg/mini_sudoku/L2 | 3 | +0.112 | -0.123 | +0.158 | -0.151 | -0.055 |
| rg/family_relationships/L0 | 3 | +0.137 | -0.097 | +0.184 | +0.001 | +0.285 |
| rg/basic_arithmetic/L0 | 3 | +0.280 | +0.097 | +0.316 | +0.046 | +0.436 |
| rg/family_relationships/L1 | 3 | -0.042 | -0.354 | +0.021 | +0.053 | +0.484 |
| rg/basic_arithmetic/L2 | 3 | +0.305 | +0.127 | +0.340 | +0.039 | +0.589 |
| rg/letter_counting/L3 | 3 | -0.154 | -0.587 | -0.067 | +0.053 | +0.122 |
| rg/leg_counting/L2 | 3 | +0.239 | +0.068 | +0.273 | +0.020 | +0.454 |
| rg/basic_arithmetic/L3 | 3 | +0.297 | +0.144 | +0.327 | +0.005 | +0.253 |
| rg/mini_sudoku/L0 | 3 | +0.154 | -0.189 | +0.223 | -0.140 | +0.606 |
| rg/leg_counting/L3 | 3 | +0.320 | +0.156 | +0.353 | -0.020 | +0.562 |
| rg/leg_counting/L1 | 3 | +0.283 | +0.118 | +0.316 | +0.014 | +0.812 |
| rg/word_sorting/L0 | 3 | -0.134 | -0.424 | -0.076 | -0.400 | -0.015 |
| rg/letter_counting/L1 | 3 | +0.002 | -0.376 | +0.077 | +0.037 | +0.199 |
| rg/mini_sudoku/L1 | 3 | +0.118 | -0.079 | +0.158 | +0.002 | +0.413 |
| rg/family_relationships/L2 | 3 | -0.186 | -0.590 | -0.105 | +0.053 | +0.185 |

## Token-confound check

- Spearman of mean response length per rollout vs 3-seed gain: +0.476 [-0.07259798580155191, 0.8260869565217391] (18b: +0.606); total tokens vs gain +0.685.
- Run classes: {'matched': 48, 'overshoot': 0, 'budget_limited': 0}; realised tokens per run min 2000111, mean 2040443.1458333333, max 2170979.
- 3-seed reliability +0.663 (mean pairwise seed Spearman +0.396); max forecast Spearman about +0.814.
- Cross-check with 18b: {'n_envs': 16, 'spearman_18c_vs_18b_env_gain': 0.6588235294117648, 'mean_gain_18c': 0.1230892605251736, 'mean_gain_18b': 0.10615285237630209}
- Fully matched subset: {"n_envs": 16, "forecasts": {"rho_h": {"spearman": 0.4823529411764706, "spearman_ci95": [-0.0016023088729230088, 0.8065718984962404], "regret_top1": 0.2086859809027778, "pick": "rg/mini_sudoku/L2"}, "law_alpha": {"spearman": 0.09999999999999999, "spearman_ci95": [-0.3917111398674729, 0.6115614242685019], "regret_top1": 0.081298828125, "pick": "rg/leg_counting/L2"}, "alpha": {"spearman": -0.4941176470588235, "spearman_ci95": [-0.7982789759078706, -0.016454835645240643], "regret_top1": 0.18307834201388892, "pick": "rg/family_relationships/L0"}, "difficulty": {"spearman": -0.14293705813999089, "spearman_ci95": [-0.680015120054091, 0.5024592485663071], "regret_top1": 0.18508029513888893, "pick": "rg/simple_equations/L0"}, "smaller_model": {"spearman": -0.014705882352941175, "spearman_ci95": [-0.5322638457888441, 0.5099376238236736], "regret_top1": 0.31857638888888895, "pick": "rg/letter_counting/L1"}, "random": {"spearman": -0.1264705882352941, "spearman_ci95": [-0.6358369426397912, 0.5030670906707291], "regret_top1": 0.5057237413194444, "pick": "rg/family_relationships/L2"}, "rho_only": {"spearman": -0.25, "spearman_ci95": [-0.738095238095238, 0.30442569759896126], "regret_top1": 0.040364583333333426, "pick": "rg/basic_arithmetic/L0"}, "H_only": {"spearman": 0.5441176470588236, "spearman_ci95": [0.09494292171421707, 0.8370570570570568], "regret_top1": 0.0813530815972223, "pick": "rg/simple_equations/L0"}, "pass_band": {"spearman": 0.14705882352941177, "spearman_ci95": [-0.347272
