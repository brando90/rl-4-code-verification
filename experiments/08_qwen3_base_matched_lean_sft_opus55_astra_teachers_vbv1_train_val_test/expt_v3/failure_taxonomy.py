#!/usr/bin/env python3
"""TLDR: Classify every step-658 validation cell (4 sizes x 135 tasks x 8 attempts) of experiment 08 by failure stage, from the saved generations, scored rows, kernel receipts and the committed per-cell CSVs; zero model calls, validation split only, test outputs never opened. Prepared for Lethan (1.7B/8B) and Rakshit (4B/14B)."""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

csv.field_size_limit(1 << 30)
SIZES = {"1p7B": "1.7B", "4B": "4B", "8B": "8B", "14B": "14B"}
G = 8
SALT = "rl4cv-e08-v3-taxonomy-examples:"
PRIMARY = ("no_lean_extracted", "compile_error", "compiles_zero_proved", "compiles_partially_proved_or_vacuous",
           "compiles_all_proved_not_kernel_success", "kernel_success")
OVERLAP = ("no_lean_extracted", "token_cap", "extracted_not_compiling", "compiles_zero_proved", "compiles_no_theorem_stated",
           "compiles_unproved_theorems", "compiles_vacuous_theorem", "unparseable_theorem_type", "sorry_in_file", "kernel_success")
EXAMPLE_SIZES = ("1p7B", "4B")
EXAMPLES_PER_CATEGORY = 2


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def to_bool(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "1.0"}


def first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()[:120]
    return ""


def kernel_first_unproved(kernel_theorems: str | None) -> str | None:
    """First theorem that the kernel did not accept as honest, from the scorer's per-task receipt."""
    if not kernel_theorems:
        return None
    try:
        items = ast.literal_eval(kernel_theorems)
    except (ValueError, SyntaxError):
        return "unparseable kernel_theorems receipt"
    for item in items:
        if not item.get("kernel_honest"):
            return f"{item.get('full_name')}: category={item.get('category')} axioms={item.get('axioms')} line={item.get('line')}"
    return None


def compile_error_line(recheck_dir: Path, label: str, sample: int, task: str) -> str:
    log = recheck_dir / f"{label}_s{sample}__{task}.log"
    if not log.is_file():
        return "unresolved: the frozen scorer persists only compiles=False; lean recheck log absent"
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        if "error" in line:
            return line.strip()[:200]
    return f"unresolved: recheck log has no error line ({log.name})"


def load_cells(work: Path, inputs: Path, size: str) -> tuple[dict, dict]:
    label = f"sft_{size}_f1p0_g8"
    ids = [l.strip() for l in (inputs / "vbv1_validation_task_ids.txt").read_text().splitlines() if l.strip()]
    if len(ids) != 135 or len(set(ids)) != 135:
        raise ValueError("validation manifest must hold 135 distinct tasks")
    want = {(t, s) for t in ids for s in range(G)}
    scored_path = work / "ladder" / "validation" / "scored" / f"scored_{label}.jsonl"
    raw_path = work / "ladder" / "validation" / "raw" / f"gen_{label}.jsonl"
    cells_path = inputs / f"sft_{size}_f1p0_validation_cells.csv"
    sources = {"scored_jsonl": str(scored_path), "scored_sha256": sha_file(scored_path), "raw_generations_jsonl": str(raw_path),
               "raw_sha256": sha_file(raw_path), "committed_cells_csv": cells_path.name, "committed_cells_sha256": sha_file(cells_path)}
    scored, raw, committed, per_task = {}, {}, {}, {}
    for r in read_jsonl(scored_path):
        key = (r["task_id"], int(r["sample_idx"]))
        if key in scored:
            raise ValueError(f"duplicate scored cell {key}")
        scored[key] = r
    for r in read_jsonl(raw_path):
        key = (r["task_id"], int(r["sample_idx"]))
        if key in raw:
            raise ValueError(f"duplicate raw cell {key}")
        raw[key] = {"finish_reason": r.get("finish_reason"), "completion_head": first_nonempty_line(r.get("completion") or ""),
                    "has_file_marker": "FILE:" in (r.get("completion") or ""), "has_lean_fence": "```lean" in (r.get("completion") or ""),
                    "prompt_tokens": r.get("prompt_tokens")}
    for r in read_csv(cells_path):
        committed[(r["task_id"], int(r["sample_idx"]))] = r
    for s in range(G):
        shard = work / "ladder" / "validation" / "scores" / f"{label}_s{s}" / f"scsc_{label}_s{s}_{label}_s{s}_per_task.csv"
        for r in read_csv(shard):
            per_task[(r["task"], s)] = r
    if set(scored) != want or set(committed) != want:
        raise ValueError(f"{size}: scored or committed cells do not match the 135 x 8 manifest")
    cells = {}
    for key in sorted(want):
        r, c, p, g = scored[key], committed[key], per_task.get(key, {}), raw.get(key, {})
        if r.get("status") != "scored" or not to_bool(c["known"]):
            raise ValueError(f"{size}: unknown cell {key}; unknown cells cannot be classified")
        extracted = to_bool(c["extracted"])
        compiles = bool(r.get("compiles"))
        n_stated = int(r.get("n_theorems_stated") or 0)
        n_proved = int(r.get("n_theorems_proved") or 0)
        n_vac = int(c["n_vacuous"])
        unparseable = to_bool(c["unparseable"])
        kb = float(c["kernel_binary"])
        n_sorry = int(p["agent_n_sorry"]) if p.get("agent_n_sorry") not in (None, "") else None
        if extracted != (r.get("extraction") != "no_lean_block" and bool(r.get("extraction"))) and not extracted:
            pass  # committed flag also requires a non-empty file; the committed CSV is authoritative
        if kb == 1.0 and not (compiles and n_stated >= 1 and n_proved == n_stated and n_vac == 0 and not unparseable):
            raise ValueError(f"{size}: kernel success without the kernel conditions at {key}")
        if not extracted:
            primary = "no_lean_extracted"
        elif not compiles:
            primary = "compile_error"
        elif n_proved == 0:
            primary = "compiles_zero_proved"
        elif n_proved < n_stated or n_vac > 0 or unparseable:
            primary = "compiles_partially_proved_or_vacuous"
        elif kb == 1.0:
            primary = "kernel_success"
        else:
            primary = "compiles_all_proved_not_kernel_success"
        flags = {"no_lean_extracted": not extracted, "token_cap": bool(r.get("truncated")), "extracted_not_compiling": extracted and not compiles,
                 "compiles_zero_proved": compiles and n_proved == 0, "compiles_no_theorem_stated": compiles and n_stated == 0,
                 "compiles_unproved_theorems": compiles and n_proved < n_stated, "compiles_vacuous_theorem": compiles and n_vac > 0,
                 "unparseable_theorem_type": unparseable, "sorry_in_file": bool(n_sorry), "kernel_success": kb == 1.0}
        cells[key] = {"task_id": key[0], "sample_idx": key[1], "primary": primary, "flags": flags, "generated_tokens": r.get("generated_tokens"),
                      "finish_reason": g.get("finish_reason"), "extraction": r.get("extraction"), "compiles": compiles, "n_examples": r.get("n_examples"),
                      "n_theorems_stated": n_stated, "n_theorems_proved": n_proved, "n_vacuous": n_vac, "IC_tests": r.get("IC_tests"), "IC_proofs": r.get("IC_proofs"),
                      "agent_n_sorry": n_sorry, "kernel_first_unproved": kernel_first_unproved(p.get("kernel_theorems")), "lean_sha256": c.get("lean_sha256") or None,
                      "completion_head": g.get("completion_head"), "has_file_marker": g.get("has_file_marker"), "has_lean_fence": g.get("has_lean_fence")}
    return cells, sources


def summarize(cells: dict) -> dict:
    n = len(cells)
    primary = Counter(c["primary"] for c in cells.values())
    overlap = Counter(f for c in cells.values() for f, v in c["flags"].items() if v)
    cap_by_primary = Counter(c["primary"] for c in cells.values() if c["flags"]["token_cap"])
    gen_tokens_by_primary = {}
    for p in PRIMARY:
        toks = [int(c["generated_tokens"]) for c in cells.values() if c["primary"] == p and c["generated_tokens"] is not None]
        gen_tokens_by_primary[p] = {"n": len(toks), "mean": round(sum(toks) / len(toks), 1) if toks else None, "max": max(toks) if toks else None}
    tasks = {}
    for c in cells.values():
        tasks.setdefault(c["task_id"], []).append(c["primary"] == "kernel_success")
    k_success = [sum(v) for v in tasks.values()]
    return {"cells_declared": 1080, "cells_known": n, "primary_counts": {p: primary.get(p, 0) for p in PRIMARY},
            "primary_shares": {p: round(primary.get(p, 0) / n, 4) for p in PRIMARY},
            "primary_share_task_bootstrap_ci95": task_bootstrap(cells),
            "overlapping_flag_counts": {f: overlap.get(f, 0) for f in OVERLAP},
            "token_cap_by_primary": {p: cap_by_primary.get(p, 0) for p in PRIMARY},
            "generated_tokens_by_primary": gen_tokens_by_primary,
            "tasks": {"n": len(tasks), "mixed_success": sum(1 for k in k_success if 0 < k < G), "all_fail": sum(1 for k in k_success if k == 0),
                      "all_success": sum(1 for k in k_success if k == G)}}


def task_bootstrap(cells: dict, draws: int = 10000, seed: int = 0) -> dict:
    """Percentile 95% interval of each primary share and of the token-cap share: tasks resampled with all 8 attempts together."""
    import numpy as np

    ids = sorted({c["task_id"] for c in cells.values()})
    pos = {t: i for i, t in enumerate(ids)}
    mats = {p: np.zeros((len(ids), G)) for p in PRIMARY + ("token_cap",)}
    for c in cells.values():
        mats[c["primary"]][pos[c["task_id"]], c["sample_idx"]] = 1
        if c["flags"]["token_cap"]:
            mats["token_cap"][pos[c["task_id"]], c["sample_idx"]] = 1
    idx = np.random.default_rng(seed).integers(0, len(ids), size=(draws, len(ids)))
    out = {}
    for name, m in mats.items():
        per_task = m.mean(axis=1)
        boot = per_task[idx].mean(axis=1)
        lo, hi = np.quantile(boot, [0.025, 0.975])
        out[name] = {"share": round(float(per_task.mean()), 4), "ci95": [round(float(lo), 4), round(float(hi), 4)]}
    out["method"] = f"{draws} task-bootstrap draws, seed {seed}, unit = task with its 8 attempts; percentile interval; p-val=n/a (no hypothesis test)"
    return out


def pick_examples(cells: dict, label: str, recheck_dir: Path) -> dict:
    out = {}
    for p in PRIMARY:
        if p == "kernel_success":
            continue
        pool = sorted((c for c in cells.values() if c["primary"] == p),
                      key=lambda c: hashlib.sha256(f"{SALT}{c['task_id']}#{c['sample_idx']}".encode()).hexdigest())
        chosen = []
        for c in pool[:EXAMPLES_PER_CATEGORY]:
            if p == "no_lean_extracted":
                line = (f"extraction={c['extraction']}; finish={c['finish_reason']}; FILE marker={c['has_file_marker']}; lean fence={c['has_lean_fence']}; "
                        f"first line={c['completion_head']!r}")
            elif p == "compile_error":
                line = compile_error_line(recheck_dir, label, c["sample_idx"], c["task_id"])
            elif p in ("compiles_zero_proved", "compiles_partially_proved_or_vacuous"):
                line = (f"proved {c['n_theorems_proved']}/{c['n_theorems_stated']} theorems, vacuous={c['n_vacuous']}, sorry={c['agent_n_sorry']}; "
                        f"first unproved: {c['kernel_first_unproved']}")
            else:
                line = f"IC_tests={c['IC_tests']}, examples={c['n_examples']}, proved {c['n_theorems_proved']}/{c['n_theorems_stated']}"
            chosen.append({"task_id": c["task_id"], "sample_idx": c["sample_idx"], "generated_tokens": c["generated_tokens"], "finish_reason": c["finish_reason"],
                           "token_cap": c["flags"]["token_cap"], "lean_sha256": c["lean_sha256"], "first_error_line": line})
        out[p] = chosen
    return out


KINDS = (("failing_test_native_decide_false", r"native_decide' evaluated that the proposition"),
         ("unknown_identifier_or_constant_or_field", r"unknown (identifier|constant)|Invalid field"),
         ("type_or_application_mismatch_or_synthesis", r"type mismatch|Function expected|failed to synthesize|Not a definitional equality"),
         ("failed_proof_tactic", r"unsolved goals|tactic '.*' failed|simp made no progress|rewrite failed|The rfl tactic"),
         ("syntax_or_parse", r"unexpected token|expected "))


def sample_error_kinds(sample_dir: Path) -> dict:
    """Coarse first-error kinds over the deterministic 24-per-size sample of compile-error files rechecked with `lake env lean`."""
    out = {"selection": "first 24 compile_error cells per size (1.7B, 4B) in ascending sha256('rl4cv-e08-v3-taxonomy-sample:' + task_id + '#' + sample_idx)",
           "kinds_regex_order": [k for k, _ in KINDS], "per_size": {}}
    if not sample_dir.is_dir():
        out["status"] = "sample recheck directory absent"
        return out
    for size, label in (("1.7B", "sft_1p7B_f1p0_g8"), ("4B", "sft_4B_f1p0_g8")):
        counts, first_lines, n_logs, n_no_error = Counter(), Counter(), 0, 0
        for log in sorted(sample_dir.glob(f"{label}_s*__*.log")):
            n_logs += 1
            text = log.read_text(encoding="utf-8", errors="replace")
            line = next((l for l in text.splitlines() if "error:" in l), None)
            if line is None:
                n_no_error += 1
                counts["no_error_line_in_log"] += 1
                continue
            msg = line.split("error:", 1)[1].strip()
            first_lines[msg[:60]] += 1
            counts[next((k for k, rx in KINDS if re.search(rx, msg)), "other")] += 1
        out["per_size"][size] = {"n_files": n_logs, "n_without_error_line": n_no_error, "kinds": dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))),
                                 "first_error_prefixes_60chars": dict(sorted(first_lines.items(), key=lambda kv: (-kv[1], kv[0])))}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", type=Path, default=Path("/lfs/skampere1/0/brando9/rl4cv_e08"))
    ap.add_argument("--inputs", type=Path, default=Path("/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/inputs"))
    ap.add_argument("--recheck-dir", type=Path, default=Path("/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/results/lean_recheck"))
    ap.add_argument("--out", type=Path, default=Path("/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/results/failure_taxonomy.json"))
    ap.add_argument("--cells-out", type=Path, default=Path("/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3/results/failure_taxonomy_cells.jsonl"))
    a = ap.parse_args(argv)
    payload = {"status": "validation_failure_taxonomy_zero_model_calls", "split": "VeriBench V1 validation (135 tasks x 8 attempts; D-013)",
               "checkpoint": "step 658 (5,752,936 loss tokens) at every size", "prepared_for": "Lethan (1.7B/8B) and Rakshit (4B/14B); no training launched",
               "primary_rule": "first match: not extracted -> no_lean_extracted; not compiles -> compile_error; proved=0 -> compiles_zero_proved; "
                               "proved<stated or vacuous or unparseable -> compiles_partially_proved_or_vacuous; kernel_binary=1 -> kernel_success; else compiles_all_proved_not_kernel_success",
               "token_cap_is_overlapping": "truncated at 12,288 generated tokens is reported as a flag and cross-tabulated against the primary category",
               "example_selection": f"first {EXAMPLES_PER_CATEGORY} cells per failure category in ascending sha256('{SALT}' + task_id + '#' + sample_idx)",
               "p_value": "n/a (deterministic counts over complete 1,080-cell manifests)",
               "validation_ids_sha256": sha_file(a.inputs / "vbv1_validation_task_ids.txt"), "systems": {}, "examples": {}}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.cells_out.open("w", encoding="utf-8") as fh:
        for size, pretty in SIZES.items():
            cells, sources = load_cells(a.work, a.inputs, size)
            payload["systems"][pretty] = {**summarize(cells), "sources": sources}
            if size in EXAMPLE_SIZES:
                payload["examples"][pretty] = pick_examples(cells, f"sft_{size}_f1p0_g8", a.recheck_dir)
            for c in cells.values():
                fh.write(json.dumps({"size": pretty, **{k: v for k, v in c.items() if k != "completion_head"}}, sort_keys=True) + "\n")
    payload["compile_error_first_error_sample"] = sample_error_kinds(a.recheck_dir.parent / "lean_recheck_sample")
    payload["cells_jsonl_sha256"] = sha_file(a.cells_out)
    a.out.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({s: {"primary": v["primary_counts"], "cap_by_primary": v["token_cap_by_primary"]} for s, v in payload["systems"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
