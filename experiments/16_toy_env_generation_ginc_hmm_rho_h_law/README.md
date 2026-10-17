# Experiment 16: can the ρ–H law pick or generate reinforcement learning environments for a new target benchmark? (toy GINC-style hidden Markov model tasks, CPU only)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/README.md>

Created 10-15-2026 by ultimate_brando9 (Brando's assistant) as night 1 of a nightly series Brando asked for on 10-14-2026. Everything runs on one 4-CPU machine with no GPU (no SNAP cluster access yet). Live numbers: [results.md](results.md). Checkpoint: [CKPT_e16_toy_env_gen.md](CKPT_e16_toy_env_gen.md).

## Night 2 continuation

The completed `16_toy_env_generation_ginc_hmm_rho_h_law/expt_v2` run used four-token outputs, exact Kullback–Leibler (KL) regularization, generated mixtures and a prospective held-out-scale forecast. All 384 budget cells completed; 224 had positive observed joint utility, but the law-selected n4 gain was +0.0375 [−0.3500, +0.4500] percentage points (p-val=0.500): **TIE WITH BASELINES**, without established meaningful transfer. See [protocol](expt_v2/PROTOCOL.md), [live results](results.md) and [checkpoint](CKPT_e16_night2.md). This folder remains active because its oracle and experiment modules are imported by `tests/test_e16_ginc_toy.py`, and the nightly continuation depends on its results.

## Goal

- **Brando's question (10-14-2026, voice note):** "the goal of the project is to see if … using the predictive laws that Varun had for the other project … we can use those laws to … automatically generate environments for new benchmarks", starting from toy benchmarks such as GINC (hidden Markov model mixtures) or "something simpler … some sort of Gaussian thing … some MDP that we know and we can control", and then "see how it generalizes to other tasks".
- **The law.** The ICLR 2027 submission (Varun and Brando) predicts the held-out utility of a reinforcement learning (RL) environment before any RL, from two measurements under the starting policy: usable signal density ρ (admitted leave-one-out advantage mass per million generated tokens) and effective coverage H (normalized effective sample size of that mass across prompts). Utility follows paper Eq. 7, `Û = b0 + bN·x_N + bC·s(C) + b_ρ·s(C)·z(log ρ) + b_H·s(C)·z(H)`. Both measurements and the fit are reused unchanged from `src/rl4cv/experience.py` and `src/rl4cv/utility_model.py` (the code that reproduces the paper's 14B numbers).
- **Why a toy.** In a toy family we control every knob and have an exact verifier, so we can see whether "probe candidate environments, rank them with the law, train on the pick" transfers to a target benchmark that no candidate equals, at a cost of minutes, before trying it on Lean or VeriBench.

## Hypotheses and success test

- **T1, scale transfer.** Eq. 7 fit on the three smallest models predicts the largest model's utility curves: lower RMSE (root mean squared error) and higher pairwise rank accuracy than the budget-and-scale-only baseline, and leave-one-scale-out agrees.
- **T2, environment choice.** At the held-out scale, the law's pick has lower allocation regret on the target than (a) a uniformly random candidate, and also than the simple pre-RL rules a skeptic would try first: (b) the best fixed environment from the small scales, (c) the highest starting success, (d) the highest mixed-group share.
- **Verdict rule (agent-suggested, set before v2 ran).** SUCCESS if T1 and T2 hold against every baseline; CHOICE ONLY if T2 beats random but not (b)–(d); NO ADVANTAGE otherwise. A run where no candidate improves the target at all is reported as **NOT YET MEANINGFUL** whatever the verdict says, because the law can then only rank how much each environment hurts.

## Design

### Environment generator (`expt_v1/ginc_toy.py`)

- A *concept* is a small hidden Markov model (HMM) over V = 16 symbols, as in GINC (Xie et al. 2021, "An Explanation of In-context Learning as Implicit Bayesian Inference"). Minimal numpy re-implementation; the original GINC code in `brando90/beyond-scale-language-data-diversity/src/ginc` (hmmlearn + Hugging Face) is heavier than a CPU pilot needs, and deterministic slot/value emissions are replaced by an emission-sharpness knob.
- A *prompt* is a prefix x₁..x_l sampled from one concept; the policy emits the next symbol. Doing well requires inferring which concept produced the prefix (GINC's implicit Bayesian inference).
- *Knobs* that define an environment: hidden states S ∈ {4, 8, 12}; emission sharpness ∈ {2, 4, 8} (higher = lower emission entropy); number of concepts mixed n ∈ {2, 64}; prefix length l ∈ {4, 8, 12, 16, 24}.
- *Verifier / reward*: exact. Reward 1 when the emitted symbol equals the Bayes-optimal next symbol argmax_v p(x_{l+1} = v | x_{1:l}, true concept), computed with the forward algorithm; 0 otherwise.
- *Candidates*: 12 environments from a fixed fractional design over the four knobs (`CANDIDATES` in `run_pilot.py`), all drawn from the pretraining concept bank.

### Start policies and scale grid N (`expt_v1/policy.py`)

- Four tiny causal transformers: 4.5k, 28k, 105k and 604k parameters (d_model 16/32/64/128, 1–3 layers).
- Each is pretrained by next-token prediction for 1,500 steps (batch 64, documents of 32 symbols) on the pretraining bank: 9 (S, sharpness) settings × 64 concepts. The pretrained model is the RL start policy, the analogue of the paper's warm start.

### ρ and H

- Probe: 512 prompts per candidate, G = 8 samples each at temperature 1 under the start policy; `rl4cv.experience.measure_environment` gives ρ, H, the mixed-group share and starting success. Every response is one token and every response is admitted.

### RL

- GRPO-style (group relative policy optimization) policy gradient with leave-one-out advantages (paper Eq. 2), G = 8, 32 prompts per step, Adam at 5e-4, no KL (Kullback–Leibler) penalty in v1/v2; 200 steps. Budgets C = 12.8k, 25.6k and 51.2k generated tokens (steps 50/100/200). Two seeds per (scale, environment).
- Utility U(E, N, C) = target greedy accuracy after RL minus the start policy's, on fixed target prompts (4,000).

### Target benchmarks

- **v1 (pilot_v1):** two targets built from concepts the start policies never saw (held-out concept bank).
- **v2 (pilot_v2, primary):** the GINC-faithful target. GINC's in-context test uses the pretraining concepts in a new prompt format, so the target is all nine pretraining settings mixed, prefix length 10 (a length no candidate uses). The v1 held-out-concept target stays as the far-transfer secondary.

### Sanity family (`expt_v3`, coded and run 10-15-2026; protocol in [expt_v3/PROTOCOL.md](expt_v3/PROTOCOL.md))

Night 3 (10-16-2026, `run_mdp_v2.py`, six scales, three start-policy repeats, bootstrap intervals): **NO ADVANTAGE**. The law picks the noisy, already-solved b15 at every budget (regret 10.78 pts [9.53, 12.28] vs uniform random 4.42 and best fixed from s1–s5 1.47). The toy part is complete; see [results.md](results.md).

- A known small Markov decision process (MDP): a chain or grid of a few states with Gaussian rewards, where the optimal policy and the value of each training distribution are computable exactly. Knobs: horizon, reward noise, start-state distribution. It checks the ρ–H pipeline in a case where the "right" environment is known analytically.

## What would change the plan

- If no candidate ever improves the target, the toy is in a forgetting regime and says nothing about the law. Fix the RL setup first (KL to the start policy, mixtures of settings as candidates) before reading T1/T2.
- If log ρ and H are almost collinear, the law has one effective feature; responses need variable lengths or partial credit so ρ and H can separate.

## Structure

```
16_toy_env_generation_ginc_hmm_rho_h_law/
├── README.md                 design (this file)
├── results.md                results ledger
├── CKPT_e16_toy_env_gen.md   Rule 44 checkpoint
└── expt_v1/
    ├── ginc_toy.py           generator + exact verifier (numpy)
    ├── policy.py             tiny transformers, pretraining, sampling, GRPO (+ optional KL to start)
    ├── run_pilot.py          one scale per process: pretrain | probe ρ/H + RL per candidate
    ├── analyze.py            Eq. 7 fits, T1/T2, baselines, correlations -> analysis*.md/json
    ├── diag_lr.py            learning-rate diagnostic (after v1)
    ├── diag_kl.py            KL-to-start diagnostic (after v2)
    └── results/pilot_v1, results/pilot_v2   raw JSONL rows, logs, analyses (start_*.pt not committed)
expt_v3/                      known-MDP sanity family (exact DP target value)
    ├── PROTOCOL.md           frozen before RL
    ├── known_mdp.py          chain MDP, exact value, episode sampler
    ├── run_mdp.py            start policies, probes, GRPO + KL, exact-gradient oracle (one process per scale)
    ├── analyze_mdp.py        gate, separation, T1/T2, oracle agreement -> analysis_mdp.md/json
    └── results/mdp_v1        raw JSONL rows and analysis
```

## Reproduce (CPU, about 25 minutes wall clock on 4 cores)

```bash
python3 -m venv ~/.venvs/rl4cv-toy && ~/.venvs/rl4cv-toy/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch && ~/.venvs/rl4cv-toy/bin/pip install numpy pytest
cd experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v1
R=results/pilot_v2
for s in n1 n2 n3 n4; do python run_pilot.py --scale $s --out $R --stage pretrain --targets v2; done   # n4 ~7 min
printf "n4 0:3\nn4 3:6\nn4 6:9\nn4 9:12\nn3 0:6\nn3 6:12\nn2 0:12\nn1 0:12\n" | xargs -P 4 -L 1 sh -c 'python run_pilot.py --scale $0 --out '$R' --stage rl --targets v2 --envs $1'
python analyze.py --run $R --tag v2
```

Known MDP (about 4 minutes on 4 cores):

```bash
cd experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v3
for s in n1 n2 n3 n4; do python run_mdp.py --scales $s --out results/mdp_v1 & done; wait
python run_mdp.py --stage start --out results/mdp_v1 && python analyze_mdp.py --run results/mdp_v1
```

Test: `pytest tests/test_e16_ginc_toy.py tests/test_e16_known_mdp.py` (forward algorithm against brute-force enumeration, sampler statistics, reward and ρ plumbing; numpy only).

**TLDR-end:** [rl4cv: e16 toy env generation] This folder holds the design, CPU code and first pilot for testing whether the ρ–H law can pick training environments for a new target benchmark, on GINC-style HMM tasks with an exact verifier. Night 1 ran end to end, but every RL run lowered the target (a forgetting regime), and log ρ and H came out 0.995 correlated, so the law test is not yet meaningful; night 2 fixes the RL setup first.

**Snapshot:**
```
v2 target (9 pretraining settings mixed, l=10), held-out scale 604k params, 51.2k tokens:
law pick e10_S4_sh4_n64_L24  U = -3.80 pts   (oracle: same env)
uniform random candidate     regret 12.63 pts
best fixed env from small N  regret  0.00 pts   (same pick as the law)
positive-utility runs: 0 / 288; corr(in-env gain, target U) = -0.92
```
