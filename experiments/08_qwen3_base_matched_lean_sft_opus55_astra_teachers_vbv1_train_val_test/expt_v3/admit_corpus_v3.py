#!/usr/bin/env python3
"""TLDR: Joint admission of the experiment 08 version-3 expansion corpus on skampere1 (zero model calls): verify the 1,315 original examples, the 685 cached teacher responses and the 587 MBPP pairs by hash, convert MBPP rows into the exact version-1 messages schema, deduplicate the union by normalized Lean hash and word-5-gram Jaccard >= 0.70 (originals always kept), screen every rendered text against the validation and test splits, run the tokenizer prefix / loss-mask / 16,384-token checks, and write the host-only candidate corpus plus a committed manifest and stats. Prepared for Lethan and Rakshit; never repairs a rejected example."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

WORK = Path(os.environ.get("E08_WORK", "/lfs/skampere1/0/brando9/rl4cv_e08"))
REPO = Path(os.environ.get("E08_REPO", str(WORK / "rl-4-code-verification")))
EXP = REPO / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(EXP / "expt_v1" / "scripts"))
os.environ.setdefault("HF_HOME", str(WORK / "cache" / "huggingface"))
csv.field_size_limit(1 << 30)

S_V1_SHA = "885d4ae2d6cf193bddc43df6ad6274cacfa8c98a5e5ecd63bd2519472f5e7354"
MBPP_SHA = "2a3380227dedcb53aa449d50e2823e4a34bfb25ecdcf5b0c1c618b280d6b3c8a"
SYSTEM_SHA = "dc051963de1199dd4f77c9f8f96218eb45be331c819b8e76693b063b206143cd"
ADDENDUM_SHA = "a7a0fc1b7be6b4ede41fd6b31e1e1dcae3d2fd320a6cddf9b311cf55855a18f5"
VERIBENCH_PIN = "c11b99badfa386fd26810b208eef1eb8dc9f6806"
SEP = "\n\n---\n\n"
THRESHOLD, SHINGLE_N, MAX_TOTAL = 0.70, 5, 16384
ORDER_SALT = "rl4cv-e08-v3-sft-order-v1:"
FENCE_RE = re.compile(r"```[A-Za-z0-9_+-]*\n(.*?)```", re.S)
TEACHER_ORDER = {"opus55": 0, "astra": 1}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def envelope(path: str, lean: str) -> str:
    """Frozen MBPP assistant encoding (mbpp_conversion_spec.md): FILE line, lean fence, the kept bytes unchanged, closing fence."""
    return f"FILE: {path}\n```lean\n{lean}{'' if lean.endswith(chr(10)) else chr(10)}```\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inputs", type=Path, default=WORK / "sft_v3" / "inputs")
    ap.add_argument("--out-dir", type=Path, default=WORK / "sft_v3")
    ap.add_argument("--mbpp", type=Path, default=Path("/lfs/skampere1/0/brando9/rl4cv_e02a_v3/sft/lean_warmstart_v3.jsonl"))
    ap.add_argument("--tokenizer-size", default="8B")
    a = ap.parse_args(argv)
    from rl4cv.screens import jaccard, norm_hash, screen, shingles
    from rl4cv.veribench.exp103 import extract_lean, load_single_call
    from template_check import MODELS, load_tokenizers, render

    vb_root = REPO / "external" / "veribench"
    vb_head = subprocess.run(["git", "-C", str(vb_root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    if vb_head != VERIBENCH_PIN:
        raise RuntimeError(f"VeriBench clone at {vb_head}, expected pin {VERIBENCH_PIN}")
    mod = load_single_call(str(vb_root))
    tok = load_tokenizers([a.tokenizer_size])[a.tokenizer_size]["tokenizer"]

    # ---- originals: always kept
    s_v1_path = WORK / "sft" / "s_v1.jsonl"
    if sha(s_v1_path.read_bytes()) != S_V1_SHA:
        raise RuntimeError("s_v1.jsonl hash drift")
    originals = read_jsonl(s_v1_path)
    v1_manifest = {(r["task_id"], r["teacher"], r["r"]): r for r in read_csv(a.inputs / "sft_set_manifest.csv")}
    if len(originals) != 1315 or len(v1_manifest) != 1315:
        raise RuntimeError("original corpus must hold 1,315 examples")
    system = originals[0]["messages"][0]["content"]
    if sha(system.encode()) != SYSTEM_SHA:
        raise RuntimeError("system prompt drift")
    user0 = originals[0]["messages"][1]["content"]
    addendum = user0[user0.index(SEP) + len(SEP):] if SEP in user0 else None
    # the addendum is the suffix after the LAST separator that reproduces the frozen hash
    for i in [m.start() for m in re.finditer(re.escape(SEP), user0)]:
        if sha(user0[i + len(SEP):].encode()) == ADDENDUM_SHA:
            addendum = user0[i + len(SEP):]
    if addendum is None or sha(addendum.encode()) != ADDENDUM_SHA:
        raise RuntimeError("addendum not recoverable from the original corpus")
    user_by_task = {}
    for r in originals:
        if sha(r["messages"][0]["content"].encode()) != SYSTEM_SHA or not r["messages"][1]["content"].endswith(SEP + addendum):
            raise RuntimeError(f"original example {r['index']} is not in the frozen prompt format")
        user_by_task.setdefault(r["task_id"], r["messages"][1]["content"])

    split_rows = {r["task_id"]: r for r in read_csv(a.inputs / "vbv1_split_manifest.csv")}
    train = {t for t, r in split_rows.items() if r["split"] == "train"}
    dataset = vb_root / "veribench_dataset"
    protected = {}
    for tid, r in split_rows.items():
        if r["split"] in ("validation", "test"):
            protected[f"{r['split']}/py/{tid}"] = (dataset / "py_src" / r["py_relpath"]).read_text(encoding="utf-8", errors="replace")
            protected[f"{r['split']}/lean/{tid}"] = (dataset / "lean_src" / "veribench" / r["gold_relpath"]).read_text(encoding="utf-8", errors="replace")
    if len(protected) != 714:
        raise RuntimeError(f"protected corpus has {len(protected)} texts, expected 714")

    examples = []  # dicts with source, ids, messages, lean, hashes, reason (None = admitted so far)
    for r in originals:
        m = v1_manifest[(r["task_id"], r["teacher"], r["r"])]
        response = r["messages"][2]["content"]
        if sha(response.encode()) != m["response_sha256"]:
            raise RuntimeError(f"original {r['index']} response hash drift")
        lean = None
        for sub in (f"{r['teacher']}_s{r['r']}_s0", f"{r['teacher']}_s{r['r']}_rec1_s0"):
            p = WORK / "jobs" / sub / r["task_id"] / "verifier" / "solution.lean"
            if p.is_file() and sha(p.read_bytes()) == m["lean_sha256"]:
                lean = p.read_text(encoding="utf-8")
        if lean is None:
            raise RuntimeError(f"original {r['index']} verified Lean file missing")
        examples.append({"source": "v1_selected", "example_id": f"v1/{r['index']}", "task_id": r["task_id"], "teacher": r["teacher"], "sample": f"s{r['r']}",
                         "family": split_rows[r["task_id"]]["family"], "messages": r["messages"], "lean": lean, "lean_sha256": m["lean_sha256"],
                         "response_sha256": m["response_sha256"], "reason": None, "v1_index": int(r["index"]), "model": None})

    # ---- cached per-teacher-cap candidates
    cached = read_csv(a.inputs / "cached_train_candidates.csv")
    if len(cached) != 685:
        raise RuntimeError("expected 685 cached candidates")
    cached.sort(key=lambda c: (c["task_id"], TEACHER_ORDER[c["teacher"]], c["sample"]))
    for c in cached:
        reason, lean, response = None, None, None
        if c["task_id"] not in train:
            reason = "not_train_split"
        rp = Path(c["response_path"])
        if reason is None:
            if not rp.is_file():
                reason = "response_file_missing"
            else:
                response = rp.read_text(encoding="utf-8", errors="replace")
                if sha(response.encode()) != c["response_sha256"]:
                    reason = "response_hash_mismatch"
        if reason is None:
            for sub in (f"{c['teacher']}_{c['sample']}_s0", f"{c['teacher']}_{c['sample']}_rec1_s0"):
                p = WORK / "jobs" / sub / c["task_id"] / "verifier" / "solution.lean"
                if p.is_file() and sha(p.read_bytes()) == c["lean_sha256"]:
                    lean = p.read_text(encoding="utf-8")
            if lean is None:
                reason = "verified_lean_file_missing"
        if reason is None:
            user = user_by_task.get(c["task_id"])
            if user is None:
                reason = "no_frozen_prompt_for_task"
        if reason is None:
            instruction = user[: -len(SEP + addendum)]
            ext = extract_lean(response, tuple(mod.required_paths(instruction, "vbv1")), root=vb_root)
            if ext.lean != lean:
                reason = "extraction_inconsistent"
        examples.append({"source": "cached_cap_excluded", "example_id": c["cell_id"], "task_id": c["task_id"], "teacher": c["teacher"], "sample": c["sample"],
                         "family": c["family"], "messages": None if reason else [{"role": "system", "content": system}, {"role": "user", "content": user},
                                                                                  {"role": "assistant", "content": response}],
                         "lean": lean, "lean_sha256": c["lean_sha256"], "response_sha256": c["response_sha256"], "reason": reason, "v1_index": None, "model": None})

    # ---- MBPP rows -> frozen envelope
    if sha(a.mbpp.read_bytes()) != MBPP_SHA:
        raise RuntimeError("MBPP file hash drift")
    mbpp_rows = read_jsonl(a.mbpp)
    if len(mbpp_rows) != 587:
        raise RuntimeError("expected 587 MBPP rows")
    for i, r in enumerate(mbpp_rows):
        reason, msgs, resp = None, None, None
        lean = r["lean"]
        if sha(lean.encode()) != r["lean_sha256"]:
            reason = "lean_hash_mismatch"
        elif sha(r["system"].encode()) != SYSTEM_SHA:
            reason = "system_prompt_differs"
        elif not r["user"].endswith(SEP + addendum):
            reason = "user_prompt_not_in_frozen_template"
        else:
            instruction = r["user"][: -len(SEP + addendum)]
            paths = tuple(mod.required_paths(instruction, "vbv1"))
            if len(paths) != 1:
                reason = "required_path_not_unique"
            else:
                resp = envelope(paths[0], lean)
                ext = extract_lean(resp, paths, root=vb_root)
                if ext.lean != lean:
                    reason = "envelope_round_trip_mismatch"
                elif "</think>" in resp or resp.startswith("\n"):
                    reason = "template_alters_response"
                else:
                    msgs = [{"role": "system", "content": r["system"]}, {"role": "user", "content": r["user"]}, {"role": "assistant", "content": resp}]
        examples.append({"source": "mbpp_lean_warmstart_v3", "example_id": f"mbpp/{i}/{r['task_id']}", "task_id": r["task_id"], "teacher": r["teacher"], "sample": r["model"],
                         "family": "mbpp", "messages": msgs, "lean": lean, "lean_sha256": r["lean_sha256"], "response_sha256": sha(resp.encode()) if resp else None,
                         "reason": reason, "v1_index": None, "model": r["model"]})

    # ---- joint normalized dedup (exact norm hash + word-5-gram Jaccard >= 0.70), originals always kept, candidates in order
    for e in examples:
        e["lean_norm_hash"] = norm_hash(e["lean"]) if e["lean"] is not None else None
        e["shingles"] = shingles(e["lean"]) if e["lean"] is not None else frozenset()
    admitted_hashes, index, admitted_items = {}, defaultdict(list), {}
    dup_pairs = []
    for e in examples:
        if e["reason"] is not None:
            continue
        if e["source"] != "v1_selected":
            if e["lean_norm_hash"] in admitted_hashes:
                e["reason"] = "duplicate_norm_hash"
                dup_pairs.append((e["example_id"], admitted_hashes[e["lean_norm_hash"]], 1.0))
                continue
            cands = {pid for s in e["shingles"] for pid in index.get(s, ())}
            best, best_id = 0.0, None
            for pid in cands:
                j = jaccard(e["shingles"], admitted_items[pid])
                if j > best:
                    best, best_id = j, pid
            e["max_jaccard_to_admitted"] = round(best, 4)
            if best >= THRESHOLD:
                e["reason"] = "near_duplicate_word5gram"
                dup_pairs.append((e["example_id"], best_id, round(best, 4)))
                continue
        admitted_hashes.setdefault(e["lean_norm_hash"], e["example_id"])
        admitted_items[e["example_id"]] = e["shingles"]
        for s in e["shingles"]:
            index[s].append(e["example_id"])

    # ---- held-out screen on every rendered text (file, full assistant text, each fenced block)
    pool = {}
    for e in examples:
        if e["reason"] is not None:
            continue
        resp = e["messages"][2]["content"]
        pool[f"{e['example_id']}#file"] = e["lean"]
        pool[f"{e['example_id']}#response"] = resp
        for k, block in enumerate(FENCE_RE.findall(resp)):
            pool[f"{e['example_id']}#block{k}"] = block
    rep = screen(pool, protected, n=SHINGLE_N, threshold=THRESHOLD)
    hit_ids = {h["item_id"].rsplit("#", 1)[0]: h for h in rep["exact"] + rep["near"]}
    for e in examples:
        if e["reason"] is None and e["example_id"] in hit_ids:
            e["reason"] = "heldout_screen_hit"
            e["screen_hit"] = hit_ids[e["example_id"]]

    # ---- tokenizer prefix / mask / length checks
    for e in examples:
        e["n_prompt_tokens"] = e["n_assistant_tokens"] = e["n_total_tokens"] = None
        if e["reason"] is not None:
            continue
        m = e["messages"]
        rend = render(tok, m[0]["content"], m[1]["content"], m[2]["content"])
        e["n_prompt_tokens"], e["n_assistant_tokens"], e["n_total_tokens"] = rend["n_prompt_tokens"], rend["n_assistant_tokens"], rend["n_total_tokens"]
        if not (rend["byte_prefix_ok"] and rend["token_prefix_ok"] and rend["span_matches_expected"]):
            e["reason"] = "template_alters_response"
        elif not rend["within_cap"]:
            e["reason"] = "over_length_cap"
        if e["reason"] is not None and e["source"] == "v1_selected":
            raise RuntimeError(f"original example {e['example_id']} fails a check version 1 passed: {e['reason']}")

    # ---- outputs
    for e in examples:
        e["order_key"] = sha(f"{ORDER_SALT}{e['source']}|{e['task_id']}|{e['teacher']}|{e['sample']}".encode())
    out_dir = a.out_dir
    (out_dir / "results").mkdir(parents=True, exist_ok=True)
    corpus_path = out_dir / "s_v3_candidates.jsonl"
    admitted = [e for e in examples if e["reason"] is None]
    with corpus_path.open("w", encoding="utf-8") as fh:
        for i, e in enumerate(sorted(admitted, key=lambda e: (e["source"] != "v1_selected", e["v1_index"] if e["v1_index"] is not None else 0, e["order_key"]))):
            fh.write(json.dumps({"index": i, "source": e["source"], "example_id": e["example_id"], "task_id": e["task_id"], "teacher": e["teacher"], "sample": e["sample"],
                                 "model": e["model"], "order_key": e["order_key"], "lean_sha256": e["lean_sha256"], "response_sha256": e["response_sha256"],
                                 "lean_norm_hash": e["lean_norm_hash"], "n_prompt_tokens": e["n_prompt_tokens"], "n_assistant_tokens": e["n_assistant_tokens"],
                                 "provenance": {"v1_index": e["v1_index"], "envelope": "mbpp_conversion_spec.md v1" if e["source"].startswith("mbpp") else "teacher response verbatim"},
                                 "messages": e["messages"]}, ensure_ascii=False) + "\n")
    cols = ["source", "example_id", "task_id", "family", "teacher", "sample", "model", "lean_sha256", "lean_norm_hash", "response_sha256",
            "n_prompt_tokens", "n_assistant_tokens", "n_total_tokens", "admitted", "rejection_reason", "max_jaccard_to_admitted", "order_key"]
    manifest_path = out_dir / "results" / "admitted_corpus_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for e in examples:
            w.writerow({**e, "admitted": int(e["reason"] is None), "rejection_reason": e["reason"] or "", "max_jaccard_to_admitted": e.get("max_jaccard_to_admitted", "")})
    by_source = {}
    for src in ("v1_selected", "cached_cap_excluded", "mbpp_lean_warmstart_v3"):
        es = [e for e in examples if e["source"] == src]
        ad = [e for e in es if e["reason"] is None]
        by_source[src] = {"candidates": len(es), "admitted": len(ad), "admitted_loss_tokens": sum(e["n_assistant_tokens"] for e in ad),
                          "admitted_prompt_tokens": sum(e["n_prompt_tokens"] for e in ad), "admitted_unique_tasks": len({e["task_id"] for e in ad}),
                          "rejections_by_reason": dict(sorted(Counter(e["reason"] for e in es if e["reason"]).items())),
                          "admitted_per_family": dict(sorted(Counter(e["family"] for e in ad).items()))}
    new_admitted = [e for e in admitted if e["source"] != "v1_selected"]
    stats = {"written_utc": stamp(), "status": "candidate_corpus_prepared_not_locked", "prepared_for": "Lethan (1.7B/8B) and Rakshit (4B/14B); no training launched",
             "inputs": {"s_v1_sha256": S_V1_SHA, "mbpp_sha256": MBPP_SHA, "system_prompt_sha256": SYSTEM_SHA, "addendum_sha256": ADDENDUM_SHA, "veribench_pin": vb_head,
                        "cached_candidates_csv_sha256": sha((a.inputs / "cached_train_candidates.csv").read_bytes()),
                        "split_manifest_sha256": sha((a.inputs / "vbv1_split_manifest.csv").read_bytes())},
             "rules": {"dedup": "exact rl4cv.screens.norm_hash on the Lean file, then word-5-gram Jaccard >= 0.70 against every already admitted Lean file; originals always kept; "
                                "cached candidates visited in (task_id, opus55 before astra, sample) order, then MBPP rows in file order",
                       "heldout_screen": f"rl4cv.screens.screen over file + full assistant text + each fenced block against {len(protected)} validation/test Python and gold Lean texts; exact or Jaccard >= 0.70 rejects",
                       "render": "Qwen3 Base tokenizer chat template (template_check.render): byte and token prefix, loss span = '<think>\\n\\n</think>\\n\\n' + response + '<|im_end|>\\n', total <= 16,384",
                       "mbpp_envelope": "FILE: <required path>\\n```lean\\n<kept Lean bytes>\\n```\\n (newline added only if the file lacks one); rejected when extraction does not round-trip",
                       "order_key": "sha256('rl4cv-e08-v3-sft-order-v1:' + source + '|' + task_id + '|' + teacher + '|' + sample); final training order fixed by PROTOCOL.md"},
             "totals": {"candidates": len(examples), "admitted": len(admitted), "admitted_new": len(new_admitted),
                        "admitted_loss_tokens_total": sum(e["n_assistant_tokens"] for e in admitted), "admitted_new_loss_tokens": sum(e["n_assistant_tokens"] for e in new_admitted),
                        "unique_tasks_admitted": len({e["task_id"] for e in admitted}), "unique_veribench_train_tasks_admitted": len({e["task_id"] for e in admitted if e["task_id"] in train}),
                        "unique_mbpp_tasks_admitted": len({e["task_id"] for e in admitted if e["source"].startswith("mbpp")}),
                        "rejections_by_reason": dict(sorted(Counter(e["reason"] for e in examples if e["reason"]).items()))},
             "by_source": by_source, "duplicate_pairs_first_50": dup_pairs[:50], "n_duplicate_pairs": len(dup_pairs),
             "heldout_screen": {k: rep[k] for k in ("n_pool", "n_protected", "n_exact", "n_near", "threshold", "shingle_n")},
             "tokenizer": {"size": a.tokenizer_size, "model": MODELS[a.tokenizer_size]},
             "files": {"corpus_host_only": str(corpus_path), "corpus_sha256": sha(corpus_path.read_bytes()), "manifest_csv": manifest_path.name, "manifest_sha256": sha(manifest_path.read_bytes())}}
    (out_dir / "results" / "admitted_corpus_stats.json").write_text(json.dumps(stats, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"totals": stats["totals"], "by_source": {k: {kk: v[kk] for kk in ("candidates", "admitted", "admitted_loss_tokens", "admitted_unique_tasks", "rejections_by_reason")} for k, v in by_source.items()},
                      "heldout_screen": stats["heldout_screen"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
