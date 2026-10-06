"""Check experiment 05's preflight: locked prompt hashes, Base vs post-trained chat-template rendering, stop-token behavior and scoring.

Usage (on the GPU host, inside experiment 01's venv with this repository's src on PYTHONPATH):

    python preflight_check_e05.py --model Qwen/Qwen3-1.7B-Base --revision <sha> --gen gen_pf.jsonl \\
        --scored scored_pf.jsonl --pack PACK --ids preflight_ids.txt --out preflight.json

Exits 0 when every PROTOCOL.md preflight condition holds, 1 otherwise; the JSON receipt is written either way.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import sys
from pathlib import Path

from rl4cv.veribench.exp103 import build_prompt
from rl4cv.veribench.pack import load_pack, read_task_ids

LOCKED = {
    "addendum_sha256": "a7a0fc1b7be6b4ede41fd6b31e1e1dcae3d2fd320a6cddf9b311cf55855a18f5",
    "system_prompt_sha256": "dc051963de1199dd4f77c9f8f96218eb45be331c819b8e76693b063b206143cd",
}
# Experiment 01's post-trained Qwen3-1.7B, whose rendering experiment 01's probe used.
REFERENCE = ("Qwen/Qwen3-1.7B", "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--model", required=True)
    ap.add_argument("--revision", required=True)
    ap.add_argument("--gen", required=True, type=Path)
    ap.add_argument("--scored", required=True, type=Path)
    ap.add_argument("--pack", required=True, type=Path)
    ap.add_argument("--ids", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)

    from transformers import AutoTokenizer

    gen = [json.loads(l) for l in args.gen.read_text(encoding="utf-8").splitlines() if l.strip()]
    scored = [json.loads(l) for l in args.scored.read_text(encoding="utf-8").splitlines() if l.strip()]
    tasks = load_pack(args.pack, read_task_ids(args.ids))

    base_tok = AutoTokenizer.from_pretrained(args.model, revision=args.revision)
    ref_tok = AutoTokenizer.from_pretrained(REFERENCE[0], revision=REFERENCE[1])
    render = []
    for t in tasks:
        msgs = build_prompt(t.instruction).messages()
        a = base_tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=True)
        b = ref_tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=True)
        render.append({"task_id": t.task_id, "identical": a == b, "base_chars": len(a), "reference_chars": len(b)})

    hash_ok = all(r.get(k) == v for r in gen for k, v in LOCKED.items())
    finish = collections.Counter(r["finish_reason"] for r in gen)
    checks = {
        "cells_generated": len(gen),
        "cells_expected": 2 * len(tasks),
        "prompt_hashes_match_locked": hash_ok,
        "stop_tokens_recorded": sorted({tuple(r["sampling"].get("stop_tokens") or []) for r in gen}),
        "rendering_identical_to_post_trained_qwen3_1.7b": all(r["identical"] for r in render),
        "finish_reasons": dict(finish),
        "any_stop": finish.get("stop", 0) > 0,
        "cells_scored": sum(1 for r in scored if r.get("status") == "scored"),
        "extraction_methods": dict(collections.Counter(r["extraction"] for r in gen)),
        "mean_generated_tokens": sum(r["generated_tokens"] for r in gen) / max(len(gen), 1),
        "IC_tests": [r.get("IC_tests") for r in scored],
        "IC_proofs": [r.get("IC_proofs") for r in scored],
    }
    passed = (
        checks["cells_generated"] == checks["cells_expected"]
        and hash_ok
        and checks["rendering_identical_to_post_trained_qwen3_1.7b"]
        and checks["cells_scored"] == checks["cells_expected"]
    )
    receipt = {
        "date": dt.date.today().strftime("%m-%d-%Y"),
        "model": args.model,
        "revision": args.revision,
        "reference_rendering": {"model": REFERENCE[0], "revision": REFERENCE[1]},
        "checks": checks,
        "rendering": render,
        "stop_token_note": "If no cell stops, PROTOCOL.md requires inspecting completions and recording the behavior before launch.",
        "verdict": "PASS" if passed and checks["any_stop"] else ("PASS_NEEDS_STOP_REVIEW" if passed else "FAIL"),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
