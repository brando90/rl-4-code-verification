# Amendment — experiment 14 stop rule, numpy pin (11-27-2026)

**Doc link:** https://github.com/brando90/rl-4-code-verification/blob/main/experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/AMENDMENT_stop_rule_numpy_pin_11-27-2026.md

**TLDR:** A rerun of the locked experiment 14 analyzer uses numpy 2.2.6 and scipy 1.16.3, the versions that produced the published H2 replay. `PROTOCOL.md` and `analyze_e14.py` are unchanged. On any other numpy, the replay comparison uses an absolute tolerance of 5e-6 on `delta_median` and exact equality on `positive_splits`.

**Status:** adopted 11-27-2026 as a dated amendment. It does not edit the locked protocol. The 10-12-2026 run stays the published result.

## What the QA found

`docs/qa_11-26-2026/reports/QA_NUMBERS_opus55.md` and `docs/NEXT_STEPS_11-26-2026.md` §3.1: `reproduce_e07_h2` compares the experiment 07 H2 replay with exact `==`. On numpy 2.5.3 the n_A = 50 median was −0.012140 against the published −0.012139. The split count 92 of 2,000 was identical. The locked run recorded numpy 2.2.6 and scipy 1.16.3 (`results.md`, `reviews/light_qa_codex_gpt6_astra_ultra_10-12-2026.md`).

The published n_A = 50 pair in `expt_v1/results/results_tables_e14.md` is:

- `delta_median` = −0.012138953190928725
- `positive_splits` = 92

## Rule for a rerun

1. Install `expt_v1/requirements-locked-rerun-11-27-2026.txt` (`numpy==2.2.6`, `scipy==1.16.3`) and run `analyze_e14.py` as the protocol states. Exact equality remains the stop rule on that pin.
2. If that pin cannot be installed, do not run `analyze_e14.py` on the newer numpy. Use `expt_v1/stop_rule_amendment_11-27-2026.py` instead. A median passes when the absolute difference from the published value is at most 5e-6. `positive_splits` stays exact. The same rule applies at n_A of 25, 100 and 250.
3. 5e-6 is wider than the sixth-decimal drift named in the QA note (about 1.2e-6 at n_A = 50) and tighter than 1e-4, so a real median change still stops the rerun.
4. This amendment does not change the published tables, the frozen forecast, or the locked protocol's validity section.

**TLDR-end:** [rl4cv: e14 numpy pin] Reruns pin numpy 2.2.6 and scipy 1.16.3; any other numpy uses a 5e-6 median tolerance and exact split counts, in a new file, leaving the locked analyzer as it is.
