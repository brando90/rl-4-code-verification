"""Score experiment 18a responses with Reasoning Gym's own score_answer (GSM8K: exact numeric match), CPU only.

Reads <run>/raw/<model_tag>/<set>.jsonl, regenerates each RG entry from the frozen config (refusing if the question
hash differs from build time) and writes compact rows to <run>/scored/<model_tag>/<set>.jsonl. Usage:

    python score.py --run ~/e18a/run --model-tag qwen3_0p6b
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e18a_common as C  # noqa: E402


def score_set(run: Path, model_tag: str, spec: C.SetSpec, n_items_built: int, raw_root: Path, out_root: Path) -> int:
    raw = raw_root / model_tag / f"{spec.file_stem}.jsonl"
    if not raw.exists():
        print(f"missing {spec.set_id} for {model_tag}", flush=True)
        return 0
    items = {it["item_id"]: it for it in C.read_jsonl(run / "items" / f"{spec.file_stem}.jsonl")}
    ds = C.rg_dataset(spec, n_items_built) if spec.source == "rg" else None
    entries: dict[str, dict] = {}
    rows = []
    for r in C.read_jsonl(raw):
        item = items[r["item_id"]]
        if r["question_sha256"] != item["question_sha256"]:
            raise RuntimeError(f"{r['item_id']}: response was generated for a different question")
        extracted = C.extract_answer(r["text"])
        if ds is not None:
            if r["item_id"] not in entries:
                entry = ds[item["idx"]]
                if C.sha256_text(entry["question"]) != item["question_sha256"]:
                    raise RuntimeError(f"{r['item_id']}: regenerated RG entry differs from the built item")
                entries[r["item_id"]] = entry
            try:
                score = float(ds.score_answer(extracted, entries[r["item_id"]]))
                error = None
            except Exception as exc:  # a verifier crash on a malformed answer is a failed answer, recorded
                score, error = 0.0, f"{type(exc).__name__}: {exc}"[:200]
        else:
            score, error = C.gsm8k_score(extracted, item["gold"]), None
        rows.append({"set_id": spec.set_id, "item_id": r["item_id"], "sample": r["sample"], "score": score,
                     "pass": 1.0 if C.is_pass(score) else 0.0, "has_answer_tag": extracted is not None,
                     "capped": r["finish_reason"] == "length", "generated_tokens": r["generated_tokens"],
                     "model_tag": model_tag, "backend_version": r.get("backend_version"),
                     "score_error": error})
    return C.write_jsonl_atomic(out_root / model_tag / f"{spec.file_stem}.jsonl", rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", required=True)
    ap.add_argument("--model-tag", required=True, choices=sorted(C.MODELS))
    ap.add_argument("--sets", default="all")
    ap.add_argument("--raw-subdir", default="", help="smoke only: read raw_<subdir>, write scored_<subdir>")
    args = ap.parse_args(argv)
    run = Path(args.run)
    manifest = json.loads((run / "items" / "manifest.json").read_text())
    n_built = {m["set_id"]: m["n_items"] for m in manifest["sets"]}
    raw_root = run / (f"raw_{args.raw_subdir}" if args.raw_subdir else "raw")
    out_root = run / (f"scored_{args.raw_subdir}" if args.raw_subdir else "scored")
    for spec in C.select_sets(args.sets):
        if spec.set_id not in n_built:
            continue
        n = score_set(run, args.model_tag, spec, n_built[spec.set_id], raw_root, out_root)
        if n:
            print(f"scored {spec.set_id}: {n} responses", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
