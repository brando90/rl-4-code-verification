#!/usr/bin/env python3
"""TLDR: Screen the rewritten MBPP Python files against the pinned VeriBench corpus (exact normalized hash and word-5-gram Jaccard >= 0.70 over py_src and lean_src) with `rl4cv.screens`, and write the screen report and the sorted declared manifest with its SHA-256 (experiment 02A v3 PROTOCOL § 2; zero model calls)."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rl4cv.screens import screen  # noqa: E402

THRESHOLD = 0.70
SHINGLE_N = 5


def protected_corpus(veribench_root: Path) -> dict[str, str]:
    """Every VeriBench py_src *.py and every non-build, non-playground lean_src *.lean (expt_v2 build_fvapps_external24.py)."""
    dataset = veribench_root / "veribench_dataset"
    py_root, lean_root = dataset / "py_src", dataset / "lean_src"
    if not py_root.is_dir() or not lean_root.is_dir():
        raise FileNotFoundError("expected VeriBench veribench_dataset/{py_src,lean_src}")
    files = [p for p in py_root.rglob("*.py") if "__pycache__" not in p.parts]
    files += [p for p in lean_root.rglob("*.lean") if ".lake" not in p.parts and "lean-playground" not in p.parts]
    corpus = {str(p.relative_to(dataset)): p.read_text(encoding="utf-8", errors="replace") for p in sorted(files)}
    if not corpus:
        raise RuntimeError("protected VeriBench corpus is empty; contamination screening fails closed")
    return corpus


def git_head(root: Path) -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()


def pinned_commit(lock: Path, name: str) -> str:
    return json.loads(lock.read_text())[name]["commit"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rewrite-manifest", type=Path, required=True)
    ap.add_argument("--veribench-root", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--declared-manifest", type=Path, required=True)
    args = ap.parse_args(argv)
    for p in (args.report, args.declared_manifest):
        if p.exists():
            raise FileExistsError(f"refusing to overwrite {p}")
    pin = pinned_commit(REPO_ROOT / "external" / "deps.lock.json", "veribench")
    head = git_head(args.veribench_root)
    if head != pin:
        raise RuntimeError(f"VeriBench checkout {head} is not the pinned {pin}")
    rewrite = json.loads(args.rewrite_manifest.read_text())
    pool: dict[str, str] = {}
    for t in rewrite["kept"]:
        text = Path(t["path"]).read_text(encoding="utf-8")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != t["sha256"]:
            raise RuntimeError(f"{t['task_id']}: file changed since the rewrite manifest")
        pool[t["task_id"]] = text
    protected = protected_corpus(args.veribench_root)
    report = screen(pool, protected, n=SHINGLE_N, threshold=THRESHOLD)
    clean = sorted(report["clean_ids"])
    by_id = {t["task_id"]: t for t in rewrite["kept"]}
    tasks = [{"task_id": tid, "mbpp_task_id": by_id[tid]["mbpp_task_id"], "lean_stem": by_id[tid]["lean_stem"],
              "function": by_id[tid]["function"], "py_sha256": by_id[tid]["sha256"]} for tid in clean]
    ids_text = "".join(tid + "\n" for tid in clean)
    declared = {
        "manifest_kind": "declared_manifest_e02a_v3",
        "written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_rewrite_manifest_sha256": hashlib.sha256(args.rewrite_manifest.read_bytes()).hexdigest(),
        "veribench_pin": pin,
        "n_tasks": len(tasks),
        "task_ids_sha256": hashlib.sha256(ids_text.encode("utf-8")).hexdigest(),
        "tasks": tasks,
    }
    out = {
        "written_utc": declared["written_utc"],
        "veribench_root": str(args.veribench_root.resolve()), "veribench_head": head, "veribench_pin": pin,
        "protected_corpus": {"n_files": len(protected), "n_py": sum(1 for k in protected if k.endswith(".py")),
                             "n_lean": sum(1 for k in protected if k.endswith(".lean")),
                             "exact_hash_normalization": "rl4cv.screens.normalize", "word_shingle_n": SHINGLE_N,
                             "near_duplicate_threshold": THRESHOLD},
        "n_pool": report["n_pool"], "n_exact": report["n_exact"], "n_near": report["n_near"], "n_clean": len(clean),
        "exact": report["exact"], "near": report["near"],
        "max_jaccard_among_clean": max((h for h in _all_hits(pool, protected, report)), default=None),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    body = json.dumps(declared, indent=1, sort_keys=True) + "\n"
    args.declared_manifest.write_text(body, encoding="utf-8")
    (args.declared_manifest.with_suffix(".sha256")).write_text(hashlib.sha256(body.encode("utf-8")).hexdigest() + "  " + args.declared_manifest.name + "\n")
    print(json.dumps({"n_pool": report["n_pool"], "n_exact": report["n_exact"], "n_near": report["n_near"], "n_clean": len(clean),
                      "task_ids_sha256": declared["task_ids_sha256"], "declared_manifest_sha256": hashlib.sha256(body.encode()).hexdigest()}))
    return 0


def _all_hits(pool, protected, report):
    """Near-miss distribution among clean items is informative: recompute max Jaccard per clean id from the screen output."""
    # rl4cv.screens.screen only lists hits at or above the threshold; re-run per-item for the clean ones is O(n) and cheap.
    from rl4cv.screens import jaccard, shingles
    prot = {pid: shingles(t) for pid, t in protected.items()}
    for iid in report["clean_ids"]:
        sh = shingles(pool[iid])
        yield max((jaccard(sh, p) for p in prot.values()), default=0.0)


if __name__ == "__main__":
    raise SystemExit(main())
