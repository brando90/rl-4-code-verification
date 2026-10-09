# Fathom AI summary: Apollo–Diana–Hebe self-improvement loop call (10-08-2026)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/meetings/oct_7_2026/summary.md>

**TLDR:** Fathom's own AI summary of the meeting, verbatim. It covers the proposed Apollo → Diana → Hebe loop (Fathom: "Alpha Hippie"), Brando's factorized geometric-mean metric for localizing errors, and accepting only edits that regress no task. It is Fathom's paraphrase; the [transcript](transcription.md) is the primary record.

- **Verbatim check:** 5603 bytes, sha256 `d5a5941ebf65902f8c8b7ba69a77313350d320f904e7575fd48bc81c72864483`.

Everything between the `BEGIN` and `END` markers is Fathom's output exactly as the connector returned it, written to disk by a script rather than retyped; nothing was corrected or reformatted.

<!-- BEGIN VERBATIM FATHOM OUTPUT: get_meeting_summary(recording_id=191183027), retrieved 10-08-2026 -->
## Meeting Purpose

[Discussing the Apollo-Diana-Alpha Hippie self-improvement loop.](https://fathom.video/calls/855071170?tab=summary&timestamp=104.0)

## Key Takeaways

  - [**The Loop:** A self-improvement loop is proposed: Apollo (agent) generates trajectories → Diana (measurement) analyzes them → Alpha Hippie (optimizer) applies targeted fixes to Apollo's model or harness.](https://fathom.video/calls/855071170?tab=summary&timestamp=104.0)
  - [**Factorized Metrics:** Brando proposed a factorized metric (e.g., geometric mean of sub-scores) to replace pass/fail. This provides granular feedback for targeted optimization, solving the problem of uninterpretable aggregate scores.](https://fathom.video/calls/855071170?tab=summary&timestamp=395.0)
  - [**Critical Challenges:** Two core challenges were identified: 1) reliably localizing errors to the model vs. harness, and 2) preventing performance regression on previously solved tasks.](https://fathom.video/calls/855071170?tab=summary&timestamp=366.0)
  - [**Research Path:** The recommended strategy is to first validate the factorized metric on a simple, verifiable benchmark (e.g., SweBench), then automate its creation and integrate it into the loop.](https://fathom.video/calls/855071170?tab=summary&timestamp=1981.0)

## Topics

### The Apollo-Diana-Alpha Hippie Loop

  - [**Goal:** Create a recursive self-improvement loop to make Apollo more powerful.](https://fathom.video/calls/855071170?tab=summary&timestamp=104.0)
  - [**Components:**](https://fathom.video/calls/855071170?tab=summary&timestamp=104.0)
      - [**Apollo:** The problem-solving agent (e.g., using Qwen-3B).](https://fathom.video/calls/855071170?tab=summary&timestamp=1265.0)
      - [**Diana:** The measurement system, analyzing Apollo's trajectories for accuracy, efficiency, and failure modes.](https://fathom.video/calls/855071170?tab=summary&timestamp=301.0)
      - [**Alpha Hippie:** The optimizer, applying targeted improvements (e.g., post-training, harness edits) based on Diana's feedback.](https://fathom.video/calls/855071170?tab=summary&timestamp=171.0)

### Challenge 1: Localizing Errors

  - [**Problem:** Diana can identify *what* failed but not *why* (i.e., whether the model or harness is at fault). This prevents targeted, effective optimization.](https://fathom.video/calls/855071170?tab=summary&timestamp=366.0)
  - [**Proposed Solution: Factorized Metrics**](https://fathom.video/calls/855071170?tab=summary&timestamp=395.0)
      - [**Method:** Decompose a single pass/fail metric into a set of interpretable sub-scores (e.g., `compiles`, `passes_tests`, `has_docstring`).](https://fathom.video/calls/855071170?tab=summary&timestamp=545.0)
      - [**Aggregation:** Combine sub-scores using a geometric mean to create a smooth, differentiable proxy for the overall goal.](https://fathom.video/calls/855071170?tab=summary&timestamp=695.0)
      - [**Benefit:** Provides granular feedback, enabling targeted optimization of the weakest component.](https://fathom.video/calls/855071170?tab=summary&timestamp=772.0)
      - [**Validation:** Initial experiments on SweBench and VeriBench show the factorized metric correlates with the downstream pass@k metric.](https://fathom.video/calls/855071170?tab=summary&timestamp=2798.0)

### Challenge 2: Preventing Regression

  - [**Problem:** Harness modifications for one task often cause performance regression on others, preventing monotonic improvement.](https://fathom.video/calls/855071170?tab=summary&timestamp=3472.0)
  - [**Proposed Solution: A Monotonic Acceptance Policy**](https://fathom.video/calls/855071170?tab=summary&timestamp=4191.0)
      - [**Method:** Use the factorized metric to analyze the impact of a proposed edit on *all* tasks.](https://fathom.video/calls/855071170?tab=summary&timestamp=3965.0)
      - [**Policy:** Accept an edit only if it improves the target task *without* degrading performance on any other task.](https://fathom.video/calls/855071170?tab=summary&timestamp=4191.0)
      - [**Benefit:** Ensures monotonic, surgical improvements, avoiding the "catastrophic forgetting" problem.](https://fathom.video/calls/855071170?tab=summary&timestamp=4191.0)

### Research Strategy & Next Steps

  - [**Recommendation:** Validate the core idea on a simple, verifiable benchmark (e.g., SweBench) before automating the full loop.](https://fathom.video/calls/855071170?tab=summary&timestamp=1981.0)
  - [**Rationale:** This approach isolates variables, making it easier to diagnose failures and confirm the factorized metric's effectiveness.](https://fathom.video/calls/855071170?tab=summary&timestamp=1981.0)
  - [**Future Work:**](https://fathom.video/calls/855071170?tab=summary&timestamp=3666.0)
      - [Automate factorized metric creation (e.g., using IRT models).](https://fathom.video/calls/855071170?tab=summary&timestamp=832.0)
      - [Formalize the monotonic acceptance policy.](https://fathom.video/calls/855071170?tab=summary&timestamp=4191.0)
      - [Investigate scaling laws for model vs. harness complexity.](https://fathom.video/calls/855071170?tab=summary&timestamp=3722.0)

## Next Steps

  - [**Brando:** Add the team to the "RL for code verification" GitHub repo.](https://fathom.video/calls/855071170?tab=summary&timestamp=2906.0)
  - [**Team:** Review the repo and experiment with the factorized metric concept.](https://fathom.video/calls/855071170?tab=summary&timestamp=2906.0)
  - [**Team:** Discuss the factorized metric and regression issues with Varun and Alan.](https://fathom.video/calls/855071170?tab=summary&timestamp=3607.0)

<!-- END VERBATIM FATHOM OUTPUT -->
