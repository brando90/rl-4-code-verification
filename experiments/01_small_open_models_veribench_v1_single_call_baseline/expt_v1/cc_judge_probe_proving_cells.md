# Judge experiment 01's 11 proving G = 8 probe cells with the locked FSC judge, and add the probe's `scsc` and `fsc_compiled` channels

**TLDR:** `PROTOCOL.md` puts every cell with IC_tests · IC_proofs > 0 in the FSC judge's scope and lists the probe's reward channels as "`kernel_binary`, `proof_fraction` (plus `scsc` and `fsc_compiled` once judged)". The G = 8 probe's proving cells were never judged: 4 in `qwen3.5-9b_g8` and 7 in `qwen3-14b_g8`, found by the Gemini 4 Argon QA test and listed open in `REPORT.md` entry 17. Brando, 10-07-2026: "now judge the 11 proving G=8 probe cells". Judge each one with the locked design (GPT-6 Sol high and Claude Opus 5.5 max, 3 repeats each, median of 3, mean of the 2, divided by 5) on the same `vb103_judge` Valkyrie route. Then compute the probe's `scsc` and `fsc_compiled` channels and publish them beside the kernel channels.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

## Rules for this task

- **Checkout:** `/lfs/skampere1/0/brando9/rl4cv_e01/rl-4-code-verification` on `main`. Pull first, pull before every push, stage explicit paths only (`CLAUDE.md` D-012). Never touch other sessions' tmux sessions, ports or files (`rl4cv-e02a-v3-*`, `rl4cv-e07-*`, `rl4cv-e08-*`).
- **Checkpoint:** `expt_v1/CKPT_e01_probe_judge.md` (Created / Last updated from `date`). Status file: `/lfs/skampere1/0/brando9/rl4cv_e01/STATUS_e01_probe_judge`.
- **Reuse, don't fork:** reuse the median-of-3 machinery that the FSC repeat correction added to `judge_rl4cv_e01.py` today (commit `b993603`: `r23`, `fsc-median3`, the per-task harvest fallback for the Valkyrie tracker regression). Keep its TLDR header current, and change nothing that existing suites rely on.
- **Spend:** the judge total is $289.78 of the code's $400 cap. This task needs about 11 × 2 members × 3 repeats = 66 cells, roughly $10. Stop with `BLOCKED: spend cap` before any admission that could cross $400.
- **Retries:** re-send a cell only when its receipt shows no model request was served, at most once, as the identical cell. Served `model_error` cells stay unmeasured and are listed.

## Steps

1. **Find the cells.** From the probe's scored JSONL on this host (`/lfs/skampere1/0/brando9/rl4cv_e01/out/…/scored_<label>_g8.jsonl`), list every (task, sample) with IC_tests · IC_proofs > 0 for all 8 probe models. Record the list, with model, task, sample, factors and the solution file's SHA-256, in `expt_v1/results/judge/probe_proving_cells.json`. If the count is not 11 (4 for Qwen3.5-9B, 7 for Qwen3-14B), stop and record why.
2. **Build.** Add a `build-probe` action for suite `rl4cv-e01-probe:<label>`:
   - **Items:** each item is one (task, sample) cell. The item id `<task_id>__s<k>` keeps two samples of one task apart.
   - **Inputs:** the candidate is that sample's `verifier/solution.lean` from the probe job directory; the gold file and Python source come from the pack, assembled exactly as `build_model_pack` does.
   - **Prompts:** rendered once per item, with repeats `__r1`…`__r3` byte-identical.
   - **Packaging:** use its own pack and benchmark (`veribench-rl4cv-e01-probe-<label>`), and require a round-trip `verdict: PASS`.
   - Zero model calls. Commit and push.
3. **Run.** Deploy one collect-only judge service per probe suite on a claimed free port block in 9710–9718 (claim file, health 200 with the bearer and 401 without), then admit both configs. Supervise until terminal, harvest, run the single recovery pass if needed, and tear down (`ss -tlnp` must show the ports free; remove the claim).
4. **Aggregate.**
   - **FSC:** per item, the median of 3 per member, then the mean of the 2, divided by 5 (experiment 103's completeness rule, as in `fsc-median3`). Write `expt_v1/results/fsc_probe_<label>.json`.
   - **Per-cell rewards:** `scsc` = (1 · 1 · FSC)^(1/3) for the judged cells and exactly 0 for every cell with IC_tests · IC_proofs = 0. `fsc_compiled` uses `rl4cv.rewards`. Judge-dependent values on non-proving cells with IC_tests = 1 are outside the locked judge scope: report how many such cells there are and leave their `fsc_compiled` as unmeasured (`null`), never 0.
   - **Probe summaries:** recompute them for the `scsc` channel (and `fsc_compiled` only where measured) with `rl4cv.probe`: mean reward, mixed-group share, ρ, H and per-split max mixed-group share.
5. **Publish.**
   - In `results.md`, add the `scsc` (and `fsc_compiled`, marked partial) rows to the probe table and a dated "Probe proving cells judged (10-07-2026)" note: the 11 cells with their FSC and SCSC, spend, and whether Gate G1 or experiment 02's seed splits change. G1 is locked on `kernel_binary`, so they should not.
   - Add a `REPORT.md` entry and mark item 17's "unjudged G = 8 positive cells" as resolved.
   - Update the `README.md` status and the `experiments/README.md` row 01.
   - Run `make test`, commit and push.
   - Write `DONE` to the status file and give the checkpoint its final state: the per-cell table, spend and run ids.

**TL;DR:** Judge the 4 + 7 proving G = 8 probe cells with both locked judges at 3 repeats each on the same route, add the probe's `scsc` (and partial `fsc_compiled`) channel, and publish it with spend, without touching any earlier evidence.
