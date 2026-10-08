# TLDR: Recompile experiment 01's single-call Lean files with the frozen scorer, classify why each fails, and measure a proof-error-to-sorry ablation (a diagnostic, never a VeriBench score).
"""Why do small Qwen models score SCSC ≈ 0 on VeriBench V1? A zero-spend, CPU-only diagnostic.

For every G = 1 cell of experiment 01 (model × 896 tasks) this script:

1. Recompiles the model's `solution.lean` with the frozen scorer's exact command (`lake env lean <file>`
   from the grading Lean project) and checks the result against the recorded `compiles` field.
2. Parses every `error:` diagnostic and assigns it a message category (parse, unknown name, type error,
   tactic failure, termination, ...) and the region it sits in (theorem proof, theorem statement,
   definition, `example` test, other).
3. Compiles a definitions-only variant (all `theorem`/`lemma`/`example` blocks removed): does the
   implementation alone elaborate?
4. Runs a proof-error-to-sorry ablation: every theorem/lemma whose *proof* holds an error has its proof
   replaced by `by sorry`, repeated for up to `--max-rounds` recompiles. Definitions, statements and
   `example` tests are never edited, because the frozen scorer's IC_tests only asks for a compiling file
   with at least one `example` and does not inspect examples for `sorry`. If the ablated file compiles,
   the frozen scorer's own functions (`analyze_lean_file`, `ic_pp_for_compiled`, i.e. the kernel axiom
   check) give its IC_tests and IC_proofs. A `sorry` proof counts zero there, as in VeriBench.

The ablation measures one edited-file outcome using an honest `sorry` fallback; it does not bound what
a model with compiler feedback could achieve. It edits the model's output, so its numbers are diagnostics
and must never be reported as VeriBench scores.

Usage (on the host that holds experiment 01's outputs and the pinned scorer checkout):

    python diagnose_zero_scores.py --exp01-out /lfs/skampere1/0/brando9/rl4cv_e01/out \\
        --scorer-dir <repo>/external/veribench_scorer/scripts/scsc --work-dir <dir> \\
        --labels qwen3-14b_g1 qwen3.5-9b_g1 --workers 24
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import signal
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ERROR_RE = re.compile(r"^(?P<file>[^\n]+?):(?P<line>\d+):(?P<col>\d+): error: (?P<msg>[^\n]*)$", re.M)
SORRY_WARN_RE = re.compile(r"^[^\n]+?:\d+:\d+: warning: declaration uses 'sorry'", re.M)

MODIFIERS = r"(?:(?:private|protected|noncomputable|partial|unsafe|nonrec|scoped|local)\s+)*"
DECL_KWS = (
    "theorem|lemma|def|abbrev|example|instance|structure|inductive|class|opaque|axiom|namespace|end|section|"
    "open|variable|universe|set_option|attribute|macro|macro_rules|syntax|notation|infix|infixl|infixr|prefix|"
    "postfix|elab|deriving|mutual|import|export|include|omit|constant|constants|initialize|builtin_initialize|"
    "run_cmd|#eval|#check|#print|#guard|#guard_msgs|#reduce|#exit"
)
DECL_START_RE = re.compile(r"^(?:@\[[^\n]*?\]\s*)*" + MODIFIERS + r"(?P<kw>" + DECL_KWS + r")(?![\w'.])")
PROOF_KWS = {"theorem", "lemma"}
DEF_KWS = {"def", "abbrev", "instance", "structure", "inductive", "class", "opaque", "mutual"}

CATEGORIES = [
    ("timeout", re.compile(r"timeout|maximum recursion depth|heartbeats", re.I)),
    ("index_bounds_proof", re.compile(r"failed to prove index is valid", re.I)),
    ("termination", re.compile(r"termination|structural recursion|decreasing", re.I)),
    ("type_error", re.compile(r"type mismatch|failed to synthesize|function expected|ambiguous|"
                              r"expected type|type expected|don't know how to synthesize|has type|mismatch", re.I)),
    ("parse", re.compile(r"unexpected token|unexpected character|unexpected identifier|^expected |unterminated|"
                         r"invalid 'end'|missing end", re.I)),
    ("unknown_name", re.compile(r"unknown (identifier|constant|namespace|tactic|attribute|declaration|module)|"
                                r"invalid field|is not a field|unknown universe", re.I)),
    ("tactic_failed", re.compile(r"unsolved goals|failed|no goals|made no progress|linarith|omega|"
                                 r"could not|did not|not a rfl|decide|rfl|aesop|norm_num|simp", re.I)),

]

# Lean 3 idioms only (`cases h with` is also valid Lean 4, so it is not counted). The 10-07-2026 summaries were
# written with an earlier, looser version that also counted `cases … with`; their `files_with_lean3_markers` is not reported.
LEAN3_MARKERS = re.compile(r"^\s*begin\s*$|^import (data|tactic|algebra|logic|init)\.|λ\s*\w+\s*,|^\s*assume\s|"
                           r"\bnat\.(succ|zero|rec)\b|\blist\.(nil|cons)\b", re.M)


def categorize(msg: str) -> str:
    for name, rx in CATEGORIES:
        if rx.search(msg):
            return name
    return "other"


# ---------------------------------------------------------------------------
# Lean source segmentation (conservative lexical boundaries, not a Lean parser)
# ---------------------------------------------------------------------------
def _masked_source(src: str) -> str:
    """Use the frozen scorer's lexer; retain positions but hide quoted identifiers too."""
    if _RRE is None:
        raise RuntimeError("load the frozen scorer before segmenting Lean source")
    masked = _RRE.kernel_axioms.strip_comments(src)
    return re.sub(r"«[^»]*»", lambda m: "".join("\n" if c == "\n" else " " for c in m[0]), masked)


def segment(src: str) -> list[dict]:
    """Conservatively split declarations, including indented ones; preserve source line coordinates."""
    lines = src.split("\n")
    masked = _masked_source(src)
    code = masked.split("\n")
    starts: list[tuple[int, str]] = []
    # Find actual comment openers using the canonical literal-preserving mask;
    # skip each whole comment so nested doc-like text cannot become a prefix.
    literal_mask = _RRE.kernel_axioms.strip_comments(src, keep_literals=True)
    comment_starts = {}
    pos = 0
    while pos < len(src):
        if literal_mask[pos] == " " and src.startswith("--", pos):
            end = src.find("\n", pos)
            pos = len(src) if end < 0 else end
        elif literal_mask[pos] == " " and src.startswith("/-", pos):
            end = _RRE.kernel_axioms._block_end(src, pos)
            following = masked[end:].lstrip()
            if (src.startswith(("/--", "/-!"), pos)
                    and not src[src.rfind("\n", 0, pos) + 1:pos].strip()
                    and (DECL_START_RE.match(following) or following.startswith("@["))):
                comment_starts[src.count("\n", 0, pos)] = "prefix" if src.startswith("/--", pos) else "comment"
            pos = end
        else:
            pos += 1
    for i, line in enumerate(code):
        m = DECL_START_RE.match(line.lstrip())
        if m:
            starts.append((i, m.group("kw")))
        elif i in comment_starts:
            starts.append((i, comment_starts[i]))
        elif line.lstrip().startswith("@["):
            starts.append((i, "prefix"))  # keep standalone attributes attached to the next command
        elif line and not line[0].isspace():
            # Unknown column-zero syntax must not be swallowed by an earlier proof.
            starts.append((i, "other"))
    if not starts or starts[0][0] != 0:
        starts.insert(0, (0, "header"))
    blocks = []
    for j, (i, kw) in enumerate(starts):
        end = starts[j + 1][0] if j + 1 < len(starts) else len(lines)
        b = {"kind": kw, "start": i + 1, "end": end, "kw_line": i + 1,
             "text": "\n".join(lines[i:end])}
        b["proof_pos"] = proof_position(code, b) if kw in PROOF_KWS else None
        if re.search(r"\b(?:where|termination_by|decreasing_by)\b", "\n".join(code[i:end])):
            b["proof_pos"] = None  # do not remove attached auxiliary definitions
        if b["proof_pos"] is not None:
            pl, pc = b["proof_pos"]
            body = "\n".join([code[pl - 1][pc + 2:]] + code[pl:end])
            if re.search(r"(?<![\w\'.])(?:" + DECL_KWS + r")(?![\w\'.])|@\[", body):
                b["proof_pos"] = None  # e.g. another declaration on the same source line
        blocks.append(b)
    merged = []
    for b in blocks:
        if merged and merged[-1]["kind"] == "prefix" and b["kind"] in PROOF_KWS | DEF_KWS | {"example", "axiom", "constant", "prefix"}:
            prefix = merged.pop()
            b["start"] = prefix["start"]
            b["text"] = "\n".join(lines[b["start"] - 1:b["end"]])
        merged.append(b)
    return merged


def proof_position(lines: list[str], block: dict) -> tuple[int, int] | None:
    """Locate a depth-zero body assignment in masked code; reject ambiguous term headers."""
    depth = 0
    for ln in range(block["kw_line"], block["end"] + 1):
        s = lines[ln - 1]
        for token in re.finditer(r":=|[\w']+|[^\s]", s):
            word = token[0]
            if word in "([{⟨" and len(word) == 1:
                depth += 1
            elif word in ")]}⟩" and len(word) == 1:
                if not depth:
                    return None
                depth -= 1
            elif depth == 0:
                if word.startswith(("let", "have")) or word in {"show", "by", "do", "match", "if", "fun", "λ"}:
                    # These can contain := within the theorem's statement. Fail closed.
                    return None
                if word == ":=":
                    return ln, token.start()
    return None


def region_of(blocks: list[dict], line: int, col: int) -> tuple[str, int | None]:
    for idx, b in enumerate(blocks):
        if b["start"] <= line <= b["end"]:
            kind = b["kind"]
            if kind in PROOF_KWS:
                pp = b["proof_pos"]
                if pp is not None and (line, col) >= pp:
                    return "theorem_proof", idx
                return "theorem_statement", idx
            if kind == "example":
                return "example_test", idx
            if kind in DEF_KWS:
                return "definition", idx
            return "other", idx
    return "other", None


def sorry_proofs(src: str, blocks: list[dict], idxs: set[int]) -> str:
    """Replace only identified proof bodies, preserving all line positions across rounds."""
    lines = src.split("\n")
    for idx in sorted(idxs):
        b = blocks[idx]
        if b["kind"] not in PROOF_KWS or b["proof_pos"] is None:
            raise ValueError("refusing to ablate a block without a safe theorem proof boundary")
        pl, pc = b["proof_pos"]
        lines[pl - 1] = lines[pl - 1][:pc] + ":= by sorry"
        for ln in range(pl, b["end"]):
            lines[ln] = ""
    return "\n".join(lines)


def defs_only(src: str, blocks: list[dict]) -> str:
    lines = src.split("\n")
    out: list[str] = []
    for b in blocks:
        if b["kind"] in PROOF_KWS or b["kind"] == "example":
            continue
        out.extend(lines[b["start"] - 1 : b["end"]])
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Compilation: the frozen scorer's command, with a process-group kill on timeout
# ---------------------------------------------------------------------------
def compile_file(path: Path, lake_dir: str, timeout: int) -> dict:
    """`lake env lean <file>` from the grading project, exactly as the frozen `compile_lean_file` runs it."""
    t0 = time.monotonic()
    proc = subprocess.Popen(["lake", "env", "lean", str(path)], cwd=lake_dir, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        out, err = proc.communicate(timeout=timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        out, err = proc.communicate()
        rc = 124
    combined = f"{out}\n{err}"
    errors = [
        {"line": int(m["line"]), "col": int(m["col"]), "msg": m["msg"][:240]}
        for m in ERROR_RE.finditer(combined)
        if Path(m["file"]).name == path.name
    ]
    return {"rc": rc, "success": rc == 0, "timeout": rc == 124, "errors": errors,
            "sorry_warnings": len(SORRY_WARN_RE.findall(combined)), "seconds": round(time.monotonic() - t0, 2)}


_RRE = None


def frozen_scorer(scorer_dir: str):
    global _RRE
    if _RRE is None:
        sys.path.insert(0, scorer_dir)
        import run_real_eval as rre  # the pinned frozen scorer (external/deps.lock.json: veribench_scorer)

        _RRE = rre
    return _RRE


def frozen_factors(path: Path, split: str, scorer_dir: str, lake_dir: str | None = None) -> dict:
    """IC_tests / IC_proofs of a file that compiles, via the frozen scorer's own analysis and kernel check."""
    rre = frozen_scorer(scorer_dir)
    analysis = rre.analyze_lean_file(str(path), split)
    analysis.compiles = True
    ic_ap = 1.0 if analysis.n_examples > 0 else 0.0
    ic_pp = rre.ic_pp_for_compiled(str(path), lake_dir or rre.LAKE_DIR, analysis)
    if not analysis.compiles:
        ic_ap = 0.0
    k = analysis.kernel or {}
    return {"IC_tests": ic_ap, "IC_proofs": ic_pp, "n_examples": analysis.n_examples,
            "n_theorems": analysis.n_theorems, "kernel_probe_ok": k.get("probe_ok"),
            "kernel_n_honest": k.get("n_honest"), "kernel_n_theorems": k.get("n_theorems"),
            "kernel_n_sorry_ax": k.get("n_sorry_ax")}


# ---------------------------------------------------------------------------
# One cell
# ---------------------------------------------------------------------------
DIGIT_NS_RE = re.compile(r"^namespace\s+(\d[\w'.]*)\s*$", re.M)


def escape_digit_namespaces(src: str) -> tuple[str, int]:
    """Wrap digit-leading namespace names (invalid Lean identifiers, e.g. `namespace 1_MyAdd`) in «»."""
    names = sorted(set(DIGIT_NS_RE.findall(_masked_source(src))), key=len, reverse=True)

    def replace_code(pattern: str, replacement: str) -> None:
        nonlocal src
        masked = _masked_source(src)
        src = re.sub(pattern, lambda m: m.expand(replacement)
                     if masked[m.start():m.end()] == m[0] else m[0], src, flags=re.M)
    for name in names:
        q = re.escape(name)
        replace_code(rf"^(namespace|end|open|export)(\s+)(?:{q})(?=\s|$)", rf"\1\2«{name}»")
        replace_code(rf"(?<![\w«.]){q}\.", f"«{name}».")
    return src, len(names)


NON_DECL_AFTER_DOC_RE = re.compile(r"^(namespace|open|end|section|import|set_option|variable|universe|#|/-|--)")


def repair_surface_syntax(src: str) -> tuple[str, dict]:
    """Comment and name fixes only (no code change): escape digit-leading namespaces, turn a stand-alone `-!`
    line into the comment closer `-/`, and turn a `/--` doc comment that precedes a non-declaration into the
    module doc `/-!`."""
    src, n_ns = escape_digit_namespaces(src)
    # A malformed closer may occur inside a block comment, never alter string data.
    literal_mask = _RRE.kernel_axioms.strip_comments(src, keep_literals=True)
    n_close = 0

    def close_comment(m):
        nonlocal n_close
        if literal_mask[m.start():m.end()].strip():
            return m[0]
        n_close += 1
        return m[1] + "-/"

    src = re.sub(r"^([ \t]*)-![ \t]*$", close_comment, src, flags=re.M)
    lines, n_doc, i = src.split("\n"), 0, 0
    literal_lines = _RRE.kernel_axioms.strip_comments(src, keep_literals=True).split("\n")
    while i < len(lines):
        if lines[i].startswith("/--") and not literal_lines[i].strip():
            j = i
            while j < len(lines) and "-/" not in lines[j][(3 if j == i else 0):]:
                j += 1
            k = j + 1
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k < len(lines) and NON_DECL_AFTER_DOC_RE.match(lines[k]):
                lines[i] = "/-!" + lines[i][3:]
                n_doc += 1
            i = j + 1
            continue
        i += 1
    return "\n".join(lines), {"namespaces_escaped": n_ns, "comment_closers_fixed": n_close, "module_docs_fixed": n_doc}


def diagnose_cell(job: dict) -> dict:
    lake_dir, scorer_dir, timeout = job["lake_dir"], job["scorer_dir"], job["timeout"]
    frozen_scorer(scorer_dir)  # supplies the canonical comment/string lexer for segmentation
    row = {k: job[k] for k in ("label", "task_id", "split", "scored_compiles", "scored_IC_tests",
                               "scored_IC_proofs", "truncated", "extraction", "think")}
    sol = Path(job["solution"])
    if not sol.is_file() or not sol.read_text(encoding="utf-8", errors="replace").strip():
        row["status"] = "no_file"
        return row
    src = sol.read_text(encoding="utf-8", errors="replace")
    work = Path(job["work"])
    work.mkdir(parents=True, exist_ok=True)
    if job.get("repair_surface_syntax"):
        # diagnostic variant: comment and namespace-name fixes only; every definition, test and proof is the model's own
        src, row["surface_repairs"] = repair_surface_syntax(src)
        sol = work / "surface_repaired.lean"
        sol.write_text(src, encoding="utf-8")
    elif job.get("escape_digit_namespace"):
        # diagnostic variant: only the namespace name is escaped; everything else is the model's own text
        src, row["n_namespaces_escaped"] = escape_digit_namespaces(src)
        sol = work / "namespace_escaped.lean"
        sol.write_text(src, encoding="utf-8")
    blocks = segment(src)
    row["status"] = "file"
    row["lean3_markers"] = len(LEAN3_MARKERS.findall(src))
    row["n_blocks"] = Counter(b["kind"] for b in blocks)

    orig = compile_file(sol, lake_dir, timeout)
    row["recompile_success"] = orig["success"]
    row["recompile_timeout"] = orig["timeout"]
    row["n_errors"] = len(orig["errors"])
    row["first_error"] = orig["errors"][0]["msg"] if orig["errors"] else None
    row["error_categories"] = Counter(categorize(e["msg"]) for e in orig["errors"])
    row["error_regions"] = Counter(region_of(blocks, e["line"], e["col"])[0] for e in orig["errors"])

    if orig["success"]:
        row["original_factors"] = frozen_factors(sol, job["split"], scorer_dir, lake_dir)
        row["class"] = "compiles"
        return row

    d = work / "defs_only.lean"
    d.write_text(defs_only(src, blocks), encoding="utf-8")
    dres = compile_file(d, lake_dir, timeout)
    row["defs_only_success"] = dres["success"]
    row["defs_only_error_categories"] = Counter(categorize(e["msg"]) for e in dres["errors"])

    # Proof replacement preserves line coordinates, so every round uses the original region map.
    sorried: set[int] = set()
    abl = {"rounds": 0, "stop": "max_rounds"}
    errors = orig["errors"]
    timed_out = orig["timeout"]
    for rnd in range(1, job["max_rounds"] + 1):
        if timed_out:
            abl["stop"] = "timeout"
            break
        regions = [region_of(blocks, e["line"], e["col"]) for e in errors]
        blocking = [r for r, _ in regions if r != "theorem_proof"]
        if blocking or not errors:
            abl["stop"] = "blocking_errors" if blocking else "failed_without_error_lines"
            abl["blocking_regions"] = Counter(blocking)
            break
        new = {i for r, i in regions if r == "theorem_proof" and i is not None} - sorried
        if not new:
            abl["stop"] = "no_progress"
            break
        sorried |= new
        cur = sorry_proofs(src, blocks, sorried)
        a = work / "ablated.lean"
        a.write_text(cur, encoding="utf-8")
        res = compile_file(a, lake_dir, timeout)
        abl["rounds"] = rnd
        if res["success"]:
            abl["stop"] = "compiles"
            break
        errors, timed_out = res["errors"], res["timeout"]
    abl["n_proofs_sorried"] = len(sorried)
    if abl["stop"] == "compiles":
        abl.update(frozen_factors(work / "ablated.lean", job["split"], scorer_dir, lake_dir))
        row["class"] = "compiles_after_proof_ablation"
    elif not dres["success"]:
        row["class"] = "definitions_fail"
    else:
        row["class"] = "tests_or_statements_fail"
    row["ablation"] = abl
    return row


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
def think_stats(completion: str) -> dict:
    if "</think>" not in completion:
        return {"has_close": False, "chars": None, "empty": None}
    pre = completion.split("</think>", 1)[0].replace("<think>", "").strip()
    return {"has_close": True, "chars": len(pre), "empty": len(pre) == 0}


def build_jobs(args, label: str) -> list[dict]:
    out = Path(args.exp01_out)
    scored = [json.loads(x) for x in (out / "scored" / f"scored_{label}.jsonl").read_text().splitlines() if x.strip()]
    raw = {}
    rawp = out / "raw" / f"gen_{label}.jsonl"
    for x in rawp.read_text().splitlines():
        if x.strip():
            r = json.loads(x)
            raw[(r["task_id"], int(r["sample_idx"]))] = think_stats(r.get("completion") or "")
    jobs = []
    for r in scored:
        if int(r.get("sample_idx", 0)) != 0:
            continue
        tid = r["task_id"]
        jobs.append({
            "label": label, "task_id": tid, "split": r.get("split"),
            "scored_compiles": r.get("compiles"), "scored_IC_tests": r.get("IC_tests"),
            "scored_IC_proofs": r.get("IC_proofs"), "truncated": r.get("truncated"),
            "extraction": r.get("extraction"), "think": raw.get((tid, 0)),
            "solution": str(out / "jobs" / f"{label}_s0" / tid / "verifier" / "solution.lean"),
            "work": str(Path(args.work_dir) / "cells" / label / tid),
            "lake_dir": args.lake_dir, "scorer_dir": args.scorer_dir,
            "timeout": args.timeout, "max_rounds": args.max_rounds,
            "escape_digit_namespace": args.escape_digit_namespace,
            "repair_surface_syntax": args.repair_surface_syntax,
        })
    # a variant only differs from the base run on cells it actually edits
    if args.repair_surface_syntax:
        jobs = [j for j in jobs if Path(j["solution"]).is_file() and any(repair_surface_syntax(
            Path(j["solution"]).read_text(encoding="utf-8", errors="replace"))[1].values())]
    elif args.escape_digit_namespace:
        jobs = [j for j in jobs if Path(j["solution"]).is_file()
                and DIGIT_NS_RE.search(_masked_source(Path(j["solution"]).read_text(encoding="utf-8", errors="replace")))]
    return jobs


def wilson(k: int, n: int, z: float = 1.959964) -> list[float | None]:
    if not 0 <= k <= n:
        raise ValueError("Wilson counts must satisfy 0 <= k <= n")
    if n == 0:
        return [None, None]
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def summarize(label: str, rows: list[dict]) -> dict:
    unmeasured = [r["task_id"] for r in rows if r["status"] == "diagnostic_error"]
    if unmeasured:
        raise ValueError(f"unmeasured diagnostic cells retained in rows; refusing zero-filled summary: {unmeasured}")
    n = len(rows)
    files = [r for r in rows if r["status"] == "file"]
    cls = Counter(r.get("class", r["status"]) for r in rows)
    mismatch = [r["task_id"] for r in files if bool(r["recompile_success"]) != bool(r["scored_compiles"])]
    noncomp = [r for r in files if not r["recompile_success"]]
    cat_any = Counter()
    region_any = Counter()
    first = Counter()
    for r in noncomp:
        for c in r["error_categories"]:
            cat_any[c] += 1
        for g in r["error_regions"]:
            region_any[g] += 1
        if r["first_error"]:
            first[re.sub(r"'[^']*'|`[^`]*`|\d+", "_", r["first_error"])[:90]] += 1
    abl_ok = [r for r in files if r.get("class") == "compiles_after_proof_ablation"]
    orig_ok = [r for r in files if r.get("class") == "compiles"]

    def fac(r):
        return r["ablation"] if r.get("class") == "compiles_after_proof_ablation" else r.get("original_factors", {})

    pos = [r for r in abl_ok + orig_ok if fac(r).get("IC_tests", 0) * fac(r).get("IC_proofs", 0) > 0]
    ic_t = sum(fac(r).get("IC_tests", 0.0) for r in abl_ok + orig_ok) / n if n else 0.0
    ic_p = sum(fac(r).get("IC_proofs", 0.0) for r in abl_ok + orig_ok) / n if n else 0.0
    think = [r for r in files if r.get("think") and r["think"].get("has_close")]
    summ = {
        "label": label, "n_cells": n, "n_with_file": len(files), "n_no_file": n - len(files),
        "recompile_vs_scored_mismatches": mismatch,
        "classes": dict(cls),
        "compiles_original": [len(orig_ok), wilson(len(orig_ok), n)],
        "compiles_after_proof_ablation_incl_original": [len(abl_ok) + len(orig_ok), wilson(len(abl_ok) + len(orig_ok), n)],
        "definitions_only_compile_among_noncompiling": [sum(1 for r in noncomp if r.get("defs_only_success")), len(noncomp)],
        "ablation_IC_tests_mean_over_n": round(ic_t, 4),
        "ablation_IC_proofs_mean_over_n": round(ic_p, 4),
        "cells_IC_tests_x_IC_proofs_positive_after_ablation": [len(pos), wilson(len(pos), n)],
        "noncompiling_files_with_error_category": dict(cat_any.most_common()),
        "noncompiling_files_with_error_region": dict(region_any.most_common()),
        "top_first_errors": first.most_common(12),
        "files_with_lean3_markers": sum(1 for r in files if r.get("lean3_markers")),
        "think": {
            "n_with_close_tag": len(think),
            "n_empty_think": sum(1 for r in think if r["think"]["empty"]),
            "ablation_compile_rate_empty_think": _rate([r for r in think if r["think"]["empty"]]),
            "ablation_compile_rate_nonempty_think": _rate([r for r in think if not r["think"]["empty"]]),
        },
    }
    return summ


def _rate(rows: list[dict]) -> list:
    k = sum(1 for r in rows if r.get("class") in ("compiles", "compiles_after_proof_ablation"))
    return [k, len(rows), wilson(k, len(rows))]


def _jsonable(o):
    if isinstance(o, Counter):
        return dict(o)
    raise TypeError(type(o))


def _pct(k: int, n: int, ci: list | None = None) -> str:
    s = f"{k}/{n} ({100 * k / n:.1f}%)" if n else "0/0"
    return s + (f" [{100 * ci[0]:.1f}, {100 * ci[1]:.1f}]" if ci and all(x is not None for x in ci) else "")


def render(summaries: list[dict]) -> str:
    """Markdown tables for results.md, straight from the per-model summaries."""
    out = ["| Model | Cells with a file | Recompile disagrees with recorded result | No file (cut off or no Lean) | "
           "Definitions fail | Tests or statements fail | Compiles after proof→`sorry` | Compiles as is |",
           "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for s in summaries:
        n, c = s["n_cells"], s["classes"]
        out.append(f"| {s['label'].removesuffix('_g1')} | {s['n_with_file']}/{n} | {len(s['recompile_vs_scored_mismatches'])} | "
                   f"{c.get('no_file', 0)} | {c.get('definitions_fail', 0)} | {c.get('tests_or_statements_fail', 0)} | "
                   f"{c.get('compiles_after_proof_ablation', 0)} | {c.get('compiles', 0)} |")
    out += ["", "| Model | Compiles after proof→`sorry` (incl. as is), 95% Wilson CI | Cells with IC_tests·IC_proofs > 0 after ablation | "
            "Ablation IC_tests (mean over listed cells) | Ablation IC_proofs (mean over listed cells) | Definitions compile, among non-compiling files | "
            "Empty reasoning block |", "|---|---:|---:|---:|---:|---:|---:|"]
    for s in summaries:
        n = s["n_cells"]
        k, ci = s["compiles_after_proof_ablation_incl_original"]
        p, pci = s["cells_IC_tests_x_IC_proofs_positive_after_ablation"]
        dk, dn = s["definitions_only_compile_among_noncompiling"]
        t = s["think"]
        out.append(f"| {s['label'].removesuffix('_g1')} | {_pct(k, n, ci)} | {_pct(p, n, pci)} | {s['ablation_IC_tests_mean_over_n']:.3f} | "
                   f"{s['ablation_IC_proofs_mean_over_n']:.3f} | {_pct(dk, dn)} | {t['n_empty_think']}/{t['n_with_close_tag']} |")
    cats = ["parse", "unknown_name", "type_error", "tactic_failed", "termination", "index_bounds_proof", "timeout", "other"]
    regs = ["theorem_proof", "theorem_statement", "definition", "example_test", "other"]
    out += ["", "Share of non-compiling files with at least one error of each kind (a file can have several):", "",
            "| Model | Non-compiling files | " + " | ".join(cats) + " | " + " | ".join(f"in {r}" for r in regs) + " |",
            "|---|---:|" + "---:|" * (len(cats) + len(regs))]
    for s in summaries:
        nc = s["n_with_file"] - s["compiles_original"][0]
        cat, reg = s["noncompiling_files_with_error_category"], s["noncompiling_files_with_error_region"]
        out.append(f"| {s['label'].removesuffix('_g1')} | {nc} | " + " | ".join(f"{100 * cat.get(x, 0) / max(nc, 1):.0f}%" for x in cats)
                   + " | " + " | ".join(f"{100 * reg.get(x, 0) / max(nc, 1):.0f}%" for x in regs) + " |")
    subsets = [f"{s['label']}: {s['n_cells']}/{s['n_declared_cells']} declared cells measured"
               for s in summaries if s.get("n_declared_cells", s["n_cells"]) != s["n_cells"]]
    if subsets:
        out[:0] = ["Measured-subset diagnostics: " + "; ".join(subsets) + ". Unmeasured cells are not zeros.", ""]
    return "\n".join(out) + "\n"


def _cell_factors(r: dict, ablated: bool) -> tuple[float, float]:
    if r.get("class") == "compiles":
        f = r.get("original_factors", {})
    elif ablated and r.get("class") == "compiles_after_proof_ablation":
        f = r["ablation"]
    else:
        f = {}
    return f.get("IC_tests", 0.0), f.get("IC_proofs", 0.0)


def combined_summary(label: str, work_dirs: list[str]) -> dict:
    """Frozen-scorer factors over all cells when a variant's rows replace the base rows for the cells it edited.

    `work_dirs[0]` is the base run; each later directory overrides the cells it contains."""
    if not work_dirs:
        raise ValueError("a base run is required")
    cells: dict[str, dict] = {}
    base_ids: set[str] = set()
    for index, wd in enumerate(work_dirs):
        p = Path(wd) / f"rows_{label}.jsonl"
        receipt_path = Path(wd) / f"summary_{label}.json"
        receipt = json.loads(receipt_path.read_text())
        if receipt.get("label") != label or receipt.get("n_declared_cells", receipt["n_cells"]) != receipt["n_cells"]:
            raise ValueError(f"wrong label or incomplete declared cohort in {receipt_path}")
        seen: set[str] = set()
        # Missing variant files are missing evidence, not a no-op transformation.
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            tid = r["task_id"]
            if r["label"] != label or tid in seen:
                raise ValueError(f"wrong label or duplicate task in {p}: {tid}")
            if index and tid not in base_ids:
                raise ValueError(f"variant task absent from base manifest: {tid}")
            seen.add(tid)
            cells[tid] = r
        if len(seen) != receipt["n_cells"]:
            raise ValueError(f"rows do not match the completed summary receipt: {p}")
        if index == 0:
            base_ids = seen
    rows = list(cells.values())
    n = len(rows)
    if not n:
        raise ValueError("cannot combine an empty base run")
    unmeasured = [r["task_id"] for r in rows if r.get("status") == "diagnostic_error"]
    if unmeasured:
        raise ValueError(f"unmeasured diagnostic cells retained in rows; refusing zero-filled summary: {unmeasured}")
    out = {"label": label, "work_dirs": work_dirs, "n_cells": n,
           "n_cells_from_variants": sum(1 for r in rows if any(k in r for k in ("surface_repairs", "n_namespaces_escaped"))),
           "n_diagnostic_errors": sum(1 for r in rows if r.get("status") == "diagnostic_error")}
    for name, ablated in (("as_written", False), ("failing_proofs_sorried", True)):
        f = [_cell_factors(r, ablated) for r in rows]
        comp = sum(1 for r in rows if r.get("class") == "compiles"
                   or (ablated and r.get("class") == "compiles_after_proof_ablation"))
        pos = sum(1 for t, q in f if t * q > 0)
        out[name] = {"compiles": [comp, wilson(comp, n)], "IC_tests_mean": round(sum(t for t, _ in f) / n, 4),
                     "IC_proofs_mean": round(sum(q for _, q in f) / n, 4), "cells_IC_tests_x_IC_proofs_positive": [pos, wilson(pos, n)]}
    return out


def render_combined(rows: list[tuple[str, dict]]) -> str:
    out = ["| Model | Files as scored | Compile, as written [95% CI] | IC_tests | IC_proofs | Cells with IC_tests·IC_proofs > 0 | "
           "Compile after failing proofs → `sorry` | IC_tests | IC_proofs | Cells with IC_tests·IC_proofs > 0 |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for variant, c in rows:
        a, b = c["as_written"], c["failing_proofs_sorried"]
        n = c["n_cells"]
        out.append(f"| {c['label'].removesuffix('_g1')} | {variant} | {_pct(a['compiles'][0], n, a['compiles'][1])} | {a['IC_tests_mean']:.3f} | "
                   f"{a['IC_proofs_mean']:.3f} | {_pct(a['cells_IC_tests_x_IC_proofs_positive'][0], n, a['cells_IC_tests_x_IC_proofs_positive'][1])} | "
                   f"{_pct(b['compiles'][0], n, b['compiles'][1])} | {b['IC_tests_mean']:.3f} | {b['IC_proofs_mean']:.3f} | "
                   f"{_pct(b['cells_IC_tests_x_IC_proofs_positive'][0], n, b['cells_IC_tests_x_IC_proofs_positive'][1])} |")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--exp01-out")
    ap.add_argument("--scorer-dir", help="pinned frozen scorer's scripts/scsc directory")
    ap.add_argument("--lake-dir", default=None, help="grading Lean project; defaults to the frozen scorer's LAKE_DIR")
    ap.add_argument("--work-dir", required=True)
    ap.add_argument("--labels", nargs="+", required=True)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--timeout", type=int, default=600, help="per-compile seconds (frozen scorer: 600)")
    ap.add_argument("--max-rounds", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--render", action="store_true", help="only print markdown tables from existing summaries")
    ap.add_argument("--combine", nargs="+", default=None, metavar="VARIANT_DIR",
                    help="only print frozen-scorer factors over all cells, base rows overridden by each variant in turn")
    ap.add_argument("--escape-digit-namespace", action="store_true",
                    help="diagnostic variant: wrap digit-leading namespace names in «» first (only cells that have one)")
    ap.add_argument("--repair-surface-syntax", action="store_true",
                    help="diagnostic variant: namespace escape plus comment-syntax fixes (only cells it edits)")
    args = ap.parse_args(argv)
    if args.render:
        print(render([json.loads((Path(args.work_dir) / f"summary_{lb}.json").read_text()) for lb in args.labels]))
        return 0
    if args.combine:
        pretty = {"full_nsfix": "+ namespace escaped", "full_surface": "+ comment syntax repaired"}
        names = ["model's own file"] + [pretty.get(Path(d).name, f"+ {Path(d).name}") for d in args.combine]
        combos = []
        for lb in args.labels:
            for k, name in enumerate(names):
                c = combined_summary(lb, [args.work_dir] + args.combine[:k])
                combos.append((name, c))
                (Path(args.work_dir) / f"combined_{lb}__{k}.json").write_text(json.dumps(c, indent=2) + "\n")
        print(render_combined(combos))
        return 0
    if not (args.exp01_out and args.scorer_dir):
        ap.error("--exp01-out and --scorer-dir are required unless --render")
    scorer = frozen_scorer(args.scorer_dir)
    if args.lake_dir is None:
        args.lake_dir = scorer.LAKE_DIR
    wd = Path(args.work_dir)
    wd.mkdir(parents=True, exist_ok=True)
    for label in args.labels:
        rows_path = wd / f"rows_{label}.jsonl"
        done = {}
        if rows_path.is_file():
            for x in rows_path.read_text().splitlines():
                if x.strip():
                    r = json.loads(x)
                    done[r["task_id"]] = r
        declared_jobs = build_jobs(args, label)
        selected_jobs = declared_jobs[:args.limit] if args.limit else declared_jobs
        jobs = [j for j in selected_jobs if j["task_id"] not in done]
        print(f"{label}: {len(done)} done, {len(jobs)} to run", file=sys.stderr, flush=True)
        with rows_path.open("a", encoding="utf-8") as fh, ProcessPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(diagnose_cell, j): j for j in jobs}
            for k, f in enumerate(as_completed(futs), 1):
                j = futs[f]
                try:
                    r = f.result()
                except Exception as exc:  # recorded, never dropped: the cell stays in the denominator
                    r = {k2: j[k2] for k2 in ("label", "task_id", "split")}
                    r.update(status="diagnostic_error", error=repr(exc)[:300])
                done[r["task_id"]] = r
                fh.write(json.dumps(r, default=_jsonable) + "\n")
                fh.flush()
                if k % 50 == 0:
                    print(f"{label}: {k}/{len(jobs)}", file=sys.stderr, flush=True)
        rows = [json.loads(json.dumps(r, default=_jsonable)) for r in done.values()]
        summ = summarize(label, rows)
        summ["n_declared_cells"] = len(declared_jobs)
        summ["cohort"] = "full declared set" if len(rows) == len(declared_jobs) else "measured subset"
        (wd / f"summary_{label}.json").write_text(json.dumps(summ, indent=2, default=_jsonable) + "\n")
        print(json.dumps({k: summ[k] for k in ("label", "classes", "compiles_after_proof_ablation_incl_original",
                                                 "cells_IC_tests_x_IC_proofs_positive_after_ablation")}),
              flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
