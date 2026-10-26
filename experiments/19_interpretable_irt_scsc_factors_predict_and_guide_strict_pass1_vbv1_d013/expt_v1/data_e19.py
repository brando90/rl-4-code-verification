"""TLDR: Input loaders for experiment 19 with hash pins and split guards: the 11-system VeriBench V1 SCSC panel (from experiment 12's committed join of VeriBench experiments 102/103), its reference-consistency rows (VeriBench experiment 111), the experiment 13 start policy's validation outcomes (experiment 08's ladder), its train-split A6 strict rate (experiment 13 v2), and the task features; test-split rows are dropped on read and never returned."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
E08 = REPO / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results"
E12_MANIFEST = REPO / "experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v1/results/input_manifest.json"
E13_A6 = REPO / "experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1/A6_S2_result.json"
FEATURES = HERE / "results/task_features_e19.csv"
START_POLICY_FILE = E08 / "ladder/sft_4B_f1p0_validation_per_task.csv"

# VeriBench experiment 111 reference-consistency rows, read from a VeriBench clone at a pinned commit.
VERIBENCH_RC_COMMIT = "07c4b4852ad482af8a3a4de7001e278245360347"
RC_FILES = {
    "x103": "experiments/111_gold_ref_tests_pbts_fspecs_on_agent_outputs_vbv1_vbv2_vbv3/results/vbv1_usual_agents/RC_ROWS_det_v2.csv",
    "x102": "experiments/111_gold_ref_tests_pbts_fspecs_on_agent_outputs_vbv1_vbv2_vbv3/results/scsc_vs_rc_preferred_metric/RC_ROWS_tmlr_v2r_and_tactic_sweep.csv",
}

# Every input file's SHA-256 is fixed at protocol lock in input_pins_e19.json (PROTOCOL.md section 2); a mismatch stops
# the analysis.
PINS_FILE = HERE / "input_pins_e19.json"

SYSTEMS = ("baseline", "claude-opus-5-max", "claude_code", "codex", "gemini-3.1-pro-high", "gpt-5.6-luna-high",
           "gpt-5.6-sol-high", "gpt-6-astra-high", "gpt-6-luna-high", "leanstral", "qwen3.6-27b-thinking")
MEASURED = "measured"  # every other source status (zero_without_call, incomplete, unmeasured_infra, model_error) is missing
FSC_CATEGORY_EDGES = "0 | (0, 0.5] | (0.5, 0.8] | (0.8, 1) | 1"
N_FSC_CATS = 5
G = 8  # samples per task in the start-policy ladder file


class SplitViolation(RuntimeError):
    """A row or file would put a test-split task into the analysis."""


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def fsc_category(f: float) -> int:
    """Ordinal FSC category used by the graded response model: 0 | (0, .5] | (.5, .8] | (.8, 1) | 1."""
    if f <= 0.0:
        return 0
    if f <= 0.5:
        return 1
    if f <= 0.8:
        return 2
    if f < 1.0:
        return 3
    return 4


@dataclass
class Split:
    train: list[str]
    validation: list[str]
    group: dict[str, str]
    test_ids: frozenset[str] = field(repr=False)

    @property
    def tasks(self) -> list[str]:
        return self.train + self.validation

    def split_of(self, task: str) -> str:
        if task in self.test_ids:
            raise SplitViolation(f"test-split task {task} reached the analysis")
        return "train" if task in set(self.train) else "validation"


def load_split(root: Path = E08) -> Split:
    """D-013 train (539) and validation (135) ids; the test id list is read only to guard against leaks."""
    train = sorted((root / "split/vbv1_train_task_ids.txt").read_text().split())
    val = sorted((root / "split/vbv1_validation_task_ids.txt").read_text().split())
    test = frozenset((root / "split/vbv1_test_task_ids.txt").read_text().split())
    if len(train) != 539 or len(val) != 135 or len(test) != 222 or (set(train) | set(val)) & test or set(train) & set(val):
        raise SplitViolation("D-013 split lists are not 539/135/222 disjoint ids")
    group = {}
    with (root / "split/vbv1_split_manifest.csv").open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r["split"] != "test":
                group[r["task_id"]] = r["group_id"]
    return Split(train, val, group, test)


@dataclass
class Panel:
    """Systems × tasks (train then validation) arrays; masks are 1 where the cell was measured."""

    systems: list[str]
    tasks: list[str]
    n_train: int
    strict: np.ndarray
    harsh: np.ndarray
    smooth: np.ndarray
    fsc: np.ndarray
    fcat: np.ndarray
    mask: np.ndarray
    status_counts: dict
    ic_tests: np.ndarray | None = None
    status: np.ndarray | None = None
    gold: np.ndarray | None = None
    gold_mask: np.ndarray | None = None


def load_panel(split: Split, manifest: Path = E12_MANIFEST, zero_without_call_missing: bool = True) -> Panel:
    """The 11-system VBV1 panel with strict = 1[IC_tests = 1 and IC_proofs = 1], harsh = strict and FSC = 1, and
    per-file smooth SCSC = (IC_tests * IC_proofs * FSC)^(1/3); FSC is the validated H2 judge's (experiments 102/103)."""
    d = json.loads(manifest.read_text())
    tasks = split.tasks
    col = {t: j for j, t in enumerate(tasks)}
    row = {s: i for i, s in enumerate(SYSTEMS)}
    shape = (len(SYSTEMS), len(tasks))
    strict, harsh, smooth, fsc, fcat, mask, ict_arr = (np.zeros(shape) for _ in range(7))
    status = np.full(shape, "", dtype=object)
    counts: dict = {}
    seen = set()
    gk = _gold_key_to_task()
    for c in d["cells"]:
        s = c["system"]
        t = gk[c["task_id"]] if "/" in c["task_id"] else c["task_id"]  # experiment 102 rows use the gold key
        if t in split.test_ids:
            continue  # dropped on read: the test split is never touched (PROTOCOL.md section 2)
        if t not in col or s not in row:
            raise RuntimeError(f"unexpected cell {s} / {t}")
        if (s, t) in seen:
            raise RuntimeError(f"duplicate cell {s} / {t}")
        seen.add((s, t))
        st = c["source_status"]
        counts[(s, st)] = counts.get((s, st), 0) + 1
        status[row[s], col[t]] = st
        measured = st == MEASURED or (st == "zero_without_call" and not zero_without_call_missing)
        if not measured:
            continue
        ict, icp, f = float(c["IC_tests"]), float(c["IC_proofs"]), float(c["FSC"])
        i, j = row[s], col[t]
        strict[i, j] = float(ict == 1.0 and icp == 1.0)
        harsh[i, j] = float(ict == 1.0 and icp == 1.0 and f == 1.0)
        smooth[i, j] = (ict * icp * f) ** (1.0 / 3.0)
        fsc[i, j], fcat[i, j], mask[i, j], ict_arr[i, j] = f, fsc_category(f), 1.0, ict
    if len(seen) != len(SYSTEMS) * len(tasks):
        raise RuntimeError(f"panel is incomplete: {len(seen)} of {len(SYSTEMS) * len(tasks)} cells")
    return Panel(list(SYSTEMS), tasks, len(split.train), strict, harsh, smooth, fsc, fcat, mask,
                 {f"{s}|{st}": n for (s, st), n in sorted(counts.items())}, ict_arr, status)


@dataclass
class StartPolicy:
    tasks: list[str]
    k: np.ndarray
    n: np.ndarray
    mean_tokens: np.ndarray
    k_capped: np.ndarray


def load_start_policy(split: Split, path: Path = START_POLICY_FILE) -> StartPolicy:
    """Experiment 13's start policy (sft_4B_f1p0) on the 135 validation tasks, 8 samples each at the v4 sampler."""
    if "test" in path.name:
        raise SplitViolation(f"refusing to read a test-split file: {path.name}")
    rows = {}
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            t = r["task_id"]
            split.split_of(t)
            if t not in set(split.validation):
                raise SplitViolation(f"{path.name}: {t} is not a validation task")
            rows[t] = r
    if sorted(rows) != split.validation:
        raise RuntimeError("start-policy file does not cover exactly the 135 validation tasks")
    v = split.validation
    k = np.array([float(rows[t]["k_kernel_binary"]) for t in v])
    n = np.array([float(rows[t]["samples_known"]) for t in v])
    if np.any(n != G) or np.any(k < 0) or np.any(k > n):
        raise RuntimeError("start-policy counts must be k of 8 for every validation task")
    return StartPolicy(v, k, n, np.array([float(rows[t]["mean_generated_tokens"]) for t in v]),
                       np.array([float(rows[t]["k_capped"]) for t in v]))


def load_a6_rate(path: Path = E13_A6) -> dict:
    """Experiment 13's A6 train diagnostic (start policy, v4 sampler, 64 train tasks × 8): strict successes / measured."""
    a = json.loads(path.read_text())
    s = a["metrics"]["strict"]
    if a.get("status") != "SOUND" or a.get("samples_per_task") != 8:
        raise RuntimeError("A6 receipt is not the SOUND 8-sample diagnostic")
    return {"successes": int(s["successes"]), "measured": int(s["measured"]), "missing": int(s["missing"]),
            "declared": int(a["declared"]), "task_count": int(a["task_count"]),
            "rate": s["successes"] / s["measured"], "bounds": list(s["full_denominator_bounds"])}


def load_features(split: Split, path: Path = FEATURES) -> list[dict]:
    rows = {}
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            split.split_of(r["task_id"])
            rows[r["task_id"]] = r
    if sorted(rows) != sorted(split.tasks):
        raise RuntimeError("feature table does not cover exactly the train and validation tasks")
    return [rows[t] for t in split.tasks]


def _gold_key_to_task(root: Path = E08) -> dict[str, str]:
    out = {}
    with (root / "split/vbv1_split_manifest.csv").open(newline="") as fh:
        for r in csv.DictReader(fh):
            out[r["gold_relpath"].removesuffix(".lean")] = r["task_id"]
    return out


RC_SYSTEM_MAP = {"x103_claude-opus-5-max": "claude-opus-5-max", "x103_gemini-3.1-pro-high": "gemini-3.1-pro-high",
                 "x103_gpt-5.6-luna-high": "gpt-5.6-luna-high", "x103_gpt-5.6-sol-high": "gpt-5.6-sol-high",
                 "x103_gpt-6-astra-high": "gpt-6-astra-high", "x103_gpt-6-luna-high": "gpt-6-luna-high",
                 "x103_qwen3.6-27b-thinking": "qwen3.6-27b-thinking", "codex": "codex", "claude_code": "claude_code",
                 "baseline": "baseline", "leanstral": "leanstral"}


RC_ROWS = HERE / "results/inputs/rc_rows_panel_trainval.csv"


def load_rc(split: Split, path: Path = RC_ROWS) -> dict:
    """Reference-consistency fractions for the 11 panel systems (copied by extract_rc_e19.py from VeriBench experiment
    111 at a pinned commit): per cell RC_tests, RC_pbt and RC_fspecs, NaN when the adapter could not state or measure it."""
    tasks = split.tasks
    col = {t: j for j, t in enumerate(tasks)}
    row = {s: i for i, s in enumerate(SYSTEMS)}
    out = {k: np.full((len(SYSTEMS), len(tasks)), np.nan) for k in ("RC_tests", "RC_pbt", "RC_fspecs")}
    seen = set()
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            s, t = r["system"], r["task_id"]
            split.split_of(t)
            if (s, t) in seen:
                raise RuntimeError(f"duplicate RC row {s} / {t}")
            seen.add((s, t))
            i, j = row[s], col[t]
            for name, num, den in (("RC_tests", "tests_pass", "n_tests"), ("RC_pbt", "pbt_survived", "n_pbt"),
                                   ("RC_fspecs", "obligations_proved", "n_obligations")):
                if r[den] not in ("",) and r[num] not in ("",) and float(r[den]) > 0:
                    out[name][i, j] = float(r[num]) / float(r[den])
    return out


X103_SYSTEMS = ("claude-opus-5-max", "gemini-3.1-pro-high", "gpt-5.6-luna-high", "gpt-5.6-sol-high", "gpt-6-astra-high",
                "gpt-6-luna-high", "qwen3.6-27b-thinking")
LOST = ("model_error", "incomplete", "unmeasured_infra")


def attach_gold_target(panel: Panel, split: Split, path: Path = RC_ROWS) -> dict:
    """Strict gold-check pass@1 (tests + PBTs), per cell, as VeriBench experiment 111 defines it
    (results/scsc_vs_rc_preferred_metric/README.md): 1 when the agent's own code passes every grounded gold unit test
    and no gold property is refuted; 0 when the file does not typecheck or the solver returned nothing
    (`zero_without_call`); missing for lost generation cells, for the withheld rating-set tasks, and when the code
    typechecks but no adapter states a grounded test or testable property. Sets panel.gold and panel.gold_mask."""
    rows = {}
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            split.split_of(r["task_id"])
            rows[(r["system"], r["task_id"])] = r
    tasks = panel.tasks
    x103_rows = {t for (s, t) in rows if s in X103_SYSTEMS}
    withheld = [t for t in tasks if t not in x103_rows]
    gold = np.zeros(panel.strict.shape)
    gmask = np.zeros(panel.strict.shape)
    why: dict[str, int] = {}
    violations = {"ic_tests_1_without_typecheck_row": 0}
    for i, s in enumerate(panel.systems):
        for j, t in enumerate(tasks):
            st = panel.status[i, j]
            r = rows.get((s, t))
            if st in LOST:
                reason = "missing: lost generation"
            elif t in withheld:
                reason = "missing: withheld rating-set task"
            elif st == "zero_without_call":
                reason, val = "0: solver returned nothing", 0.0
            elif s in X103_SYSTEMS and r is None:
                reason = "missing: no RC row for a measured cell"
            elif (s in X103_SYSTEMS and r["typechecks"] != "1") or (s not in X103_SYSTEMS and r is None):
                reason, val = "0: does not typecheck", 0.0
                if panel.ic_tests[i, j] == 1.0:
                    violations["ic_tests_1_without_typecheck_row"] += 1
            elif r["statable"] != "1":
                reason = "missing: typechecks, not statable"
            else:
                has_t = r["n_tests"] not in ("", "0")
                has_p = r["n_pbt"] not in ("", "0")
                if not has_t and not has_p:
                    reason = "missing: no grounded test or testable property"
                else:
                    ok = (not has_t or r["tests_pass"] == r["n_tests"]) and (not has_p or r["pbt_survived"] == r["n_pbt"])
                    reason, val = ("1: every gold check passes", 1.0) if ok else ("0: a gold check fails", 0.0)
            why[reason] = why.get(reason, 0) + 1
            if not reason.startswith("missing"):
                gold[i, j], gmask[i, j] = val, 1.0
    panel.gold, panel.gold_mask = gold, gmask
    return {"definition": "VeriBench 111 strict gold-check pass@1, tests + PBTs variant", "cell_reasons": why,
            "withheld_tasks_in_train_validation": len(withheld), "consistency_violations": violations}
