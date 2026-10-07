"""TLDR: Fetch the inputs for experiment 07 phase A: gold test lists for SWE-bench Verified and every public submission's per-instance report.json files."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

S3_BUCKET = "swe-bench-submissions"
EXPERIMENTS_COMMIT = "40f164d5b8f1d249bf95a6df8b74b577fd8e519d"
GOLD_REVISION = "c104f840cc67f8b6eec6f759ebc8b2693d585d4a"
GOLD_DATASET = "princeton-nlp/SWE-bench_Verified"


def build_gold(dataset: str, revision: str, out: Path) -> None:
    """Write one JSON line per task: instance_id, FAIL_TO_PASS and PASS_TO_PASS gold test lists."""
    from datasets import load_dataset  # optional dependency, only needed here

    rows = load_dataset(dataset, split="test", revision=revision)
    if len(rows) != 500 or len({r["instance_id"] for r in rows}) != 500:
        raise ValueError("locked gold dataset requires 500 unique task IDs")
    with out.open("w") as fh:
        for r in rows:
            parse = lambda v: json.loads(v) if isinstance(v, str) else list(v)  # noqa: E731
            rec = {"instance_id": r["instance_id"], "FAIL_TO_PASS": parse(r["FAIL_TO_PASS"]), "PASS_TO_PASS": parse(r["PASS_TO_PASS"])}
            fh.write(json.dumps(rec) + "\n")


def submission_source(sub_dir: Path) -> str:
    """'s3' unless the submission's metadata names its own artifact repository (mid-2026 onward)."""
    for name in ("metadata.yaml", "metadata.yml"):
        meta_path = sub_dir / name
        if meta_path.is_file():
            import yaml

            meta = yaml.safe_load(meta_path.read_text()) or {}
            repo = (meta.get("assets") or {}).get("repo")
            if repo:
                return f"github:{repo}"
    return "s3"


def sync_s3(split: str, sub: str, dest: Path) -> int:
    """Download a submission's report.json files and all_preds.jsonl with unsigned S3 access; return the report count."""
    prefix = f"s3://{S3_BUCKET}/{split}/{sub}"
    sync = ["aws", "s3", "sync", "--no-sign-request", "--only-show-errors", f"{prefix}/logs/", str(dest / "logs"),
            "--exclude", "*", "--include", "*/report.json"]
    subprocess.run(sync, check=True)
    # A failed cp may leave a truncated file; never interpret its missing task rows as no generation.
    pending = dest / "all_preds.jsonl.partial"
    result = subprocess.run(["aws", "s3", "cp", "--no-sign-request", "--only-show-errors", f"{prefix}/all_preds.jsonl", str(pending)],
                            check=False)
    if result.returncode == 0:
        for line in pending.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                if not isinstance(row.get("instance_id"), str) or "model_patch" not in row:
                    raise ValueError("invalid prediction row; leave submission unmeasured pending download repair")
        pending.replace(dest / "all_preds.jsonl")
    else:
        pending.unlink(missing_ok=True)
    return len(list((dest / "logs").glob("*/report.json")))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--experiments-repo", type=Path, required=True, help="clone of SWE-bench/experiments at the pinned commit")
    ap.add_argument("--split", default="verified")
    ap.add_argument("--out", type=Path, required=True, help="raw data root on the host (not committed)")
    ap.add_argument("--gold-dataset", default="princeton-nlp/SWE-bench_Verified")
    ap.add_argument("--gold-revision", required=True, help="exact Hugging Face dataset revision (commit sha)")
    args = ap.parse_args()

    git = ["git", "-C", str(args.experiments_repo)]
    commit = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    if (commit, args.split, args.gold_dataset, args.gold_revision) != (EXPERIMENTS_COMMIT, "verified", GOLD_DATASET, GOLD_REVISION):
        raise ValueError("inputs differ from the locked phase A pins; use a separate protocol/version")
    if subprocess.check_output([*git, "status", "--porcelain", "--untracked-files=all", "--", "evaluation/verified"], text=True).strip():
        raise ValueError("submission metadata tree is dirty; restore the pinned input checkout first")
    names = subprocess.check_output([*git, "ls-tree", "-d", "--name-only", "HEAD:evaluation/verified"], text=True).splitlines()
    if not names:
        raise ValueError("pinned submission inventory is empty")
    inputs = {"experiments_commit": commit, "split": args.split, "gold_dataset": args.gold_dataset,
              "gold_revision": args.gold_revision, "submissions": sorted(names)}
    args.out.mkdir(parents=True, exist_ok=True)
    gold_path, manifest_path = args.out / "gold_tests.jsonl", args.out / "inputs_manifest.json"
    if gold_path.exists():
        if not manifest_path.is_file():
            raise ValueError("cached gold lacks provenance; use a fresh --out directory")
        manifest = json.loads(manifest_path.read_text())
        digest = hashlib.sha256(gold_path.read_bytes()).hexdigest()
        if manifest != inputs | {"gold_sha256": digest}:
            raise ValueError("cached inputs differ from pinned provenance; use a fresh --out directory")
    else:
        pending = gold_path.with_suffix(".jsonl.partial")
        build_gold(args.gold_dataset, args.gold_revision, pending)
        pending.replace(gold_path)
        inputs["gold_sha256"] = hashlib.sha256(gold_path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(inputs, indent=1) + "\n")

    inventory = []
    for name in sorted(names):
        sub_dir = args.experiments_repo / "evaluation" / args.split / name
        dest = args.out / "submissions" / sub_dir.name
        dest.mkdir(parents=True, exist_ok=True)
        for name in ("metadata.yaml", "metadata.yml", "results/results.json", "per_instance_details.json"):
            if (sub_dir / name).is_file():
                shutil.copy(sub_dir / name, dest / Path(name).name)
        source = submission_source(sub_dir)
        entry = {"submission": sub_dir.name, "source": source, "reports": 0, "error": None}
        if source == "s3":
            try:
                entry["reports"] = sync_s3(args.split, sub_dir.name, dest)
            except subprocess.CalledProcessError as exc:
                entry["error"] = f"s3 sync failed: exit {exc.returncode}"
        else:
            entry["error"] = "github-hosted logs: fetch adapter not yet implemented"
        inventory.append(entry)
        print(json.dumps(entry), flush=True)
    pending_inventory = args.out / "inventory.json.partial"
    pending_inventory.write_text(json.dumps(inventory, indent=1) + "\n")
    pending_inventory.replace(args.out / "inventory.json")


if __name__ == "__main__":
    main()
