# Experiment 20: IRT ability-matched prompt selection for GRPO on Lean, strict vs smooth reward (Qwen3-1.7B SFT, VBV1, D-013)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/README.md>

**TLDR:** This is Azalia's test with IRT as the decomposition: does an item response theory (IRT) decision about which prompts GRPO trains on raise held-out validation strict pass@1 at an equal rollout cost? The comparisons are uniform sampling, a scalar pass-rate filter and DAPO-style dynamic sampling, crossed with strict versus smooth reward. Status: **DISPATCHING 10-21-2026.** The worker runs Phase 0 calibration first; GPUs are on Sherlock and API spend is $0.

| Field | Value |
|---|---|
| Trigger | Brando, 10-21-2026: "let's use them [Sang Truong's textbook and lecture recommendations] to make an excellent prompt and test if the azalia idea works for IRT" |
| Design source | Brando's Google Doc "IRT for RL on Lean code verification: literature, Experiment 20, ready-to-run prompt" (10-20-2026); revised into [expt_v1/cc.md](expt_v1/cc.md), adding Sang's textbook (*AI Measurement Science*, chapters 3, 4, 6, 8, 9, 10), CS321M Lectures 2–5 and experiment 19's results |
| Question (Azalia, rl4cv D-008) | Does the decomposition-guided decision (IRT-online prompt selection, arm C) beat uniform (A), the scalar pass-rate filter (S) and DAPO (E) on held-out strict pass@1 at matched rollouts? Is a smooth reward (B, D) a substitute for it, or does it add to it? |
| Primary hypothesis (H1) | C − A ≥ +1.5 points of validation strict pass@1 at update 48, with a 95% paired task-bootstrap interval above 0 (2 seeds) |
| Start policy | Qwen3-1.7B-Base Lean SFT, experiment 08 v4 seed 20260831 (validation strict pass@1 about 5%) |
| Compute | Sherlock via the private runner (`sherlockctl`). Caps: Phase 0 10, pilot 15, main 130, evaluation 80; 200 GPU-h total, $0 API |
| Gates | G0: the item model predicts held-out active groups with AUC ≥ 0.70. Pilot: A has < 50% active groups, and C has ≥ 1.5× A's. Smoke test: ≤ 1% of tokens with log-probability mismatch > 0.05 |
| Owner | A Claude Code worker on SNAP `skampere1`, tmux `cc-rl4cv-e20-irt-prompt-selection`, dispatched by session `local_268be283` |

## Dispatch (model and effort, outside the prompt per agents-config Rule 36)

- **Worker:** Claude Code `claude-fable-5-1` at `max` effort, profile `cc` (the `clauded` wrapper, personal `~/.claude` config) on `skampere1`, full access (bypass permissions on); deployment `deploy_ed87a5b1900b45d2af6e22c1707cc31e`.
- **Why this model:** the work is design-heavy: GRPO on Sherlock in Apptainer, the Lean grader inside the reward, an IRT fit and gates. It needs the strongest model, not a regular execution worker.
- **Fallback:** Codex `gpt-6-astra` at `ultra` (personal `~/.codex` on `skampere1`, full access verified there on 10-12-2026).

## Files

- [expt_v1/cc.md](expt_v1/cc.md): the runbook (prompt).
- `PROTOCOL.md`: written and frozen by the worker before any training.
- [results.md](results.md): the live results ledger.
- [CKPT_e20.md](CKPT_e20.md): the resume record.

## Related

- [Experiment 19](../19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013/results.md), the offline precondition. IRT picks a start policy's learnable prompts at AUC 0.862 (not IRT-specific; task features 0.954), and a selected pool roughly triples learnable groups per update.
- Experiment 13 (smooth versus strict reward on the 4B start policy; its IRT arm C was dropped): an A-sel prompt-selection arm was proposed there and not adopted.
