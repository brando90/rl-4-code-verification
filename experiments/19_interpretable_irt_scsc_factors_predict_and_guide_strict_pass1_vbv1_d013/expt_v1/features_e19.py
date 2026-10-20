"""TLDR: Deterministic, interpretable task-content features for experiment 19's explanatory item response theory (IRT) models, computed from each VeriBench V1 task's Python source and gold Lean reference at the pinned VeriBench commit (no model outputs, no scores)."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPLIT_MANIFEST = REPO / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split/vbv1_split_manifest.csv"
VERIBENCH_PIN = json.loads((REPO / "external/deps.lock.json").read_text())["veribench"]["commit"]
PY_ROOT = "veribench_dataset/py_src/"
GOLD_ROOT = "veribench_dataset/lean_src/veribench/"

# Family groups: the five core sets keep their own level; IndustrySet families collapse by provenance.
CORE_FAMILIES = ("security_set", "humaneval_set", "easy_set", "realcode_set", "cs_set")
FAMILY_GROUPS = ("security_set", "humaneval_set", "easy_set", "realcode_set", "cs_set", "industry_real", "industry_synthetic")
REFERENCE_GROUP = "security_set"  # dropped level of the one-hot coding

# Pre-registered primary feature set (PROTOCOL.md section 3.3). Counts enter as log1p, flags as 0/1.
PY_FEATURES = ("py_stmts", "py_funcs", "py_loops", "py_branches", "py_float", "py_str", "py_check_asserts")
GOLD_FEATURES = ("gold_theorems", "gold_examples", "gold_loc")
LOG_FEATURES = ("py_stmts", "py_funcs", "py_loops", "py_branches", "py_check_asserts", "gold_theorems", "gold_examples", "gold_loc")

_THEOREM = re.compile(r"^\s*(?:@\[[^\]]*\]\s*)*(?:private\s+|protected\s+)?(?:theorem|lemma)\s")
_EXAMPLE = re.compile(r"^\s*example\b")


def family_group(family: str) -> str:
    if family in CORE_FAMILIES:
        return family
    if family.endswith("_real"):
        return "industry_real"
    if family.endswith("_synthetic"):
        return "industry_synthetic"
    raise ValueError(f"unknown VeriBench family: {family}")


def git_show(rel: str, *, repo: Path, commit: str = VERIBENCH_PIN) -> str:
    out = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{rel}"], capture_output=True, text=True, check=True)
    return out.stdout


def _impl_nodes(tree: ast.Module) -> list[ast.AST]:
    """Top-level function and class definitions other than the task's `check` harness."""
    return [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name != "check"]


def python_features(src: str) -> dict[str, float]:
    """Counts over the implementation (everything except `check` and the `__main__` block), plus the number of
    asserts in `check` (the task's own Python unit tests)."""
    tree = ast.parse(src)
    impl = _impl_nodes(tree)
    walk = [m for n in impl for m in ast.walk(n)]
    check = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "check"]
    names = {m.id for m in walk if isinstance(m, ast.Name)} | {m.attr for m in walk if isinstance(m, ast.Attribute)}
    consts = [m.value for m in walk if isinstance(m, ast.Constant)]
    return {
        "py_stmts": float(sum(isinstance(m, ast.stmt) for m in walk)),
        "py_funcs": float(sum(isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) for m in walk)),
        "py_loops": float(sum(isinstance(m, (ast.For, ast.AsyncFor, ast.While, ast.comprehension)) for m in walk)),
        "py_branches": float(sum(isinstance(m, (ast.If, ast.IfExp, ast.Match)) for m in walk)),
        "py_float": float("float" in names or any(isinstance(c, float) for c in consts)),
        "py_str": float("str" in names),
        "py_check_asserts": float(sum(isinstance(m, ast.Assert) for c in check for m in ast.walk(c))),
    }


def lean_features(src: str) -> dict[str, float]:
    """Declaration counts and non-comment line count of the gold reference (block comments removed)."""
    body = re.sub(r"/-.*?-/", "", src, flags=re.S)
    lines = [ln for ln in body.splitlines() if ln.strip() and not ln.strip().startswith("--")]
    return {
        "gold_theorems": float(sum(bool(_THEOREM.match(ln)) for ln in lines)),
        "gold_examples": float(sum(bool(_EXAMPLE.match(ln)) for ln in lines)),
        "gold_loc": float(len(lines)),
    }


def raw_features(veribench_repo: Path, manifest: Path = SPLIT_MANIFEST) -> list[dict]:
    """One row per train or validation VeriBench V1 task: id, split, family group, core flag and the raw
    (untransformed) features. Test-split sources are never read."""
    rows = []
    with manifest.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r["split"] == "test":
                continue
            py = git_show(PY_ROOT + r["py_relpath"], repo=veribench_repo)
            gold = git_show(GOLD_ROOT + r["gold_relpath"], repo=veribench_repo)
            if hashlib.sha256(py.encode()).hexdigest() != r["py_sha256"] or hashlib.sha256(gold.encode()).hexdigest() != r["gold_sha256"]:
                raise RuntimeError(f"{r['task_id']}: source hash differs from the D-013 split manifest")
            row = {"task_id": r["task_id"], "split": r["split"], "family": r["family"], "family_group": family_group(r["family"]),
                   "core": int(r["core"])}
            row.update(python_features(py))
            row.update(lean_features(gold))
            rows.append(row)
    return rows


def design_matrix(rows: list[dict], train_mask: np.ndarray, features: tuple[str, ...] = PY_FEATURES + GOLD_FEATURES) -> tuple[np.ndarray, list[str]]:
    """Design matrix (tasks × columns): an intercept, then log1p counts and flags z-scored with train-split moments only,
    then family-group indicators (reference level dropped). Column names are returned for coefficient tables."""
    cols, names = [np.ones(len(rows))], ["intercept"]
    for f in features:
        v = np.array([float(r[f]) for r in rows])
        if f in LOG_FEATURES:
            v = np.log1p(v)
        mu, sd = v[train_mask].mean(), v[train_mask].std()
        cols.append((v - mu) / sd if sd > 0 else np.zeros_like(v))
        names.append(f)
    for g in FAMILY_GROUPS:
        if g == REFERENCE_GROUP:
            continue
        cols.append(np.array([1.0 if r["family_group"] == g else 0.0 for r in rows]))
        names.append(f"family:{g}")
    return np.column_stack(cols), names


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--veribench", type=Path, default=Path.home() / "veribench", help="a VeriBench clone containing the pinned commit")
    ap.add_argument("--out", type=Path, default=HERE / "results/task_features_e19.csv")
    args = ap.parse_args()
    rows = raw_features(args.veribench)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} task rows to {args.out} (VeriBench {VERIBENCH_PIN})")


if __name__ == "__main__":
    main()
