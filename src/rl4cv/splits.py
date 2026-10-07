"""Deterministic, group-aware, stratified train / validation / test split of the VeriBench V1 tasks (D-013).

Unit: one VeriBench V1 task (one ``veribench_dataset/py_src`` program and its gold Lean reference under
``veribench_dataset/lean_src/veribench``). Tasks that copy or nearly copy each other form one group, and a
group never straddles two splits. Two tasks are linked when

* their normalized texts hash equal, or their word-5-gram Jaccard similarity is >= 0.70 (``rl4cv.screens``),
  on the Python source or on the gold Lean reference; or
* they are one security safe / vulnerable pair (``security_6858/{vulnerabilities,safe}/<stem>[_safe]``,
  ``security_python/{vulnerabilities,safe}/<n>_*``).

Every group is visited once in sha256(salt:group) order and goes to the split with the largest remaining
deficit against its families' largest-remainder targets (a family is the first ``py_src`` directory, e.g.
``humaneval_set``). The assignment never reads a model output or score, so it is outcome-blind, and the
same inputs and salt always give byte-identical manifests.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from rl4cv.screens import jaccard, norm_hash, shingles
from rl4cv.veribench.pack import CORE_SPLITS

SPLITS = ("train", "validation", "test")
DEFAULT_FRACTIONS = (0.60, 0.15, 0.25)
DEFAULT_SALT = "rl4cv-d013-vbv1-split-v1"
DEFAULT_THRESHOLD = 0.70
DEFAULT_NGRAM = 5
MANIFEST_FIELDS = ("task_id", "family", "core", "split", "group_id", "group_size", "py_relpath", "gold_relpath", "py_sha256", "gold_sha256")


@dataclass(frozen=True)
class VBTask:
    task_id: str
    family: str
    core: bool
    py_relpath: str
    py_text: str
    gold_relpath: str | None
    gold_text: str | None


def task_id_for(py_relpath: str) -> str:
    """VeriBench task id: the lowercased ``py_src`` path without ``.py``, with ``/`` replaced by ``__``."""
    p = py_relpath.replace("\\", "/")
    if p.endswith(".py"):
        p = p[:-3]
    return p.lower().replace("/", "__")


def _match_key(relpath: str) -> str:
    """Key that pairs ``my_boolean_double_neg.py`` with ``MyBooleanDoubleNeg.lean`` in the same directory."""
    p = relpath.replace("\\", "/")
    directory, _, name = p.rpartition("/")
    stem = name.rsplit(".", 1)[0]
    return f"{directory.lower()}/{re.sub(r'[^a-z0-9]', '', stem.lower())}"


def pair_key(py_relpath: str) -> str | None:
    """Key shared by a security task's vulnerable and safe versions; None outside the security set."""
    parts = py_relpath.replace("\\", "/").split("/")
    if len(parts) != 4 or parts[0] != "security_set" or parts[2] not in ("vulnerabilities", "safe"):
        return None
    stem = parts[3][:-3] if parts[3].endswith(".py") else parts[3]
    if parts[1] == "security_python":
        m = re.match(r"(\d+)_", stem)
        return f"security_python:{m.group(1)}" if m else None
    stem = stem.lower()
    if parts[2] == "safe" and stem.endswith("_safe"):
        stem = stem[: -len("_safe")]
    return f"{parts[1]}:{stem}"


def load_vbv1_tasks(veribench_root: str | Path) -> tuple[list[VBTask], dict]:
    """Every ``py_src`` program with its gold Lean file (matched by directory and alphanumeric stem)."""
    root = Path(veribench_root)
    py_root = root / "veribench_dataset" / "py_src"
    lean_root = root / "veribench_dataset" / "lean_src" / "veribench"
    if not py_root.is_dir() or not lean_root.is_dir():
        raise FileNotFoundError(f"expected {py_root} and {lean_root}")
    lean_by_key: dict[str, list[str]] = {}
    for f in sorted(lean_root.rglob("*.lean")):
        rel = f.relative_to(lean_root).as_posix()
        lean_by_key.setdefault(_match_key(rel), []).append(rel)
    tasks: list[VBTask] = []
    unmatched_py: list[str] = []
    ambiguous: dict[str, list[str]] = {}
    used_lean: set[str] = set()
    for f in sorted(py_root.rglob("*.py")):
        if "__pycache__" in f.parts:
            continue
        rel = f.relative_to(py_root).as_posix()
        cands = lean_by_key.get(_match_key(rel), [])
        gold_rel = cands[0] if len(cands) == 1 else None
        if len(cands) > 1:
            ambiguous[rel] = cands
        elif not cands:
            unmatched_py.append(rel)
        if gold_rel:
            used_lean.add(gold_rel)
        family = rel.split("/", 1)[0]
        tasks.append(
            VBTask(
                task_id=task_id_for(rel),
                family=family,
                core=family in CORE_SPLITS,
                py_relpath=rel,
                py_text=f.read_text(encoding="utf-8"),
                gold_relpath=gold_rel,
                gold_text=(lean_root / gold_rel).read_text(encoding="utf-8") if gold_rel else None,
            )
        )
    ids = [t.task_id for t in tasks]
    if len(set(ids)) != len(ids):
        dup = sorted({i for i in ids if ids.count(i) > 1})
        raise ValueError(f"task ids collide after lowercasing: {dup[:10]}")
    all_lean = {rel for rels in lean_by_key.values() for rel in rels}
    mapping = {
        "py_files": len(tasks),
        "gold_matched": sum(1 for t in tasks if t.gold_relpath),
        "py_without_gold": unmatched_py,
        "py_with_ambiguous_gold": ambiguous,
        "gold_without_py": sorted(all_lean - used_lean),
    }
    return tasks, mapping


class _UnionFind:
    def __init__(self, items: list[str]):
        self.parent = {i: i for i in items}

    def find(self, x: str) -> str:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            lo, hi = sorted((ra, rb))
            self.parent[hi] = lo


def similar_pairs(texts: dict[str, str], *, threshold: float = DEFAULT_THRESHOLD, n: int = DEFAULT_NGRAM) -> list[tuple[str, str, str, float]]:
    """All pairs whose normalized texts hash equal ('exact') or whose word-n-gram Jaccard is >= threshold ('near')."""
    ids = sorted(texts)
    hashes = {i: norm_hash(texts[i]) for i in ids}
    sh = {i: shingles(texts[i], n) for i in ids}
    out = []
    for a_idx, a in enumerate(ids):
        for b in ids[a_idx + 1 :]:
            if hashes[a] == hashes[b]:
                out.append((a, b, "exact", 1.0))
                continue
            sa, sb = sh[a], sh[b]
            if not sa or not sb:
                continue
            # Jaccard <= min/max size ratio, so skip pairs that cannot reach the threshold.
            if min(len(sa), len(sb)) < threshold * max(len(sa), len(sb)):
                continue
            j = jaccard(sa, sb)
            if j >= threshold:
                out.append((a, b, "near", round(j, 4)))
    return out


def group_tasks(tasks: list[VBTask], *, threshold: float = DEFAULT_THRESHOLD, n: int = DEFAULT_NGRAM) -> tuple[dict[str, str], list[dict]]:
    """Map each task id to its group id (the smallest member id) and list every linking edge with its reason."""
    ids = [t.task_id for t in tasks]
    uf = _UnionFind(ids)
    edges: list[dict] = []
    for kind, texts in (("py", {t.task_id: t.py_text for t in tasks}), ("gold", {t.task_id: t.gold_text for t in tasks if t.gold_text})):
        for a, b, how, j in similar_pairs(texts, threshold=threshold, n=n):
            edges.append({"a": a, "b": b, "reason": f"{kind}_{how}", "jaccard": j})
            uf.union(a, b)
    by_pair: dict[str, list[str]] = {}
    for t in tasks:
        k = pair_key(t.py_relpath)
        if k:
            by_pair.setdefault(k, []).append(t.task_id)
    for k, members in sorted(by_pair.items()):
        for other in members[1:]:
            edges.append({"a": members[0], "b": other, "reason": "security_pair", "jaccard": None})
            uf.union(members[0], other)
    return {i: uf.find(i) for i in ids}, edges


def largest_remainder(n: int, fractions: tuple[float, ...]) -> list[int]:
    """Integer counts summing to n, proportional to fractions (Hamilton's method, ties to the earlier split)."""
    raw = [n * f for f in fractions]
    base = [math.floor(x) for x in raw]
    order = sorted(range(len(raw)), key=lambda i: (-(raw[i] - base[i]), i))
    for i in order[: n - sum(base)]:
        base[i] += 1
    return base


def _rank(salt: str, key: str) -> str:
    return hashlib.sha256(f"{salt}:{key}".encode("utf-8")).hexdigest()


def assign_splits(tasks: list[VBTask], group_of: dict[str, str], *, fractions: tuple[float, ...] = DEFAULT_FRACTIONS, salt: str = DEFAULT_SALT) -> dict[str, str]:
    """Assign whole groups, in salted-hash order, to the split with the largest summed per-family deficit."""
    if len(fractions) != len(SPLITS) or abs(sum(fractions) - 1.0) > 1e-9 or min(fractions) <= 0:
        raise ValueError(f"fractions must be {len(SPLITS)} positive numbers summing to 1, got {fractions}")
    fam_of = {t.task_id: t.family for t in tasks}
    fam_sizes: dict[str, int] = {}
    for t in tasks:
        fam_sizes[t.family] = fam_sizes.get(t.family, 0) + 1
    target = {f: largest_remainder(n, fractions) for f, n in fam_sizes.items()}
    assigned = {f: [0] * len(SPLITS) for f in fam_sizes}
    members: dict[str, list[str]] = {}
    for tid, g in group_of.items():
        members.setdefault(g, []).append(tid)
    split_of: dict[str, str] = {}
    for g in sorted(members, key=lambda g: (_rank(salt, g), g)):
        best_s, best_score = 0, None
        for s in range(len(SPLITS)):
            score = sum(target[fam_of[m]][s] - assigned[fam_of[m]][s] for m in members[g])
            # Ties go to the split whose salted (group, split) hash is smallest, so no split is favoured.
            key = (score, _rank(salt, f"{g}|{SPLITS[s]}"))
            if best_score is None or key[0] > best_score[0] or (key[0] == best_score[0] and key[1] < best_score[1]):
                best_s, best_score = s, key
        for m in members[g]:
            assigned[fam_of[m]][best_s] += 1
            split_of[m] = SPLITS[best_s]
    return split_of


def leakage_report(tasks: list[VBTask], split_of: dict[str, str], *, n: int = DEFAULT_NGRAM, top: int = 20) -> dict:
    """Largest cross-split word-n-gram Jaccard (Python and gold Lean): every value is below the grouping threshold."""
    report: dict = {}
    for kind, attr in (("py", "py_text"), ("gold", "gold_text")):
        sh = {t.task_id: shingles(getattr(t, attr), n) for t in tasks if getattr(t, attr)}
        ids = sorted(sh)
        pairs = []
        for a_idx, a in enumerate(ids):
            for b in ids[a_idx + 1 :]:
                if split_of[a] == split_of[b]:
                    continue
                j = jaccard(sh[a], sh[b])
                if j > 0:
                    pairs.append((round(j, 4), a, b))
        pairs.sort(key=lambda p: (-p[0], p[1], p[2]))
        report[kind] = {
            "max_cross_split_jaccard": pairs[0][0] if pairs else 0.0,
            "top_pairs": [{"jaccard": j, "a": a, "split_a": split_of[a], "b": b, "split_b": split_of[b]} for j, a, b in pairs[:top]],
        }
    return report


def _sha256_file(text: str | None) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest() if text is not None else ""


def build_split(veribench_root: str | Path, *, fractions: tuple[float, ...] = DEFAULT_FRACTIONS, salt: str = DEFAULT_SALT, threshold: float = DEFAULT_THRESHOLD, n: int = DEFAULT_NGRAM, with_leakage: bool = True) -> dict:
    """Load, group and assign; returns manifest rows, a summary and (optionally) the cross-split leakage report."""
    tasks, mapping = load_vbv1_tasks(veribench_root)
    group_of, edges = group_tasks(tasks, threshold=threshold, n=n)
    split_of = assign_splits(tasks, group_of, fractions=fractions, salt=salt)
    sizes: dict[str, int] = {}
    for g in group_of.values():
        sizes[g] = sizes.get(g, 0) + 1
    rows = [
        {
            "task_id": t.task_id,
            "family": t.family,
            "core": int(t.core),
            "split": split_of[t.task_id],
            "group_id": group_of[t.task_id],
            "group_size": sizes[group_of[t.task_id]],
            "py_relpath": t.py_relpath,
            "gold_relpath": t.gold_relpath or "",
            "py_sha256": _sha256_file(t.py_text),
            "gold_sha256": _sha256_file(t.gold_text),
        }
        for t in sorted(tasks, key=lambda t: t.task_id)
    ]
    manifest_csv = manifest_to_csv(rows)

    summary = _split_summary(rows, sizes, edges, mapping, manifest_csv, fractions, salt, threshold, n)
    out = {"rows": rows, "manifest_csv": manifest_csv, "summary": summary, "edges": edges}
    if with_leakage:
        out["leakage"] = leakage_report(tasks, split_of, n=n)
    return out


def _split_summary(rows: list[dict], sizes: dict[str, int], edges: list[dict], mapping: dict,
                   manifest_csv: str, fractions: tuple[float, ...], salt: str, threshold: float, n: int) -> dict:
    """Summarize the manifest's counts, grouping evidence and reproducibility parameters."""
    def counts(pred) -> dict:
        c = {s: 0 for s in SPLITS}
        for r in rows:
            if pred(r):
                c[r["split"]] += 1
        return c

    families = sorted({r["family"] for r in rows})
    size_hist: dict[str, int] = {}
    for s in sizes.values():
        size_hist[str(s)] = size_hist.get(str(s), 0) + 1
    edge_counts: dict[str, int] = {}
    for e in edges:
        edge_counts[e["reason"]] = edge_counts.get(e["reason"], 0) + 1
    return {
        "schema": "rl4cv-vbv1-split-v1",
        "decision": "D-013",
        "parameters": {"fractions": dict(zip(SPLITS, fractions)), "salt": salt, "jaccard_threshold": threshold, "ngram": n},
        "tasks": len(rows),
        "groups": len(sizes),
        "group_size_histogram": dict(sorted(size_hist.items(), key=lambda kv: int(kv[0]))),
        "link_edges_by_reason": dict(sorted(edge_counts.items())),
        "counts": {"all": counts(lambda r: True), "core_614": counts(lambda r: r["core"] == 1), "industryset_282": counts(lambda r: r["core"] == 0)},
        "counts_by_family": {f: counts(lambda r, f=f: r["family"] == f) for f in families},
        "gold_mapping": mapping,
        "manifest_sha256": hashlib.sha256(manifest_csv.encode("utf-8")).hexdigest(),
    }


def manifest_to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r[k] for k in MANIFEST_FIELDS})
    return buf.getvalue()


def read_manifest(path: str | Path) -> dict[str, str]:
    """task_id -> split from a committed manifest CSV."""
    with open(path, encoding="utf-8", newline="") as fh:
        return {r["task_id"]: r["split"] for r in csv.DictReader(fh)}


def main(argv: list[str] | None = None) -> int:
    """CLI: build the split from a VeriBench checkout and write the manifest, id lists, summary and leakage report."""
    ap = argparse.ArgumentParser(description="Build the D-013 VeriBench V1 train/validation/test split")
    ap.add_argument("--veribench-root", required=True, type=Path)
    ap.add_argument("--veribench-commit", required=True, help="commit the checkout is at (recorded, not checked out)")
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--fractions", type=float, nargs=3, default=list(DEFAULT_FRACTIONS))
    ap.add_argument("--salt", default=DEFAULT_SALT)
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    args = ap.parse_args(argv)
    res = build_split(args.veribench_root, fractions=tuple(args.fractions), salt=args.salt, threshold=args.threshold)
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "vbv1_split_manifest.csv").write_text(res["manifest_csv"], encoding="utf-8")
    for s in SPLITS:
        ids = [r["task_id"] for r in res["rows"] if r["split"] == s]
        (out / f"vbv1_{s}_task_ids.txt").write_text("".join(i + "\n" for i in ids), encoding="utf-8")
    summary = dict(res["summary"], veribench_commit=args.veribench_commit)
    (out / "vbv1_split_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (out / "vbv1_split_links.json").write_text(json.dumps(res["edges"], indent=1) + "\n", encoding="utf-8")
    (out / "vbv1_split_leakage.json").write_text(json.dumps(res["leakage"], indent=2) + "\n", encoding="utf-8")
    c = summary["counts"]
    print(f"{summary['tasks']} tasks in {summary['groups']} groups -> all {c['all']} core {c['core_614']} industry {c['industryset_282']}")
    print(f"max cross-split Jaccard: py {res['leakage']['py']['max_cross_split_jaccard']} gold {res['leakage']['gold']['max_cross_split_jaccard']}")
    print(f"manifest sha256 {summary['manifest_sha256']} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
