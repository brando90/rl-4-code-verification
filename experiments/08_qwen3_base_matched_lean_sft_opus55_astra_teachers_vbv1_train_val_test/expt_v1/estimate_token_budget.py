"""Zero-call SFT token-budget inputs: Qwen3 token lengths of VeriBench gold Lean files and experiment 103's single-call teacher yields per D-013 split.

Subcommands:
  gold  --veribench-root <checkout at the pin>                       (any host with the Qwen3 tokenizer)
  e103  --private <VeriBench experiment 103 private/ dir on skampere1> (host-only receipts, read-only)
Both read the split manifest committed next to this script and write JSON under results/.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "results" / "split" / "vbv1_split_manifest.csv"
TOKENIZER = ("Qwen/Qwen3-8B-Base", "49e3418fbbbca6ecbdf9608b4d22e5a407081db4")
E103_MODELS = ("claude-opus-5-max", "gpt-6-astra-high")


def _tokenizer():
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(TOKENIZER[0], revision=TOKENIZER[1])


def _stats(xs: list[int]) -> dict:
    xs = sorted(xs)
    if not xs:
        return {"n": 0}
    return {"n": len(xs), "mean": round(st.mean(xs)), "median": xs[len(xs) // 2], "p90": xs[int(len(xs) * 0.9)], "max": xs[-1], "total": sum(xs)}


def _manifest() -> list[dict]:
    with open(MANIFEST, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def gold(veribench_root: Path) -> dict:
    tok = _tokenizer()
    lean_root = veribench_root / "veribench_dataset" / "lean_src" / "veribench"
    py_root = veribench_root / "veribench_dataset" / "py_src"
    out = {}
    for split in ("train", "validation", "test"):
        rows = [r for r in _manifest() if r["split"] == split]
        n = lambda p: len(tok(p.read_text(encoding="utf-8"), add_special_tokens=False)["input_ids"])  # noqa: E731
        out[split] = {"gold_lean_tokens": _stats([n(lean_root / r["gold_relpath"]) for r in rows]), "python_tokens": _stats([n(py_root / r["py_relpath"]) for r in rows])}
    return {"tokenizer": TOKENIZER, "by_split": out}


def e103(private: Path) -> dict:
    """Kernel-pass proxy: IC_tests = IC_proofs = 1 with >= 1 theorem and >= 1 example (no vacuity check)."""
    tok = _tokenizer()
    split_of = {r["task_id"]: r["split"] for r in _manifest()}
    out: dict = {"proxy": "IC_ap == 1 and IC_pp == 1 and kernel_n_theorems >= 1 and agent_n_ex >= 1; vacuity not checked", "models": {}}
    passed: dict[str, set[str]] = {}
    for m in E103_MODELS:
        with open(private / "scsc_vbv1" / m / f"scsc_expt103-single-call-vbv1-{m}_{m}_per_task.csv", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        ok_all = {
            r["task"]
            for r in rows
            if r["submission_status"] != "empty" and r["IC_ap"] == "1.0" and r["IC_pp"] == "1.0" and int(r["kernel_n_theorems"] or 0) >= 1 and int(r["agent_n_ex"] or 0) >= 1
        }
        passed[m] = ok_all
        for split in ("train", "validation", "test"):
            sel = [r for r in rows if split_of.get(r["task"]) == split]
            measured = [r for r in sel if r["submission_status"] != "empty"]
            ok = [r for r in sel if r["task"] in ok_all]
            lens = []
            for r in ok:
                f = private / "jobs" / m / r["task"] / "verifier" / "solution.lean"
                if f.is_file():
                    lens.append(len(tok(f.read_text(encoding="utf-8"), add_special_tokens=False)["input_ids"]))
            out["models"].setdefault(m, {})[split] = {"tasks": len(sel), "measured": len(measured), "kernel_pass_proxy": len(ok), "kernel_pass_share_of_tasks": round(len(ok) / max(1, len(sel)), 4), "passing_lean_tokens": _stats(lens)}
    train = {t for t, s in split_of.items() if s == "train"}
    out["train_union_tasks"] = len((passed[E103_MODELS[0]] | passed[E103_MODELS[1]]) & train)
    out["train_intersection_tasks"] = len((passed[E103_MODELS[0]] & passed[E103_MODELS[1]]) & train)
    out["train_tasks"] = len(train)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gold")
    g.add_argument("--veribench-root", required=True, type=Path)
    g.add_argument("--out", type=Path, default=HERE / "results" / "token_budget_gold_lengths.json")
    e = sub.add_parser("e103")
    e.add_argument("--private", required=True, type=Path)
    e.add_argument("--out", type=Path, default=HERE / "results" / "token_budget_e103_teacher_yields.json")
    args = ap.parse_args(argv)
    res = gold(args.veribench_root) if args.cmd == "gold" else e103(args.private)
    args.out.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=1)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
