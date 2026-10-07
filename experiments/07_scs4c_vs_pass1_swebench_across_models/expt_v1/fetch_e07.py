"""TLDR: Fetch the inputs for experiment 07 phase A: gold test lists for SWE-bench Verified and every public submission's per-instance report.json files."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

S3_BUCKET = "swe-bench-submissions"


def build_gold(dataset: str, revision: str, out: Path) -> None:
    """Write one JSON line per task: instance_id, FAIL_TO_PASS and PASS_TO_PASS gold test lists."""
    from datasets import load_dataset  # optional dependency, only needed here

    rows = load_dataset(dataset, split="test", revision=revision)
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
    subprocess.run(["aws", "s3", "cp", "--no-sign-request", "--only-show-errors", f"{prefix}/all_preds.jsonl", str(dest / "all_preds.jsonl")],
                   check=False)
    return len(list((dest / "logs").glob("*/report.json")))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--experiments-repo", type=Path, required=True, help="clone of SWE-bench/experiments at the pinned commit")
    ap.add_argument("--split", default="verified")
    ap.add_argument("--out", type=Path, required=True, help="raw data root on the host (not committed)")
    ap.add_argument("--gold-dataset", default="princeton-nlp/SWE-bench_Verified")
    ap.add_argument("--gold-revision", required=True, help="exact Hugging Face dataset revision (commit sha)")
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    gold_path = args.out / "gold_tests.jsonl"
    if not gold_path.exists():
        build_gold(args.gold_dataset, args.gold_revision, gold_path)

    inventory = []
    for sub_dir in sorted((args.experiments_repo / "evaluation" / args.split).iterdir()):
        if not sub_dir.is_dir():
            continue
        dest = args.out / "submissions" / sub_dir.name
        dest.mkdir(parents=True, exist_ok=True)
        for name in ("metadata.yaml", "results/results.json", "per_instance_details.json"):
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
    (args.out / "inventory.json").write_text(json.dumps(inventory, indent=1) + "\n")


if __name__ == "__main__":
    main()
