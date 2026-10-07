#!/usr/bin/env python3
"""TLDR: Score teacher Lean files with VeriBench's frozen scorer bytes (`score_scsc.py --skip-tc` in the validated Lean 4.22.0 grading project): materialize job dirs, map `mbpp__task_<id>` through a placeholder gold dir, read back IC_tests / IC_proofs / theorem counts / axioms, add the vacuity screen and `kernel_binary`, and prove the adapter on 3 gold and 3 broken files (experiment 02A v3 PROTOCOL § 5)."""
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

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "src"))
SCORER = REPO_ROOT / "external" / "veribench_scorer"
SCORE_SCSC = SCORER / "experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py"
FROZEN_SHA256 = {
    "scripts/scsc/run_real_eval.py": "6e82b3d1cd6d3686aaec3d45f273cd902b03b962c0c2eca48f2c2b4f25f41fa9",
    "scripts/scsc/kernel_axioms.py": "5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287",
    "experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py": "b3713c48e0fdb24adec93b77be8785d20e48897ee8d1fd8ce31fdf37101e81d6",
}
# Experiment 01/05's validated grading project (Lean v4.22.0 + Mathlib v4.22.0, built .lake); read-only here.
DEFAULT_LAKE_DIR = Path("/lfs/skampere1/0/brando9/rl4cv_e01/rl-4-code-verification/external/veribench_scorer/veribench_dataset/lean_src")
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
SPLIT = "mbpp"
SOLUTION_FILE_RE = re.compile(r'^SOLUTION_FILE="/home/user/lean_project/Veribench/([A-Za-z0-9_]+)\.lean"$', re.M)
PROVIDER_ENV = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN",
                "ANTHROPIC_AUTH_TOKEN", "VALKYRIE_API_KEY", "PYTHONPATH", "PYTHONHOME")
FACTOR_FIELDS = ("IC_ap", "IC_pp", "agent_compiles", "agent_n_ex", "agent_n_thm", "kernel_n_theorems", "kernel_n_honest",
                 "kernel_n_sorry_ax", "kernel_n_native_decide", "kernel_n_declared_axiom", "kernel_n_unknown", "kernel_probe_ok")


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
    return {"commit": head, "sha256": hashes}


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


def pack_stems(pack: Path) -> dict[str, str]:
    """task_id -> lean stem, read from each task's tests/test.sh SOLUTION_FILE line (as the service does)."""
    out = {}
    for d in sorted(p for p in pack.iterdir() if p.is_dir()):
        m = SOLUTION_FILE_RE.search((d / "tests" / "test.sh").read_text(encoding="utf-8"))
        if not m:
            raise RuntimeError(f"{d.name}: no SOLUTION_FILE line")
        out[d.name] = m.group(1)
    return out


def make_placeholders(pack: Path, gold_dir: Path) -> int:
    """One empty `mbpp/<stem>.lean` per pack task: the frozen scorer needs a gold path only to resolve task identity (FSC is never computed)."""
    (gold_dir / SPLIT).mkdir(parents=True, exist_ok=True)
    stems = pack_stems(pack)
    for tid, stem in stems.items():
        if not tid.startswith(SPLIT + "__"):
            raise RuntimeError(f"{tid}: task id is not in the {SPLIT} split")
        (gold_dir / SPLIT / f"{stem}.lean").touch()
    return len(stems)


def pack_view(pack: Path, task_ids: list[str], dest: Path) -> Path:
    """A pack directory holding only the job's tasks, so the scorer's fixed-denominator rows cover exactly this job."""
    dest.mkdir(parents=True, exist_ok=True)
    for tid in task_ids:
        src = pack / tid
        if not (src / "task.toml").is_file():
            raise RuntimeError(f"{tid}: pack task has no task.toml")
        link = dest / tid
        if not link.exists():
            link.symlink_to(src.resolve(), target_is_directory=True)
    return dest


def cmd_placeholders(a) -> int:
    n = make_placeholders(a.pack, a.gold_dir)
    print(json.dumps({"gold_dir": str(a.gold_dir), "n_placeholders": n}))
    return 0


def cmd_mapping_gate(a) -> int:
    frozen = check_frozen()
    log = a.out.with_suffix(".log")
    rc = run_scorer(["--verify-mapping", "--pack", str(a.pack), "--gold-dir", str(a.gold_dir), "--lake-dir", str(a.lake_dir)], log, a.python)
    text = log.read_text(encoding="utf-8", errors="replace")
    tail = text[text.rfind("pack tasks"):] if "pack tasks" in text else text[-1500:]
    nums = {k: int(v) for k, v in re.findall(r"^(pack tasks|gold keys|mapped|unmapped)\s*:\s*(\d+)", tail, re.M)}
    distinct = re.search(r"distinct references: (\d+)", tail)
    n_pack = len([p for p in a.pack.iterdir() if p.is_dir()])
    ok = rc == 0 and "MAPPING GATE: PASS" in tail and nums.get("pack tasks") == n_pack and nums.get("mapped") == n_pack \
        and nums.get("unmapped") == 0 and distinct and int(distinct.group(1)) == n_pack
    out = {"written_utc": stamp(), "pack": str(a.pack), "gold_dir": str(a.gold_dir), "n_pack_tasks": n_pack, "scorer": frozen,
           "counts": nums, "distinct_references": int(distinct.group(1)) if distinct else None, "exit_code": rc,
           "scorer_output_tail": tail[-800:], "verdict": "PASS" if ok else "FAIL"}
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: out[k] for k in ("n_pack_tasks", "counts", "distinct_references", "verdict")}))
    return 0 if ok else 1


def load_cells(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def gen_rows(cells: list[dict], model: str) -> list[dict]:
    rows = []
    for c in cells:
        rows.append({"task_id": c["task_id"], "sample_idx": 0, "model": c.get("model", model), "lean": c.get("lean") or "",
                     "finish_reason": c.get("finish_reason"), "measured": c.get("measured"), "extraction": c.get("extraction"),
                     "generated_tokens": c.get("generated_tokens"), "prompt_sha256": c.get("prompt_sha256")})
    return rows


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
    rc = run_scorer(["--job-dir", str(job.resolve()), "--pack", str(view), "--name", f"{a.name}_s0", "--gold-dir", str(a.gold_dir),
                     "--lake-dir", str(a.lake_dir), "--skip-tc", "--out-dir", str(out_dir)], out_dir / "scorer.log", a.python)
    receipt = {"written_utc": stamp(), "name": a.name, "n_cells": len(cells), "job_dir": str(job), "pack_view": str(view),
               "scorer": frozen, "lake": lake_evidence(a.lake_dir), "exit_code": rc, "out_dir": str(out_dir)}
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
    m = re.match(r"^\s*(?:noncomputable\s+)?(?:@\[.*?\]\s*)?theorem\s+\S+", block, re.S)
    rest = block[m.end():] if m else block
    opens, closes = "([{⟨", ")]}⟩"
    depth, start = 0, None
    i = 0
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


def theorem_types(src: str) -> list[str]:
    sys.path.insert(0, str(SCORER / "scripts" / "scsc"))
    import run_real_eval  # noqa: E402  frozen scorer, imported not edited

    return [_theorem_type(b) for b in run_real_eval._split_theorem_blocks(src)]


def vacuous_theorems(src: str) -> list[str]:
    from rl4cv.rewards import is_vacuous_statement

    return [t for t in theorem_types(src) if t and is_vacuous_statement(t)]


def classify(cell: dict, row: dict | None, n_vacuous: int) -> str:
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
        return "forbidden_axiom"
    if (_i(row.get("kernel_n_honest")) or 0) < n_thm:
        return "unproved_theorem"
    if n_vacuous > 0:
        return "vacuous_theorem"
    return "kept"


def scored_cell(cell: dict, row: dict | None, lean: str) -> dict:
    from rl4cv.rewards import ScoredResponse, reward_kernel_binary

    vac = vacuous_theorems(lean) if lean.strip() else []
    out = {k: cell.get(k) for k in ("task_id", "teacher", "model", "run_id", "status", "finish_reason", "served", "measured", "truncated",
                                      "extraction", "generated_tokens", "requests_sent", "cost_usd", "prompt_sha256")}
    out.update(lean_sha256=sha(lean.encode("utf-8")) if lean else None, lean_bytes=len(lean.encode("utf-8")) if lean else 0)
    if row is not None:
        n_thm = _i(row.get("kernel_n_theorems"))
        if n_thm is None:
            n_thm = _i(row.get("agent_n_thm")) or 0
        n_honest = _i(row.get("kernel_n_honest")) or 0
        s = ScoredResponse(extracted=bool(lean.strip()), compiles=_b(row.get("agent_compiles")), n_examples=_i(row.get("agent_n_ex")) or 0,
                           n_theorems_stated=n_thm, n_theorems_proved=n_honest, vacuous_theorems=len(vac), truncated=bool(cell.get("truncated")))
        ic_tests_scorer = _f(row.get("IC_ap"))
        if ic_tests_scorer is not None and abs(ic_tests_scorer - s.ic_tests) > 1e-9:
            raise ValueError(f"{cell['task_id']}: IC_tests mismatch scorer {ic_tests_scorer} vs reconstructed {s.ic_tests}")
        try:
            kernel_theorems = ast.literal_eval(row.get("kernel_theorems") or "[]")
        except (ValueError, SyntaxError):
            kernel_theorems = row.get("kernel_theorems")
        out.update(scored=True, compiles=s.compiles, IC_tests=s.ic_tests, IC_proofs=_f(row.get("IC_pp")), IC_proofs_reconstructed=s.ic_proofs,
                   n_examples=s.n_examples, n_theorems_stated=n_thm, n_theorems_proved=n_honest,
                   kernel_n_sorry_ax=_i(row.get("kernel_n_sorry_ax")), kernel_n_native_decide=_i(row.get("kernel_n_native_decide")),
                   kernel_n_declared_axiom=_i(row.get("kernel_n_declared_axiom")), kernel_n_unknown=_i(row.get("kernel_n_unknown")),
                   kernel_probe_ok=row.get("kernel_probe_ok"), kernel_declared_axioms=row.get("kernel_declared_axioms"),
                   kernel_theorems=kernel_theorems, n_vacuous=len(vac), vacuous_statements=vac[:5],
                   kernel_binary=reward_kernel_binary(s))
    else:
        out.update(scored=False, kernel_binary=0.0 if cell.get("served", True) else None)
    out["failure_class"] = classify(cell, row, len(vac))
    return out


def cmd_readback(a) -> int:
    cells = load_cells(a.cells)
    rows = per_task_rows(a.scores_root / f"{a.name}_s0")
    job = a.job_root / f"{a.name}_s0"
    out_rows = []
    for c in cells:
        lean_path = job / c["task_id"] / "verifier" / "solution.lean"
        lean = lean_path.read_text(encoding="utf-8") if lean_path.is_file() else ""
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
GOLD3 = ["easy_set/1_MyAdd.lean", "easy_set/10_MyEvenSumParity.lean", "easy_set/12_MyStringLength.lean"]
VB_IDS_BROKEN = ["easy_set__11_myfirstchar", "easy_set__13_myuppercase", "easy_set__14_myremovespaces"]
BROKEN = {
    "broken_empty": "",
    "broken_nocompile": "import Mathlib\n\nnamespace Broken\n\nexample : 1 + 1 = 3 := by decide\n\ntheorem t : 1 + 1 = 2 := by decide\n\nend Broken\n",
    "broken_sorry": ("import Mathlib\n\nnamespace BrokenSorry\n\ndef f (n : Nat) : Nat := n + 0\n\nexample : f 3 = 3 := by decide\n\n"
                     "theorem f_id : ∀ n : Nat, f n = n := by\n  sorry\n\nend BrokenSorry\n"),
}
EXPECT = {"gold": {"agent_compiles": True, "IC_ap": 1.0}, "broken_empty": {"agent_compiles": False, "IC_ap": 0.0, "IC_pp": 0.0},
          "broken_nocompile": {"agent_compiles": False, "IC_ap": 0.0, "IC_pp": 0.0},
          "broken_sorry": {"agent_compiles": True, "IC_ap": 1.0, "IC_pp": 0.0}}


def _minimal_pack(dest: Path, task_ids: list[str], task_toml: str) -> Path:
    for tid in task_ids:
        (dest / tid).mkdir(parents=True, exist_ok=True)
        (dest / tid / "task.toml").write_text(task_toml)
    return dest


def cmd_adapter_check(a) -> int:
    from rl4cv.veribench.jobs import materialize_jobs

    frozen = check_frozen()
    work = a.work
    if work.exists():
        raise FileExistsError(f"{work} exists; adapter checks are write-once")
    work.mkdir(parents=True)
    gold_root = SCORER / "veribench_dataset" / "lean_src" / "veribench"
    files = {f"gold_{Path(g).stem}": (gold_root / g).read_text(encoding="utf-8") for g in GOLD3}
    files.update(BROKEN)
    names = list(files)
    vb_ids = [Path(g).parent.name + "__" + Path(g).stem.lower() for g in GOLD3] + VB_IDS_BROKEN
    mb_ids = [f"{SPLIT}__task_{900001 + k}" for k in range(len(names))]
    task_toml = (a.pack / sorted(p.name for p in a.pack.iterdir() if p.is_dir())[0] / "task.toml").read_text()
    paths = {}
    # Path A: this experiment's identity (mbpp ids, placeholder gold dir, pack view with task.toml only).
    gold_a = work / "gold_a"
    (gold_a / SPLIT).mkdir(parents=True)
    for tid in mb_ids:
        (gold_a / SPLIT / f"{tid.split('__', 1)[1]}.lean").touch()
    pack_a = _minimal_pack(work / "pack_a", mb_ids, task_toml)
    rows_a = [{"task_id": tid, "sample_idx": 0, "model": "adapter-check", "lean": files[n]} for tid, n in zip(mb_ids, names)]
    job_a = materialize_jobs(rows_a, work / "jobs", "adapter_a")[0]
    rc_a = run_scorer(["--job-dir", str(job_a.resolve()), "--pack", str(pack_a), "--name", "adapter_a_s0", "--gold-dir", str(gold_a),
                       "--lake-dir", str(a.lake_dir), "--skip-tc", "--out-dir", str(work / "scores_a")], work / "scores_a.log", a.python)
    # Path B: the canonical VeriBench identity (VeriBench task ids, the pinned gold dir) on the same bytes.
    pack_b = _minimal_pack(work / "pack_b", vb_ids, task_toml)
    rows_b = [{"task_id": tid, "sample_idx": 0, "model": "adapter-check", "lean": files[n]} for tid, n in zip(vb_ids, names)]
    job_b = materialize_jobs(rows_b, work / "jobs", "adapter_b")[0]
    rc_b = run_scorer(["--job-dir", str(job_b.resolve()), "--pack", str(pack_b), "--name", "adapter_b_s0", "--gold-dir", str(gold_root),
                       "--lake-dir", str(a.lake_dir), "--skip-tc", "--out-dir", str(work / "scores_b")], work / "scores_b.log", a.python)
    pt_a, pt_b = per_task_rows(work / "scores_a"), per_task_rows(work / "scores_b")
    comparison, identical, expectations_met = [], True, True
    for n, ta, tb in zip(names, mb_ids, vb_ids):
        ra, rb = pt_a.get(ta, {}), pt_b.get(tb, {})
        fa = {k: ra.get(k) for k in FACTOR_FIELDS}
        fb = {k: rb.get(k) for k in FACTOR_FIELDS}
        same = fa == fb
        identical &= same
        exp = EXPECT["gold" if n.startswith("gold_") else n]
        met = all((_b(ra.get(k)) if isinstance(v, bool) else _f(ra.get(k))) == v for k, v in exp.items())
        expectations_met &= met
        cell = scored_cell({"task_id": ta, "served": True, "lean": files[n]}, ra or None, files[n])
        comparison.append({"file": n, "sha256": sha(files[n].encode("utf-8")), "bytes": len(files[n].encode("utf-8")), "mbpp_task_id": ta,
                           "veribench_task_id": tb, "factors_adapter": fa, "factors_canonical": fb, "identical": same, "expected": exp,
                           "expectations_met": met, "failure_class": cell["failure_class"], "kernel_binary": cell["kernel_binary"],
                           "n_vacuous": cell.get("n_vacuous")})
    gold_kept = all(c["kernel_binary"] == 1.0 for c in comparison if c["file"].startswith("gold_"))
    out = {"written_utc": stamp(), "scorer": frozen, "lake": lake_evidence(a.lake_dir), "scorer_exit_codes": {"adapter": rc_a, "canonical": rc_b},
           "work": str(work), "files": comparison, "all_identical": identical, "all_expectations_met": expectations_met,
           "gold_files_kernel_binary_1": gold_kept,
           "verdict": "PASS" if (rc_a == 0 and rc_b == 0 and identical and expectations_met and gold_kept) else "FAIL",
           "meaning": ("PASS: on identical Lean bytes, the mbpp placeholder-gold identity path and the canonical VeriBench identity path "
                       "yield the same IC_tests, IC_proofs, theorem counts and kernel axiom counts from the frozen scorer; the three gold "
                       "files are kept (kernel_binary = 1) and the three broken files are rejected as expected.")}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: out[k] for k in ("scorer_exit_codes", "all_identical", "all_expectations_met", "gold_files_kernel_binary_1", "verdict")}))
    for c in comparison:
        print(c["file"], c["failure_class"], c["factors_adapter"])
    return 0 if out["verdict"] == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--lake-dir", type=Path, default=DEFAULT_LAKE_DIR)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("placeholders"); p.add_argument("--pack", type=Path, required=True); p.add_argument("--gold-dir", type=Path, required=True)
    p = sub.add_parser("mapping-gate"); p.add_argument("--pack", type=Path, required=True); p.add_argument("--gold-dir", type=Path, required=True); p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("score")
    for flag in ("--cells", "--job-root", "--pack", "--gold-dir", "--scores-root", "--views-root"):
        p.add_argument(flag, type=Path, required=True)
    p.add_argument("--name", required=True)
    p = sub.add_parser("readback")
    for flag in ("--cells", "--job-root", "--scores-root", "--out"):
        p.add_argument(flag, type=Path, required=True)
    p.add_argument("--name", required=True)
    p = sub.add_parser("adapter-check"); p.add_argument("--pack", type=Path, required=True); p.add_argument("--work", type=Path, required=True); p.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    return {"placeholders": cmd_placeholders, "mapping-gate": cmd_mapping_gate, "score": cmd_score, "readback": cmd_readback,
            "adapter-check": cmd_adapter_check}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
