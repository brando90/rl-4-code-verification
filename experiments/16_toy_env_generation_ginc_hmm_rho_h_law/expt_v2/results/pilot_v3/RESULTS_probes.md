# Probe results: 16_toy_env_generation_ginc_hmm_rho_h_law Night 2

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v2/results/pilot_v3/RESULTS_probes.md>

**TLDR:** The original-law pooled coverage gate passes. Conditional entropy is a different quantity and is reported separately.

| Scale | Coordinate | Pearson [95% bootstrap interval] | Spearman | Kendall | Cells |
|---|---|---:|---:|---:|---:|
| pooled | H | 0.6731 [0.5826, 0.7244] p-val=n/a | 0.6635 | 0.4867 | 64 |
| pooled | conditional_entropy_nats | -0.7925 [-0.8148, -0.7601] p-val=n/a | -0.8457 | -0.6777 | 64 |
| n1 | H | 0.6927 [0.5973, 0.7593] p-val=n/a | 0.6971 | 0.5833 | 16 |
| n1 | conditional_entropy_nats | -0.7795 [-0.8185, -0.7261] p-val=n/a | -0.8529 | -0.7167 | 16 |
| n2 | H | 0.7707 [0.6523, 0.8363] p-val=n/a | 0.8471 | 0.6667 | 16 |
| n2 | conditional_entropy_nats | -0.8672 [-0.8928, -0.8269] p-val=n/a | -0.9382 | -0.8167 | 16 |
| n3 | H | 0.8080 [0.6905, 0.8678] p-val=n/a | 0.8765 | 0.7167 | 16 |
| n3 | conditional_entropy_nats | -0.8838 [-0.9055, -0.8506] p-val=n/a | -0.9471 | -0.8333 | 16 |
| n4 | H | 0.8408 [0.7348, 0.8909] p-val=n/a | 0.8206 | 0.6333 | 16 |
| n4 | conditional_entropy_nats | -0.9091 [-0.9267, -0.8780] p-val=n/a | -0.9618 | -0.8667 | 16 |

Intervals: 2,000 resamples of 512 prompt groups within each fixed environment, paired across scales, seed 1617. They cover probe-prompt noise conditional on these starting checkpoints and candidates; they exclude pretraining and environment-family uncertainty. Spearman and Kendall are descriptive point estimates. No null-hypothesis test is used for these diagnostics. The user-chosen gate is absolute pooled Pearson correlation below 0.85 for log usable signal density versus the original law’s effective coverage H. Entropy uses eight sampled continuations per prompt scored by exact forward probabilities; it is not the law’s H. See the prospective protocol clarification for the distinction.

| Scale | Environment | rho | H | Four-token entropy (nats) | Mixed-group share |
|---|---|---:|---:|---:|---:|
| n1 | e00 | 45602.0 | 0.7912 | 6.4682 | 0.9375 |
| n1 | e01 | 47690.3 | 0.8976 | 3.7593 | 0.9863 |
| n1 | e02 | 38613.5 | 0.8452 | 5.9423 | 0.9492 |
| n1 | e03 | 31943.2 | 0.7635 | 6.5361 | 0.8926 |
| n1 | e04 | 32836.9 | 0.7382 | 8.6703 | 0.8887 |
| n1 | e05 | 41451.6 | 0.8587 | 4.3759 | 0.9707 |
| n1 | e06 | 37462.5 | 0.8194 | 6.4837 | 0.9473 |
| n1 | e07 | 40924.1 | 0.8563 | 5.8128 | 0.9668 |
| n1 | e08 | 34288.7 | 0.8453 | 9.1313 | 0.9590 |
| n1 | e09 | 46787.8 | 0.8919 | 5.1346 | 0.9922 |
| n1 | e10 | 53139.8 | 0.8525 | 4.2277 | 0.9844 |
| n1 | e11 | 35478.9 | 0.7974 | 6.4890 | 0.9375 |
| n1 | m00 | 44154.6 | 0.8746 | 4.2250 | 0.9766 |
| n1 | m01 | 43073.4 | 0.8612 | 4.5595 | 0.9648 |
| n1 | m02 | 42140.4 | 0.8669 | 5.2944 | 0.9746 |
| n1 | m03 | 39716.4 | 0.8079 | 5.8689 | 0.9473 |
| n2 | e00 | 49019.9 | 0.7889 | 6.4682 | 0.9395 |
| n2 | e01 | 56108.7 | 0.8685 | 3.7593 | 0.9824 |
| n2 | e02 | 42633.1 | 0.8207 | 5.9423 | 0.9629 |
| n2 | e03 | 35561.7 | 0.7946 | 6.5361 | 0.9258 |
| n2 | e04 | 34824.9 | 0.7246 | 8.6703 | 0.8965 |
| n2 | e05 | 51361.1 | 0.8481 | 4.3759 | 0.9707 |
| n2 | e06 | 41490.8 | 0.7948 | 6.4837 | 0.9531 |
| n2 | e07 | 47646.7 | 0.8323 | 5.8128 | 0.9688 |
| n2 | e08 | 36891.4 | 0.8232 | 9.1313 | 0.9727 |
| n2 | e09 | 53353.4 | 0.8754 | 5.1346 | 0.9844 |
| n2 | e10 | 58101.1 | 0.8518 | 4.2277 | 0.9824 |
| n2 | e11 | 38042.3 | 0.8070 | 6.4890 | 0.9551 |
| n2 | m00 | 51138.7 | 0.8506 | 4.2250 | 0.9766 |
| n2 | m01 | 50968.7 | 0.8295 | 4.5595 | 0.9785 |
| n2 | m02 | 49887.5 | 0.8455 | 5.2944 | 0.9785 |
| n2 | m03 | 45628.1 | 0.8032 | 5.8689 | 0.9551 |
| n3 | e00 | 50018.3 | 0.7988 | 6.4682 | 0.9355 |
| n3 | e01 | 58484.8 | 0.8748 | 3.7593 | 0.9863 |
| n3 | e02 | 44987.3 | 0.8365 | 5.9423 | 0.9766 |
| n3 | e03 | 38478.3 | 0.8059 | 6.5361 | 0.9395 |
| n3 | e04 | 35352.4 | 0.7473 | 8.6703 | 0.9043 |
| n3 | e05 | 55437.4 | 0.8528 | 4.3759 | 0.9805 |
| n3 | e06 | 41390.6 | 0.7953 | 6.4837 | 0.9453 |
| n3 | e07 | 51199.8 | 0.8338 | 5.8128 | 0.9805 |
| n3 | e08 | 37065.8 | 0.8255 | 9.1313 | 0.9609 |
| n3 | e09 | 56134.9 | 0.8922 | 5.1346 | 0.9863 |
| n3 | e10 | 57734.9 | 0.8503 | 4.2277 | 0.9805 |
| n3 | e11 | 36900.1 | 0.7999 | 6.4890 | 0.9473 |
| n3 | m00 | 54142.5 | 0.8544 | 4.2250 | 0.9746 |
| n3 | m01 | 53139.8 | 0.8463 | 4.5595 | 0.9844 |
| n3 | m02 | 52119.7 | 0.8456 | 5.2944 | 0.9805 |
| n3 | m03 | 46569.8 | 0.8075 | 5.8689 | 0.9609 |
| n4 | e00 | 49796.0 | 0.8012 | 6.4682 | 0.9375 |
| n4 | e01 | 58532.7 | 0.8723 | 3.7593 | 0.9805 |
| n4 | e02 | 45261.9 | 0.8325 | 5.9423 | 0.9707 |
| n4 | e03 | 41115.9 | 0.8090 | 6.5361 | 0.9492 |
| n4 | e04 | 34637.5 | 0.7425 | 8.6703 | 0.8926 |
| n4 | e05 | 59321.8 | 0.8620 | 4.3759 | 0.9844 |
| n4 | e06 | 41142.1 | 0.7900 | 6.4837 | 0.9473 |
| n4 | e07 | 50275.5 | 0.8334 | 5.8128 | 0.9746 |
| n4 | e08 | 37828.7 | 0.8232 | 9.1313 | 0.9668 |
| n4 | e09 | 56488.0 | 0.8877 | 5.1346 | 0.9805 |
| n4 | e10 | 56854.2 | 0.8537 | 4.2277 | 0.9824 |
| n4 | e11 | 37868.0 | 0.8083 | 6.4890 | 0.9590 |
| n4 | m00 | 58489.1 | 0.8652 | 4.2250 | 0.9902 |
| n4 | m01 | 56902.2 | 0.8493 | 4.5595 | 0.9824 |
| n4 | m02 | 53488.6 | 0.8533 | 5.2944 | 0.9746 |
| n4 | m03 | 47764.4 | 0.7997 | 5.8689 | 0.9648 |

**TLDR-end:** [rl4cv: 16_toy_env_generation_ginc_hmm_rho_h_law] Probe measurements keep effective coverage and conditional entropy distinct; all 64 cells are preserved.
