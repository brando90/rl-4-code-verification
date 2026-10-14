# Run experiment 12 version 2 (corrected hidden-test adapter) on skampere1 — owner runbook

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v2/cc.md>

**TLDR:** You (Emily, or an agent on her account) rerun the hidden gold-reference test evaluation of experiment 12 with the corrected adapter `scripts/adapter_v2.py`, zero model calls, CPU Lean only. The design, the locked protocol, the frozen forecast and the mapping census already exist; do not change them. Order: verify hashes → controls C1–C4 with the new adapter → evaluate the 4,626 compiling primary cells (optionally the secondary panels) → analyses P1–P3, G-A and the sensitivities of `PROTOCOL.md` § 5 → publish `results.md` with every denominator and the forecast verdicts, failed or not. Expect about 4–5 hours of wall-clock for the primary panel at two Lean workers when version 1's compiled modules are reused, about 10 hours from scratch.

## 0. Rules that bind

- Read `~/agents-config/INDEX_RULES.md`, the repository `CLAUDE.md`, then this folder's `README.md`, `DESIGN.md`, `PROTOCOL.md` (locked), `results.md` and `forecasts/e12_v2_forecast.json` (frozen; never edit). Version-1 files under `../expt_v1/` are frozen: import, never edit.
- Zero model calls, zero judge calls, zero GPUs. Never read sealed data (experiments 107, 109) or experiment 08's test split.
- Never edit a candidate file, gold file, recorded factor, frozen forecast or version-1 result. Never re-sample, drop or reorder cells by outcome. Infrastructure retries rerun the identical cell with a receipt.
- Work under `/lfs/skampere1/0/$USER/rl4cv_e12_v2/` (never DFS home); raw bridges, probes, logs and receipts stay on the host; commit manifests, hashes and summaries. Other users' tmux sessions and processes are untouchable. Keep Lean parallelism polite (`nice -n 10`, two workers unless the load average is below 20 on the 128-core host, then at most four).
- Push small and often on `main` (D-012): pull before every push, stage explicit paths, `make test` before every push. Keep `CKPT_e12_v2.md` live with the six headings and a dated Log line per update.

## 1. Host layout

```
WORK=/lfs/skampere1/0/$USER/rl4cv_e12_v2          # your run root (brando9 may use /lfs/skampere1/0/brando9/rl4cv_e12/v2)
$WORK/rl-4-code-verification                       # your clone on main
$WORK/controls_v2/                                 # C1–C4 modules, bridges, probes, logs
$WORK/evaluation_v2/                               # per-group receipts <sha256(task:sha)>.json, modules/, *_Bridge.lean, *_Agreement_*.lean, logs
$WORK/cells_v2.jsonl                               # one record per declared cell, newline = commit boundary
V1=/lfs/skampere1/0/brando9/rl4cv_e12              # version-1 work root, read-only
$V1/evaluation_A2/modules/E12Eval<24 hex>.olean    # compiled candidates you may reuse when the candidate hash is unchanged
```

Candidate files live at the paths recorded in `../expt_v1/results/input_manifest_A1.json` (VeriBench experiment 103's and 102's private trees under `/lfs/skampere1/0/brando9/`); they are world-readable. The frozen grading project (Lean v4.22.0 + Mathlib) is the one `../expt_v1/scripts/compile_reproduction.py` names as `LAKE`.

## 2. Verify before anything runs (zero outcomes)

```bash
cd $WORK/rl-4-code-verification && git pull --ff-only origin main
export PYTHONPATH=$PWD/src
E=experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems
python3 -m pytest -q tests/test_e12_adapter_v2.py                         # 64 passed
python3 - <<'EOF'
import hashlib, json, pathlib
from rl4cv.forecast import verify_forecast
E = pathlib.Path('experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems')
assert verify_forecast(E/'expt_v2/forecasts/e12_v2_forecast.json')
f = json.loads((E/'expt_v2/forecasts/e12_v2_forecast.json').read_text())['inputs']
for name, path in [('adapter_v2.py_sha256', 'expt_v2/scripts/adapter_v2.py'), ('mapping_census_v2.json_sha256', 'expt_v2/results/mapping_census_v2.json'),
                   ('hidden_tests_manifest.json_sha256', 'expt_v1/results/hidden_tests_manifest.json'), ('input_manifest_A1.json_sha256', 'expt_v1/results/input_manifest_A1.json')]:
    assert hashlib.sha256((E/path).read_bytes()).hexdigest() == f[name], name
print('forecast and pinned inputs verified')
EOF
```

If any assertion fails, stop and report; do not "fix" a hash.

## 3. Runtime and controls

Version 2 ships the adapter, not a new runtime. Create `expt_v2/scripts/runtime_v2.py` as a subclass of `../expt_v1/scripts/runtime_e12.py`'s `Runtime` whose `evaluate` calls `adapter_v2.map_symbols` (it returns `(mapping, diagnostics, summary)`), `adapter_v2.per_test_plan`, `adapter_v2.bridge` and `adapter_v2.cell_outcome`, keeps the version-1 `lean()` runner (600 s timeout, `E12_TEST_i=` markers) and the version-1 agreement-probe construction (only application arguments enter probes, never expected values). Then create `controls_v2.py` from `../expt_v1/scripts/controls_e12.py` by swapping the adapter import; the 50 prescribed tasks are `../expt_v1/results/control_selection.json`. Commit both with tests before running them.

```bash
tmux new -s rl4cv-e12v2-controls -d "cd $WORK/rl-4-code-verification && PYTHONPATH=$PWD/src nice -n 10 python3 $E/expt_v2/scripts/controls_v2.py --work $WORK/controls_v2 --out $E/expt_v2/results/controls_v2.json 2>&1 | tee $WORK/controls_v2.log; echo \$? > $WORK/controls_v2.exit"
```

Expectations are unchanged (C1 ≥ 98%, C2 ≥ 95%, C3 ≥ 60% over ≥ 50 compiling mutants, C4 ≥ 95%). A miss is an appended, dated amendment in `PROTOCOL.md` plus a forecast note, then a full rerun; never a weakened threshold. Version 1's controls took about 30 minutes per round at two workers.

## 4. Evaluation (after all four controls pass)

Create `evaluate_v2.py` from `../expt_v1/scripts/evaluate_e12.py`: same manifests, same cell keys, same resume-safe JSONL, same infrastructure-retry limit of 1, with `Runtime` replaced by the version-2 runtime and the record fields of `PROTOCOL.md` § 4. Reuse a version-1 `.olean` when `evaluation_A2/modules/E12Eval<key[:24]>.lean` has the candidate's SHA-256 (copy, do not link into the read-only tree).

```bash
tmux new -s rl4cv-e12v2-evaluate -d "cd $WORK/rl-4-code-verification && PYTHONPATH=$PWD/src nice -n 10 python3 $E/expt_v2/scripts/evaluate_v2.py --work $WORK --panels primary 2>&1 | tee $WORK/evaluation_v2.log; echo \$? > $WORK/evaluation_v2.exit"
```

Send the Rule 70 `[RUN START]` and `[RUN DONE]` emails (To `brando.science@gmail.com`; CC `brandojazz@gmail.com`, `brando9@stanford.edu`, `brando@vals.ai`). Publish a milestone (progress JSON, CKPT line, commit) every 250 unique jobs as version 1 did. Secondary panels (`--panels secondary`, 33,984 cells, 756 unique jobs) are optional descriptives; run them after the primary panel completes.

**Compute estimate (source: version-1 checkpoint milestones).** Version 1 evaluated 4,630 unique primary jobs between 17:16 PDT 10-09-2026 and about 02:45 PDT 10-10-2026 (≈ 9.5 h, two `nice -n 10` Lean workers, ≈ 15 s per job per worker, 0 timeouts, 0 infrastructure retries), and all 5,386 jobs by 05:09 PDT (≈ 12 h). Version 2 has 4,626 primary groups. Reusing the compiled modules removes the candidate compile and leaves one bridge compile plus at most one probe per group: estimate 4–5 h at two workers, 2–3 h at four. From scratch: ≈ 10 h at two workers. Disk: version 1's `evaluation_A2/` is 1.9 GB of receipts and logs; budget 3 GB.

## 5. Analysis and publication

Create `analyze_v2.py` from `../expt_v1/scripts/analyze_e12.py` with the cohorts of `PROTOCOL.md` § 5 (primary P2/P3 cohort = fully applicable; sensitivities S-V2a–d). Seed 20261009, 10,000 task-cluster draws. Report every prediction of `forecasts/e12_v2_forecast.json` as "x [lo, hi] p-val=n/a, threshold source, verdict", failed ones exactly like held ones, with denominators (cells, tasks, systems). Then:

- `results.md`: append the evaluation sections below the census (never edit the census); per-system table; sensitivities; the 20 inspected disagreements selected by the version-1 rule; the paired version-1 versus version-2 table on the 394 changed-entry-point cells and the 20 version-1 inspected rows.
- `../results.md` (version 1): only the one-line pointer at the top changes.
- `experiments/README.md` row 12 and `docs/DECISIONS.md` if a decision is needed (coordinate with the master session).
- `CKPT_e12_v2.md`: DONE with the outcome hash, commits and the exact verification commands.

## TL;DR

Verify hashes, port the runtime/controls/evaluator/analyzer by swapping in `adapter_v2`, pass C1–C4 unchanged, evaluate 4,626 primary cells (≈ 4–5 h reusing version-1 modules), analyze with the fully-applicable cohort, publish with every denominator and every forecast verdict.
