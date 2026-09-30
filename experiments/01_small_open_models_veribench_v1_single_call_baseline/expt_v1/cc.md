# Experiment 01 v1 — run small open-weight Qwen models on all 896 VeriBench V1 tasks (single call) and probe for RL signal

**TLDR:** On a GPU host, you will:

- serve each model in `models.yaml` with vLLM;
- generate one single-call answer per VeriBench V1 task (896 tasks) with experiment 103's exact prompt, plus 8 samples on a 132-task probe subset;
- kernel-score every cell with experiment 103's frozen scorer, and publish IC_tests, IC_proofs, FSC and SCSC with full denominators;
- report the per-split mixed-group share, ρ and H.

**Success:** every declared cell has a terminal receipt and a scored or explicitly unmeasured status, and `results.md` shows the gate G1 verdict with its numbers.

**Deliverable:** a draft PR on `brando90/rl-4-code-verification` titled "Experiment 01: small Qwen models on VeriBench V1 (single call) — results", containing summaries only.

**Constraints:**

- Never change the prompt, extraction, scorer or sampling settings from `PROTOCOL.md`.
- Never re-sample a cell because of its score.
- Never run the FSC judge before decision D-102 is recorded.
- Launch full GPU runs only after Brando approves the estimate.

Read `~/agents-config/INDEX_RULES.md`, then this repository's `CLAUDE.md` and this experiment's `PROTOCOL.md` (locked) before acting.

---

## 0. Scope and rules you must hold

- **What you measure.** This is a measurement, not an optimization. The protocol is locked. If reality forces a change (a missing file, a hash mismatch, a model that will not load), stop that item, write the deviation into `expt_v1/results/REPORT.md` → "Open questions for Brando", and continue with the unaffected cells.
- **VeriBench's evaluation rules apply to every number you report.**
  - SCSC is the only aggregate, always shown with IC_tests, IC_proofs, FSC and n.
  - Unmeasured cells stay in the denominator and are listed.
  - Exact model IDs and Hugging Face revisions are recorded.
- **Model calls.** No direct provider API calls. The FSC judge runs only through experiment 103's `vb103_judge` Valkyrie agent, and only once D-102 names the route and payer.
- **Storage.** Work under `/lfs/$(hostname)/0/$USER/rl4cv_e01/`, never DFS home. Raw generations and job directories stay there; commit summaries only.

## 1. Set up

```bash
WORK=/lfs/$(hostname)/0/$USER/rl4cv_e01 && mkdir -p $WORK && cd $WORK
git clone https://github.com/brando90/rl-4-code-verification.git && cd rl-4-code-verification
make external                       # fetches veribench (c11b99ba) and the frozen scorer (59059a20d)
python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev,gen]"   # vLLM; on a CPU-only box add torch+transformers and pass --backend hf
VERIBENCH_ROOT=$PWD/external/veribench python -m pytest -q   # all tests must pass
```

Record `nvidia-smi`, `vllm --version` and `lean --version` in `expt_v1/results/environment.txt`.

## 2. Verify the pins (stop on any mismatch)

1. **Scorer hashes.** `sha256sum` of these files under `external/veribench_scorer` must start with the prefixes in `PROTOCOL.md`:
   - `scripts/scsc/run_real_eval.py`
   - `scripts/scsc/kernel_axioms.py`
   - `experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py`
2. **Prompt hashes.** The prompt test in `tests/test_veribench_adapters.py` already checks the addendum and system-prompt hashes; confirm it passed.
3. **Extraction bundle.** Experiment 103 recorded the pushed `single_call.py` bundle as SHA-256 `6e1a9b0d…`, while the committed file is `c7cbe3e6…`.
   - Look for the pushed bundle on the host experiment 103 used (its `private/` tree or the Valkyrie agent download) and diff `extract_files` and `resolve_paths`.
   - Record "extraction logic identical: yes/no" in `REPORT.md`.
   - If it differs, keep going with the committed logic and state the difference.

## 3. Freeze the tasks and the models

1. **Locate experiment 103's gated v6 pack and task-id list** (if it is not on the host, generate the current v7 pack with `python external/veribench/vb_harbor/adapter/adapter.py --output $WORK/pack_v7`, which writes 896 task directories, and record the deviation from experiment 103's v6 prompt in `REPORT.md`). Experiment 103's deployment record names skampere1: `/lfs/skampere1/0/brando9/veribench_vb103/…/private/packs/vbv1_896` and `private/task_ids_vbv1.txt`. Then:
   - check that the id list's SHA-256 equals `5d4e64e4…` (full value in `PROTOCOL.md`);
   - check that every task directory has `instruction.md` stamped `agent-spec v6`;
   - check the count is 896.

   Set `PACK` and `TASK_IDS`.
2. **Grading Lean project (`LAKE_DIR`).** Use experiment 103's if it is on the host (Lean v4.22.0, Mathlib v4.22.0 built). Otherwise build one from the pinned scorer in minutes, never by compiling Mathlib from source:
   `curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y --default-toolchain none`, then `cd external/veribench_scorer/veribench_dataset/lean_src && lake exe cache get` (validated on 09-30-2026: downloads the prebuilt Mathlib cache and prints "Completed successfully!"), and set `LAKE_DIR` to that directory. Confirm `lake env lean` on one gold file exits 0.
3. **Resolve models.** Web-search the current small-Qwen lineup (agents-config SOTA-model rule). Then resolve each `models.yaml` id to its current Hugging Face commit (`huggingface_hub.HfApi().model_info(id).sha`) and write `expt_v1/results/model_revisions.json`.
   - Record the search date and any newer small Qwen release you found.
   - Do not silently add it: a new model is a new condition.
4. **Write the probe subset:**
   `python -m rl4cv.veribench.pack --task-ids $TASK_IDS --per-split 4 --salt rl4cv-probe-v1 --out $OUT/probe_task_ids.txt`
   Record its SHA-256 and its task count (at most 132).

## 4. Preflight (bounded, end to end, with controls)

- **Model run.** Use the smallest model on 5 tasks (the first 5 probe ids): run `bash expt_v1/run_model.sh eval Qwen/Qwen3.5-0.8B <rev> preflight-qwen3.5-0.8b`, with `TASK_IDS` pointing to a 5-id file and a separate `OUT`.
- **Scorer controls.** Materialize a control job by hand:
  - 2 tasks with the pack's `tests/gold.lean` as `solution.lean` must give IC_tests = IC_proofs = 1;
  - 1 task with an empty file must give 0 and 0;
  - 1 task with a gold file whose first theorem proof is replaced by `sorry` must give IC_proofs < 1.
- **Pass condition.** Smoke passes only if every rule in `PROTOCOL.md` → "Pass/fail / abort rules" holds. Write the evidence to `expt_v1/results/preflight.json`.

## 5. Estimate, ask, then launch (GPU discipline)

- **Estimate.** From the preflight, estimate GPU-hours for every model (G = 1 and G = 8) and the scorer CPU-hours.
- **Ask.** Post the estimate and the chosen GPUs to Brando, then wait for an explicit go.
- **Launch after the go.** Run the models smallest to largest, one GPU job at a time per device, inside `tmux` or `nohup` with a checkpoint file `expt_v1/CKPT_e01.md`. The checkpoint holds the start time, current model and stage, and the next resume command.

```bash
export PACK TASK_IDS LAKE_DIR SCORER=$PWD/external/veribench_scorer OUT=$WORK/out
bash expt_v1/run_model.sh eval  <id> <revision> <label> [tp]
bash expt_v1/run_model.sh probe <id> <revision> <label> [tp]    # not for the Qwen3.6-27B route control
```

- **Stop checks.** `run_model.sh` stops if any declared cell lacks a generation row, which is the one-to-one manifest check.
- **Reading scores.** The frozen scorer writes legacy column names (`IC_ap`, `IC_pp`, `TC`), which `rl4cv` maps to IC_tests, IC_proofs and FSC. It also pads every pack task that has no output as 0 and prints an 896-task table row, so read the `rl4cv.veribench.summarize` output and never that printed row. Validated on CPU on 09-30-2026: [`results/pipeline_validation_cpu_09-30-2026.json`](results/pipeline_validation_cpu_09-30-2026.json).
- **Resuming.** Rerunning a stage resumes: generation skips finished cells, and job and score directories are write-once.

## 6. FSC (only after D-102 is recorded in `docs/DECISIONS.md`)

- **Which cells.** Every scored cell with IC_tests · IC_proofs > 0, plus the 60-file audit per model defined in `PROTOCOL.md`.
- **How.** Reuse experiment 103's judge pipeline as a new, separately labelled suite:
  - build the items with `judge_vbv1.py`: the pack's `tests/gold.lean`, the longest `python` block of the instruction, and the scored `solution.lean`;
  - deploy `vb103_judge`;
  - `judge_controller.py admit|harvest|fsc`.

  Check that the judge controls pass (oracle, blank, shuffled, vacuous, halfdel).
- **Export and re-collect.** Write `$OUT/fsc/<job>.json` as a map from `task_id` to FSC, then rerun `collect`, `summarize` and `probe` so that `scsc` and `fsc_compiled` appear.
- **If D-102 is still open.** Report FSC as "unmeasured (D-102)". Report SCSC as exact only where IC_tests · IC_proofs = 0, and as unmeasured elsewhere.

## 7. Report and publish

1. **Fill `results.md`.** Both tables, the gate G1 verdict with the numbers that decide it, and the route-control comparison with experiment 103's Valkyrie row.
2. **Write the summary.** Add `expt_v1/results/results_summary_<MM-DD-YYYY__HH-MM-SS>.md` covering the question, setup, exact model IDs and revisions, tables, failure taxonomy (cut off at cap, no Lean block, compile errors, kernel failures), limitations and the next step for experiment 02.
3. **Commit summaries only.** Commit the JSON summaries, `model_revisions.json`, `preflight.json`, `REPORT.md` and the probe `rho_h_*.json` and `.md`. Never commit raw generations, secrets or `.env` files.
4. **Clean up the GPUs.** Kill your servers, confirm with `nvidia-smi` that your processes are gone, and record the final state.
5. **Publish.** Push a branch and open the draft PR named in the TLDR, with a 5–10 bullet summary and a short test plan.

TL;DR: This prompt runs experiment 01. It serves small Qwen models with vLLM, answers all 896 VeriBench V1 tasks with experiment 103's single-call prompt plus an 8-sample probe, scores them with the frozen VeriBench kernel scorer (FSC via `vb103_judge` only after D-102), and publishes the factor table and the RL-signal probe in a draft PR.
