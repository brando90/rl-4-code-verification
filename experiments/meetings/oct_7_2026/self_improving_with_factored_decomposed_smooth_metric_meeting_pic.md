# Whiteboard: factorized smooth metric and the Apollo–Diana–Hebe loop (10-08-2026)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/meetings/oct_7_2026/self_improving_with_factored_decomposed_smooth_metric_meeting_pic.md>

**TLDR:** This is a text description of Brando's whiteboard photo from the 10-08-2026 meeting, so agents can search and use it without opening the image. The board covers three things:

- a smooth score built as the geometric mean of a file's factors, which should track pass@1 (**S = F(…) ≈ pass@1**);
- the task × factor matrix it produces;
- the improvement loop: Diana measures, the improver model **Hebe** (Qwen3.6 30B A3B) edits the model, harness or prompts, and the next agent is measured again.

Each section gives the literal reading first, then its meaning from the [transcript](transcription.md).

- **Image:** [self_improving_with_factored_decomposed_smooth_metric_meeting_pic.jpeg](self_improving_with_factored_decomposed_smooth_metric_meeting_pic.jpeg), 4080×3072, sha256 `5c7a73f14123767f2e7d21b5fc9a6b0a5d581bf4bfeb57a4f1c4a81e2db64a66`.
- **Origin:** Brando added it to this folder on 10-08-2026. The transcript ends with "let's take a picture of this". A person is partly visible at the left edge.
- **Reading conventions:** `[?]` marks a glyph I could not read with confidence. Handwritten S, δ and f look alike on this board.

## 1. Top center: task × factor matrix

- **Written:** a grid labeled "features", with a separate last column headed "S" `[?]`. Row "x₁" reads `1 | 0.01 | 1 | 0.01 ‖ 0`; the other rows are empty.
- **Meaning:** one row per task x_i and one column per factor. A task can score 0 on the pass/fail outcome while its factors still show partial progress. Transcript: "a matrix of all these features … and all the items … this can be zero, but then the proxy could be … 0.01. And you can see it's like it compiles, but it does this and this."

## 2. Middle left: the target relation

- **Written:** `S = F(…) ≈ pass@1`.
- **Meaning:** a factorized score S, a function of the factors, should approximate the downstream metric. Brando: "can we create a … factorized measure with interpretable properties that correlates with the one we care about. And then if we can, then we optimize this one by optimizing these guys."

## 3. Left boxes: what a solution file contains

- **Written:**
  - **First box** (a faint label to its left reads ".lean" `[?]`): f with arrows to d, T and PBT, and Thms → Prfs.
  - **Second box:** f, d, T and PBT.
- **Meaning:** the parts of a correct file. f is the implementation, d the docstring, T the tests and PBT the property-based tests; Thms (theorems) and Prfs (proofs) appear only in the Lean (VeriBench) box. The second box is a Python file, as in SWE-bench. Transcript: "it has like an implementation … it has some doc string, and it has some tests … property-based tests … In VariBench … We can even have theorems. And we can have proofs."

## 4. Bottom left: the geometric mean on SWE-bench

- **Written:**
  - `pass@1 ≈ S` over `0.77 ≈ S = f ∧ d ∧ T`.
  - Per-factor annotations: f = `1` marked `×`; d = `0.6` marked `~`; T = `0.6` with an overbar.
  - Below: `f(xᵢ) ↔ S = ( * · * · * )^(1/3)`, labeled "SWE-Bench".
- **Meaning:**
  - The logical "and" of the factors becomes a product, and its cube root is the geometric mean.
  - **`×` marks a harsh 0/1 factor**, such as compilation. Brando: "this one is zero, one. If it doesn't compile, you're screwed … for harsh metrics, I'll write like a cross."
  - **`~` marks a smooth, model-judged factor:** "you can have an LLN help you with the doc string."
  - **The overbar marks an average over tests:** "if we have 10 tests, we can smooth this out by making it an average."
  - **0.77 is illustrative.** With the numbers written, (1 · 0.6 · 0.6)^(1/3) ≈ 0.71.

## 5. Center: the downstream metric

- **Written:** a sampled tree of attempts with ✓ and ✗ leaves, feeding `pass@1 = downstream eval metric`, with a `k` (pass@k) and an arrow up to `0.8`.
- **Meaning:** the benchmark's single aggregate number, such as 0.8, is hard to act on. "if I get a big number 0.8, what do I do with that?"

## 6. Right top: the improvement loop

- **Written:**
  - `Measurement δ_Diana(·)` `[?]` → `S_t` → `improver model f_Hebe(·)`, with "Qwen3.6 30B A3B" `[version digit ?]` under it.
  - → `Edits δ_t` → {`model`, `harness`, `(prompts)`} → `c₁, c₂, …, c₆`.
  - `δ_t` ↓ `A_{t+1} (agent)`, which takes task `x` in `ENV_x ~ x̄ ȳ` `[?]` and produces trajectory `y`, which feeds back to `S_{t+1}`, with `0.8` beside it.
- **Meaning:**
  - Diana measures agent t (S_t).
  - Hebe, the improver, proposes an edit δ_t to the model, the harness or the prompts, that is, to one of the components c₁…c₆.
  - The edited agent A_{t+1} runs on tasks; its trajectories y are measured again as S_{t+1}.
  - The improver is a Qwen 30B mixture-of-experts model with 3B active parameters: "this is Q1, A3B … 30B? activate 3B."
  - Fathom transcribed "Hebe" as "Alpha Hippie" and "Hibi".

## 7. Bottom right: why it failed, from a computational graph

- **Written:** in parentheses, `x → (s₁) — (s₂)`, crossing edges to `(s₃) (s₄)`, then `(s₅) (s₆) → y`. Then `f_Diana → why → δ`, with `δ_Hebe` above.
- **Meaning:** the AlphaApollo team's idea is to treat the agent as a computational graph with a score per component. Diana can then say *why* a run failed, and Hebe turns that into an edit δ. Transcript: "if we can structuralize the agents … we'll have the computational graph. Then we can have the controller-wise metric, like here we have S1, S2 … the score for each component inside the computational graph."

## 8. Top left: weight-space sketch

- **Written:** axes w₁ and w₂ with a curve and two dots.
- **Meaning:** Brando's argument that RL keeps moving the weights while the data changes the loss landscape: "Let's say I'm just having two weights, and then you have a loss function … When you do RL, you're still moving the weights."

## What this means for experiments here

- **Validate before optimizing.** First check that S tracks pass@1 across systems ([experiment 07](../../07_scs4c_vs_pass1_swebench_across_models/README.md), H1). Only then use the factors to choose edits or rewards.
- **Analyze at task × factor level.** The unit of analysis is the matrix in section 1, not only aggregates.
  - Hard factors are gates, as in this repository's compile gate (D-003) and the SCS4C patch gate.
  - Smooth factors carry the partial credit.
- **The board is Brando's first sketch, not the adopted definitions.**
  - On SWE-bench the adopted score is SCS4C: a patch gate times the geometric mean of T_fix, T_keep and D_gold, without the docstring.
  - VeriBench uses SCSC = (IC_tests · IC_proofs · FSC)^(1/3).
- **Edit acceptance.** Brando proposed accepting an edit only if no task's factors regress (a greedy monotone rule) to stop the regressions the team reported. See [related_work](../../../docs/related_work/README.md) for AlphaApollo, AlphaDiana and Hebe.
