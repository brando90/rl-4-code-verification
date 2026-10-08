#!/usr/bin/env python3
"""TLDR: Screen every kept teacher Lean file (kernel_binary = 1) against VeriBench `lean_src` and `py_src` and every declared held-out panel's files available at the pin (exact normalized hash; word-5-gram Jaccard >= 0.70) before it may enter the SFT set; hits are excluded and reported, cell receipts and `kernel_binary` stay unchanged (experiment 02A v3 PROTOCOL § 2; zero model calls)."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rl4cv.screens import jaccard, screen, shingles  # noqa: E402
from screen_mbpp_tasks import protected_corpus  # noqa: E402

THRESHOLD, SHINGLE_N = 0.70, 5
# Held-out panels beyond VeriBench V1 whose files may exist at the VeriBench pin (VeriBench V2 / V2.1 come from VeriSoftBench).
# At the pin, VeriBench V2's five full-source task inputs live under a private directory that is not checked in, so only the
# E97-P001 multi-file task (Python sources and tests) is available; its files are screened, and the absence of the rest is reported.
PANEL_DIRS = ("experiments/97_vsb_multifile_python_to_lean/task",
              "experiments/91_lean_to_python_hopefully_unsaturated_vb/expt_v5_full_source/data",
              "experiments/91_lean_to_python_hopefully_unsaturated_vb/expt_v5_full_source/private")
PANEL_EXCLUDE = ("scripts/", "runs/", "/results/", "__pycache__", ".lake/")


def panel_corpus(veribench_root: Path) -> dict[str, str]:
    out = {}
    for rel in PANEL_DIRS:
        base = veribench_root / rel
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if p.suffix in (".lean", ".py") and p.is_file() and not any(x in str(p) for x in PANEL_EXCLUDE):
                out[str(p.relative_to(veribench_root))] = p.read_text(encoding="utf-8", errors="replace")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scored", type=Path, required=True, help="scored_cells.jsonl (all teachers)")
    ap.add_argument("--job-root", type=Path, required=True, help="jobs root holding <teacher>_s0/<task_id>/verifier/solution.lean")
    ap.add_argument("--veribench-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    rows = [json.loads(l) for l in a.scored.read_text(encoding="utf-8").splitlines() if l.strip()]
    kept = [r for r in rows if r.get("kernel_binary") == 1.0]
    pool = {}
    for r in kept:
        p = a.job_root / f"{r['teacher']}_s0" / r["task_id"] / "verifier" / "solution.lean"
        text = p.read_text(encoding="utf-8")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != r["lean_sha256"]:
            raise RuntimeError(f"{r['teacher']}/{r['task_id']}: file hash differs from scored_cells")
        pool[f"{r['teacher']}/{r['task_id']}"] = text
    vb = protected_corpus(a.veribench_root)
    panels = panel_corpus(a.veribench_root)
    protected = {**{"veribench_dataset/" + k: v for k, v in vb.items()}, **panels}
    report = screen(pool, protected, n=SHINGLE_N, threshold=THRESHOLD) if pool else {"n_pool": 0, "n_exact": 0, "n_near": 0, "exact": [], "near": [], "clean_ids": []}
    prot_sh = {pid: shingles(t) for pid, t in protected.items()}
    per_cell = {}
    for cid, text in pool.items():
        sh = shingles(text)
        best = max(((jaccard(sh, p), pid) for pid, p in prot_sh.items()), default=(0.0, None))
        per_cell[cid] = {"max_word5_jaccard": round(best[0], 4), "nearest": best[1]}
    excluded = sorted({h["item_id"] for h in report["exact"]} | {h["item_id"] for h in report["near"]})
    out = {"written_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "veribench_root": str(a.veribench_root.resolve()),
           "protected": {"n_veribench_files": len(vb), "n_panel_files": len(panels), "panel_dirs_present": [d for d in PANEL_DIRS if (a.veribench_root / d).is_dir()],
                         "threshold": THRESHOLD, "shingle_n": SHINGLE_N},
           "n_kept_cells_screened": len(pool), "n_exact": report["n_exact"], "n_near": report["n_near"], "excluded_cells": excluded,
           "exact": report["exact"], "near": report["near"], "clean_cells": sorted(report["clean_ids"]),
           "max_jaccard_among_clean": max((v["max_word5_jaccard"] for k, v in per_cell.items() if k not in excluded), default=None),
           "per_cell": per_cell}
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("n_kept_cells_screened", "n_exact", "n_near", "max_jaccard_among_clean")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
