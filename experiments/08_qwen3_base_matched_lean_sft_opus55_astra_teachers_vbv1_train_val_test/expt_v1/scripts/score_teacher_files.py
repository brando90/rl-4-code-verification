#!/usr/bin/env python3
"""TLDR: Score Lean files with VeriBench's frozen scorer bytes (`score_scsc.py --skip-tc`, pin `59059a20`, full-file hashes checked) in experiment 08's private Lean v4.22.0 + Mathlib grading project: materialize job dirs as `rl4cv.veribench.jobs` does, read back IC_tests / IC_proofs / theorem counts / kernel axioms, run the pinned syntactic non-vacuity screen on every stated theorem type, compute `kernel_binary` with `rl4cv.rewards`, classify failures, and prove the adapter on 3 train gold files, 3 broken files, a compiling vacuous control and 5 experiment-103 Astra train files (PROTOCOL §§ 4–5; zero model calls)."""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "src"))
EXP = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("E08_WORK", "/lfs/skampere1/0/brando9/rl4cv_e08"))
SCORER = REPO_ROOT / "external" / "veribench_scorer"
SCORE_SCSC = SCORER / "experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py"
FROZEN_SHA256 = {
    "scripts/scsc/run_real_eval.py": "6e82b3d1cd6d3686aaec3d45f273cd902b03b962c0c2eca48f2c2b4f25f41fa9",
    "scripts/scsc/kernel_axioms.py": "5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287",
    "experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py": "b3713c48e0fdb24adec93b77be8785d20e48897ee8d1fd8ce31fdf37101e81d6",
}
DEFAULT_LAKE_DIR = WORK / "grading" / "lean_src"          # experiment 08's private copy of experiment 01's validated grading project
DEFAULT_PACK = WORK / "pack_train539"                      # served pack: task.toml per task gives the scorer its fixed denominator
GOLD_DIR = SCORER / "veribench_dataset" / "lean_src" / "veribench"   # the frozen scorer's own pinned gold (native VeriBench mapping)
DATASET_GOLD = REPO_ROOT / "external" / "veribench" / "veribench_dataset" / "lean_src" / "veribench"   # the dataset pin c11b99ba (byte-identical gold)
VACUITY_SOURCES = {"rl4cv_rewards": REPO_ROOT / "src" / "rl4cv" / "rewards.py",
                   "veribench_nonvacuous_test": REPO_ROOT / "external" / "veribench" / "tests" / "test_reference_specs_nonvacuous.py"}
E103_PRIVATE = Path("/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private")
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
PROVIDER_ENV = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_AUTH_TOKEN",
                "VALKYRIE_API_KEY", "MODEL_GATEWAY_API_KEY", "PYTHONPATH", "PYTHONHOME")
FACTOR_FIELDS = ("IC_ap", "IC_pp", "agent_compiles", "agent_n_ex", "agent_n_thm", "kernel_n_theorems", "kernel_n_honest",
                 "kernel_n_sorry_ax", "kernel_n_native_decide", "kernel_n_declared_axiom", "kernel_n_unknown", "kernel_probe_ok")
# The pinned VeriBench syntactic non-vacuity patterns that concern theorem statements (tests/test_reference_specs_nonvacuous.py at the pin).
VB_VACUOUS = {
    "theorem states True": re.compile(r"(?:theorem|lemma)\s+\S+[^:\n]*:\s*True\s*:=", re.M),
    "theorem states x = x": re.compile(r"(?:theorem|lemma)\s+\S+[^:\n]*:\s*(\S+(?:\s+\S+)?)\s*=\s*\1\s*:=", re.M),
    "theorem proved by trivial": re.compile(r"(?:theorem|lemma)\s+\S+[^\n]*?:=\s*by\s+trivial\s*$", re.M),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def check_frozen() -> dict:
    lock = json.loads((REPO_ROOT / "external/deps.lock.json").read_text())["veribench_scorer"]
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=SCORER, text=True, capture_output=True, check=True).stdout.strip()
    if head != lock["commit"]:
        raise RuntimeError(f"veribench_scorer checkout {head} != pinned {lock['commit']}")
    hashes = {}
    for rel, want in FROZEN_SHA256.items():
        got = sha((SCORER / rel).read_bytes())
        if got != want:
            raise RuntimeError(f"frozen scorer byte mismatch: {rel} {got} != {want}")
        hashes[rel] = got
    return {"commit": head, "sha256": hashes, "gold_dir": str(GOLD_DIR)}


def vacuity_evidence() -> dict:
    return {"implementation": "per stated theorem type (run_real_eval._split_theorem_blocks header types): rl4cv.rewards.is_vacuous_statement "
                              "(conclusion literally True or a syntactic self-equality); plus VeriBench's pinned theorem patterns "
                              "(states True, states x = x, proved by trivial) on the comment-stripped file; an unparseable theorem type makes "
                              "the keep decision unmeasured",
            "sources_sha256": {k: sha(p.read_bytes()) for k, p in VACUITY_SOURCES.items()}}


def lake_evidence(lake_dir: Path) -> dict:
    manifest = json.loads((lake_dir / "lake-manifest.json").read_text())
    mathlib = next((p for p in manifest.get("packages", []) if p.get("name") == "mathlib"), {})
    return {"lake_dir": str(lake_dir), "lean_toolchain": (lake_dir / "lean-toolchain").read_text().strip(),
            "mathlib_rev": mathlib.get("rev"), "mathlib_input_rev": mathlib.get("inputRev")}


def scorer_env() -> dict:
    env = {k: v for k, v in os.environ.items() if k not in PROVIDER_ENV}
    env["PATH"] = str(Path.home() / ".elan" / "bin") + ":" + env.get("PATH", "")
    return env


def run_scorer(args: list[str], log_path: Path, python: str) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("ab") as log:
        log.write(f"\n=== {stamp()} {python} {SCORE_SCSC.name} {' '.join(args)}\n".encode())
        log.flush()
        return subprocess.run([python, str(SCORE_SCSC), *args], env=scorer_env(), stdout=log, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL, cwd=str(SCORE_SCSC.parent)).returncode


def pack_view(pack: Path, task_ids: list[str], dest: Path) -> Path:
    """A pack directory holding only the job's tasks (symlinks), so the scorer's fixed-denominator rows cover exactly this job."""
    dest.mkdir(parents=True, exist_ok=True)
    for tid in task_ids:
        src = pack / tid
        if not (src / "task.toml").is_file():
            raise RuntimeError(f"{tid}: pack task has no task.toml")
        link = dest / tid
        if not link.exists():
            link.symlink_to(src.resolve(), target_is_directory=True)
    return dest


def load_cells(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def gen_rows(cells: list[dict], model: str) -> list[dict]:
    return [{"task_id": c["task_id"], "sample_idx": 0, "model": c.get("model", model), "lean": c.get("lean") or "", "finish_reason": c.get("finish_reason"),
             "measured": c.get("measured"), "extraction": c.get("extraction"), "generated_tokens": c.get("generated_tokens"),
             "prompt_sha256": c.get("prompt_sha256")} for c in cells]


def cmd_score(a) -> int:
    from rl4cv.veribench.jobs import materialize_jobs

    frozen = check_frozen()
    cells = load_cells(a.cells)
    ids = [c["task_id"] for c in cells]
    if len(set(ids)) != len(ids):
        raise RuntimeError("duplicate task ids in cells")
    jobs = materialize_jobs(gen_rows(cells, a.name), a.job_root, a.name)
    job = jobs[0]
    view = pack_view(a.pack, ids, a.views_root / a.name)
    out_dir = a.scores_root / f"{a.name}_s0"
    if out_dir.exists():
        raise FileExistsError(f"{out_dir} exists; scorer out-dirs are write-once")
    out_dir.mkdir(parents=True)
    rc = run_scorer(["--job-dir", str(job.resolve()), "--pack", str(view), "--name", f"{a.name}_s0", "--gold-dir", str(GOLD_DIR),
                     "--lake-dir", str(a.lake_dir), "--skip-tc", "--out-dir", str(out_dir)], out_dir / "scorer.log", a.python)
    receipt = {"written_utc": stamp(), "name": a.name, "n_cells": len(cells), "job_dir": str(job), "pack_view": str(view), "scorer": frozen,
               "lake": lake_evidence(a.lake_dir), "exit_code": rc, "out_dir": str(out_dir)}
    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=1) + "\n")
    print(json.dumps({"name": a.name, "n_cells": len(cells), "exit_code": rc, "out_dir": str(out_dir)}))
    return rc


# ---- read-back -------------------------------------------------------------------------------------------------
def _f(x):
    try:
        return None if x in (None, "", "None") else float(x)
    except (TypeError, ValueError):
        return None


def _i(x):
    v = _f(x)
    return None if v is None else int(round(v))


def _b(x) -> bool:
    return str(x).strip().lower() == "true"


def per_task_rows(scores_dir: Path) -> dict[str, dict]:
    found = sorted(scores_dir.glob("*_per_task.csv"))
    if len(found) != 1:
        raise FileNotFoundError(f"expected one *_per_task.csv in {scores_dir}, found {len(found)}")
    with found[0].open(newline="", encoding="utf-8") as fh:
        return {r["task"]: r for r in csv.DictReader(fh)}


def _theorem_type(block: str) -> str:
    """The stated type of a `theorem` block: text after the first top-level ':' of the header and before the top-level ':='."""
    m = re.match(r"^\s*(?:private\s+)?(?:protected\s+)?(?:noncomputable\s+)?(?:@\[.*?\]\s*)?(?:theorem|lemma)\s+\S+", block, re.S)
    rest = block[m.end():] if m else block
    opens, closes = "([{⟨", ")]}⟩"
    depth, start, i = 0, None, 0
    while i < len(rest):
        c = rest[i]
        if c in opens:
            depth += 1
        elif c in closes:
            depth -= 1
        elif depth == 0 and c == ":":
            if rest.startswith(":=", i):
                return ""
            start = i + 1
            break
        i += 1
    if start is None:
        return ""
    typ, depth, j = rest[start:], 0, 0
    while j < len(typ):
        c = typ[j]
        if c in opens:
            depth += 1
        elif c in closes:
            depth -= 1
        elif depth == 0 and (typ.startswith(":=", j) or (typ[j] == "\n" and typ[j + 1:].lstrip().startswith("|"))):
            break
        j += 1
    return " ".join(typ[:j].split())


def _strip_comments(text: str) -> str:
    text = re.sub(r"/-.*?-/", "", text, flags=re.S)
    return "\n".join(line.split("--")[0] for line in text.splitlines())


def theorem_types(src: str) -> list[str]:
    sys.path.insert(0, str(SCORER / "scripts" / "scsc"))
    import run_real_eval  # noqa: E402  frozen scorer, imported not edited

    return [_theorem_type(b) for b in run_real_eval._split_theorem_blocks(src)]


def vacuity(src: str) -> dict:
    """Per-theorem-type screen plus VeriBench's pinned file-level theorem patterns; `unparseable` lists blocks without a readable type."""
    from rl4cv.rewards import is_vacuous_statement

    types = theorem_types(src)
    unparseable = [i for i, t in enumerate(types) if not t]
    vac = [t for t in types if t and is_vacuous_statement(t)]
    code = _strip_comments(src)
    patterns = {name: len(p.findall(code)) for name, p in VB_VACUOUS.items()}
    return {"n_types": len(types), "unparseable": unparseable, "vacuous_types": vac, "pattern_hits": patterns,
            "n_vacuous": max(len(vac), sum(patterns.values()))}


def classify(cell: dict, row: dict | None, vac: dict | None) -> str:
    if not cell.get("served", True):
        return "unmeasured"
    if not (cell.get("lean") or "").strip():
        return "no_lean"
    if row is None:
        return "unscored"
    if not _b(row.get("agent_compiles")):
        return "no_typecheck"
    if (_i(row.get("agent_n_ex")) or 0) < 1:
        return "no_example"
    n_thm = _i(row.get("kernel_n_theorems"))
    if n_thm is None:
        n_thm = _i(row.get("agent_n_thm")) or 0
    if n_thm < 1:
        return "no_theorem"
    if (_i(row.get("kernel_n_declared_axiom")) or 0) > 0 or (_i(row.get("kernel_n_native_decide")) or 0) > 0:
        return "forbidden_axiom"          # a declared axiom or native_decide in a named theorem (also unproved under the kernel rule)
    if (_i(row.get("kernel_n_honest")) or 0) < n_thm:
        return "unproved_theorem"         # sorry / admit (sorryAx) or any theorem whose axioms leave the allowed set
    if vac and vac["unparseable"]:
        return "unparseable_theorem_type"
    if vac and vac["n_vacuous"] > 0:
        return "vacuous_theorem"
    return "kept"


def scored_cell(cell: dict, row: dict | None, lean: str) -> dict:
    from rl4cv.rewards import ScoredResponse, reward_kernel_binary

    vac = vacuity(lean) if lean.strip() else None
    keys = ("task_id", "teacher", "r", "model", "run_id", "status", "finish_reason", "served", "measured", "truncated", "extraction", "generated_tokens",
            "reasoning_tokens", "in_tokens", "requests_sent", "cost_usd", "prompt_sha256", "response_sha256", "lean_source", "extraction_consistent",
            "response_text_sha256", "response_text_bytes", "response_path", "error_type", "unserved_evidence", "phase", "kwargs")
    out = {k: cell.get(k) for k in keys}
    out.update(lean_sha256=sha(lean.encode("utf-8")) if lean else None, lean_bytes=len(lean.encode("utf-8")) if lean else 0)
    if row is not None:
        n_thm = _i(row.get("kernel_n_theorems"))
        if n_thm is None:
            n_thm = _i(row.get("agent_n_thm")) or 0
        n_honest = _i(row.get("kernel_n_honest")) or 0
        s = ScoredResponse(extracted=bool(lean.strip()), compiles=_b(row.get("agent_compiles")), n_examples=_i(row.get("agent_n_ex")) or 0,
                           n_theorems_stated=n_thm, n_theorems_proved=n_honest, vacuous_theorems=(vac["n_vacuous"] if vac else 0),
                           truncated=bool(cell.get("truncated")))
        ic_tests_scorer = _f(row.get("IC_ap"))
        if ic_tests_scorer is not None and abs(ic_tests_scorer - s.ic_tests) > 1e-9:
            raise ValueError(f"{cell['task_id']}: IC_tests mismatch scorer {ic_tests_scorer} vs reconstructed {s.ic_tests}")
        try:
            kernel_theorems = ast.literal_eval(row.get("kernel_theorems") or "[]")
        except (ValueError, SyntaxError):
            kernel_theorems = row.get("kernel_theorems")
        kb = reward_kernel_binary(s)
        if vac and vac["unparseable"] and kb == 1.0:
            kb = None   # an unparseable theorem type makes the keep decision unmeasured, never accepted
        out.update(scored=True, compiles=s.compiles, IC_tests=s.ic_tests, IC_proofs=_f(row.get("IC_pp")), IC_proofs_reconstructed=s.ic_proofs,
                   n_examples=s.n_examples, n_theorems_stated=n_thm, n_theorems_proved=n_honest,
                   kernel_n_sorry_ax=_i(row.get("kernel_n_sorry_ax")), kernel_n_native_decide=_i(row.get("kernel_n_native_decide")),
                   kernel_n_declared_axiom=_i(row.get("kernel_n_declared_axiom")), kernel_n_unknown=_i(row.get("kernel_n_unknown")),
                   kernel_probe_ok=row.get("kernel_probe_ok"), kernel_declared_axioms=row.get("kernel_declared_axioms"), kernel_theorems=kernel_theorems,
                   n_vacuous=vac["n_vacuous"] if vac else 0, vacuous_statements=(vac["vacuous_types"][:5] if vac else []),
                   vacuity_pattern_hits=(vac["pattern_hits"] if vac else None), unparseable_theorem_types=(vac["unparseable"] if vac else []),
                   kernel_binary=kb)
    else:
        out.update(scored=False, kernel_binary=0.0 if (cell.get("served", True) and not (cell.get("lean") or "").strip()) else None)
    out["failure_class"] = classify(cell, row, vac)
    return out


def cmd_readback(a) -> int:
    cells = load_cells(a.cells)
    rows = per_task_rows(a.scores_root / f"{a.name}_s0")
    job = a.job_root / f"{a.name}_s0"
    out_rows = []
    for c in cells:
        lean_path = job / c["task_id"] / "verifier" / "solution.lean"
        lean = lean_path.read_text(encoding="utf-8") if lean_path.is_file() else ""
        if lean and c.get("lean_sha256") and sha(lean.encode("utf-8")) != c["lean_sha256"]:
            raise RuntimeError(f"{c['task_id']}: materialized file hash differs from the harvested cell")
        out_rows.append(scored_cell(c, rows.get(c["task_id"]), lean))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("w", encoding="utf-8") as fh:
        for r in out_rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    counts: dict[str, int] = {}
    for r in out_rows:
        counts[r["failure_class"]] = counts.get(r["failure_class"], 0) + 1
    print(json.dumps({"name": a.name, "n": len(out_rows), "classes": counts, "kept": counts.get("kept", 0)}))
    return 0


# ---- adapter check ---------------------------------------------------------------------------------------------
BROKEN = {
    "broken_empty": "",
    "broken_nocompile": "import Mathlib\n\nnamespace Broken\n\nexample : 1 + 1 = 3 := by decide\n\ntheorem t : 1 + 1 = 2 := by decide\n\nend Broken\n",
    "broken_sorry": ("import Mathlib\n\nnamespace BrokenSorry\n\ndef f (n : Nat) : Nat := n + 0\n\nexample : f 3 = 3 := by decide\n\n"
                     "theorem f_id : ∀ n : Nat, f n = n := by\n  sorry\n\nend BrokenSorry\n"),
}
VACUOUS_CONTROL = ("import Mathlib\n\nnamespace VacuousControl\n\ndef f (n : Nat) : Nat := n + 1\n\nexample : f 1 = 2 := by decide\n\n"
                   "theorem trivially_true : True := trivial\n\nend VacuousControl\n")
EXPECT = {"gold": {"agent_compiles": True, "IC_ap": 1.0, "IC_pp": 1.0, "kernel_binary": 1.0, "failure_class": "kept"},
          "broken_empty": {"agent_compiles": False, "IC_ap": 0.0, "IC_pp": 0.0, "kernel_binary": 0.0, "failure_class": "no_lean"},
          "broken_nocompile": {"agent_compiles": False, "IC_ap": 0.0, "IC_pp": 0.0, "kernel_binary": 0.0, "failure_class": "no_typecheck"},
          "broken_sorry": {"agent_compiles": True, "IC_ap": 1.0, "IC_pp": 0.0, "kernel_binary": 0.0, "failure_class": "unproved_theorem"},
          "vacuous_control": {"agent_compiles": True, "IC_ap": 1.0, "IC_pp": 1.0, "kernel_binary": 0.0, "failure_class": "vacuous_theorem"},
          "gold_native_decide_diagnostic": {"agent_compiles": True, "IC_ap": 1.0},
          "e103_astra": {}}


def manifest_rows() -> dict[str, dict]:
    with (EXP / "results" / "split" / "vbv1_split_manifest.csv").open(encoding="utf-8", newline="") as fh:
        return {r["task_id"]: r for r in csv.DictReader(fh)}


def cmd_adapter_check(a) -> int:
    from rl4cv.veribench.jobs import materialize_jobs

    frozen = check_frozen()
    work = a.work
    if work.exists():
        raise FileExistsError(f"{work} exists; adapter checks are write-once")
    work.mkdir(parents=True)
    rows_m = manifest_rows()
    train = sorted(t for t, r in rows_m.items() if r["split"] == "train")
    # Deterministic choices in task-id order. Gold: the first 3 train references whose pinned text never uses `native_decide` (403 of the 896
    # references use it, mostly in `example`s but sometimes in named theorems, where the frozen scorer counts the theorem as not honest);
    # the first 2 train references that do use it are scored as a diagnostic of that rejection. Then 3 broken, 1 vacuous control and the
    # first 5 Astra files that exist and are non-empty.
    def gold_text(tid: str) -> str:
        return (DATASET_GOLD / rows_m[tid]["gold_relpath"]).read_text(encoding="utf-8")
    clean_gold = [t for t in train if "native_decide" not in gold_text(t)]
    nd_gold = [t for t in train if "native_decide" in gold_text(t)]
    gold_ids, gold_nd_ids = clean_gold[:3], nd_gold[:2]
    rest = [t for t in train if t not in gold_ids and t not in gold_nd_ids]
    broken_ids, vac_id = rest[:3], rest[3]
    astra_csv = E103_PRIVATE / "scsc_vbv1" / "gpt-6-astra-high" / "scsc_expt103-single-call-vbv1-gpt-6-astra-high_gpt-6-astra-high_per_task.csv"
    with astra_csv.open(encoding="utf-8", newline="") as fh:
        astra_rows = {r["task"]: r for r in csv.DictReader(fh)}
    astra_ids = []
    for tid in rest[4:]:
        p = E103_PRIVATE / "jobs" / "gpt-6-astra-high" / tid / "verifier" / "solution.lean"
        if p.is_file() and p.read_text(encoding="utf-8").strip() and tid in astra_rows:
            astra_ids.append(tid)
        if len(astra_ids) == 5:
            break
    files: dict[str, tuple[str, str]] = {}   # task_id -> (kind, lean)
    for tid in gold_ids:
        files[tid] = ("gold", gold_text(tid))
    for tid in gold_nd_ids:
        files[tid] = ("gold_native_decide_diagnostic", gold_text(tid))
    for tid, (kind, text) in zip(broken_ids, BROKEN.items()):
        files[tid] = (kind, text)
    files[vac_id] = ("vacuous_control", VACUOUS_CONTROL)
    for tid in astra_ids:
        files[tid] = ("e103_astra", (E103_PRIVATE / "jobs" / "gpt-6-astra-high" / tid / "verifier" / "solution.lean").read_text(encoding="utf-8"))
    ids = list(files)
    rows = [{"task_id": tid, "sample_idx": 0, "model": "adapter-check", "lean": files[tid][1]} for tid in ids]
    job = materialize_jobs(rows, work / "jobs", "adapter")[0]
    view = pack_view(a.pack, ids, work / "pack_view")
    out_dir = work / "scores"
    rc = run_scorer(["--job-dir", str(job.resolve()), "--pack", str(view), "--name", "adapter_s0", "--gold-dir", str(GOLD_DIR), "--lake-dir", str(a.lake_dir),
                     "--skip-tc", "--out-dir", str(out_dir)], work / "scores.log", a.python)
    pt = per_task_rows(out_dir) if rc == 0 else {}
    results, ok_all = [], rc == 0
    for tid in ids:
        kind, text = files[tid]
        row = pt.get(tid)
        cell = scored_cell({"task_id": tid, "served": True, "lean": text}, row, text)
        exp = EXPECT[kind]
        got = {"agent_compiles": bool(cell.get("compiles")), "IC_ap": cell.get("IC_tests"), "IC_pp": cell.get("IC_proofs"), "kernel_binary": cell.get("kernel_binary"),
               "failure_class": cell["failure_class"]}
        met = all(got.get(k) == v for k, v in exp.items())
        entry = {"task_id": tid, "kind": kind, "sha256": sha(text.encode("utf-8")), "bytes": len(text.encode("utf-8")), "factors": {k: (row or {}).get(k) for k in FACTOR_FIELDS},
                 "got": got, "expected": exp, "n_vacuous": cell.get("n_vacuous"), "vacuity_pattern_hits": cell.get("vacuity_pattern_hits"), "expectations_met": met}
        if kind == "e103_astra":
            ref = astra_rows[tid]
            same = {k: ((row or {}).get(k) == ref.get(k)) for k in ("IC_ap", "IC_pp", "agent_compiles", "agent_n_ex", "kernel_n_theorems", "kernel_n_honest",
                                                                   "kernel_n_sorry_ax", "kernel_n_native_decide", "kernel_n_declared_axiom")}
            entry.update(e103_factors={k: ref.get(k) for k in same}, reproduces_e103=all(same.values()), per_field=same,
                         e103_file_sha256=sha((E103_PRIVATE / "jobs" / "gpt-6-astra-high" / tid / "verifier" / "solution.lean").read_bytes()))
            met = entry["reproduces_e103"]
            entry["expectations_met"] = met
        ok_all &= met
        results.append(entry)
    out = {"written_utc": stamp(), "scorer": frozen, "lake": lake_evidence(a.lake_dir), "vacuity": vacuity_evidence(), "scorer_exit_code": rc, "work": str(work),
           "pack": str(a.pack), "n_files": len(results), "files": results, "verdict": "PASS" if ok_all else "FAIL",
           "gold_selection": {"dataset_gold": str(DATASET_GOLD), "scorer_gold_identical": GOLD_DIR.exists() and all((GOLD_DIR / rows_m[t]["gold_relpath"]).read_bytes() == gold_text(t).encode("utf-8") for t in gold_ids + gold_nd_ids),
                              "rule": "first 3 train references (task-id order) whose text never uses native_decide; first 2 that do are scored as a diagnostic",
                              "n_train_gold_with_native_decide": len(nd_gold), "n_train_gold": len(train)},
           "meaning": ("PASS: the frozen scorer in experiment 08's private grading project keeps the 3 train gold files (IC_tests = IC_proofs = 1, kernel_binary 1), "
                       "rejects the 3 broken variants (empty, non-compiling, sorry), fails the keep rule on a compiling file whose only theorem is `True` "
                       "despite perfect kernel factors, reproduces experiment 103's IC_tests / IC_proofs / theorem and axiom counts on 5 Astra train files, and the "
                       "two native_decide gold diagnostics compile with IC_tests = 1 (their kernel_binary shows how native_decide in a named theorem is rejected).")}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": out["verdict"], "scorer_exit_code": rc, "n_files": len(results),
                      "files": [(r["kind"], r["task_id"], r["got"]["failure_class"], r["got"]["kernel_binary"], r["expectations_met"]) for r in results]}))
    return 0 if out["verdict"] == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--lake-dir", type=Path, default=DEFAULT_LAKE_DIR)
    ap.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("frozen")
    p = sub.add_parser("score")
    for flag in ("--cells", "--job-root", "--scores-root", "--views-root"):
        p.add_argument(flag, type=Path, required=True)
    p.add_argument("--name", required=True)
    p = sub.add_parser("readback")
    for flag in ("--cells", "--job-root", "--scores-root", "--out"):
        p.add_argument(flag, type=Path, required=True)
    p.add_argument("--name", required=True)
    p = sub.add_parser("adapter-check")
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--out", type=Path, default=EXP / "results" / "scorer_adapter_check.json")
    a = ap.parse_args(argv)
    if a.cmd == "frozen":
        print(json.dumps({"scorer": check_frozen(), "lake": lake_evidence(a.lake_dir), "vacuity": vacuity_evidence()}, indent=1))
        return 0
    return {"score": cmd_score, "readback": cmd_readback, "adapter-check": cmd_adapter_check}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
