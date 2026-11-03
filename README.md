# rl-4-code-verification

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/README.md>

**TLDR:** This project tests whether the ρ–H environment-utility law generalizes from math to RL for Lean 4 code verification, and uses it to pick the environments and rewards that most improve VeriBench. The law comes from Varun and Brando's ICLR 2027 submission: before RL, it measures usable signal density ρ and effective coverage H under the starting policy, and from them predicts held-out RL gains across model scale. The measurement and prediction code is implemented and tested (it reproduces the paper's 14B numbers exactly). Five gated experiments are designed, starting with the first-ever VeriBench numbers for small open Qwen models.

**Creating training data? Start with the [VeriBench data format guide and complete Python/Lean examples](docs/veribench_data_format/README.md).** It explains the required sections, meaningful proved properties, validation commands, and training-data eligibility; the original example archive is included.

## The question

The paper shows, in math, that the held-out utility of an RL prompt distribution can be forecast before training. It fits a five-coefficient model at 1.7B–8B, and that model predicted untouched 14B curves at 2.29-point RMSE.

The crux here is whether the same forecast works in a structurally different domain:

- **Verifier:** the Lean kernel.
- **Responses:** long structured files containing implementation, tests, specifications and proofs.
- **Target:** VeriBench's conjunctive SCSC score, whose least saturated factor, formal specification coverage (FSC), is judged by an LLM.

Details: [docs/PLAN.md](docs/PLAN.md).

## What we already know

([docs/FACTS_veribench_baselines.md](docs/FACTS_veribench_baselines.md))

- **Small models give essentially zero RL signal without an SFT warm start (updated 10-09-2026).** Experiment [`05`](experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/results.md) measured Qwen3-1.7B/4B/8B-Base at G=8 on all 896 VeriBench V1 tasks (done 10-05/06-2026): `kernel_binary` mixed-group share is 0.000 (1.7B, the decider), 0.006 (4B) and 0.000 (8B), all far below the 0.05 "RL from Base viable" threshold — **SFT warm start needed** at every measured size. The smallest Qwen solver run before that (Qwen3.6-27B) scored SCSC 0.002, because almost none of its output compiled.
- **Version names.** VBV1 is the original VeriBench (896 tasks), VBV2 the private VeriSoftBench-derived tasks, and VBV3 VeriBench-Infinity (`brando90/veribench-inf`); the full glossary is in `CLAUDE.md`.
- **Frontier agents are nearly saturated on the kernel factors.** They score IC_tests and IC_proofs of about 0.98–1.0 on VeriBench V1. FSC is their lowest factor (0.90–0.96 raw, lower on VBV2).
- **The FSC judge is lenient.** It is lenient on partial coverage, and it scores files that do not compile. FSC is therefore always gated on compilation here.

## Repository map

| Path | Content |
|---|---|
| [`docs/PLAN.md`](docs/PLAN.md) | The full plan: hypotheses (levels L1–L5), environment families, reward channels, held-out panels, gates, compute, risks |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Decision log, including the open decisions only Brando can make (D-101 to D-107) |
| [`docs/FACTS_veribench_baselines.md`](docs/FACTS_veribench_baselines.md) | Sourced VeriBench numbers: small-model gap, saturation, judge facts and cost |
| [`docs/DATASETS.md`](docs/DATASETS.md) | Candidate pools (FVAPPS, Vericoding, VERINA, synthetic) and contamination screens |
| [`docs/veribench_data_format/`](docs/veribench_data_format/README.md) | Contributor guide, browsable Python/Lean example pair, original archive, provenance, and validation receipt |
| [`docs/SMOOTH_TO_HARSH.md`](docs/SMOOTH_TO_HARSH.md) | Project line: Azalia's suggestion that the smooth score should improve the harsh score. Source email, what experiments 04 to 24 already did, state, first-step sketch |
| [`docs/meeting_notes/`](docs/meeting_notes/README.md) | Summaries plus the verbatim meeting notes |
| [`docs/related_work/`](docs/related_work/README.md) | AlphaApollo and AlphaDiana (Zhanke Zhou's agent systems): summary, AlphaApollo PDF, links to our factorized-metric experiments |
| [`experiments/`](experiments/README.md) | Three experiments for Brando's two goals (D-007): 01 the shared baseline (running), 02 Varun's question (ρ–H-guided Lean environment design, phases 02A–02D), 03 Allen's coverage question; plus deferred ideas. Each has a design README, and 01 has a locked protocol, run script and agent prompt |
| [`src/rl4cv/`](src/rl4cv/__init__.py) | `experience` (ρ, H), `utility_model` (Eq. 7, LOSO, baselines), `forecast` (hash-frozen forecasts), `cells` (2×2 construction), `rewards` (reward channels), `screens` (contamination), `probe`, `veribench/` (experiment 103 prompt reuse, vLLM generation, scorer jobs, collection) |
| [`tests/`](tests/) | 33 tests, including an exact reproduction of the paper's frozen 14B forecast scores |
| [`external/deps.lock.json`](external/deps.lock.json) | Pinned commits of VeriBench, its frozen scorer, and the rl-env-scaling fork |

## Quick start

```bash
git clone https://github.com/brando90/rl-4-code-verification.git && cd rl-4-code-verification
make external          # pinned clones of veribench, the frozen scorer, rl-env-scaling (no submodules; see docs/DECISIONS.md D-002)
pip install -e ".[dev]" && make test
```

Running experiment 01 needs a GPU host with vLLM (`pip install -e ".[gen]"`); follow [its agent prompt](experiments/01_small_open_models_veribench_v1_single_call_baseline/expt_v1/cc.md).

## Relationship to other repositories

- **[VeriBench](https://github.com/brando90/veribench)** (private) is the target benchmark and a pinned dependency. Any VeriBench number reported here follows VeriBench's evaluation rules (see [CLAUDE.md](CLAUDE.md)).
- **[rl-env-scaling](https://github.com/brando90/rl-env-scaling)** is Brando's fork of the paper's workspace. It is still the 08-12-2026 planning snapshot, so the paper's code and NeMo RL configs arrive only after the fork is synced with upstream `madanva/rl-env-scaling` (decision D-105).

## License

Apache-2.0 ([LICENSE](LICENSE)).
