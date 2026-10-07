# Experiment 02A v3 protocol — Lean warm-start data from Valkyrie teachers

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v3/PROTOCOL.md>

**TLDR:** This fixes, before any teacher call, the source tasks, contamination screens, prompt bytes, teacher models and settings, scorer bytes, keep rule, analysis and decision rule for building kernel-verified Lean warm-start data from MBPP. Nothing in it trains a model or touches VeriBench tasks.

**Lock line:** `NOT LOCKED` — the SNAP worker replaces this line with `LOCKED <UTC time> at commit <hash>` after § Preflight passes and before the first teacher call. After the lock, any change is a new version (`expt_v4`).

## 1. Source and task build (zero model calls)

- **Dataset:** `google-research-datasets/mbpp`, configuration `full`, revision `4bb6404fdc6cacfda99d4ac4205087b89d32030c`, all four files (`prompt`, `train`, `validation`, `test`): 974 tasks. Record each file's SHA-256.
- **Rewrite** each task deterministically into VeriBench's Python task layout (VeriBench `veribench_dataset/py_src/easy_set/*.py` is the model): a module docstring holding MBPP's `text`; MBPP's `code` unchanged; `check(candidate)` whose body is MBPP's `test_setup_code` plus each `test_list` and `challenge_test_list` assert with the reference function's name replaced by `candidate`; and a `__main__` block running `check(<reference function>)`. The function name comes from parsing `code` with `ast`; a task whose `code` defines no unique top-level function that the asserts call is dropped and listed.
- **Python gate:** run each rewritten file with `python3 -I` under a 30 s timeout in an empty temporary directory; keep it only if it exits 0. Dropped tasks are listed with the reason.
- **Task identity:** task id `mbpp__task_<task_id>`; Lean file stem `task_<task_id>`; split label `mbpp`. These must normalize to the same identity in the frozen scorer's mapping (`mbpp__task_1` ↔ `mbpp/task_1.lean` → `mbpp/task_1`); § 7 checks every declared task, not a sample.

## 2. Contamination screens (zero model calls)

- `rl4cv.screens` (exact normalized hash; word-5-gram Jaccard ≥ 0.70) of each rewritten Python file against every VeriBench `py_src/**/*.py` and every non-build, non-playground `lean_src/**/*.lean` at the `veribench` pin in `external/deps.lock.json` (the protected corpus that `expt_v2/scripts/build_fvapps_external24.py` builds).
- Remove every exact or near hit; list each with its nearest VeriBench file and score. MBPP is not HumanEval-derived; VeriSoftBench is not involved.
- **Generated Lean is screened too** (`docs/DATASETS.md` → screens 1–2 cover "the Python source and any Lean text"): before a kept teacher file can enter the SFT set, it is screened (exact normalized hash; word-5-gram Jaccard ≥ 0.70) against VeriBench `lean_src` and `py_src` and against every declared held-out panel's Lean and Python (VeriBench V1; VeriBench V2 / V2.1 where its files are available at the pin). A hit is excluded from the SFT set and reported separately; its cell receipt and `kernel_binary` value are kept unchanged.
- The screened task list, sorted by task id, is the **declared manifest**. Its SHA-256 is recorded before the first call.

## 3. Prompt (frozen bytes)

- `instruction.md` and `tests/test.sh` per task come from VeriBench's Harbor adapter functions `generate_instruction(py_content, lean_stem)` and `generate_test_sh`, using the **agent-spec v6** adapter bytes that built experiment 103's gated pack (the version experiments 01 and 05 also used), recovered with `git show <commit>:<path>` and hash-recorded. The `test.sh` canary is a fixed placeholder string.
- The teacher sees exactly what `vb103_single_call` sends: its frozen `SYSTEM_PROMPT` and the user message `instruction + "\n\n---\n\n" + addendum_vbv1.md` (bytes as imported by `rl4cv.veribench.exp103`).
- **Held-out check:** before the lock, confirm and record that the system prompt, the instruction template and `addendum_vbv1.md` contain no VeriBench task text, reference Lean or Python program, because these bytes become the SFT input. If any VeriBench example is embedded, stop and report; do not edit the bytes.

## 4. Teachers and route (D-108)

- **Route:** Valkyrie runs (`valkyrie run start --agent vb103_single_call --benchmark <service> …`) against a new collect-only benchmark service (experiment 103's `vb_service_single_call`, run read-only, `VB_NO_COMPILER=1`, `VB_COLLECT_ONLY=1`, `VB_CONTROL_PACK=1`) on `skampere1`, serving this experiment's pack behind a bearer-protected tunnel. Funded by Vals.
- **D-108 vendor-agent rule and the exception this needs.** D-108 (Brando, 10-07-2026) asks that each model run in its vendor's strongest current agent. On 10-07-2026 no such route is runnable for these teachers on Valkyrie: the native Claude Code and Codex agents (VeriBench experiment 107) were excluded after their credential routes were withdrawn, so the limitation is the approved funding route, and Valkyrie has no Antigravity (`agy`) or other Google agent for Gemini 4 Argon. This version therefore uses one common single-call agent for every family, which also matches the single-call output format the warm-started policy will be probed and trained with. **This is an exception to D-108 and needs Brando's explicit approval, recorded as a decision in `docs/DECISIONS.md`, before the first teacher call (including the § 7 preflight calls).** Without it the run stops after the zero-call steps with status `BLOCKED: awaiting D-108 exception`. **Approved:** Brando, 10-07-2026, recorded as D-014. Compliant vendor agents (or Terminus 2 with a Lean compiler in the sandbox) are the next version if the exception is refused or this version is PARTIAL.
- **Teachers** (one family each; selectors confirmed against the gateway registry dump and recorded with every setting before the lock; no selector with fallback models):

  | Family | Model | Settings |
  |---|---|---|
  | Anthropic | Claude Fable 5.1 (the no-fallback selector) | highest compute effort the registry allows; `max_tokens` 128,000 |
  | OpenAI | GPT-6 Astra | highest reasoning effort selector the registry serves; `max_tokens` 128,000 |
  | Google | Gemini 4 Argon (`google/gemini-4-argon`) | reasoning effort high (its highest); temperature 1.0; `max_tokens` 65,536 (registry default for the rater route) or higher if the registry allows |

- **Payer and identity (D-108):** before the first call, record the host, Valkyrie environment and organization, the agent's gateway-key secret mapping (by name only) and the payer, with non-secret evidence.
- **Calls:** exactly one declared call per (task, teacher), with at most **two model requests per cell in total**, counting the agent's own internal re-send after HTTP 429/5xx. A cell is re-sent (once, as the identical cell) only when its receipts positively show that no model request was served: the sandbox or service failed before the agent started, or `requests_sent = 0`, or every request ended in HTTP 429/5xx with no response, and the shared two-request allowance is not exhausted. A served or possibly served call (client timeout, a failure after a response arrived, a collection failure after generation) is never re-sent: recover its artifacts from the run output if they exist, otherwise it stays `unmeasured`. No cell is re-sampled or dropped because of its content or score; unmeasured cells stay in the denominator.

## 5. Scoring

- **Scorer bytes:** `score_scsc.py`, `run_real_eval.py` and `kernel_axioms.py` from the `veribench_scorer` pin (`59059a20d40adf3289869e58302169ad78102877`), hashes checked against `external/deps.lock.json`. Run with `--skip-tc` in experiment 01/05's validated Lean v4.22.0 + Mathlib grading project on `skampere1`.
- **Non-VeriBench task mapping:** the scorer requires a gold-file mapping only to resolve task ids and split labels. Supply a `--gold-dir` of empty placeholder `mbpp/task_<task_id>.lean` files, one per task (no placeholder is ever read as a reference, because FSC is not computed). Verify on 3 VeriBench gold files and 3 deliberately broken files that the adapter reproduces the scorer's IC_tests and IC_proofs exactly before scoring teacher files.
- **Keep rule:** `rl4cv.rewards.reward_kernel_binary == 1` (typechecks; at least one `example` and at least one theorem; every stated theorem kernel-proved with axioms only in {`propext`, `Classical.choice`, `Quot.sound`}; no vacuous theorem by `rl4cv.rewards.is_vacuous_statement`). `sorry`, `admit`, declared axioms and `native_decide` in named theorems fail.

## 6. Analysis and decision

- Per teacher: declared, measured, unmeasured and kept counts; the **observed yield** kept / declared (a lower bound, because unmeasured cells count as not kept); the **measured-cell yield** kept / measured with its 95% Wilson interval (unit = task), stated as conditional on measurement; and the **missing-outcome bounds** (all unmeasured cells fail / all succeed).
- Union: kept (task, teacher) pairs and distinct tasks kept, with the per-family overlap.
- Failure taxonomy per teacher: no extractable Lean, does not typecheck, no `example`, no theorem, unproved theorem, forbidden axiom, vacuous theorem, unmeasured.
- Length of kept files (tokens under the Qwen3 tokenizer) and number of theorems per kept file.
- **Decision** (README § decision criterion), applied to the kept pairs and distinct tasks after the generated-Lean screen: SUFFICIENT if kept pairs ≥ 1,024 and distinct tasks kept ≥ 512; INSUFFICIENT if kept pairs < 300; PARTIAL otherwise. If the missing-outcome bounds fall on different sides of a threshold, the scientific verdict is **UNRESOLVED** (with an operational statement of how much verified data exists now). Counts are reported with their denominators whatever the verdict.

## 7. Preflight (before the lock, at most 5 tasks × 3 teachers, recorded and excluded from the manifest's analysis)

1. Rewritten-file and screen statistics; manifest hash.
2. Scorer adapter check (§ 5), plus the mapping gate run on **every** declared task's (task id, placeholder path) pair.
3. Service health (200 with the bearer, 401 without, local and through the tunnel) and the read-back per-task limit ≥ 2 × the agent's client timeout + 600 s.
4. One live call per teacher on one task outside the manifest's analysis (`mbpp__preflight_*` ids), scored end to end: status, finish reason, delivered settings and reported charge recorded.

## 8. What is committed

Committed: this protocol with its lock line, the scripts, the declared manifest and its hash, screen reports, per-cell receipts without secrets, scored summaries, `results.md`. Kept on the host only (`/lfs/skampere1/0/brando9/rl4cv_e02a_v3/`): raw teacher responses, Lean files and the assembled SFT set.
