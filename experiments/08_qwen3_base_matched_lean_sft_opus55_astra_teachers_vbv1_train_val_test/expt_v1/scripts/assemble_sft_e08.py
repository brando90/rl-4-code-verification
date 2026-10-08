#!/usr/bin/env python3
"""TLDR: Assemble experiment 08's SFT set S by PROTOCOL § 7: candidates are kept (kernel_binary = 1), extraction-consistent, screen-clean main-manifest cells whose rendered example fits 16,384 tokens; per task visit `opus55` then `astra`, r = 1…4, drop a file whose `rl4cv.screens.norm_hash` equals an already selected file for that task from either teacher, keep the first 2 eligible distinct files per teacher; each example is [system, user, assistant = the teacher's response text verbatim]; order ascending sha256("rl4cv-e08-sft-order-v1:" + task_id + "|" + teacher + "|" + r). Writes the host-only `$WORK/sft/s_v1.jsonl`, the committed manifest CSV (ids and hashes and token counts, no contents) and `sft_set_stats.json` (runs in the transformers interpreter; zero model calls)."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import statistics as st
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
EXP = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("E08_WORK", "/lfs/skampere1/0/brando9/rl4cv_e08"))
os.environ.setdefault("HF_HOME", str(WORK / "cache" / "huggingface"))
TEACHER_ORDER = ("opus55", "astra")
SAMPLE_ORDER = ("s1", "s2", "s3", "s4")
MAX_TOTAL = 16384
PER_TEACHER_CAP = 2
ORDER_SALT = "rl4cv-e08-sft-order-v1:"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def order_key(task_id: str, teacher: str, r: str) -> str:
    """r is the sample number as a digit string ('1'..'4'), i.e. the trailing digit of the run label s1..s4."""
    return sha(f"{ORDER_SALT}{task_id}|{teacher}|{r}".encode("utf-8"))


def quantiles(xs: list[int]) -> dict:
    if not xs:
        return {"n": 0}
    xs = sorted(xs)
    q = lambda p: xs[min(len(xs) - 1, int(p * len(xs)))]
    return {"n": len(xs), "total": sum(xs), "mean": round(st.mean(xs), 1), "median": xs[len(xs) // 2], "p10": q(0.10), "p90": q(0.90), "max": xs[-1], "min": xs[0]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scored", type=Path, default=EXP / "results" / "scored_cells.jsonl")
    ap.add_argument("--screen", type=Path, default=EXP / "results" / "generated_lean_screen.json")
    ap.add_argument("--job-root", type=Path, required=True)
    ap.add_argument("--pack", type=Path, default=WORK / "pack_train539")
    ap.add_argument("--out", type=Path, default=WORK / "sft" / "s_v1.jsonl", help="host-only JSONL (never committed)")
    ap.add_argument("--manifest-out", type=Path, default=EXP / "results" / "sft_set_manifest.csv")
    ap.add_argument("--stats-out", type=Path, default=EXP / "results" / "sft_set_stats.json")
    ap.add_argument("--tokenizer-size", default="8B", help="any size: the four tokenizers are byte-identical (template_check.json)")
    a = ap.parse_args(argv)
    from rl4cv.screens import norm_hash
    from rl4cv.veribench.exp103 import build_prompt
    from template_check import MODELS, load_tokenizers, render

    tok = load_tokenizers([a.tokenizer_size])[a.tokenizer_size]["tokenizer"]
    rows = [json.loads(l) for l in a.scored.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("phase", "main") == "main"]
    screen = json.loads(a.screen.read_text())
    excluded_screen = set(screen.get("excluded_cells", {}))
    pack_check = json.loads((EXP / "results" / "pack_check.json").read_text())
    expected_prompt = {t["task_id"]: t["prompt_sha256"] for t in pack_check["tasks"]}
    import csv as _csv
    with (EXP / "results" / "split" / "vbv1_split_manifest.csv").open(encoding="utf-8", newline="") as fh:
        family = {r["task_id"]: r["family"] for r in _csv.DictReader(fh)}
    by_task: dict[str, dict[str, dict[str, dict]]] = {}
    for r in rows:
        by_task.setdefault(r["task_id"], {}).setdefault(r["teacher"], {})[r["r"]] = r
    exclusions: dict[str, int] = {}
    excluded_list = []
    selected = []
    prompts = {}
    for tid in sorted(by_task):
        instruction = (a.pack / tid / "instruction.md").read_text(encoding="utf-8")
        p = build_prompt(instruction, root=REPO_ROOT / "external" / "veribench")
        if p.prompt_sha256 != expected_prompt[tid]:
            raise RuntimeError(f"{tid}: prompt hash drift")
        prompts[tid] = p
        chosen_hashes: set[str] = set()
        for teacher in TEACHER_ORDER:
            n_teacher = 0
            for s in SAMPLE_ORDER:
                r = by_task[tid].get(teacher, {}).get(s)
                if r is None:
                    continue
                cid = f"{teacher}/{s}/{tid}"
                reason = None
                if r.get("kernel_binary") != 1.0:
                    continue                      # not kept: counted in the scored taxonomy, not an S exclusion
                if r.get("extraction_consistent") is not True:
                    reason = "extraction_inconsistent"
                elif cid in excluded_screen:
                    reason = "screen_hit"
                if reason is None:
                    lean_path = a.job_root / (f"{teacher}_{s}_rec1_s0" if r.get("recovered") else f"{teacher}_{s}_s0") / tid / "verifier" / "solution.lean"
                    lean = lean_path.read_text(encoding="utf-8")
                    response = Path(r["response_path"]).read_text(encoding="utf-8", errors="replace")
                    if sha(lean.encode("utf-8")) != r["lean_sha256"] or sha(response.encode("utf-8")) != r["response_text_sha256"]:
                        raise RuntimeError(f"{cid}: hash drift")
                    rend = render(tok, p.system, p.user, response)
                    if not (rend["byte_prefix_ok"] and rend["token_prefix_ok"] and rend["span_matches_expected"]):
                        reason = "template_alters_response"
                    elif not rend["within_cap"]:
                        reason = "over_length_cap"
                if reason is None:
                    h = norm_hash(lean)
                    if h in chosen_hashes:
                        reason = "duplicate_file_norm_hash"
                    elif n_teacher >= PER_TEACHER_CAP:
                        reason = "per_teacher_cap"
                if reason is not None:
                    exclusions[reason] = exclusions.get(reason, 0) + 1
                    excluded_list.append({"cell": cid, "reason": reason})
                    continue
                chosen_hashes.add(h)
                n_teacher += 1
                selected.append({"task_id": tid, "teacher": teacher, "r": s[1:], "sample": s, "family": family[tid], "order_key": order_key(tid, teacher, s[1:]),
                                 "lean_sha256": r["lean_sha256"], "lean_norm_hash": h, "response_sha256": r["response_text_sha256"], "prompt_sha256": p.prompt_sha256,
                                 "n_prompt_tokens": rend["n_prompt_tokens"], "n_assistant_tokens": rend["n_assistant_tokens"], "n_total_tokens": rend["n_total_tokens"],
                                 "response": response, "run_id": r.get("run_id")})
    selected.sort(key=lambda e: e["order_key"])
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("w", encoding="utf-8") as fh:
        for i, e in enumerate(selected):
            p = prompts[e["task_id"]]
            fh.write(json.dumps({"index": i, "task_id": e["task_id"], "teacher": e["teacher"], "r": e["r"], "order_key": e["order_key"],
                                 "messages": [{"role": "system", "content": p.system}, {"role": "user", "content": p.user}, {"role": "assistant", "content": e["response"]}]},
                                ensure_ascii=False) + "\n")
    a.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["index", "task_id", "family", "teacher", "r", "order_key", "lean_sha256", "lean_norm_hash", "response_sha256", "prompt_sha256", "n_prompt_tokens", "n_assistant_tokens",
            "n_total_tokens", "run_id"]
    with a.manifest_out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for i, e in enumerate(selected):
            w.writerow({"index": i, **{k: e[k] for k in cols if k != "index"}})
    fam_counts: dict[str, int] = {}
    for e in selected:
        fam_counts[e["family"]] = fam_counts.get(e["family"], 0) + 1
    stats = {"written_utc": stamp(), "sft_path_host_only": str(a.out.resolve()), "sft_sha256": sha(a.out.read_bytes()), "n_examples": len(selected),
             "n_distinct_tasks": len({e["task_id"] for e in selected}), "n_train_tasks": 539, "per_teacher": {t: sum(1 for e in selected if e["teacher"] == t) for t in TEACHER_ORDER},
             "per_family": dict(sorted(fam_counts.items())), "per_task_examples_histogram": {str(k): sum(1 for tid in by_task if sum(1 for e in selected if e["task_id"] == tid) == k)
                                                                                           for k in range(0, 2 * PER_TEACHER_CAP + 1)},
             "assistant_tokens": quantiles([e["n_assistant_tokens"] for e in selected]), "prompt_tokens": quantiles([e["n_prompt_tokens"] for e in selected]),
             "total_tokens": quantiles([e["n_total_tokens"] for e in selected]), "exclusions_by_reason": dict(sorted(exclusions.items())), "excluded": excluded_list,
             "rule": {"teacher_order": TEACHER_ORDER, "sample_order": SAMPLE_ORDER, "per_teacher_cap": PER_TEACHER_CAP, "max_total_tokens": MAX_TOTAL,
                      "order": "ascending sha256('rl4cv-e08-sft-order-v1:' + task_id + '|' + teacher + '|' + r) with r in '1'..'4'",
                      "assistant_span": "'<think>\\n\\n</think>\\n\\n' + response verbatim + '<|im_end|>\\n' (template_check.json); the NeMo RL data pipeline's trailing EOS is counted at lock 2"},
             "tokenizer": {"size": a.tokenizer_size, "model": MODELS[a.tokenizer_size]},
             "manifest_csv": str(a.manifest_out.relative_to(REPO_ROOT)), "manifest_sha256": sha(a.manifest_out.read_bytes())}
    a.stats_out.write_text(json.dumps(stats, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: stats[k] for k in ("n_examples", "n_distinct_tasks", "per_teacher", "exclusions_by_reason")}, indent=1))
    print(json.dumps({"assistant_tokens": stats["assistant_tokens"], "prompt_tokens": {k: stats["prompt_tokens"].get(k) for k in ("total", "mean")}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
