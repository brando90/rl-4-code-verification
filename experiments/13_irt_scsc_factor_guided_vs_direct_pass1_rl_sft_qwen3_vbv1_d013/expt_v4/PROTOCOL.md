# Experiment 13 v4 protocol: factored vs direct reward where the strict reward has signal

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v4/PROTOCOL.md>

**Status:** FROZEN 10-20-2026, before any v4 generation. One light QA round (Codex `gpt-6-astra`, ultra) returned FIXES_NEEDED with 3 critical findings. All 8 findings are fixed in this version ([review record](LIGHT_QA_10-20-2026.md)). Changes after this lock are numbered amendments made before the data they affect.

**TLDR:** Does RL on a factored partial-credit reward (arm B) improve strict pass@1 more than RL on the strict reward itself (arm A), at a matched token budget? Arm P is a placebo matched only to the start policy's marginal factored-reward density.

v2 and v3 could not answer this. Under their rollout sampler (temperature 1, no truncation), the start policy had **0/4,302** measured strict successes on its train anchor panel, so arm A had no gradient.

v4 rolls out with the historical evaluation sampler, under which the start policy's strict reward varies within groups. It trains the filtered policy that this sampler actually samples from. Every technical gate runs on an arm whose reward varies, and the test split is evaluated once.

## 1. Why v4, and the evidence used to choose the sampler

**v2 (terminal at T2, `625a2e6`).** Under temperature 1 and top-p 1, the strict outcomes were:

- the start policy (`sft_4B_f1p0`, full-schedule anchor panel): **0/4,302** measured, 10 missing ([anchors](../expt_v2/RESULTS_ANCHORS_S2.md));
- all three frozen train policies together (base, half and full schedule): 0/12,916 measured ([item-model fit report](../expt_v2/RESULTS_CALIBRATION_S2.md));
- compilation among well-formed outputs (Q2): 0/1,294;
- T2's strict-reward update: 0/255.

Every advantage was zero, and no weight changed.

**v3 (condition `v3-A7`).** Other agents launched it on 10-16, before Brando's 10-20 "GO". It reran the technical gates on the factored reward and passed T2–T4, and it runs a paired A/B/P pilot at the same sampler. Arm A still has essentially no signal there, so v3 cannot test factored vs direct. Its outcomes are never pooled with v4.

**Sampler evidence.** This is existing, train-only data, read before any v4 data exists. The source is the v2 Amendment A6 diagnostic: start policy `sft_4B_f1p0`, 64 seeded train tasks × 8 samples, frozen float16 runtime, temperature 0.6, top-p 0.95, top-k 20 and 12,288 new tokens.

- **Bound result** ([report](../expt_v2/RESULTS_A6_DIAGNOSTIC_S2.md), [aggregate receipt](../expt_v2/phase1/A6_S2_result.json)): **48/512 strict successes, 496 measured, 16 missing**. The full-denominator bounds are [9.375%, 12.5%].
- **Unbound design counts.** On 10-20-2026 the v2 master computed three more counts from the private scoring receipts, without opening task identities:
  - tasks by strict successes out of 8: 0: 51 · 1: 2 · 2: 3 · 3: 3 · 5: 2 · 6: 1 · 7: 1 · 8: 1;
  - complete groups with mixed strict outcomes: **8/54**;
  - complete groups with a varying factored reward: **49/54**.

  No committed receipt holds these counts yet. Before admission, the implementation commits a reducer, and the v4 admission binds its output and input hashes. These counts motivated the design only. They enter no gate or statistic; V4-G0 measures the same quantity afresh.

**Provenance disclosure.** The v4 sampler is the historical evaluation sampler. A6 chose it because it gave nonzero strict success on validation (historical reference 100/1,080, 9.26%), so the choice is validation-informed. v4 adds no validation reads before checkpoint selection (§ 4), and opens no test data before its single test evaluation.

## 2. Fixed design

**Inherited unchanged from v2 and v3:**

- **Start policy:** `sft_4B_f1p0`, Qwen3-4B, 658 SFT steps, with the same hash-bound export.
- **Numerics and trainer:** S2 numerics (float16, identical for the vLLM 0.10.0 generator and the NeMo RL 0.4.0 trainer).
- **Prompts:** templates, prompts and the train/validation/test split (539/135/222).
- **Scorer and rewards:** the official strict scorer, and B's frozen guarded geometric-mean formula. The factored reward is a training proxy and is never reported as official SCSC.
- **Recipe:**
  - AdamW at learning rate 1e-6, betas (0.9, 0.999), weight decay 0.01;
  - clipping 0.2 below and 0.28 above;
  - KL coefficient 0;
  - token-normalized loss;
  - importance-weight cap 2;
  - 256 rollouts per update, in groups of the size G chosen by V4-G0: 32 groups at G=8, or 16 groups at G=16.

**Changed:**

1. **Rollout sampler** (fixed here, not selected later): temperature 0.6, top-k 20, top-p 0.95, at most 12,288 new tokens. This is the historical evaluation sampler from `expt_v2/phase2/evaluation_contract.py`, and the A6 diagnostic used it.
2. **Training objective: the policy optimized is the filtered policy that is sampled.**
   - **Filtered policy.** At each position s with trainer logits z, the support S(s) is computed in the pinned generator's order: temperature scaling to z/0.6, then the 20 highest logits, then the smallest top-probability prefix of that renormalized top-20 distribution with mass at least 0.95. The filtered policy π̃(a|s) is softmax(z/0.6) restricted to S(s) and renormalized. Tie handling matches the generator; V4-T1 verifies it.
   - **Ratios.** Both the importance-ratio numerator (current weights) and denominator (old weights) are trainer-computed log π̃. Both use the support computed at the old weights for that position. Support selection carries no gradient, and every ratio is defined.
   - **Behaviour probabilities.** The generator records, per position, the sampled token and its 20 highest raw log-probabilities. Because the top-p step acts on the renormalized top-20 distribution, these determine the generator's support and its π̃ exactly. If the pinned engine cannot record them, V4-T1 fails as unimplementable. v4 then stops and never falls back to an unfiltered objective without a new amendment.
   - **Discarded mass.** The trainer reports, per position, the probability mass outside S(s) under softmax(z/0.6).
3. **Length and context contracts.** The response cap is 12,288 new tokens. The previous 8,192-token cap and 15,945-token context are retired.
   - **Context:** for each engine, the maximum prompt tokens over every prompt v4 uses (train, validation and test), plus 12,288. For train alone that is 7,753 + 12,288 = 20,041 tokens. Admission binds the computed value and checks it against the model's maximum position embeddings.
   - **Validators:** every inherited validator is migrated, and tests reject the old values.
   - **Token-matching overshoot:** at most one crossing group, so at most G × 12,288 tokens (98,304 at G=8, 196,608 at G=16). The inherited rule stays: the paired checkpoint token difference must be ≤ 1% of the target, or token matching fails before main.
   - **Resources:** V4-T4 measures memory, scoring timeouts and costs at the new lengths.
4. **Arms.**
   - **A:** strict reward.
   - **B:** factored reward.
   - **P, placebo.**
     - *Reference distribution:* the multiset of B rewards on all measured slots of the V4-G0 batch, which uses the start policy at the v4 sampler. Missing slots are excluded, counted and reported. P is admitted only if at least 90% of the G0 slots are measured; otherwise P is excluded and its contrasts are unmeasured.
     - *Hash:* the admission records the distribution's SHA-256, taken over the sorted rewards written as 17-significant-digit decimals, before any P update.
     - *Draws:* each (seed, update, slot) gets an independent draw from that distribution, using a counter-based generator keyed by SHA-256 of `e13v4-placebo`, seed, update and slot. This stream is domain-separated from every other random stream. All draws are computed and bound before P's first response, so they are independent of P's outputs.
     - *What P controls:* P matches the start policy's marginal factored-reward density only. It does not match B's within-group variance, its within-task advantage structure, or how B's density changes during training. Each update reports P's and B's reward mean, fraction of groups with nonzero variance, and mean within-group variance. B − P is read only as "B beyond a random reward matched to the start density".
   - **C (IRT-weighted) is excluded.** Its item-response model fit was not admitted in v2, and G1 was INCONCLUSIVE. The IRT question continues offline.
5. **Gates run on arms whose reward varies** (§ 3).

**Seeds:** pilot seeds 1301 and 1302; main seeds 13011, 13012 and 13013. A, B and P share the same prompt-group stream per seed.

**Split use:** train only until validation selection. Validation has 135 tasks. Test has 222 tasks and is evaluated once, only for the selected checkpoints.

## 3. Gates (in order; no gate is retried after it computes its statistics)

A4 governs infrastructure attempts: an attempt that generated nothing may be fixed and rerun, with at most 3 attempts.

- **V4-T1, probability and support agreement.** Run on the frozen 8-response train probe at the v4 sampler. Pass requires:
  - zero sampled tokens outside the trainer's recomputed support;
  - identical generator and trainer supports at ≥ 99% of sampled positions;
  - for log π̃ on the sampled tokens, median absolute generator–trainer error ≤ 0.01 and 99th-percentile error ≤ 0.10;
  - importance truncation at cap 2 on ≤ 1% of tokens.

  The discarded-mass distribution is also reported (median and 99th percentile).
- **V4-G0, group-size selection.** This was Brando's 10-20-2026 idea (see `../../ideas/grpo_group_size_vs_start_pass1/`). The procedure was set with a Codex `gpt-6-astra` ultra consult, graded 8/10 ADD. It runs once, after V4-T1 passes and before any update, and its procedure is frozen here before its generation.
  - **Sample:** 32 seeded train tasks × 32 samples from the start policy at the v4 sampler. Tasks are drawn with NumPy `default_rng(1304001)` from the sorted train IDs, with no outcome filtering. Each sample is scored with the official strict scorer and B's reward.
  - **Cost:** about 3 device-hours of generation (A6 took 1.40 for 512 responses) and about 8 processor-hours of Lean scoring. It is reported separately from the token-matched learning budget.
  - **Estimates:** take a task with s strict successes out of 32. The probability that a group of size G is mixed is estimated without bias as q̂_G = 1 − [C(s,G) + C(32−s,G)] / C(32,G), with impossible terms set to zero. Averaging over tasks gives q̄_G. At 256 rollouts per update:
    - expected nonzero-advantage samples: N_G = 256·q̄_G;
    - expected mixed groups: M_G = (256/G)·q̄_G.
  - **Rule:** choose G=16 only if the one-sided 95% lower bounds of both N_16 − 1.2·N_8 and M_16 − 3 are above zero. The bounds come from a paired percentile bootstrap over whole tasks (10,000 draws, seed 1304002). Otherwise keep G=8.
  - **Missing scores:** tasks with missing scores are evaluated twice, once with every missing slot a success and once with every missing slot a failure. G=16 requires the rule to hold under both.
  - **Scope:** one G applies to every arm and seed.
  - **Disclosure:** this is design selection on train tasks with the start policy. It precedes any update, validation read or test read.
  - **Also used for:** this batch defines P's reference distribution (§ 2) and supplies V4-T2's batch.
- **V4-T2, one real update.**
  - **Batch:** a deterministic subset of the V4-G0 batch. It takes the first 256/G tasks in G0's seeded order, and for each task the G samples with the lowest sample indices.
  - **Reward:** A's strict reward if at least one complete group (all G slots measured) has mixed strict outcomes. Otherwise B's reward, if at least one complete group has a varying B reward. Otherwise the gate stops with no resampling. This fallback is declared here, before any v4 data.
  - **Pass requires all of:**
    - finite advantages, at least one nonzero;
    - a finite, nonzero gradient norm before clipping, reported as in `expt_v2/phase2/a6_gradient_reporting.py`;
    - a changed weight hash;
    - generator refit agreement on log π̃ with a median ≤ 0.01;
    - zero sampled refit tokens outside the trainer's support at the updated weights.

    A weight-hash change alone is not accepted, because AdamW weight decay changes weights with zero advantage.
  - **Reported:** the fraction of positions whose support changed between the old and new weights.
- **V4-T3, saved-batch replay.** The replay uses exactly the V4-T2 batch, rewards and advantages, plus the pre-update weights, random state, optimizer state and scheduler state. Its loss must agree within 1e-3.
- **V4-T4, measured cost at the new lengths.** It records:
  - device-hours per update;
  - peak trainer memory at the longest admissible sequence (maximum train prompt + 12,288 tokens), from one synthetic forward and backward pass, which must fit;
  - generated-token throughput;
  - Lean wall time and the deterministic-timeout rate;
  - storage growth.

  These measurements feed the § 5 cost estimate.
- **B audits.** These amend parent § 3 explicitly for this $0 version.
  - *What the parent requires:* functioning independent coverage checks before B training. The validated formal-specification coverage (FSC) judge route needs Valkyrie calls, and rl4cv judge calls are paused.
  - *Controls v4 still runs:* the train mutation audits (padding, deletion and substitution, with every reward-increasing mutation reported), and hidden gold-test coverage on the fixed train audit cohort. Both are local, and v2 admitted the hidden-test route ([controls](../expt_v2/RESULTS_HIDDEN_CONTROLS_S2.md)).
  - *Stop rule (frozen):* stop B if its mean reward rises while its mean theorem count or available train coverage falls more than 10% relative to its own start on the audit cohort.
  - *What stays open:* FSC is unmeasured, and reward-hacking safety is not established.
- **Learning pilot:** A, B and P on seeds 1301 and 1302, 30 updates each.
- **V4-T5, learning-feasibility selection on arm A.**
  - **Statistic:** A/1301's train strict-reward mean over updates 21–30, minus its mean over updates 1–10. It must be at least **2 percentage points**.
  - **Conservative completion:** missing slots count as successes in updates 1–10 and as failures in updates 21–30.
  - **Extension:** if the gate fails, all six pilot trajectories extend once to 60 updates, keeping the arms paired, and the comparison becomes 1–10 against 51–60. If that also fails, stop and publish.
  - **Interpretation:** this is a disclosed feasibility selection, not efficacy evidence for B − A.
  - A/1302 is reported as a replication and never rescues a failure. B's and P's own reward curves are reported descriptively.

## 4. Main study, admitted only after V4-T5 passes and resources fit

- **Token budget:** T = 25,600 × ceil(mean generated tokens per rollout). The mean is taken over all generated slots of A/1301 and A/1302, updates 1–30, whether or not the pilot was extended. Both trajectories must have completed 30 updates.
  - Every arm and seed is checkpointed at T/4, T/2, 3T/4 and T.
  - Groups are complete, with no refills.
  - The ≤ 1% paired token rule from § 2 applies.
- **Checkpoint selection:** per arm and seed, choose the checkpoint with the highest validation strict mean, evaluated at the v4 sampler on 135 tasks × 8 samples. Ties go to the later checkpoint (inherited).
- **Test evaluation:** once, on the selected checkpoints, on 222 tasks × 16 samples at the v4 sampler (inherited).
- **Primary outcome:** average task strict rate over 16 samples per task, averaged over seeds. The primary contrast is B − A, at matched token budgets. Pooled results are reported, and core (152 tasks) and IndustrySet (70 tasks) separately.
- **Inference (parent § 7, inherited):**
  - two-sided exact paired-seed sign-swap p-values under within-block exchangeability. With three seeds the minimum two-sided p is 2/8 = 0.25, so no confirmatory claim at α = 0.05 is available.
  - The primary family is B − A alone, because C is excluded, so the Holm correction is trivial.
  - Descriptive 95% intervals come from 10,000 bootstrap draws that resample paired seed blocks, then task groups paired across arms.
  - Seeds of paired arms are never resampled independently.
- **Secondary:** P − A and B − P (each with its exact p-value and interval), unbiased pass@4 and pass@16, regression counts, component trajectories and the reward-hacking audits.
- **Guards:** full denominators throughout, with missing cells kept as missing and given completion bounds. Per arm, report generated, prompt and optimized tokens, plus device-hours.

## 5. Resources, safety and timing

- **Cost:** $0 to Vals. SNAP GPUs only, with no Valkyrie or provider calls. FSC and official SCSC are reported unavailable while rl4cv judge calls are paused.
- **Cost estimate before main (parent § 6):** recompute the full cost from the V4-T4 and pilot measurements, including validation and test at the new lengths, and add the 25% reserve. Hard-stop at the allocated limit, keeping missing cells rather than exceeding it.
- **Devices:**
  - only idle GPUs (no compute process) on skampere1 devices 0, 5 and 7;
  - idle GPUs on skampere2 or skampere3, if the v4 device guard (new, hash-bound code) admits them;
  - never a GPU another user or experiment occupies.
- **Before launch:** check experiment 120's GPU use. Run the v4 auto-resume watchdog from day one, using the pattern of `expt_v3/phase2/autoresume_watchdog.py`.
- **Timing:** start after v3-A7's six `result_30.json`, or after B_1301's `T5_30.json` FAIL, whichever comes first. Never take GPUs from running v3-A7 trajectories.
- **Admission:** this protocol, its implementation, tests and the A6 count reducer are bound in a v4 admission record, which is pushed before the first v4 generation.

## 6. What v4 does not claim

- No IRT-guided result.
- No official SCSC or FSC.
- No reward-hacking safety.
- No control by P beyond the start policy's marginal reward density.
- Results are scoped to the 4B SFT start, this filtered sampler and these budgets.
- No pooling with v2 or v3-A7.
