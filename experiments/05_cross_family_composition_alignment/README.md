# Experiment 05 — cross-family composition and target alignment (beyond the paper's boundary)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/05_cross_family_composition_alignment/README.md>

**TLDR:** This extends the model where the paper failed. The paper's frozen uniform mixture was predicted last yet gained +1.4 to +4.6 points. Here we train on single families (`full`, `impl`, `spec`, `proof`, `math`) and their mixtures, add alignment and composition coordinates, and test prospectively whether they predict which mixture most improves VeriBench.

## Goal, hypothesis and decision criterion

- **Motivation.** Solving VeriBench probably needs several skills at once (implementation, specification, proof). Its candidate environments also come from different sources than VeriBench, which the paper's within-source design never faced.
- **Hypothesis.** Adding (a) an alignment coordinate α(E, VeriBench) and (b) mixture-composition coordinates to Eq. 7 makes a frozen mixture forecast beat the uniform-portfolio and fixed-family rules.
  - Candidate α measures: the rl-env-scaling fork's embedding alignment score, or a starting-policy transfer probe (the loss change on panel prompts after a few gradient steps on E).
  - Candidate composition coordinates: component ρ and H and component weights.
- **Decision.** A positive result is the natural second paper. A negative result bounds the claim to within-family allocation.

## Method

1. **Families at 1.7B and 4B.** Train on single families and on three frozen mixtures (uniform, proof-heavy, spec-heavy), each drawn with an outcome-blind hash rule as in the paper.
2. **Measure before RL.** ρ, H and α for every family and mixture.
3. **Forecast before training.** Fit the extended model on the single families and freeze the mixture forecasts (`rl4cv.forecast`) before any mixture is trained.
4. **Outcomes.** VeriBench V1 SCSC and its factors, the within-source panel, plus a regression panel for unintended effects (meeting notes B): the paper's OpenR1 math panel and a general code benchmark.

## Status

| Step | Status |
|---|---|
| Design | Done (09-30-2026) |
| Everything else | TODO, after experiments 03 and 04 |
