# Review experiment 10 protocol revision 2 and its analysis code before the lock

**TLDR:** You are a skeptical reviewer of a locked-to-be statistical replay. Check that `PROTOCOL.md` (revision 2) is sound and that `expt_v1/analyze_e10.py` implements it exactly. Write one review file with numbered, evidenced findings and concrete fixes.

## Scope

You may run code on synthetic data (`expt_v1/synthetic_e10.py write ...`) and the unit tests (`tests/test_e10_replay.py`).

Do not edit any other file, commit, push or call model APIs, and do not compute any statistic on the real experiment 07 data. That would read outcomes before the lock (D-004 in `CLAUDE.md`).

## Context

- **Worktree:** `/Users/brandomiranda/vb_worktrees/rl4cv-e10-review-fable-v2`, commit `94cb414`, yours alone.
- **Experiment:** `experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/`. Read `README.md`, `PROTOCOL.md` (revision 2), `results.md` and `reviews/design_review_gpt6_astra_ultra_10-09-2026.md` (the 15 findings revision 2 claims to address).
- **Code:**
  - `expt_v1/analyze_e10.py`
  - `expt_v1/synthetic_e10.py`
  - `tests/test_e10_replay.py`
  - Run with `/private/tmp/claude-501/-Users-brandomiranda-rl-4-code-verification/bbba4177-5a6e-45eb-8b64-05225e885ec0/scratchpad/e10syn/venv/bin/python` (numpy), or `uv run --isolated --no-project --python 3.12 --with numpy --with pytest python -m pytest -q tests/test_e10_replay.py`.
- **Data the code will read at the lock:** `experiments/07_.../expt_v1/results/per_cell_e07.jsonl.gz`. Field names only, no statistics.

## Check, in priority order

1. **Code ↔ protocol fidelity:**
   - the stratified selection (R0–R3h): equal validation-gain distribution per stratum, weighted prefix rule, hash ties;
   - the unstratified comparators;
   - the paired contrasts and their signs;
   - the utility guard inputs;
   - the H2 partial correlation (average ranks, covariates, conditioning, undefined handling);
   - the endpoint-disjoint predictive comparison;
   - the dyadic bootstrap weights (m_i·m_j over distinct original systems, the same splits);
   - the estimand as a split average with percentile intervals;
   - degenerate-split handling and the P_pos identity-only weights;
   - the drift sensitivity.
2. **Correctness bugs:** off-by-one in net-gain strata (1..10 at |V| = 212), float precision, NaN propagation, a silent empty selection, memory/time at 164 systems × 1,000 splits × 1,000 draws.
3. **Whether the verdict rules can be met** with the data size (power), and anything that would make a positive result misleading.
4. **Whether revision 2 truly resolves** the GPT-6 blocking findings 1, 7, 10, 11 (10 and 11 concern experiment 11 and the issues; just say whether the protocol text is consistent).

## Output

Write `/Users/brandomiranda/vb_worktrees/rl4cv-e10-review-fable-v2/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/reviews/review_claude_fable_5_1_protocol_r2_and_code_10-09-2026.md`:

- **Header:** `# Title`, then `**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/reviews/review_claude_fable_5_1_protocol_r2_and_code_10-09-2026.md>`, then `**TLDR:**`.
- **Reviewer:** your exact model, effort and account profile.
- **Findings:** numbered, each with severity (blocking / major / minor), file and line evidence, and a concrete fix (a code diff where possible).
- **Closing line:** whether it is safe to lock after the fixes.

Keep it under about 2,000 words, then stop.

TL;DR: Read-only review of experiment 10's revision-2 protocol and analysis code. Write one findings file with evidence and fixes, and touch nothing else.
