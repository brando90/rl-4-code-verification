# Experiment 19: interpretable IRT for SCSC factors, explain/predict and guide strict pass@1 (VBV1, D-013, zero model calls)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013/README.md>

**TLDR:** The IRT (item response theory) half of the "does the decomposed metric guide the harsh metric?" question, run offline with existing data. (1) On the 11 unsealed VeriBench V1 systems, do IRT models of the SCSC factors, with task content as explanatory variables, predict held-out strict success (rl4cv 13's kernel strict reward), harsh SCSC and VeriBench 111's strict gold-check pass@1 (what people want) better than simple baselines and the plain smooth score? (2) Before any RL, can an IRT forecast pick the prompts on which experiment 13's start policy gives mixed strict groups? That is the precondition for an IRT-selected prompt pool to raise strict pass@1, scored against experiment 13's own frozen AUC ≥ 0.70 gate. **Status: DONE 10-21-2026** ([results.md](results.md)). The IRT forecast finds experiment 13's mixed-group prompts with AUC 0.862 [0.792, 0.925], above the 0.70 gate, but no better than the panel pass rate; task features alone reach 0.954. IRT adds nothing over a simple additive model for held-out strict pass@1, and the smooth score forecasts held-out harsh and gold-check pass@1 worse than the raw rates. The pre-registration is [PROTOCOL.md](PROTOCOL.md), amended by [AMENDMENT_01](AMENDMENT_01_10-20-2026.md).

| Field | Value |
|---|---|
| Trigger | General coordinator, 10-20-2026, relaying Brando: "I really want the IRT and SCSC stuff to be running to see if they lead to downstream performance." Azalia Mirhoseini's steer: the decomposed metric should guide improvement of the downstream harsh metric, not just correlate with it. |
| Owner | Claude Code session `local_268be283` (rl4cv IRT lane); experiment 13 (SCSC RL) stays with its own owner |
| Cost | $0: zero model calls, zero GPUs, CPU only |
| Splits | D-013 train 539 / validation 135; the test split is never touched |
| Idea page | VeriBench `experiments/ideas/irt_latent_factors_for_scsc_vs_pass1_and_rl_guidance/README.md` (this folds in its Q3; Q1 was experiment 14, Q2 experiment 15) |

## Design in one table

| ID | Question | Data | Rule (from PROTOCOL.md) |
|---|---|---|---|
| E1 | Do IRT factor models predict a held-out system's validation strict, harsh and gold-check outcomes better than its train rate, a non-IRT additive model and the plain smooth score? | 11 systems × 674 tasks (VeriBench 102/103 via experiment 12; gold checks from VeriBench 111) | Paired log-loss and MAE differences with 95% task-group intervals above 0 |
| E2 | Which task features explain difficulty, and do they predict unseen tasks? | Same panel + content features from each task's Python and gold Lean | Validation new-task log loss with features beats without |
| E3 | Is FSC a second skill beside strict success? | Same panel; reference-consistency rows from VeriBench 111 | Two-skill model beats the tied one-skill model on held-out cells |
| G1 | Does an IRT forecast find the prompts where experiment 13's start policy gives mixed strict groups? | Panel + start policy's 135 × 8 validation outcomes at experiment 13 v4's sampler + its train A6 rate | AUC ≥ 0.70 (experiment 13's gate F2); "IRT-specific" needs a positive interval over two non-IRT heuristics |
| G2 | Would an IRT-weighted partial reward help? | None suitable exists | Recorded as untestable, with the cheapest test |
| G3 | Frozen per-prompt forecasts for experiment 13 v4's group-size batch | G1's model | Scored when experiment 13 publishes per-task counts |

## Files

- `PROTOCOL.md`: the pre-registration (definitions, rules, disclosures, numerical gates).
- `expt_v1/features_e19.py`: interpretable task features from the pinned VeriBench commit (train and validation tasks only).
- `expt_v1/data_e19.py`: hash-pinned loaders with test-split guards. `expt_v1/extract_rc_e19.py` copies experiment 111's reference-consistency rows for the 11 panel systems.
- `expt_v1/irt_e19.py`: the 2PL (random-intercept and explanatory), the graded response model and the two-skill model.
- `expt_v1/analyze_e19.py`: every analysis; `--synthetic N` runs it on generated data.
- `expt_v1/freeze_forecast_e19.py`: freezes this lane's predictions of its own outcomes before the real run (`expt_v1/forecasts/`).
- `tests/test_e19_irt.py`: gradients, recovery, guards, loaders and rules (in `make test`).

## Dependencies

- Experiment 12 (`expt_v1/results/input_manifest.json`), experiment 08 v1 (split and `sft_4B_f1p0` validation ladder), experiment 13 v2 (A6 receipt).
- VeriBench pinned commit c11b99b (task sources) and 07c4b48 (experiment 111 rows).
- Experiment 13 receives any proposal as a frozen document. Its v4 protocol is never edited here.
