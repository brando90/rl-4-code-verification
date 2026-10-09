# Design review of experiments 10 and 11 (AlphaHebe promotion and feedback with a per-item factor matrix)

**TLDR:** You are a skeptical senior reviewer. Read the experiment 10 and 11 drafts, the 10-08-2026 meeting record, experiment 07's results and the relevant AlphaHebe source. Then write **one** review file with numbered findings and concrete fixes, plus your recommended picks for the open design choices. Read-only everywhere else: do not edit other files, commit, push, call model APIs or compute any statistic on the real experiment 07 data.

## Context

- **Project:** `rl-4-code-verification` (Brando Miranda, Stanford). Read `CLAUDE.md` first; its scientific-integrity rules are binding:
  - D-004: forecasts are frozen before outcomes are read.
  - Full-denominator reporting.
  - No agent-written direct provider API calls.
  - D-101 (self-hosted) and D-108 (Vals Valkyrie) for model calls.
  - D-013 (VeriBench split).
- **Worktree:** `/Users/brandomiranda/vb_worktrees/rl4cv-e10-review-codex` is a detached checkout of commit `769ade0` that you alone use.
- **The idea, from Brando's 10-08-2026 meeting with the AlphaApollo / AlphaDiana / AlphaHebe team:** AlphaDiana measures agent trajectories, AlphaHebe proposes and promotes edits, and Brando proposed using a per-item × per-factor score matrix (SCSC / SCS4C style) to guide that loop.
  - **Records:** `experiments/meetings/oct_7_2026/` (`oct_7_2026.md`, `transcription.md`, `self_improving_with_factored_decomposed_smooth_metric_meeting_pic.md`).
- **Documents under review:**
  - `experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/README.md` and `PROTOCOL.md` (DRAFT, not locked).
  - `experiments/11_hebe_gepa_factor_feedback_and_nonregression_gate_2x2_swebench_verified/README.md`.
- **Prior evidence:** `experiments/07_scs4c_vs_pass1_swebench_across_models/README.md` and `results.md`. H2 failed there: an aggregate smooth score did not rank systems better than pass@1 on held-out tasks. Experiments 06 and 09 (`results.md`) stalled on infrastructure.
- **AlphaHebe source:** read-only clone at `~/AlphaHebe-dev`, commit `f89294e`. Key files:
  - `alphahebe/control/promotion.py`
  - `alphahebe/evidence/{execution,search}.py`
  - `alphahebe/integrations/diana/search_feedback.py`
  - `alphahebe/methods/gepa/workflow.py`
  - `docs/integration.md`
  - The AlphaDiana-dev submodule is **not** readable. The public `~/AlphaDiana` (commit `ee39e42`) is the closest proxy; its `docs/` and `alphadiana/` describe the SWE-bench Verified path.
- **Data available to experiment 10:** `experiments/07_.../expt_v1/results/per_cell_e07.jsonl.gz`.
  - Size: 182 systems × 500 tasks.
  - Per-cell fields: `gate`, `t_fix`, `t_keep`, `resolved`, `included`, `common_cohort`.
  - Cohort: 164 included systems × 424 common tasks.
  - **Allowed:** inspect field names and counts, or run code on synthetic data.
  - **Forbidden:** computing any pair, split or gate statistic on the real data. That would read outcomes before the protocol lock.

## What to evaluate

1. **Is experiment 10 the right first test?** Does it attack the consequential uncertainty, and is a pair of different public systems a valid proxy for an AlphaHebe edit? What would make it more valid at the same zero-call cost?
2. **Statistical validity of PROTOCOL.md:**
   - selection on S (the P_near band, conditioning on Δpass1_S > 0, regression to the mean);
   - confounds in H2: hidden factor mass may simply track a weaker candidate. Are the covariates right?
   - the matched-rate gate comparison;
   - the system-cluster bootstrap for dyadic pair data;
   - split counts;
   - the gate = 0 handling;
   - the TRM, HRM and KRM definitions;
   - the thresholds (20% relative reduction, AUC 0.65);
   - the H4 metadata labeling rule.
   - Say exactly what you would change.
3. **Experiment 11 design:**
   - benchmark choice (SWE-bench Verified now, VeriBench V1 later);
   - the 2×2 arms and what is held fixed;
   - split sizes 50/50/200;
   - seeds and budget;
   - leakage in the factor projection (hidden test identities, test contents);
   - technical gates T0–T6;
   - anything that repeats experiment 06 and 09's infrastructure failures.
4. **Feasibility against AlphaHebe's real code:**
   - Are the five proposed integration changes (scorer factor fields, `TrainingFeedback` factors, pluggable promotion gate, record export, self-hosted endpoint) correctly located and sufficient?
   - Is anything missing, such as `ExecutionEvidence` needing per-record factors for the promotion collector?
5. **Rule compliance and reporting:** anything that would violate the repository rules above, or the agents-config statistics format `x [lo, hi] p-val=…`.
6. **Your picks for the open choices:**
   - primary pair population (P_near versus P_all);
   - q;
   - H2 covariates;
   - the H3 threshold;
   - whether H4 stays;
   - the experiment 11 benchmark and split sizes;
   - whether the experiment 11 gate arm should be binary or factor before experiment 10 reports.

## Output

Write `/Users/brandomiranda/vb_worktrees/rl4cv-e10-review-codex/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/reviews/design_review_gpt6_astra_ultra_10-09-2026.md` (create the directory if needed) with:

- **Header:** `# Title`, then a `**Doc link:**` line pointing to `https://github.com/brando90/rl-4-code-verification/blob/main/<repo-relative path of experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/reviews/design_review_gpt6_astra_ultra_10-09-2026.md>`, then a `**TLDR:**`.
- **Reviewer:** your exact model and effort.
- **Findings:** numbered, each with severity (blocking / major / minor), the issue, evidence (file and line, or code), and a concrete fix.
- **Recommended picks:** a short section.
- **Closing line:** one sentence on whether experiment 10 is ready to lock after your fixes.

Keep it under about 2,500 words. Then stop.

TL;DR: Read-only design review of experiments 10 and 11. Write one review file at `/Users/brandomiranda/vb_worktrees/rl4cv-e10-review-codex/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/reviews/design_review_gpt6_astra_ultra_10-09-2026.md` with numbered, evidenced findings, fixes and picks, and touch nothing else.
