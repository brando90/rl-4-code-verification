#!/usr/bin/env python3
"""TLDR: Build the served train pack for experiment 08's collect-only Valkyrie service (539 D-013 train tasks: experiment 103's `instruction.md` byte for byte plus a placeholder `tests/test.sh` and `task.toml`, never `solution/` or any gold), check every instruction hash against experiment 05's receipts, verify the pack holds no `.lean` file or theorem text outside the instructions, screen the system prompt, addendum and every instruction against the validation and test splits with `rl4cv.screens`, and write `results/pack_check.json` (PROTOCOL § 2; zero model calls)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "src"))
EXP = Path(__file__).resolve().parents[1]
SPLIT_DIR = EXP / "results" / "split"
E103_PRIVATE = Path("/lfs/skampere1/0/brando9/veribench_vb103/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private")
E103_PACK = E103_PRIVATE / "packs" / "vbv1_896"
E05_GEN = Path("/lfs/skampere1/0/brando9/rl4cv_e05/out/raw/gen_qwen3-8b-base_g8.jsonl")
CANARY = "rl4cv_e08_placeholder_canary"
# Mirrors experiment 103's service loader: the first instruction line must be an agent-spec stamp and test.sh needs a SOLUTION_FILE line.
AGENT_SPEC_RE = re.compile(r"^<!-- VeriBench agent-spec v([2-9]|[1-9][0-9]+)([ :].*)? -->\r?$")
SOLUTION_FILE_RE = re.compile(r'^SOLUTION_FILE="/home/user/lean_project/Veribench/([A-Za-z0-9_]+)\.lean"$', re.M)
THEOREM_RE = re.compile(r"\btheorem\b")
EXPECTED_SYSTEM_SHA = "dc051963de1199dd4f77c9f8f96218eb45be331c819b8e76693b063b206143cd"
EXPECTED_ADDENDUM_SHA = "a7a0fc1b7be6b4ede41fd6b31e1e1dcae3d2fd320a6cddf9b311cf55855a18f5"
PLACEHOLDER_TEST_SH = """#!/bin/bash
# Placeholder verifier for experiment 08's collect-only Valkyrie service. It is never executed: the service reads only the
# SOLUTION_FILE line below to learn where the agent must write its Lean file (VB_COLLECT_ONLY=1, VB_NO_COMPILER=1).
SOLUTION_FILE="/home/user/lean_project/Veribench/{stem}.lean"
CANARY="{canary}"
echo "placeholder verifier: not executed (canary $CANARY)" >&2
exit 1
"""
PLACEHOLDER_TASK_TOML = """version = "1.1"

[agent]
timeout_sec = 3600.0
env = {{}}

[verifier]
timeout_sec = 3600.0
env = {{}}

[environment]
allow_internet = true
build_timeout_sec = 3600.0
"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_ids(path: Path) -> list[str]:
    return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def e05_instruction_hashes() -> dict[str, str]:
    """instruction_sha256 per task from experiment 05's raw generation rows (read-only; rows must agree per task)."""
    out: dict[str, str] = {}
    with E05_GEN.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            t, h = r["task_id"], r["instruction_sha256"]
            if out.get(t, h) != h:
                raise RuntimeError(f"{t}: experiment 05 rows disagree on instruction_sha256")
            out[t] = h
    return out


def manifest_rows() -> dict[str, dict]:
    import csv

    with (SPLIT_DIR / "vbv1_split_manifest.csv").open(encoding="utf-8", newline="") as fh:
        return {r["task_id"]: r for r in csv.DictReader(fh)}


def protected_texts(veribench_root: Path, rows: dict[str, dict], splits: tuple[str, ...]) -> dict[str, str]:
    """Validation and test Python programs and gold Lean references at the VeriBench pin (the held-out corpus)."""
    dataset = veribench_root / "veribench_dataset"
    out = {}
    for tid, r in rows.items():
        if r["split"] not in splits:
            continue
        py = dataset / "py_src" / r["py_relpath"]
        lean = dataset / "lean_src" / "veribench" / r["gold_relpath"]
        out[f"{r['split']}/py/{tid}"] = py.read_text(encoding="utf-8", errors="replace")
        out[f"{r['split']}/lean/{tid}"] = lean.read_text(encoding="utf-8", errors="replace")
    return out


def build(out: Path, ids: list[str]) -> list[dict]:
    rows = []
    for tid in ids:
        src = E103_PACK / tid
        instruction = (src / "instruction.md").read_bytes()
        if not AGENT_SPEC_RE.match(instruction.decode("utf-8").splitlines()[0]):
            raise RuntimeError(f"{tid}: instruction is not stamped agent-spec v<N>")
        m = SOLUTION_FILE_RE.search((src / "tests" / "test.sh").read_text(encoding="utf-8"))
        if not m:
            raise RuntimeError(f"{tid}: experiment 103's test.sh has no SOLUTION_FILE line")
        stem = m.group(1)
        d = out / tid
        (d / "tests").mkdir(parents=True)
        (d / "instruction.md").write_bytes(instruction)
        test_sh = PLACEHOLDER_TEST_SH.format(stem=stem, canary=CANARY)
        (d / "tests" / "test.sh").write_text(test_sh, encoding="utf-8")
        (d / "task.toml").write_text(PLACEHOLDER_TASK_TOML.format(), encoding="utf-8")
        rows.append({"task_id": tid, "lean_stem": stem, "required_path": f"/home/user/lean_project/Veribench/{stem}.lean",
                     "instruction_sha256": sha(instruction), "instruction_bytes": len(instruction), "test_sh_sha256": sha(test_sh.encode("utf-8"))})
    return rows


def audit_pack(out: Path, ids: list[str]) -> dict:
    """No `.lean` file, no `solution/` or `gold` anywhere, and no theorem text outside instruction.md."""
    lean_files, solution_dirs, gold_files, theorem_outside, extra_files = [], [], [], [], []
    allowed = {"instruction.md", "tests/test.sh", "task.toml"}
    for root, dirs, files in os.walk(out):
        for d in dirs:
            if d == "solution":
                solution_dirs.append(os.path.join(root, d))
        for f in files:
            p = Path(root) / f
            rel = str(p.relative_to(out / p.relative_to(out).parts[0]))
            if p.suffix == ".lean":
                lean_files.append(str(p))
            if "gold" in f.lower():
                gold_files.append(str(p))
            if rel not in allowed:
                extra_files.append(str(p))
            if rel != "instruction.md" and THEOREM_RE.search(p.read_text(encoding="utf-8", errors="replace")):
                theorem_outside.append(str(p))
    n_dirs = len([p for p in out.iterdir() if p.is_dir()])
    return {"n_task_dirs": n_dirs, "n_task_dirs_expected": len(ids), "lean_files": lean_files, "solution_dirs": solution_dirs, "gold_files": gold_files,
            "theorem_text_outside_instruction": theorem_outside, "unexpected_files": extra_files,
            "ok": n_dirs == len(ids) and not lean_files and not solution_dirs and not gold_files and not theorem_outside and not extra_files}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True, help="served pack directory (write-once)")
    ap.add_argument("--veribench-root", type=Path, default=REPO_ROOT / "external" / "veribench")
    ap.add_argument("--check-out", type=Path, default=EXP / "results" / "pack_check.json")
    a = ap.parse_args(argv)
    from rl4cv.screens import jaccard, screen, shingles
    from rl4cv.veribench.exp103 import ADDENDUM_REL, build_prompt, load_single_call

    if a.out.exists():
        raise FileExistsError(f"{a.out} exists; the served pack is write-once")
    ids = read_ids(SPLIT_DIR / "vbv1_train_task_ids.txt")
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise RuntimeError("train ids must be sorted and unique")
    rows_m = manifest_rows()
    if any(rows_m[t]["split"] != "train" for t in ids) or sum(1 for r in rows_m.values() if r["split"] == "train") != len(ids):
        raise RuntimeError("train id list disagrees with the split manifest")
    a.out.mkdir(parents=True)
    rows = build(a.out, ids)
    # 2. Instruction hashes versus experiment 05's receipts.
    e05 = e05_instruction_hashes()
    mismatches = [r["task_id"] for r in rows if e05.get(r["task_id"]) != r["instruction_sha256"]]
    # Experiment 103's exact messages (system prompt + addendum) and the per-task prompt hashes.
    prompts = {}
    for r in rows:
        p = build_prompt((a.out / r["task_id"] / "instruction.md").read_text(encoding="utf-8"), root=a.veribench_root)
        if p.required_paths != (r["required_path"],):
            raise RuntimeError(f"{r['task_id']}: required paths {p.required_paths} != ({r['required_path']},)")
        r["prompt_sha256"], r["prompt_bytes"] = p.prompt_sha256, len(p.user.encode("utf-8"))
        prompts[r["task_id"]] = p
    any_p = next(iter(prompts.values()))
    mod = load_single_call(str(a.veribench_root))
    addendum_text = (a.veribench_root / ADDENDUM_REL.format(name="vbv1")).read_text(encoding="utf-8")
    audit = audit_pack(a.out, ids)
    # 3. Held-out screen: system prompt, addendum and every train instruction versus validation + test Python and gold Lean.
    protected = protected_texts(a.veribench_root, rows_m, ("validation", "test"))
    pool = {"system_prompt": mod.SYSTEM_PROMPT, "addendum_vbv1": addendum_text}
    pool.update({f"instruction/{r['task_id']}": (a.out / r["task_id"] / "instruction.md").read_text(encoding="utf-8") for r in rows})
    rep = screen(pool, protected, n=5, threshold=0.70)
    prot_sh = {k: shingles(v) for k, v in protected.items()}
    def best(text: str) -> tuple[float, str | None]:
        sh = shingles(text)
        return max(((jaccard(sh, p), k) for k, p in prot_sh.items()), default=(0.0, None))
    fixed = {k: dict(zip(("max_word5_jaccard", "nearest"), best(pool[k]))) for k in ("system_prompt", "addendum_vbv1")}
    inst_best = [best(pool[f"instruction/{r['task_id']}"]) for r in rows]
    max_inst = max(inst_best, key=lambda x: x[0]) if inst_best else (0.0, None)
    # The train instruction also embeds its own (train) Python program; its similarity to its own gold is a diagnostic only.
    check = {
        "written_utc": stamp(), "pack_dir": str(a.out.resolve()), "n_tasks": len(rows), "task_ids_sha256": sha("".join(i + "\n" for i in ids).encode()),
        "source_pack": str(E103_PACK), "copied": "instruction.md bytes only; tests/test.sh and task.toml are placeholders (canary %s); no solution/, gold or judge files" % CANARY,
        "placeholder_task_toml_sha256": sha(PLACEHOLDER_TASK_TOML.format().encode("utf-8")),
        "instruction_hash_check": {"source": str(E05_GEN), "n_compared": len(rows), "n_mismatch": len(mismatches), "mismatches": mismatches,
                                   "ok": not mismatches and len(e05) == 896},
        "pack_audit": audit,
        "prompt": {"system_prompt_sha256": any_p.system_prompt_sha256, "system_prompt_expected": EXPECTED_SYSTEM_SHA,
                   "addendum_sha256": any_p.addendum_sha256, "addendum_expected": EXPECTED_ADDENDUM_SHA,
                   "user_message": "instruction.rstrip() + '\\n\\n---\\n\\n' + addendum_vbv1.md (rl4cv.veribench.exp103.build_prompt)",
                   "ok": any_p.system_prompt_sha256 == EXPECTED_SYSTEM_SHA and any_p.addendum_sha256 == EXPECTED_ADDENDUM_SHA,
                   "mean_prompt_bytes": round(sum(r["prompt_bytes"] for r in rows) / len(rows))},
        "heldout_screen": {"protected": {"n_files": len(protected), "splits": ["validation", "test"], "kinds": ["python program", "gold Lean"]},
                           "threshold": 0.70, "shingle_n": 5, "n_pool": rep["n_pool"], "n_exact": rep["n_exact"], "n_near": rep["n_near"],
                           "exact": rep["exact"], "near": rep["near"], "fixed_texts": fixed,
                           "instructions_max_word5_jaccard": {"value": round(max_inst[0], 4), "nearest": max_inst[1]},
                           "ok": rep["n_exact"] == 0 and rep["n_near"] == 0},
        "tasks": rows,
    }
    check["verdict"] = "PASS" if (check["instruction_hash_check"]["ok"] and audit["ok"] and check["prompt"]["ok"] and check["heldout_screen"]["ok"]) else "FAIL"
    a.check_out.parent.mkdir(parents=True, exist_ok=True)
    a.check_out.write_text(json.dumps(check, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": check["verdict"], "n_tasks": len(rows), "hash_mismatches": len(mismatches), "audit_ok": audit["ok"],
                      "screen": {k: check["heldout_screen"][k] for k in ("n_exact", "n_near", "instructions_max_word5_jaccard")},
                      "system_prompt_sha256": any_p.system_prompt_sha256[:16], "addendum_sha256": any_p.addendum_sha256[:16]}))
    return 0 if check["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
