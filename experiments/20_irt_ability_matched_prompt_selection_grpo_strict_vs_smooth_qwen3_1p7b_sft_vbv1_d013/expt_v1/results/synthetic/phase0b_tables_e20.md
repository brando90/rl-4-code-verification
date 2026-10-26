# Experiment 20 Phase 0b tables

Generated 10-21-2026 12:38 PDT; synthetic=True

| Model | AUC (active 1-7 of 8) | log loss | ECE | predicted active share | observed active share |
|---|---|---|---|---|---|
| random_intercept | 0.741 | 0.4983 | 0.112 | 0.733 | 0.798 |
| explanatory | 0.730 | 0.5153 | 0.132 | 0.700 | 0.798 |
| features_only | 0.680 | 0.4888 | 0.068 | 0.762 | 0.798 |
| baseline | 0.505 | 0.5227 | 0.071 | 0.868 | 0.798 |
| panel_strict_rate | 0.262 | nan | nan | nan | nan |

Selected model: **random_intercept**; gate G0 PASS: AUC 0.741 [0.697, 0.785] (threshold 0.70, experiment 13 F2; 9/300 draws below 0.70); log loss 0.4983 vs Beta(1,1) baseline 0.5227, gain -0.0333..0.0843 p-val=0.4267; AUC minus panel strict rate [0.399, 0.566] p-val=0.003333.

Priors (R0): {"random_intercept": {"slope_sd": 0.25, "sigma_e": 0.5}, "explanatory": {"slope_sd": 0.25, "sigma_e": 0.5}}; start policy θ̂₀ = 5.651 (SD 0.040); strict pass@1 0.7762 over 4312 measured cells; active tasks 430/539.
