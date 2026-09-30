# Experiment 02A v1 — build screened Lean pools, a frozen held-out panel, Lean warm starts, and policy-relative 2×2 cells with ρ–H measurements

**TLDR:** You will:

- turn FVAPPS (and the Vericoding Lean subset) into contamination-screened VeriBench-style task pools, and freeze a 1,000-task within-source held-out panel;
- train an identical Lean warm start from Qwen3 Base at 1.7B, 4B, 8B and 14B;
- run the paper's four-stage probe to build four balanced 256-prompt cells per scale, and measure ρ and H per cell and reward channel.

**Success:** gate G2, meaning at least one family yields valid cells at all four scales (success spread ≤ 3 points, admission contrast ≥ 15 points, ρ > 0 everywhere).

**Deliverable:** a draft PR "Experiment 02A: Lean pools, warm starts and ρ–H cells", containing the Table 5 analogue, the cell manifests with hashes, and the screen reports.

**Constraints:**

- No VeriBench or panel text may enter any pool or warm-start set.
- Freeze and hash the panel before the first probe.
- Keep the verifier exactly as VeriBench's pinned kernel check.
- Stop before GPU launches until Brando approves the estimate.

Read `~/agents-config/INDEX_RULES.md`, this repository's `CLAUDE.md`, `docs/PLAN.md` and `docs/DATASETS.md` first. Also read experiment 01's `results.md`: its gate G1 verdict and length distributions set this experiment's cap and families.

---

## 1. Write and lock `PROTOCOL.md` first

Copy experiment 01's `PROTOCOL.md` structure and fill in every value below. Commit it before any probe.

- **Pool sources:** revisions and licenses.
- **Conversion rules** and the instruction template version.
- **Reference acceptance rules:** the reference compiles under Lean v4.22.0 and Mathlib v4.22.0, and the non-vacuity check passes.
- **Screens:** exact and 5-gram at 0.7.
- **Panel draw:** 1,000 tasks, salt `rl4cv-panel-v1`.
- **SFT recipe and data counts.**
- **Probe settings:** Stage A with 4,000 prompts, G = 8; the paper's decoding (temperature 0.6, top-p 0.95, top-k 20); the cap chosen from experiment 01's lengths; the band rule (≥ 3 / ≤ 4 non-capped); a hash cap of 640 per band; Stages B–C; cells of 256; Stage D gates.
- **Reward channels measured** and the gate G2 thresholds.

## 2. Pools and screens (CPU only)

1. **Download.** Get FVAPPS from Hugging Face `quinn-dougherty/fvapps` at a pinned revision; record its schema and license, and whether APPS Python solutions are present or must be joined from APPS (MIT).
2. **Convert.** Write `src/rl4cv/pools/fvapps.py` with unit tests. It emits pack-style task directories with:
   - an `instruction.md`: VeriBench's current agent-spec template, the Python solution, and the output path;
   - `tests/reference.lean`: the FVAPPS theorem statements plus the needed definitions.

   Keep a task only if `lake env lean` on the reference (with `sorry` proofs allowed for the reference *statements*) exits 0 and every statement passes the non-vacuity check.
3. **Screen.** Run `rl4cv.screens.screen` against VeriBench `veribench_dataset/py_src` and `lean_src` at the pinned commit, and against the panel candidates. Write `results/screen_report.json`; exact hits are dropped.
4. **Freeze the panel.** Draw the 1,000-task panel in outcome-blind hash order and write `results/panel_task_ids.txt` with its SHA-256. It is never probed or trained on.

## 3. Warm start (GPU; ask before launching)

Build the Lean SFT set from pool tasks only, using the teacher route set by D-104. Keep an answer only if every stated theorem is kernel-proved and the non-vacuity check passes, then train each scale with the paper's recipe. Record per-scale gate metrics at step 512. Do not select checkpoints on panel or VeriBench accuracy.

## 4. Probes and cells (GPU plus Lean CPU pool)

Per scale, run:

1. Stage A (4,000 prompts × 8).
2. `rl4cv.cells.stage_a_bands`.
3. Stages B and C on the candidates.
4. `pooled_stats` and `select_balanced_cells(n_per_cell=256)`.
5. Stage D on the selected cells.
6. `stage_d_confirmation`.

Score every response with `rl4cv.veribench` job and scorer tooling (VeriBench's frozen scorer). For judge-gated channels, judge only responses with IC > 0, and only after D-102. Then run `rl4cv.probe` on Stage D per cell and channel.

## 5. Report

- **`results.md` tables:**
  - the Table 5 analogue: scale × cell × channel, with success, q_mixed, admission, length, ρ and H;
  - stage survival counts;
  - probe token and CPU cost.
- **`cells_<scale>.json`** with hashes.
- **Gate G2 verdict** with its numbers.
- **Publish:** the draft PR named in the TLDR.
- **GPU cleanup.**

TL;DR: This prompt builds screened Lean pools and a frozen panel, trains identical Lean warm starts at four Qwen3 scales, runs the paper's four-stage probe (vLLM plus VeriBench's kernel scorer, and FSC via `vb103_judge` only after D-102) to form 2×2 cells, and publishes their ρ–H table and the gate G2 verdict.
