# Experiment 20: IRT ability-matched prompt selection for GRPO on Lean, strict vs smooth reward (Qwen3-1.7B SFT, VBV1, D-013)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/README.md>

**TLDR:** This is Azalia's test with IRT as the decomposition: does an item response theory (IRT) decision about which prompts GRPO trains on raise held-out validation strict pass@1 at an equal rollout cost? The comparisons are uniform sampling, a scalar pass-rate filter and DAPO-style dynamic sampling, crossed with strict versus smooth reward. Status: **RUNNING (10-21-2026).** Phase 0a calibration generation is running on Sherlock (array 48841018); the trainer smoke test is queued (job 48845232); [PROTOCOL.md](PROTOCOL.md) is a frozen draft (hypotheses, gates and statistics fixed before any Phase 0 outcome; lock after the pilot). Live numbers: [results.md](results.md).

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

## Goal, hypothesis and decision criterion

Azalia's test asks whether a decomposed measurement raises the preferred downstream metric rather than merely correlating with it. The decision here is which prompt groups GRPO trains on; the decomposition is a 2PL item model (difficulty, discrimination) plus the policy's latent ability. **H1 (primary):** arm C (IRT-online selection) beats arm A (uniform) by at least +1.5 points of D-013 validation strict pass@1 at update 48 with a paired task-bootstrap interval above 0 (threshold: Brando's design document; seed spread 0.56 points from experiment 08 expt_v16). **H3:** C against the scalar pass-rate filter S and DAPO E decides whether IRT adds anything beyond measuring pass rates. **H4:** the interaction (D − B) − (C − A) says whether a smooth reward substitutes for or adds to selection. Gates: G0 (the item model predicts the start policy's held-out active groups with AUC ≥ 0.70 and beats a Beta(1,1) baseline on log loss), the smoke test (≤ 1% log-probability mismatch), the pilot (A below 50% active groups, C at least 1.5× A). A NULL at any gate is a reported result. Full rules: [PROTOCOL.md](PROTOCOL.md).

## Structure

```
20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/
├── README.md                      this file
├── PROTOCOL.md                    frozen draft (hypotheses, arms, recipe, G0, statistics); locked after the pilot
├── results.md                     live ledger (status, findings, phase table, GPU-h against caps)
├── CKPT_e20.md                    dispatcher-facing checkpoint (phase boundaries)
├── CKPT_cc-rl4cv-e20-irt-prompt-selection.md   worker resume record (every event)
└── expt_v1/
    ├── cc.md                      the runbook
    ├── samplers_e20.py            Uniform / StaticFilter / DynamicDAPO / IRTOnline (+ EAP update)
    ├── loss_e20.py                GRPO objective, importance weights, truncated-support mismatch check
    ├── train_e20.py               the GRPO loop (TRL 1.16 colocated-vLLM helper, frozen v12 sampler, Lean rewards)
    ├── irt_e20.py                 count-based 2PL fits, grouped CV priors, gate G0, graded model, two-skill check
    ├── stats_e20.py               paired task-group bootstrap, sign-swap test, AUC, log loss, ECE
    ├── sherlock/                  everything that runs on Sherlock (pack builder, generation, D-109 scoring, partial credit, smoke jobs, push helper)
    ├── forecasts/                 frozen item parameters and forecasts (rl4cv.forecast), written before training
    └── results/                   committed tables, receipts, plots; E20_FINISHED.txt at the end
```

Unit tests: `tests/test_e20_samplers.py`, `tests/test_e20_loss.py`, `tests/test_e20_irt.py`, `tests/test_e20_stats.py` (in `make test`).

## Method

1. **Phase 0a (Sherlock GPU):** 539 D-013 train tasks × 8 samples of the start policy with the frozen v12 sampler (`sherlock/gen_e20.sh`, array `phase0_gen.sbatch`); the train pack is built by `sherlock/prepare_train_pack_e20.py` with experiment 08's pinned adapter and must reproduce all 135 frozen validation prompt hashes (it did: 135/135). Scoring with VeriBench's frozen scorer (59059a2, `--skip-tc`) through the D-109 logged entry (`sherlock/logged_scorer_e20.py`) and experiment 13's declaration adapter for `factored_reward` (`sherlock/partial_credit_e20.py`), both as normal-partition CPU arrays. Per-cell table committed under `expt_v1/results/`.
2. **Phase 0b (CPU):** random-intercept and explanatory 2PL (experiment 19's task features), 1PL beside them; priors by grouped 5-fold cell-level cross-validation; gate G0; graded model on the smooth reward; descriptive dimensionality check; item parameters and forecasts frozen with `rl4cv.forecast.freeze_forecast`.
3. **Smoke (GPU):** 2 updates of arm A; gate on the vLLM-versus-trainer log-probability mismatch (≤ 1% of tokens with |Δ| > 0.05 on the recomputed sampling support).
4. **Pilot (GPU):** A, C, S, seed 1, 16 updates; stop rules in PROTOCOL §6; otherwise lock the protocol.
5. **Main (GPU):** 6 arms × 2 seeds × 48 updates × 16 groups × 8 rollouts; checkpoints at 16/32/48; the pilot's runs continue as the first 16 updates of their main runs.
6. **Evaluation (GPU):** validation 135 × 8 at updates 0, 16, 32, 48 with the frozen v12 evaluation; paired task-group bootstraps (10,000 draws) for H1–H4. Test stays unopened.

## Dependencies

- Experiment 08: v4 seed-20260831 1.7B Lean SFT weights on Sherlock, the v6 pinned task adapter, the v3 frozen validation prompt hashes, the v12 sampler, expt_v16's Sherlock validation of the start policy (58/1080) and the D-109 logging code (expt_v24).
- Experiment 19: `irt_e19.py`, `features_e19.py`, `data_e19.py`, `results/task_features_e19.csv`.
- Experiment 13: `src/rl4cv/e13.py` (`factored_reward`), `expt_v1/declaration_adapter.py`, `DeclarationProbe.lean` (verbatim copies in `expt_v1/sherlock/`, hashes in `VERBATIM_COPIES.sha256`).
- Experiment 12: the 11-system panel (`expt_v1/results/input_manifest.json`).
- Sherlock: private runner (`sherlockctl`), grading project (Lean v4.22.0, Mathlib 79e94a09), vLLM 0.30.0 Apptainer image with a TRL 1.16.0 venv overlay. No API keys.

## Status

| Step | Status | Notes |
|------|--------|-------|
| Setup, branch, checkpoints, protocol draft | Done (10-21-2026) | branch `e20-irt-prompt-selection`; PROTOCOL.md frozen draft |
| Phase 0a generation (539 × 8) | In Progress | Sherlock array 48841018 (4 chunks, L40S/H100) |
| Phase 0a scoring + partial credit | TODO | arrays `phase0_score.sbatch`, `phase0_partial.sbatch`; scoring smoke passed (3/3 trials equal to expt_v16) |
| Phase 0b IRT fit, gate G0, forecasts frozen | TODO | `irt_e20.py`, driver to follow |
| Trainer smoke test | In Progress | Sherlock job 48845232 |
| Pilot (A, C, S seed 1, 16 updates) | TODO | |
| Main (6 arms × 2 seeds × 48 updates) | TODO | |
| Validation evaluation, statistics, plots | TODO | |

## Sources used for the method (what was actually opened)

- Truong and Koyejo, *AI Measurement Science* (updated 09-07-2026), chapters 3, 4, 6, 7, 8, 9 and 10 at `https://aims.stanford.edu/textbook/` (the `aimslab` address in the runbook redirects there). The section-to-choice mapping is in PROTOCOL.md "Sources opened"; note that factor models and dimensionality are chapter 7 (§7.1, §7.2) and amortized models chapter 8 (§8.1) in the current book.
- CS321M Lectures 2, 3, 4 and 5 (slide PDFs opened and text-extracted). Discussion notebooks were not opened (no browser on this host).
- Design history: Brando's Google Doc "IRT for RL on Lean code verification: literature, Experiment 20, ready-to-run prompt" (not opened; the runbook reproduces its design).
- Literature cited by the design document (not re-read in this session): Truong et al., ICML 2025 (arXiv 2503.13335); Item Response Scaling Laws (2606.07616); Lalor and Yu, DDaCLAE (2011.00080); Foster and Foerster (2502.12272); Bae et al. (2504.03380); DAPO (2503.14476); AdaRFT (2504.05520); CDAS (2505.17652); ThinkPrior (2609.09075).

## Files

- [expt_v1/cc.md](expt_v1/cc.md): the runbook (prompt).
- [PROTOCOL.md](PROTOCOL.md): frozen draft before any Phase 0 outcome; locked after the pilot.
- [results.md](results.md): the live results ledger.
- [CKPT_e20.md](CKPT_e20.md): dispatcher-facing checkpoint; [CKPT_cc-rl4cv-e20-irt-prompt-selection.md](CKPT_cc-rl4cv-e20-irt-prompt-selection.md): the worker's resume record.

## Related

- [Experiment 19](../19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013/results.md), the offline precondition. IRT picks a start policy's learnable prompts at AUC 0.862 (not IRT-specific; task features 0.954), and a selected pool roughly triples learnable groups per update.
- Experiment 13 (smooth versus strict reward on the 4B start policy; its IRT arm C was dropped): an A-sel prompt-selection arm was proposed there and not adopted.
