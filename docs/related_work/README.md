# AlphaApollo and AlphaDiana: Zhanke (Andrew) Zhou's agent systems

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/docs/related_work/README.md>

**TLDR:** AlphaApollo and AlphaDiana are agent systems from Zhanke ("Andrew") Zhou's TMLR Group at Hong Kong Baptist University, and Brando co-authored both. AlphaApollo *solves*: it runs a model with tools, applies turn-level RL and refines answers in a propose–judge–update loop. AlphaDiana *measures*: it runs one benchmark across swappable models and harnesses and records full traces. A planned third system, Hebe, would *improve* Apollo from Diana's measurements. This repository's factorized smooth scores (SCSC, also called SCS4CV, and SCS4C) are Brando's proposal for the signal that tells Hippie what to fix.

Sources checked on 10-08-2026. Zhou's homepage is <https://andrewzhou924.github.io/>.

## AlphaApollo: solve

- **Paper:** "AlphaApollo: A System for Deep Agentic Reasoning", technical report, [arXiv:2510.06261](https://arxiv.org/abs/2510.06261) v2 (03-10-2026). Local copy: [alphaapollo_arxiv_2510.06261v2.pdf](alphaapollo_arxiv_2510.06261v2.pdf), 46 pages, sha256 `33ec2f6a…3c72`.
- **Code:** [tmlr-group/AlphaApollo](https://github.com/tmlr-group/AlphaApollo) (latest release v0.2.0, 08-21-2026) · website <https://alphaapollo.org/>.
- **Three components** (paper § 2):
  - **Multi-turn agentic reasoning.** Each turn the model emits a tool call or an answer; the environment runs the tool (Python, retrieval) and returns feedback; the history is the working memory.
  - **Multi-turn agentic learning.** SFT and turn-level RL (turn-level GRPO on VeRL) optimize only model-generated tokens, decoupled from tool responses for stable training.
  - **Multi-round agentic evolution.** A propose–judge–update loop with four roles (Solver, Abstractor, Evaluator, Summarizer) and long-term memory that retrieves the top-K entries, favoring correct and then shorter solutions. Parallel solvers, including proprietary APIs, share that memory.
- **Reported results** (math only: AIME24, AIME25, CMIMC, HMMT Feb and Nov, BRUMO, SMT; Qwen2.5-Instruct 1.5B–14B; Avg@32 from the abstract): over 85% tool-call success; multi-turn RL 1.07% → 9.64% (1.5B) and 8.77% → 20.35% (7B); evolution 16.53% → 21.08% (14B).

## AlphaDiana: measure

- **Paper:** "Reasoning Is More Than the Model: Harness-Aware Evaluation of Agents on Verifiable Reasoning Tasks" (Zhou et al., 2026), at ICML 2026 workshops ([OpenReview 4vARlk9o95](https://openreview.net/forum?id=4vARlk9o95), [fnHhEf0cSE](https://openreview.net/forum?id=fnHhEf0cSE); [ICML page](https://icml.cc/virtual/2026/74812)). The homepage lists it as "AlphaDiana: A System for Evaluating Reasoning Agents".
- **PDF: not in this repository (unresolved).** On 10-08-2026 OpenReview returned only its "Verifying your browser" check to curl and to headless Chrome, and there is no arXiv or Google Drive copy. Brando can download it while signed in to OpenReview and save it here.
- **What this summary uses instead:** the ICML abstract plus the [GitHub repository](https://github.com/tmlr-group/AlphaDiana) README and `docs/concepts/` at commit `ee39e42` (08-12-2026; no tagged release).
- **What it does.** It treats the harness as a first-class variable. A run is one benchmark × one model endpoint × one harness, and the system standardizes models, harnesses, benchmarks, execution environments, scorers, budgets and trajectory logging.
  - Harnesses: DirectLLM (the no-scaffold baseline), OpenClaw, OpenCode and ZeroClaw.
  - Benchmarks: AIME 2026, GPQA-Diamond, HLE, IMO-AnswerBench, MMMU-Pro, SWE-bench Verified, Terminal-Bench 2 and custom tasks.
  - Sandboxed execution (ROCK), full traces, a dashboard and a command-line interface (`alphadiana validate | run | report`).
- **Concepts worth reusing:**
  - **Agent scaffold tax:** a harnessed cell scoring below the matched DirectLLM cell (same model, same protocol).
  - **Macro versus micro:** macro runs compare direct inference with agentic execution; micro runs ablate harness capabilities along three axes (Tool, Skill, Memory). A micro delta is an association with the whole changed condition bundle, not a causal effect of one capability.
  - **Failure attribution:** each trajectory's success or failure is attributed to reasoning, tool use, execution, state, budget, recovery or verification. These are semantic labels, not numeric factors.
  - **Reporting:** Pass@k and Avg@k with the configured sample count; compare only rows with the same runtime and evaluation contract.

## Hebe: improve (in development)

Code: private [`AndrewZhou924/AlphaHebe-dev`](https://github.com/AndrewZhou924/AlphaHebe-dev) (Brando has push and triage access; checked at `f89294e`, 09-18-2026). It optimizes agent artifacts (prompts, workflows, harness source) with bounded mutation, keeps search feedback separate from an independent held-out promotion check, and records every version; it runs AlphaDiana-dev as a pinned submodule (`3bdbb66`) and uses AlphaApollo-v3-dev only for optional SFT/GRPO. Today it promotes on any scalar improvement (`control/promotion.py`) and gives optimizers one score per task (`integrations/diana/search_feedback.py`). Source: the [10-08-2026 meeting](../../experiments/meetings/oct_7_2026/oct_7_2026.md). The [whiteboard photo](../../experiments/meetings/oct_7_2026/self_improving_with_factored_decomposed_smooth_metric_meeting_pic.jpeg) writes the improver as "f_Hebe" (an improver model, Qwen3.6 30B A3B); Fathom transcribed the name as "Alpha Hippie" and "Hibi".

- **Loop:** Apollo produces trajectories, Diana measures them, and Hebe edits either the model (post-training, for example Brando's coauthored [CoDaPO](https://arxiv.org/abs/2606.07950), ICML 2026) or the harness code.
- **Open problems raised:**
  - Localizing an error to the model or to the harness.
  - Regressions: an edit that fixes some tasks breaks others.
- **Brando's proposals:**
  - A task × factor matrix of factorized scores, so the weakest factor shows where to act.
  - Accept an edit only if no task or factor regresses (a greedy monotone acceptance policy).
  - Validate on a verifiable benchmark (SWE-bench) before automating.

## Where this repository tests the idea

| Question | Experiment |
|---|---|
| Does a factorized smooth score track the downstream metric (pass@1) across systems, and does its partial credit carry extra signal? | [07_scs4c_vs_pass1_swebench_across_models](../../experiments/07_scs4c_vs_pass1_swebench_across_models/README.md) (phase A: public SWE-bench Verified logs; phases B–C: a gold-patch differential factor on SWE-Bench Pro Verified and SCS4C as an RL reward) |
| Does decomposed feedback improve real issue resolution at a fixed repair budget? | [06_swebench_lite_factor_feedback_matched_budget](../../experiments/06_swebench_lite_factor_feedback_matched_budget/README.md) |
| With zero model calls, does a per-item factor matrix predict held-out regressions beyond pass/fail, and does a factor-matrix promotion gate beat AlphaHebe's scalar gate? | [10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs](../../experiments/10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/README.md) |
| In the live AlphaHebe loop, do factor feedback and a non-regression gate improve the self-improved harness (2×2)? | [11_hebe_gepa_factor_feedback_and_nonregression_gate_2x2_swebench_verified](../../experiments/11_hebe_gepa_factor_feedback_and_nonregression_gate_2x2_swebench_verified/README.md) |
| Does access to VeriBench's three SCSC factors improve repair or training decisions? | [04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2](../../experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/README.md) |

How the vocabularies line up:

- **Our factors are the numbers Diana lacks.** SCSC's IC_tests, IC_proofs and FSC, and SCS4C's T_fix, T_keep and D_gold, are numeric and defined by the task. Diana's failure categories are labels.
- **Our verifier is Apollo's Evaluator.** The Lean kernel or the tests play the role of Apollo's tool-assisted Evaluator.
- **Diana could supply logs for experiment 07.** Its SWE-bench Verified harness runs could feed an SCS4C analysis across harnesses, not only across models.

## Rules when using them here

- **Model calls.** Both quick starts call model providers with keys in `.env` (AlphaDiana's example uses OpenRouter). In this repository, measured generation and judging go through Vals Valkyrie when Brando runs the work (D-108) or through self-hosted open-weight inference (D-101). Never place a provider key in `.env` here (agents-config Hard Rule 9).
- **Pins.** If a run clones either system, pin the commit in `external/deps.lock.json` (D-002).
- **VeriBench split.** Training on VeriBench tasks follows the train / validation / test split (D-013).
