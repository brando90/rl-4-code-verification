"""Enumerate and time every Reasoning Gym 0.1.25 curriculum family at levels 0-3 for experiment 18a v2 (CPU only, no model).

Each (family, level) is built in its own process at its frozen v2 seed with 256 items and checked against the inclusion
rules in PROTOCOL_v2.md (time limit, gold answer verifies, a missing answer never passes, prompt fits the context, enough
distinct questions, no dominant answer, a config distinct from the family's lower levels, the same items in a second
process). Writes probe_v2.jsonl (every row, with the reason a row is out) and families_v2.json (the frozen list).
Usage:

    python probe_families.py --tokenizer qwen3_tokenizer.json --workers 4 --out-dir .
    python probe_families.py --one coin_flip 0,1,2,3 --tokenizer qwen3_tokenizer.json   # rows of one family, as JSON lines
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e18v2_common as C  # noqa: E402

# Inclusion rules (frozen in PROTOCOL_v2.md before any model saw an item).
TIME_LIMIT_S = 60.0  # build 256 items + verify the 256 gold answers, one process
KILL_AFTER_S = 120.0  # a level still running then counts as a hang
MIN_UNIQUE_QUESTIONS = 8  # v1's coin_flip has ~12 distinct questions per level; <64 is a sensitivity cut in the analysis
MAX_TOP_ANSWER_SHARE = 0.6
CHAT_OVERHEAD_TOKENS = 32  # chat-template tokens around system + user
MIN_LEVELS_PER_FAMILY = 2
TARGET_FAMILIES = {f for f, _ in C.TARGET_RG}
NEEDS_PYCOSAT = {"zebra_puzzles"}  # pycosat has no wheel; the Sherlock fallback image cannot build it


def probe_one(family: str, level: int, tokenizer_path: str | None) -> dict:
    """Build one (family, level) at its v2 seed and measure it; never raises (errors become the row's reason)."""
    C.ensure_pycosat()
    k = C.all_curricula().index(family)
    seed = C.env_seed(k, level)
    row = {"family": family, "k": k, "level": level, "seed": seed, "env_id": f"rg/{family}/L{level}"}
    try:
        row["category"] = C.family_category(family)
        spec = C.SetSpec(row["env_id"], 0, "env", "rg", family, row["category"], level, seed)
        t0 = time.time()
        ds = C.rg_dataset(spec, C.N_ITEMS)
        entries = [ds[i] for i in range(C.N_ITEMS)]
        row["gen_s"] = round(time.time() - t0, 3)
        t1 = time.time()
        gold = [float(ds.score_answer(str(e["answer"]), e)) for e in entries]
        row["gold_score_s"] = round(time.time() - t1, 3)
        none_scores = [float(ds.score_answer(None, e)) for e in entries]
        row["total_s"] = round(row["gen_s"] + row["gold_score_s"], 3)
        row["rg_config"] = C.rg_config_dict(ds)
        cfg = {k2: v for k2, v in row["rg_config"].items() if k2 not in ("seed", "size")}
        row["config_sha256"] = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
        qs = [e["question"] for e in entries]
        row["items_sha256"] = hashlib.sha256("".join(C.sha256_text(q) for q in qs).encode()).hexdigest()
        row["gold_min"] = min(gold)
        row["gold_pass_frac"] = sum(C.is_pass(g) for g in gold) / len(gold)
        row["none_score_max"] = max(none_scores)
        row["unique_questions"] = len(set(qs))
        answers = Counter(str(e["answer"]) for e in entries)
        row["top_answer"] = answers.most_common(1)[0][0][:40]
        row["top_answer_share"] = answers.most_common(1)[0][1] / len(entries)
        row["mean_question_chars"] = round(sum(map(len, qs)) / len(qs), 1)
        if tokenizer_path:
            from tokenizers import Tokenizer

            tok = Tokenizer.from_file(tokenizer_path)
            sys_n = len(tok.encode(C.system_prompt()).ids)
            lens = [len(e.ids) for e in tok.encode_batch(qs)]
            row["prompt_tokens_max"] = sys_n + max(lens) + CHAT_OVERHEAD_TOKENS
            row["prompt_tokens_mean"] = round(sys_n + sum(lens) / len(lens) + CHAT_OVERHEAD_TOKENS, 1)
        row["error"] = None
    except Exception as exc:  # recorded as the reason
        row["error"] = f"{type(exc).__name__}: {exc}"[:300]
    return row


def _run_family(family: str, levels: list[int], tokenizer: str | None, progress=None) -> list[dict]:
    """Probe the levels of one family in one worker process (one import), one JSON line per level.

    A level that prints nothing for KILL_AFTER_S is killed and recorded as a hang; the worker restarts at the next level.
    """
    import select

    rows: list[dict] = []
    todo = list(levels)
    while todo:
        cmd = [sys.executable, "-u", str(Path(__file__).resolve()), "--one", family, ",".join(map(str, todo))]
        if tokenizer:
            cmd += ["--tokenizer", tokenizer]
        err = tempfile.TemporaryFile(mode="w+")  # a file, not a pipe: a full stderr pipe would stall the worker
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=err, text=True)
        deadline = time.time() + KILL_AFTER_S + 30  # the first level also pays the import
        while todo:
            ready, _, _ = select.select([proc.stdout], [], [], max(0.0, deadline - time.time()))
            if not ready or time.time() > deadline:  # silent, or printing only non-row noise
                proc.kill()
                proc.wait()
                lvl = todo.pop(0)
                rows.append({"family": family, "level": lvl, "env_id": f"rg/{family}/L{lvl}", "hang": True,
                             "error": f"killed after {KILL_AFTER_S:.0f} s (hang or too slow)"})
                if progress:
                    progress(rows[-1])
                break
            line = proc.stdout.readline()
            if not line:  # the worker died
                proc.wait()
                lvl = todo.pop(0)
                rows.append({"family": family, "level": lvl, "env_id": f"rg/{family}/L{lvl}",
                             "error": f"process exit {proc.returncode}: {(err.seek(0), err.read())[1].strip()[-300:]}"})
                break
            if not line.startswith("{"):
                continue
            row = json.loads(line)
            todo.remove(row["level"])
            rows.append(row)
            deadline = time.time() + KILL_AFTER_S
            if progress:
                progress(row)
        else:
            proc.wait()
    return sorted(rows, key=lambda r: r["level"])


def judge(rows: list[dict], max_prompt_tokens: int) -> tuple[list[dict], list[dict]]:
    """Apply the inclusion rules: per-row reasons, then the family rules. Returns (rows with reasons, included families)."""
    for r in rows:
        reasons = []
        fam = r["family"]
        if fam in TARGET_FAMILIES:
            reasons.append("held-out target family")
        if fam in NEEDS_PYCOSAT:
            reasons.append("needs pycosat (no wheel; not buildable in the Sherlock fallback image)")
        if r.get("error"):
            reasons.append(r["error"])
        else:
            if r["total_s"] > TIME_LIMIT_S:
                reasons.append(f"too slow: {r['total_s']:.0f} s > {TIME_LIMIT_S:.0f} s for 256 items + gold check")
            if r["gold_pass_frac"] < 1.0:
                reasons.append(f"gold answer fails on {1 - r['gold_pass_frac']:.0%} of items")
            if C.is_pass(r["none_score_max"]):
                reasons.append(f"a missing answer passes (score {r['none_score_max']:.2f})")
            if r["unique_questions"] < MIN_UNIQUE_QUESTIONS:
                reasons.append(f"only {r['unique_questions']} distinct questions")
            if r["top_answer_share"] > MAX_TOP_ANSWER_SHARE:
                reasons.append(f"answer {r['top_answer']!r} on {r['top_answer_share']:.0%} of items")
            if r.get("prompt_tokens_max") is not None and r["prompt_tokens_max"] > max_prompt_tokens:
                reasons.append(f"prompt up to {r['prompt_tokens_max']} tokens > {max_prompt_tokens}")
            if r.get("determinism_ok") is False:
                reasons.append("items differ in a second process")
        r["reasons"] = reasons
    # a level whose config repeats a lower included level of the same family is a duplicate
    by_fam: dict[str, list[dict]] = {}
    for r in sorted(rows, key=lambda x: (x["family"], x["level"])):
        by_fam.setdefault(r["family"], []).append(r)
    families = []
    for fam, rs in by_fam.items():
        seen = set()
        for r in rs:
            if not r["reasons"]:
                if r["config_sha256"] in seen:
                    r["reasons"].append("same config as a lower level")
                else:
                    seen.add(r["config_sha256"])
        ok = [r for r in rs if not r["reasons"]]
        if 0 < len(ok) < MIN_LEVELS_PER_FAMILY:
            for r in ok:
                r["reasons"].append(f"family has fewer than {MIN_LEVELS_PER_FAMILY} usable levels")
            ok = []
        for r in rs:
            r["included"] = not r["reasons"]
        if ok:
            families.append({"family": fam, "k": ok[0]["k"], "category": ok[0]["category"],
                             "levels": [r["level"] for r in ok]})
    return rows, families


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--one", nargs=2, metavar=("FAMILY", "LEVELS"), help="probe one family at comma-separated levels, print JSON lines")
    ap.add_argument("--tokenizer", help="Qwen3 tokenizer.json (prompt length check)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out-dir", default=str(Path(__file__).resolve().parent))
    ap.add_argument("--families", default="all", help="comma-separated subset (tests)")
    args = ap.parse_args(argv)
    if args.one:
        real_stdout, sys.stdout = sys.stdout, sys.stderr  # a generator's own prints must not reach the row stream
        for lvl in args.one[1].split(","):
            row = probe_one(args.one[0], int(lvl), args.tokenizer)
            real_stdout.write(json.dumps(row) + "\n")
            real_stdout.flush()
        return 0
    import importlib.metadata as md

    rg_version = md.version("reasoning-gym")
    if rg_version != C.RG_VERSION:
        raise SystemExit(f"reasoning-gym {rg_version} installed; the protocol pins {C.RG_VERSION}")
    names = C.all_curricula() if args.families == "all" else args.families.split(",")
    t0 = time.time()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    log = open(out / "probe_progress.log", "a", encoding="utf-8")

    cache_path = out / "probe_cache.jsonl"
    cache = {}
    if cache_path.exists():
        for line in open(cache_path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                cache[(r.get("pass", 1), r["family"], r["level"])] = r
    lock = threading.Lock()

    def remember(rs, pass_no):
        with lock, open(cache_path, "a", encoding="utf-8") as fh:
            for r in rs:
                fh.write(json.dumps(dict(r, **{"pass": pass_no})) + "\n")

    def family_rows(f, levels, tokenizer, pass_no, prog=None):
        have = [cache[(pass_no, f, L)] for L in levels if (pass_no, f, L) in cache]
        todo = [L for L in levels if (pass_no, f, L) not in cache]
        new = _run_family(f, todo, tokenizer, prog) if todo else []
        remember(new, pass_no)
        return sorted([{k: v for k, v in r.items() if k != "pass"} for r in have + new], key=lambda r: r["level"])

    def progress(r):
        msg = f"{time.time() - t0:7.0f}s {r['env_id']:40s} " + (f"ERR {r['error'][:80]}" if r.get("error") else
                                                                f"{r['total_s']:.1f}s gold={r['gold_pass_frac']:.2f}")
        print(msg, file=log, flush=True)

    with cf.ThreadPoolExecutor(args.workers) as ex:
        rows = [r for fam_rows in ex.map(lambda f: family_rows(f, list(C.LEVELS), args.tokenizer, 1, progress), names)
                for r in fam_rows]
    # determinism: rebuild every clean row in a fresh process (another PYTHONHASHSEED) and compare item hashes
    clean: dict[str, list[dict]] = {}
    for r in rows:
        if not r.get("error") and r["total_s"] <= TIME_LIMIT_S:
            clean.setdefault(r["family"], []).append(r)
    with cf.ThreadPoolExecutor(args.workers) as ex:
        again = list(ex.map(lambda f: family_rows(f, [r["level"] for r in clean[f]], None, 2), list(clean)))
    redo = {(a["family"], a["level"]): a.get("items_sha256") for fam_rows in again for a in fam_rows}
    for fam_rows in clean.values():
        for r in fam_rows:
            r["determinism_ok"] = redo.get((r["family"], r["level"])) == r["items_sha256"]
    max_prompt = C.MAX_MODEL_LEN - C.MAX_TOKENS
    rows, families = judge(rows, max_prompt)
    C.write_jsonl_atomic(out / "probe_v2.jsonl", rows)
    n_env = sum(len(f["levels"]) for f in families)
    C.write_json_atomic(out / "families_v2.json", {
        "schema": "families_v2/v1", "rg_version": rg_version, "seed_rule": "V2_SEED_BASE + 10*k + level, k = index in sorted(CURRICULA)",
        "rules": {"time_limit_s": TIME_LIMIT_S, "kill_after_s": KILL_AFTER_S, "min_unique_questions": MIN_UNIQUE_QUESTIONS,
                  "max_top_answer_share": MAX_TOP_ANSWER_SHARE, "max_prompt_tokens": max_prompt,
                  "min_levels_per_family": MIN_LEVELS_PER_FAMILY},
        "probe_host": os.uname().nodename, "probe_wall_s": round(time.time() - t0, 1),
        "n_curricula": len(names), "n_families": len(families), "n_envs": n_env, "families": families})
    print(f"{len(families)} families, {n_env} environments included of {len(names)} curricula x 4 levels", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
