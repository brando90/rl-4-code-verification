# Night 2: four-token GINC hidden Markov model environment generation

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v2/PROTOCOL.md>

**TLDR:** Test whether Equation 7 selects positive held-out transfer after four-token rollouts and exact per-token Kullback–Leibler (KL) regularization. Freeze all design choices before reinforcement-learning outcomes; a failed decorrelation gate stops the sweep and is reported as such.

Frozen design written 10-15-2026 20:23 PDT, before pretraining/probes/outcomes.

## Definition and scope

- The existing Equation 7 is additive in standardized log usable signal density rho and effective coverage H, with budget interactions. It is not a rho-times-entropy product. Preserve `rl4cv.experience` and `rl4cv.utility_model` unchanged.
- H is normalized effective sample size of advantage mass, not conditional entropy. Also estimate four-token conditional entropy in nats with eight continuations per prompt and exact forward probabilities. This Monte Carlo diagnostic is labeled as an estimate, not exact enumeration.
- Each response has four emission tokens. Labels are sequential Bayes argmax continuations under the generating concept; these are not necessarily the globally most likely four-token string. Token partial-credit reward is the fraction matching these four fixed labels. Joint exact match is the primary target metric; token accuracy is secondary. Exact forward conditional probabilities and joint likelihoods verify the oracle independently.
- The latent concept is available to the verifier only, matching Night 1. Prefixes can be ambiguous; this is an oracle-agreement task, not predicting one realized stochastic future.

## Frozen design

- CPU only, nice 10, one PyTorch thread per process, at most eight concurrent compute processes; zero hosted inference calls and $0 spend.
- Four original transformer scales n1/n2/n3/n4; 2,000/2,500/3,000/4,000 next-token pretraining steps, batch 64, cosine learning rate 0.003, original 200,000 length-32 documents, seed 7. Initialization seed 1234; pretraining sample seed 0. No target data in pretraining.
- Twelve original base settings renamed in list order to e00–e11 (Night 1 e01→e00, …, e12→e11). Four mixtures m00–m03 generated using only n3 starting-policy base probes: rank log rho minus twice distance from median H; mix top 3/5/8/12 settings with softmax weights, broad 64-concept banks and prefix lengths 12/16/24/8. Freeze the resulting mixture manifest before full probes.
- Probe 512 prompts (seed 11), eight samples each (seed 5), four tokens, all admitted. Probe each of 16 environments at all four scales.
- Pre-training gate: before any Group Relative Policy Optimization (GRPO), require absolute Pearson correlation below 0.85 for log rho versus coverage H AND versus estimated conditional entropy, pooled and separately at each scale. This conservative interpretation checks both meanings of H in the dispatch. Record every coefficient. Do not change rewards, candidate membership or measurement to force this gate to pass; a failed gate is a scientific blocker with all 384 outcomes marked unattempted.
- GRPO: 16 prompts × 8 responses × 4 tokens per step, Adam learning rate 0.0001, 100 steps, KL coefficient exactly 1.0 to the frozen starting policy. Full-vocabulary forward KL averaged over all four visited autoregressive positions; prefix distribution is sampled on-policy. Policy-gradient term uses summed response log probability and leave-one-out reward advantages. KL is exact at sampled prefixes, not an enumeration over all possible prefixes.
- Record budgets at 25/50/100 steps = 12,800/25,600/51,200 generated tokens. Seeds 0 and 1 are two independent training trajectories per environment, with three correlated budget observations each. Total 128 trajectories / 384 budget cells.
- Training prompt pools: 20,000, seed 13. In-environment diagnostic: 512, seed 12. Primary target: fixed 4,000 prompts, seed 99, nine pretraining settings mixed, prefix length 10. Targets never train or choose hyperparameters. One starting checkpoint per scale; uncertainty does not cover pretraining variation.
- Train n1–n3 first; fit Equation 7 and rho-only/H-only/budget-scale-only ablations to their joint utilities. Freeze n4 forecasts with `freeze_forecast` before n4 reinforcement learning. Baselines: uniform random expected utility; best fixed environment at n3 averaged across budgets; largest n4 pass variance; largest n4 mixed-group share; rho-only; H-only. Resolve exact ties by averaging all tied candidates.
- No outcome-based reruns, dropped cells, extra seeds or modified budgets. Resume completed immutable stages. Infrastructure interruption requires a separate logged recovery attempt retaining initial failure evidence.

## Analysis and verdict

- Primary decision: largest budget n4 joint accuracy gain. Also report all three budgets, regression root mean squared error, pairwise rank accuracy, regret, and mixture/base choices.
- Positive-transfer prevalence must reach 30% of 384 budget cells; report separately across the 128 final-budget trajectories. This is a user acceptance target, not a guaranteed finding.
- Report bootstrap 95% confidence intervals from existing paired target prompts and training-seed resampling, with fixed selected policies and conditional on the frozen pretraining checkpoints. Two seeds cannot establish reliable population training uncertainty; paired seed sign-flip tests have coarse resolution and are labeled. Report model-fit uncertainty separately from conditional target-prompt uncertainty.
- MEANINGFUL POSITIVE TRANSFER requires the gate, prevalence ≥30%, strictly positive law-selected n4 joint utility with its interval excluding zero, and positive paired advantage over every named baseline. TIE WITH BASELINES means positive selected utility but no clear advantage over the strongest baseline. Otherwise NO ADVANTAGE. If the gate fails, report NO ADVANTAGE — prerequisite failed, law outcome unmeasured; do not imply a completed law test.
- Scientific negative results count as completed investigation of the blocking prerequisite, never as a completed 384-cell sweep. A run-done status must distinguish partial execution from success.

## Metric clarification before reinforcement learning (10-15-2026 20:29 PDT)

The initial conservative gate above added requirements beyond the dispatch's Night 1 comparison. Inspection of `expt_v1/run_pilot.py`, `src/rl4cv/experience.py` and the archived 0.995 result establishes that the cited H is effective coverage, not conditional entropy. The operative gate therefore compares **pooled log rho versus the original coverage H over the 64 scale/environment cells**, matching the original pooled 48-cell diagnostic; per-scale coefficients and entropy correlations are mandatory diagnostics, not additional admission gates. Equation 7 and its feature definitions remain unchanged. This corrects an agent-added requirement rather than changing the law to obtain a favorable correlation.

At clarification, pretraining n4 was still running and no GRPO run or utility outcome existed. Already observed full-candidate correlations: n1 coverage 0.692747 / entropy -0.779521; n2 coverage 0.770678 / entropy -0.867247. These facts are retained explicitly: the entropy interpretation would already fail at n2. Any final result must state this distinction and cannot claim that entropy was decorrelated at every scale. The user thresholds remain 0.85 for the law's actual feature and 30% positive utility; no outcome-based retuning is allowed.

## Loss normalization clarification before reinforcement learning

Both the policy-gradient term and the exact forward KL term are averaged over the four token positions, as in a per-token GRPO objective; the policy-gradient sentence above describing a sum is superseded. This keeps the relative KL coefficient at exactly 1.0 as response length changes. No reinforcement-learning outcome existed at this correction; all cells use the same final implementation, whose hashes are frozen in `manifest.json`.
