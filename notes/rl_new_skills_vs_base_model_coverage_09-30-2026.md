# Can RL teach a model genuinely new skills, or only sharpen what pretraining put there? (09-30-2026)

TLDR: On-policy RL with a sparse outcome reward can only reinforce trajectories the *current* policy actually samples, so what it can teach within a budget is bounded by the current policy's coverage of the reward; but that coverage is dynamic (weights generalize, curricula chain stepping stones, richer feedback adds bits), so "RL does nothing beyond the base model" is too strong, "RL can install any behavior because it changes the weights" is also wrong, and the true statement is a *rate* statement that tells us exactly which levers matter for RL on Lean/code verification.

Provenance: drafted by Claude Code from the 09-29-2026 Discord exchange between Brando and Allen, plus Brando's 09-30 follow-up, for Brando to edit. Paper claims below were checked against the abstracts/PDFs on 09-30-2026; page-level quotes are marked as such.

---

## 0. The exchange being answered

- **Brando (09-29):** read the abstract of *Self-Play Pretraining with Zero Data* (Cowsik et al., arXiv:2609.30063) and took it as saying RLVR does nothing beyond the base model; skeptical, given DeepSeek-R1-style results, that RL "does nothing".
- **Allen (09-29):** online RL theory needs *coverage* of the action space by the base policy (Xie, Foster, Bai, Jiang, Kakade, ICLR 2023). An LLM "action" is a 10^4–10^5-token trajectory; if the base gives it probability ~1e-12, RL can't learn it. Atari differs because a random-init policy over ~18 actions tries all of them.
- **Brando (09-30):** value iteration converges to optimal behavior from any init; huge nets get zero train error and generalize, so policy gradient probably has similar power in practice; so why can't the reward signal — new data — enter the weights like any other data, whether the init is random or pretrained? Avoid "emergence"; give mechanism.
- **Correction on the trigger paper:** Cowsik et al. do *not* claim RL only sharpens. They pretrain a *learner* by next-token prediction from random init on byte sequences emitted by programs that a *generator* proposes; the generator is trained by RL with a dense, continuous learning-progress reward (gradient alignment) plus mutation/replay for exploration. Their Discussion is about universal vs contingent structure in pretraining data, not about RLVR's limits. The "RL only sharpens" claim comes from the RLVR literature (Yue et al. 2025 and successors), covered in §5.

## 1. State the question so that it has an answer

"Genuinely new" is ill-posed for a softmax policy: every token sequence has nonzero probability, so the *support* never changes under any training. The usable definition is budget-relative:

> Behavior `b` is **reachable** under policy `π` with rollout budget `B` iff `P_π(b) ≳ 1/B`.

The question then becomes: *given base policy π₀, reward r and budget B, which behaviors can on-policy RL raise from P ≲ 1/B to P ≈ 1?* That is a question about rates, not about what is possible in principle. With unbounded compute everything is possible (value iteration); with finite compute the answer is governed by coverage.

## 2. What actually enters the weights: SFT gradient vs RL gradient

Supervised fine-tuning on external data `D_ext`:

```
∇θ L_SFT = E_{(x,τ*) ~ D_ext} [ ∇θ log πθ(τ* | x) ]
```

Policy gradient (REINFORCE / PPO / GRPO / RLOO are all instances):

```
∇θ J_RL = E_{x ~ D} E_{τ ~ πθ(·|x)} [ A(x, τ) · ∇θ log πθ(τ | x) ]
```

Three consequences:

- **(a)** In SFT the *direction* of the update is set by an external trajectory `τ*`. It does not matter that `πθ(τ*|x)` might be 1e-77; the gradient still points at `τ*`. This is how "new data goes into the model".
- **(b)** In RL the directions are `∇ log πθ(τ)` for the model's *own* samples. The outside world contributes only the scalar `A(x, τ)`. The update is a reweighting of self-generated trajectories.
- **(c)** If no sampled `τ` is rewarded, then with any mean/group baseline `A ≡ 0` and the gradient is *exactly* zero. Not small: zero. Optimizer strength, network width, "zero train error" — none of it touches a zero gradient. (Without a baseline, an all-failure group with reward −1 pushes mass *off* the sampled trajectories toward everything else uniformly; that moves the policy but carries no information about where reward lives — diffusion, not learning, and hopeless in a `V^H` space.)

So, to Brando's "if there is new data and we change the weights, why wouldn't it go in?": **it does go in, but the new data is a ≤1-bit label on a trajectory the model wrote itself.** Outcome RL never writes a new trajectory into the weights. That is the precise content of "RL can't learn what it doesn't sample", and it isn't contestable; what is contestable is what follows from it (§4).

**Information budget.** A binary outcome reward carries ≤ 1 bit of external information per rollout of `L` tokens (≤ `G` bits per group of `G`). Cross-entropy pretraining receives the target token at every position, i.e. on the order of `L · H(token) ≈ L × (2–4)` bits per `L` tokens. For `L ≈ 10^4` that is 3–4 orders of magnitude more external information per rollout-equivalent. This is the first-principles reason pretraining is where knowledge comes from and RL is where *selection* happens — Brando's prior, formalized.

## 3. Why "value iteration converges" and "big nets generalize" don't escape §2

### 3.1 Value iteration's guarantee is a coverage guarantee in disguise

`Q_{k+1}(s,a) = r(s,a) + γ E_{s'} max_{a'} Q_k(s',a')` converges from any initialization *because every sweep updates every (s,a)*: it needs the transition model, or an enumeration of `S × A`, at cost `|S||A|` per sweep. The sample-based version, Q-learning, converges from any init **under the condition that every (s,a) is visited infinitely often** (Watkins & Dayan 1992). That condition *is* coverage.

In the token MDP, `s` = prefix and `a` = token, so `|S| ~ V^H` with `V ~ 10^5`, `H ~ 10^4`. A random policy reaches a given leaf with probability `V^{-H}`; "visited infinitely often" costs ~`V^H` samples per state. Value iteration doesn't dissolve the coverage problem; it assumes it away by enumeration. Foster, Mhammedi & Rohatgi (2025) make this exact for LLMs: coverage of the base model is *not* needed for sample efficiency (with unbounded compute you can search the tree), but it **lower-bounds the runtime** of any algorithm that reaches the base model only through sampling.

**Atari.** Random init works there because (i) the *effective* state space (emulator RAM, the game's latent state machine) is small — many action sequences collapse to the same state, which is exactly why Xie et al.'s coverability coefficient is small for block MDPs (it scales with the number of latent states, not with the number of observations); (ii) reward is dense-ish and reachable by random play; (iii) the horizon to first reward is short. Montezuma's Revenge violates (ii)–(iii), and RL from random init fails there until you add intrinsic motivation (RND, Go-Explore). RLVR with a binary end-of-trajectory reward on a token tree — where no two trajectories ever merge — is the Montezuma regime, not the Breakout regime. Allen's "18 actions" framing is slightly off: the probability of one *specific* `H`-step Atari sequence is also `18^{-H}`; the real difference is state merging, which the token tree lacks.

**Coverability vs coverage — two different objects.** Xie et al.'s `C_cov = inf_μ sup_{π∈Π,h} ‖d^π_h / μ_h‖_∞` is a property of the MDP and the policy class (does *some* distribution cover every policy's visitation?), equal to cumulative reachability `max_h Σ_{(x,a)} sup_π d^π_h(x,a)`. For the token MDP and any policy class expressive enough to memorize a string, `sup_π d^π_h(x) = 1` for every prefix `x`, so `C_cov ~ V^h`: the positive result (GOLF gets regret `Õ(H √(C_cov T log|F|))` under Bellman completeness) simply does not apply. The reason RL on LLMs works at all is a different quantity — how much mass the *pretrained policy* puts on rewarded responses (Foster et al. 2025; Chen et al. 2025, "The Coverage Principle") — and that is a property of `π₀`, not of the MDP. Allen's answer conflates the two a little, but the conclusion he draws is the Foster et al. one and is right.

### 3.2 "Zero train error + generalization" fits what you sampled; it can't find what you didn't

Interpolation power lets a net fit any targets you hand it. In supervised learning the targets are given. In RL the targets — rewarded trajectories — have to be *found* first. Big net + policy gradient = "can fit any reweighting of my own samples", not "can find any trajectory". Optimization power and exploration power are different resources, and §2(c) is about the second.

**A thought experiment worth keeping.** Reward is 1 iff the model outputs a specific 64-character hex password. Base `P ≈ 16^{-64} ≈ 1e-77`.
- Outcome RL: zero gradient forever, any optimizer, any width.
- SFT with one example: solved in one step (memorization).
- Reward = number of correct *leading* characters: policy gradient solves it in ~`16 × 64 ≈ 10^3` rollouts, each step reinforcing a 1/16-probability event.

Same weights, same optimizer; the *reward density* decided everything. §6 uses this.

## 4. Where genuinely new behavior does come from (mechanisms, no "emergence")

None of these violate §2; all are consistent with the gradient formula.

**(i) Weight-space generalization.** The update direction lies in `span{∇ log π(τ_i)}` over *sampled* `τ_i`, but a step in weight space changes `π` on *every* prompt. Reinforcing "re-derive the key lemma before using it" on easy problems — where it gets sampled and rewarded — can move `P(same behavior | hard problem)` from 1e-9 to 1e-2, at which point the hard problem becomes sampleable. On the hard prompt nothing was reweighted; the policy moved as a side effect. Whether the side effect helps or hurts depends on inductive bias; empirically it often helps, which is what the "RL generalizes, SFT memorizes" results are about. The analogy to Atari's state merging: the network treats semantically similar prefixes similarly, so one update touches many prefixes — approximate state merging that lives in the function approximator rather than in the MDP.

**(ii) Iterated coverage expansion (stepping stones / curriculum).** Coverage is a property of the *current* policy `π_t`, not of `π₀`. Over rounds, RL can reach a trajectory that was negligible under `π₀` — but only through a chain of intermediate trajectories, each non-negligible under the policy *at that time*. This is why curricula matter (Rajaraman, Huang, Dudik, Schapire, Foster & Krishnamurthy 2026 prove autocurriculum reduces RL's dependence on reference-model quality to a burn-in cost nearly independent of target accuracy), why "prolonged" RL (ProRL) finds things base pass@k misses, and why frontier pipelines iterate RL → distill → RL over ever-larger environment suites. Mousavi-Hosseini & Erdogdu (2026) give the barrier its sharp form for linear autoregressive models: with **outcome** rewards, the reward queries needed to go beyond the base's support are governed by the base's *likelihood quantile* and "can be exponential in N" (sequence length), "regardless of the pre-training algorithm". Stepping stones are not a nicety; they are the only route around an exponential.

**(iii) Denser feedback channels.** Binary outcome = 1 bit/rollout. Process rewards, partial credit, and — most importantly for this repo — *environment feedback that enters the context* (a Lean error message, a failing unit test, a type mismatch) carry far more. Compiler output is external data the model conditions on inside the trajectory; it is "new data" in exactly Brando's sense. Mousavi-Hosseini & Erdogdu: with **process** rewards the query complexity drops from exponential in `N` to linear in `N` (times a token-level likelihood quantile). Cowsik et al.'s generator is a live example of RL from *random init* working: the reward is dense and continuous, the action space is small (short Brainf*ck-like programs), and they add mutation + replay for exploration — all three coverage levers pulled at once.

So "new skills" are real and mechanistic: side effects of updates on covered prompts, chains of covered steps, and information from richer channels. What is impossible is learning from a trajectory that was never sampled, and that is all Allen's claim actually requires.

## 5. Reconciling the 2025–2026 empirical record

**Sharpening side**
- Yue et al. 2025 (arXiv:2504.13837): RLVR beats base at pass@1; base beats RLVR at large `k`, across model families, RL algorithms and math/code/visual domains.
- Zhao, Meterez, Kakade, Pehlevan, Jelassi & Malach 2025, *Echo Chamber* (arXiv:2504.07912): PPO, GRPO and expert iteration all converge to a dominant output distribution that amplifies patterns in the pretraining data.
- Shao et al. 2025, *Spurious Rewards* (arXiv:2506.10947): *random* rewards give +21.4 points on MATH-500 for Qwen2.5-Math-7B (vs +29.1 with real rewards). Mechanism: the PPO/GRPO clip term amplifies the high-prior "code reasoning" behavior (65% → 90%+). The reward carried almost no information; the behavior was already there.
- Wu, Xuan, Lu, Liu, Dong, Harchaoui & Choi 2025, *The Invisible Leash* (arXiv:2507.14843): shrinkage of empirical support outweighs expansion under larger sampling budgets; answer-level entropy falls even where token entropy rises; pass@1 reliably improves.
- Clay, Gollapudi, Harilal, Jang, Morrison, Oh & Jaques 2026, *Demystifying RL Post-Training* (arXiv:2608.24949): success "depends on whether the base model already places sufficient probability mass on the desired behavior, linking it to the classical concept of exploration in RL."
- Bansal, Mohri, Qin, Alvarez-Melis & Kakade 2026, *RL Excursions during Pre-Training* (arXiv:2606.04272): general capabilities essentially unchanged by RL (degraded by SFT); RL on base checkpoints expands the distribution, and sharpening appears only after SFT.
- The ICLR 2027 submission Brando shared (*Which Environments Should LLMs Learn From?*): at 14B, pass@1 rises 5.65 points over the warm start while "native pass@4 remains below the warm start for every trained arm" — the sharpening signature in fresh data. Its `q_mixed = 1 − p^G − (1−p)^G` is the per-prompt "does this prompt produce any gradient" number, and its 11.4-point spread from environment choice alone at 4B shows how much of RL's outcome is decided by where the signal is.

**Expansion side**
- Liu, Diao, Lu, Hu, Dong, Choi, Kautz & Dong 2025, *ProRL* (arXiv:2505.24864): RL-trained models "consistently outperform base models across a wide range of pass@k evaluations, including scenarios where base models fail entirely regardless of the number of attempts" (for the finite `k` they test). Same group as *Invisible Leash*; the two are compatible — net support shrinks, while specific frontier tasks get unlocked by long training.
- Shen, Li, Rahman, Sun, Goldblum, Telgarsky & Izmailov 2026 (arXiv:2607.16097), chess + math at 5M–1B: post-RL performance is well predicted by pretraining loss; on easy puzzles RL amplifies moves SFT already preferred; on hard puzzles RL "surfaces correct moves that were *nearly* absent under SFT". *Nearly* absent — small but nonzero — is exactly §4(i)–(ii).
- Guo et al. 2025 (DeepSeek-R1, Nature 645:633–638) and every frontier reasoning model: large pass@1 gains from RL; the self-verification / backtracking behaviors that look new are documented in base models before RL (Liu et al. 2025, the Dr. GRPO paper) and get amplified.

These stop looking contradictory once you index each result by: how far from zero the base probability was; how many rounds / stepping stones were used; reward density; and what budget was used to measure the base's boundary. Two caveats on the pass@k metric itself: at large `k`, base pass@k is inflated by guessing on short-answer problems; and an RL run explores millions of rollouts per problem-set, far more than `k = 256`, so "base pass@256 > RL pass@256" says RL concentrated mass and lost diversity, not that it found nothing the base wouldn't produce in 256 tries.

## 6. Verdict on the exchange

- **Allen's mechanism:** correct and not really debatable — §2(c); Foster et al.'s runtime lower bound; Mousavi-Hosseini & Erdogdu's exponential-in-`N` barrier for outcome rewards.
- **Allen's framing:** loose in two places. Coverability (Xie et al.) is a property of the MDP + policy class, not "the base policy must be uniform over actions"; the relevant LLM quantity is the base's mass on rewarded responses (Foster et al. 2025, Chen et al. 2025). And the relevant probability is of the *set* of rewarded trajectories, not of one 128k-token string; that set can be large.
- **The strong reading "RL does nothing beyond the base model":** wrong as stated, because coverage is dynamic (§4). The defensible statement: *on-policy RL with sparse outcome reward can only learn from trajectories the current policy samples, so what it can teach in a budget is bounded by the current policy's coverage of reward; that coverage is set by pretraining and expanded by RL only slowly — through generalization and stepping stones — or faster through denser feedback.*
- **Brando's "why wouldn't the new information go into the weights?":** it does, but the information is a ≤1-bit label on the model's own sample (§2). "Just motivating some actions" hides the distinction between motivating an action you *took* and one you *didn't*; policy gradient can only do the former. Q-learning-style bootstrapping can in principle value an untaken action, but in a depth-10^4 tree you never visit it, and the bootstrapped value there is function-approximator extrapolation — §4(i) again.
- **"Random init or not":** under sparse outcome reward this is *the* variable. Random init on "write a correct Lean file" has `P(reward)` so small the gradient is identically zero at any budget, which is why nobody runs RLVR from scratch. Under dense reward, RL from random init reduces to something close to supervised learning (Cowsik et al.'s generator; the password-prefix example) — which works, but then the information is external again.
- **DeepSeek-R1-style gains** are real *and* consistent with all of this: pass@1 without a verifier at inference is what users get; turning pass@256 into pass@1 is most of the product.
- **Net effect on Brando's pro-pretraining prior:** strengthened, not weakened. Pretraining buys coverage (Chen et al. 2025: next-token prediction implicitly optimizes coverage, and coverage generalizes faster than cross-entropy); RL spends it.

## 7. What this means for RL on code verification (this repo)

Predictions and levers, all testable:

1. **Measure coverage before training.** For each VeriBench / VBV2 task, estimate base pass@k at large `k`, per component (typechecks; states ≥1 `example`; fraction of theorems kernel-checked with clean axioms; FSC). Tasks with base pass@k ≈ 0 at every affordable `k` are tasks where binary-reward RLVR from that base produces *zero gradient*. Prediction: RL gains concentrate on tasks with intermediate base pass@k; tasks at 0 stay at 0 unless one of the levers below creates signal. This is also the honest reading of the VBV2 non-saturation objective — a task the base never approaches is unsaturated *and* currently unlearnable by outcome RLVR.
2. **Reward density is the main lever.** The SCSC factorization already gives partial credit: `IC_tests ∈ {0,1}`, `IC_proofs` = fraction of stated theorems with clean kernel axioms, `FSC`. Under a binary "everything proved" reward most groups are all-zero; under `IC_proofs`, a group in which one rollout proves 3 of 7 theorems has signal. Per-theorem credit is the password-prefix reward. Caveat: partial credit invites hacking (trivial theorems, vacuous specs, `sorry`, `native_decide`), and the existing rules — `sorry`/`native_decide` earn zero, non-vacuous reference specs, the prove-first contract — are the anti-hacking half of this lever and must not be weakened for RL.
3. **Compiler feedback inside the rollout.** Multi-turn rollouts in which `lake env lean` output re-enters the context are the densest external channel available; one Lean error is many bits. Mousavi-Hosseini & Erdogdu's exponential → linear result is the theory version of "let the model see the error".
4. **Curriculum from the base's own pass@k.** Order tasks by base pass@k, or by `q_mixed` under the *current* policy, re-measured each round. Stepping stones: lemma-level tasks, spec-only tasks, proof-repair tasks before full end-to-end autoformalization. This makes §4(ii) happen on purpose rather than by luck.
5. **Distillation / SFT for the truly uncovered.** Where the base has no coverage and no curriculum reaches it, the information has to come in as trajectories: SFT on human or stronger-model Lean traces. That is not a defeat for RL; it is §2(a).
6. **Report pass@1 and pass@k together.** Sharpening shows up as pass@1 ↑ with pass@k ↓; expansion as pass@k ↑ on tasks where base pass@k ≈ 0. Reporting pass@1 alone cannot distinguish them, and for a benchmark meant to stay unsaturated the distinction is the whole story.

## 8. A clean experiment for this repo (proposal)

- Base model, fixed task subset (e.g. 100 VBV2 tasks spanning base pass@64 ∈ {0, (0, 0.1], (0.1, 0.5], > 0.5}).
- Arms, same trainer and token budget: (A) binary reward = full SCSC success; (B) `IC_proofs` partial credit; (C) B + one round of compiler feedback in the rollout; (D) C + curriculum ordered by current-policy `q_mixed`.
- Measure pass@1 and pass@64 per bucket before and after.
- Predictions: A moves only the (0, 0.1] and (0.1, 0.5] buckets and lowers pass@64; B extends gains to tasks where the base sometimes proves ≥1 theorem; C and D are the only arms that move the pass@64 = 0 bucket, and D more than C. If A moves the zero bucket, §2 is wrong and this note should be rewritten.
- Solver runs go through Harbor / Valkyrie per the VeriBench rules; scoring through `scripts/scsc/run_real_eval.py`.

## Bottom line

RL cannot learn from a trajectory it never samples (§2). Value iteration only "converges from anywhere" because it enumerates, which is coverage by brute force (§3). Big nets fit what you sampled; they don't find what you didn't (§3.2). New behavior still arrives — as side effects of updates on covered prompts, as chains of covered steps, and through denser feedback (§4) — which is why both the sharpening and the expansion papers are right about their own settings (§5). For code verification, this makes the levers concrete: per-theorem credit, compiler feedback inside the rollout, a pass@k-based curriculum, and SFT for what the base never approaches (§7).

## References

- Xie, Foster, Bai, Jiang, Kakade. *The Role of Coverage in Online Reinforcement Learning.* ICLR 2023 (notable top 5%). arXiv:2210.04157; OpenReview `LQIjzPdDt3q`.
- Foster, Mhammedi, Rohatgi. *Is a Good Foundation Necessary for Efficient Reinforcement Learning? The Computational Role of the Base Model in Exploration.* 2025. arXiv:2503.07453.
- Chen, Huang, Golowich, Malladi, Block, Ash, Krishnamurthy, Foster. *The Coverage Principle: How Pre-Training Enables Post-Training.* 2025. arXiv:2510.15020.
- Mousavi-Hosseini, Erdogdu. *Post-Training with Policy Gradients: Optimality and the Base Model Barrier.* 2026. arXiv:2603.06957.
- Rajaraman, Huang, Dudik, Schapire, Foster, Krishnamurthy. *Learning to Reason with Curriculum I: Provable Benefits of Autocurriculum.* 2026. arXiv:2603.18325.
- Yue, Chen, Lu, Zhao, Wang, Song, Huang. *Does Reinforcement Learning Really Incentivize Reasoning Capacity in LLMs Beyond the Base Model?* 2025. arXiv:2504.13837.
- Zhao, Meterez, Kakade, Pehlevan, Jelassi, Malach. *Echo Chamber: RL Post-training Amplifies Behaviors Learned in Pretraining.* 2025. arXiv:2504.07912.
- Shao et al. *Spurious Rewards: Rethinking Training Signals in RLVR.* 2025. arXiv:2506.10947.
- Wu, Xuan, Lu, Liu, Dong, Harchaoui, Choi. *The Invisible Leash: Why RLVR May or May Not Escape Its Origin.* 2025. arXiv:2507.14843.
- Liu, Diao, Lu, Hu, Dong, Choi, Kautz, Dong. *ProRL: Prolonged Reinforcement Learning Expands Reasoning Boundaries in Large Language Models.* 2025. arXiv:2505.24864.
- Liu, Chen, Li, Qi, Pang, Du, Lee, Lin. *Understanding R1-Zero-Like Training: A Critical Perspective* (Dr. GRPO). 2025. arXiv:2503.20783.
- Clay, Gollapudi, Harilal, Jang, Morrison, Oh, Jaques. *Demystifying Reinforcement Learning Post-Training of Language Models.* 2026. arXiv:2608.24949.
- Shen, Li, Rahman, Sun, Goldblum, Telgarsky, Izmailov. *Understanding Reasoning from Pretraining to Post-Training.* 2026. arXiv:2607.16097.
- Bansal, Mohri, Qin, Alvarez-Melis, Kakade. *RL Excursions during Pre-Training: Re-examining Policy Optimization for LLM Training.* 2026. arXiv:2606.04272.
- Cowsik, Dolev, Li, De Luca, Cohen, Goodman, Levine. *Self-Play Pretraining with Zero Data.* 2026. arXiv:2609.30063.
- Anonymous. *Which Environments Should LLMs Learn From? Predicting RL Utility Across Scale.* ICLR 2027 submission (PDF shared by Brando, 09-30-2026).
- Guo et al. *DeepSeek-R1 incentivizes reasoning in LLMs through reinforcement learning.* Nature 645:633–638, 2025.
- Watkins, Dayan. *Q-learning.* Machine Learning 8:279–292, 1992.
- Burda, Edwards, Storkey, Klimov. *Exploration by Random Network Distillation.* 2018. arXiv:1810.12894. Ecoffet et al. *Go-Explore.* 2019. arXiv:1901.10995.
