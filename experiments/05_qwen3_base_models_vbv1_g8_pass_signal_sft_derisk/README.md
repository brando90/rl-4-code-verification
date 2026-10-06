# Experiment 05 — Qwen3 Base 1.7B/4B/8B on VeriBench V1 at G=8: is there an RL signal without an SFT warm start?

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/README.md>

**TLDR:** The 10-05-2026 team meeting asked whether RL can start directly from the Qwen3 Base checkpoints or needs a supervised fine-tuning (SFT) warm start first, as the environment-utility paper's math runs did. This experiment samples 8 answers (G=8) from Qwen3-1.7B-Base, Qwen3-4B-Base and Qwen3-8B-Base on all 896 VeriBench V1 (VBV1) tasks and counts, per task, how many of the 8 answers are fully verified Lean files. Group-relative RL (GRPO) only learns from tasks where some but not all of the 8 answers pass (a "mixed" group), so the share of mixed groups decides the question, with Qwen3-1.7B-Base as the deciding model. Status: see [results.md](results.md).

## Origin

- **Meeting:** [10-05-2026 notes](../meetings/oct_5_2026/oct_5_2026.md) and [transcript](../meetings/oct_5_2026/transcription.md), 19:51–21:47 (Varun Madan, Brando Miranda).
- **Varun:** "basically 1.7 is the most important because if it's too hard for 1.7, then we have to reevaluate. And basically what we want to do is, like, run 8 rollouts, right? G equals 8. And then see, does it pass, like, more than 0 out of 8 times? And, like, is it not 8 out of 8?"
- **Varun, on which checkpoint:** use Qwen3 **Base**, not the instruction-tuned release, because the post-trained sizes are post-trained in different ways and so are not a controlled scale series.
- **Action item:** "Share Qwen3 warm-start weights with Brando; then Brando runs 8-rollout eval (1.7/4/8B)". Varun's warm-start weights are not available yet (D-105), so this experiment measures the Base checkpoints; the warm starts become a later `expt_v2` with the same protocol.

## Goal, hypothesis and decision criterion

- **Uncertainty.** The paper's RL starts from an SFT warm start of Qwen3 Base. Nobody has measured whether the Base checkpoints can produce a verified Lean 4 file on VeriBench-style tasks. If no group ever mixes, every GRPO advantage is zero and RL cannot start.
- **Prior evidence.** Experiment 01 ([`01_small_open_models_veribench_v1_single_call_baseline`](../01_small_open_models_veribench_v1_single_call_baseline/results.md)) measured the *post-trained* Qwen3-1.7B, 4B and 8B with the same decoding on a 128-task subset: 0 of 128 groups mixed for each, and 0 proved files at G=1 on all 896 tasks. Base checkpoints are expected to do no better.
- **Hypothesis.** The `kernel_binary` mixed-group share is below 0.05 for all three Base models; the SFT warm start is needed.
- **Decision criterion** (locked in [PROTOCOL.md](PROTOCOL.md); thresholds reused from experiment 01's gate G1 for comparability):

  | Mixed-group share over 896 tasks (`kernel_binary`) | Verdict for that model |
  |---|---|
  | below 0.05 | **SFT warm start needed**: fewer than 1 in 20 prompts would give RL any gradient |
  | 0.20 or more | **RL from Base is viable** without a warm start |
  | in between | **Marginal**: report which splits mix; a warm start is still advised |

  Qwen3-1.7B-Base decides the project-level answer, as Varun asked. The share of all-pass groups (8 of 8) is reported as the "too easy" check.
- **Diagnostic, not a verdict input.** The same statistics for the denser `ic_tests` channel (the extracted file typechecks and has at least one example, IC_tests = 1), and for `proof_fraction`. These show what an SFT warm start would have to teach: Lean 4 syntax, or proofs.

VeriBench stays held out (repository `CLAUDE.md`). This is an evaluation only: nothing here trains, tunes or selects on VeriBench. The verdict says whether RL needs a warm start; the RL training pools come from experiment 02A's screened external data.

## Structure

```
05_qwen3_base_models_vbv1_g8_pass_signal_sft_derisk/
├── README.md        ← this design doc
├── PROTOCOL.md      ← locked before the GPU run
├── results.md       ← live results and status
└── expt_v1/
    ├── cc.md            ← agent prompt for the SNAP worker that runs and lands the experiment
    ├── models.yaml      ← declared models, revisions, decoding and GPU plan
    ├── run_model_e05.sh ← one model: sharded generation → merge → jobs → kernel scoring → collect → summarize → ρ/H
    ├── launch_e05.sh    ← one tmux window per model on the planned GPUs
    ├── analyze_e05.py   ← pass-count histograms, mixed-group shares with intervals, verdicts, experiment 01 comparison
    ├── CKPT_e05.md      ← worker checkpoint (created at launch)
    └── results/         ← summaries committed here; raw generations stay on the host
```

## Method

1. **Reuse experiment 01's pipeline unchanged** (`rl4cv.veribench.generate` → `jobs` → frozen scorer → `collect` → `summarize` → `rl4cv.probe`), the same pack (experiment 103's gated v6 pack, 896 tasks), the same prompt (experiment 103's single-call system prompt and VBV1 addendum, rendered by the model's chat template) and the same decoding as experiment 01's probe: temperature 0.6, top-p 0.95, top-k 20, 12,288-token cap, per-sample seed 91·100003 + k.
2. **One Base-specific change.** The Base checkpoints' generation config stops only on `<|endoftext|>`, while the chat template ends a turn with `<|im_end|>`; the post-trained models stop on both. Generation passes `--stop-token '<|im_end|>'` so Base and post-trained answers end at the same place. Recorded per row in `sampling.stop_tokens`.
3. **Evaluate.** G = 8 on all 896 tasks for each model: 7,168 cells per model, 21,504 in total.
4. **Score.** Kernel-score every cell with the frozen scorer (`--skip-tc`). No FSC judge runs: the verdict uses kernel channels only, and SCSC is exact (zero) wherever IC_tests · IC_proofs = 0. Cells with IC_tests · IC_proofs > 0 keep FSC and SCSC as unmeasured (no judge spend in this experiment).
5. **Analyze** (`analyze_e05.py`): per model, the histogram of passes k = 0..8 per task; the mixed-group share, pass@8 share and all-pass share with 95% Wilson intervals over tasks and a one-sided exact binomial p-value against the 0.05 threshold; mean pass rate with a 95% task-bootstrap interval; the same for core (614) and IndustrySet (282) separately; ρ and H per split from `rl4cv.probe`; and, on experiment 01's 128-task probe subset, the paired comparison with the post-trained models.

## Dependencies

- **Code and pins:** the `rl4cv` package, VeriBench at the commits pinned in [`external/deps.lock.json`](../../external/deps.lock.json), vLLM 0.30.0 (experiment 01's environment on `skampere1`).
- **Host:** `skampere1` (8× A100-80GB). Experiment 01's work root there holds the validated Lean v4.22.0 grading project, the scorer checkout, the pack and the vLLM environment; this experiment reads them and writes only under its own work root.
- **Decisions:** D-101 (self-hosted inference, accepted). No judge, so D-102 is not used. D-105 (Varun's warm-start weights) gates the follow-up `expt_v2`.

## Status

| Step | Status | Notes |
|---|---|---|
| Design and protocol | Done (10-05-2026) | this folder |
| Preflight (5 tasks, prompt and stop-token checks) | Pending | `expt_v1/cc.md` step 3 |
| G = 8 on 896 tasks, 3 Base models | Pending | `skampere1` |
| Kernel scoring, analysis, verdict | Pending | |
| Follow-up `expt_v2`: Varun's SFT warm starts | Blocked on D-105 | same protocol, new condition label |
