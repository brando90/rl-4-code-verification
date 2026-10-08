#!/usr/bin/env python3
"""TLDR: PROTOCOL § 6 generated-Lean screen for experiment 08: every kept, extraction-consistent teacher cell (kernel_binary = 1) has its extracted Lean file, its full assistant response and each fenced code block screened separately with `rl4cv.screens` (exact normalized hash; word-5-gram Jaccard >= 0.70) against the validation and test splits' Python programs and gold Lean references; a hit in any text excludes the whole example and is listed with its nearest file and score, receipts and `kernel_binary` stay unchanged, and the maximum Jaccard to the task's own gold is reported as a diagnostic (zero model calls)."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "src"))
EXP = Path(__file__).resolve().parents[1]
THRESHOLD, SHINGLE_N = 0.70, 5
FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.S)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def manifest_rows() -> dict[str, dict]:
    with (EXP / "results" / "split" / "vbv1_split_manifest.csv").open(encoding="utf-8", newline="") as fh:
        return {r["task_id"]: r for r in csv.DictReader(fh)}


def protected_texts(veribench_root: Path, rows: dict[str, dict], splits: tuple[str, ...]) -> dict[str, str]:
    dataset = veribench_root / "veribench_dataset"
    out = {}
    for tid, r in rows.items():
        if r["split"] in splits:
            out[f"{r['split']}/py/{tid}"] = (dataset / "py_src" / r["py_relpath"]).read_text(encoding="utf-8", errors="replace")
            out[f"{r['split']}/lean/{tid}"] = (dataset / "lean_src" / "veribench" / r["gold_relpath"]).read_text(encoding="utf-8", errors="replace")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scored", type=Path, default=EXP / "results" / "scored_cells.jsonl")
    ap.add_argument("--job-root", type=Path, required=True, help="jobs root holding <teacher>_<r>_s0/<task_id>/verifier/solution.lean")
    ap.add_argument("--veribench-root", type=Path, default=REPO_ROOT / "external" / "veribench")
    ap.add_argument("--out", type=Path, default=EXP / "results" / "generated_lean_screen.json")
    a = ap.parse_args(argv)
    from rl4cv.screens import jaccard, screen, shingles

    rows = [json.loads(l) for l in a.scored.read_text(encoding="utf-8").splitlines() if l.strip()]
    kept = [r for r in rows if r.get("kernel_binary") == 1.0 and r.get("extraction_consistent") is True and r.get("phase", "main") == "main"]
    rows_m = manifest_rows()
    dataset = a.veribench_root / "veribench_dataset"
    pool, cells, own_gold = {}, {}, {}
    for r in kept:
        cid = f"{r['teacher']}/{r['r']}/{r['task_id']}"
        lean_path = a.job_root / f"{r['teacher']}_{r['r']}_s0" / r["task_id"] / "verifier" / "solution.lean"
        lean = lean_path.read_text(encoding="utf-8")
        if sha(lean.encode("utf-8")) != r["lean_sha256"]:
            raise RuntimeError(f"{cid}: file hash differs from scored_cells")
        response = Path(r["response_path"]).read_text(encoding="utf-8", errors="replace")
        if sha(response.encode("utf-8")) != r["response_text_sha256"]:
            raise RuntimeError(f"{cid}: response hash differs from scored_cells")
        texts = {f"{cid}#file": lean, f"{cid}#response": response}
        for i, block in enumerate(FENCE_RE.findall(response)):
            texts[f"{cid}#block{i}"] = block
        pool.update(texts)
        cells[cid] = sorted(texts)
        own_gold[cid] = (dataset / "lean_src" / "veribench" / rows_m[r["task_id"]]["gold_relpath"]).read_text(encoding="utf-8", errors="replace")
    protected = protected_texts(a.veribench_root, rows_m, ("validation", "test"))
    rep = screen(pool, protected, n=SHINGLE_N, threshold=THRESHOLD) if pool else {"n_pool": 0, "n_exact": 0, "n_near": 0, "exact": [], "near": [], "clean_ids": []}
    hits = {h["item_id"]: h for h in rep["exact"] + rep["near"]}
    prot_sh = {k: shingles(v) for k, v in protected.items()}
    per_cell, excluded = {}, {}
    for cid, names in cells.items():
        best = (0.0, None)
        for n in names:
            sh = shingles(pool[n])
            for pid, p in prot_sh.items():
                j = jaccard(sh, p)
                if j > best[0]:
                    best = (j, pid)
        own = jaccard(shingles(pool[f"{cid}#file"]), shingles(own_gold[cid]))
        cell_hits = [hits[n] for n in names if n in hits]
        per_cell[cid] = {"max_word5_jaccard_heldout": round(best[0], 4), "nearest_heldout": best[1], "own_gold_jaccard_diagnostic": round(own, 4), "n_texts": len(names),
                         "hits": cell_hits}
        if cell_hits:
            excluded[cid] = cell_hits
    out = {"written_utc": stamp(), "veribench_root": str(a.veribench_root.resolve()), "threshold": THRESHOLD, "shingle_n": SHINGLE_N,
           "protected": {"n_files": len(protected), "splits": ["validation", "test"], "kinds": ["python program", "gold Lean"]},
           "n_kept_cells_screened": len(cells), "n_texts_screened": len(pool), "n_exact": rep["n_exact"], "n_near": rep["n_near"],
           "n_excluded_cells": len(excluded), "excluded_cells": {k: v for k, v in sorted(excluded.items())}, "clean_cells": sorted(c for c in cells if c not in excluded),
           "max_heldout_jaccard_among_clean": max((v["max_word5_jaccard_heldout"] for k, v in per_cell.items() if k not in excluded), default=None),
           "own_gold_jaccard_diagnostic": {"mean": round(sum(v["own_gold_jaccard_diagnostic"] for v in per_cell.values()) / len(per_cell), 4) if per_cell else None,
                                           "max": max((v["own_gold_jaccard_diagnostic"] for v in per_cell.values()), default=None)},
           "per_cell": per_cell}
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("n_kept_cells_screened", "n_texts_screened", "n_exact", "n_near", "n_excluded_cells", "max_heldout_jaccard_among_clean", "own_gold_jaccard_diagnostic")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
