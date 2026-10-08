"""TLDR: Fetch the inputs for experiment 07 phase A: gold test lists for SWE-bench Verified and every public submission's per-instance report.json files."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

from rl4cv.scs4c import prediction_patch_presence

S3_BUCKET = "swe-bench-submissions"
EXPERIMENTS_COMMIT = "40f164d5b8f1d249bf95a6df8b74b577fd8e519d"
GOLD_REVISION = "c104f840cc67f8b6eec6f759ebc8b2693d585d4a"
GOLD_DATASET = "princeton-nlp/SWE-bench_Verified"
UNSIGNED = ("--no-sign-request", "--only-show-errors")
COPIED_METADATA = ("metadata.yaml", "metadata.yml", "results/results.json", "per_instance_details.json")


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


def read_metadata(sub_dir: Path) -> dict:
    """The submission's ``metadata.yaml`` (or ``.yml``) as a dict; empty when absent."""
    for name in ("metadata.yaml", "metadata.yml"):
        meta_path = sub_dir / name
        if meta_path.is_file():
            import yaml

            try:
                metadata = yaml.safe_load(meta_path.read_text()) or {}
            except yaml.YAMLError as exc:
                raise ValueError("invalid submission metadata YAML") from exc
            if not isinstance(metadata, dict):
                raise ValueError("submission metadata must be a mapping")
            return metadata
    return {}


def s3_list(url: str) -> list[str]:
    """Names of the keys and common prefixes directly under ``url`` (unsigned); empty when the prefix does not exist."""
    result = subprocess.run(["aws", "s3", "ls", "--no-sign-request", url.rstrip("/") + "/"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return []
    return [line.split()[-1] for line in result.stdout.splitlines() if line.split()]


def s3_prefix_exists(url: str) -> bool:
    """True when an unsigned listing of ``url`` returns at least one key or common prefix."""
    return bool(s3_list(url))


def logs_layout(logs_url: str) -> dict:
    """Record what the public ``logs/`` prefix holds, so a zero-report submission gets an exact reason.

    Submissions evaluated before the mid-2024 harness keep one flat ``<instance>.<submission>.eval.log`` text
    file per task instead of ``<instance>/report.json``; those logs carry no structured per-test status.
    """
    names = s3_list(logs_url)
    return {"logs_entries": len(names), "legacy_eval_logs": sum(n.endswith(".eval.log") for n in names),
            "instance_dirs": sum(n.endswith("/") for n in names)}


def resolve_source(sub_dir: Path, split: str, exists=None) -> dict:
    """Locate a submission's per-instance logs from its ``metadata.yaml`` ``assets`` block.

    Order: ``assets.repo`` (a self-hosted GitHub repository, mid-2026 onward); the S3 URL in
    ``assets.logs``; the ``logs/`` sibling of an S3 ``assets.trajs`` URL (ten mini-SWE-agent
    entries list ``logs: null`` although their logs are public beside the trajectories); and
    finally the folder-name convention ``s3://<bucket>/<split>/<submission>/logs``. The first
    S3 candidate that lists at least one object wins, so a mistyped or relocated URL (the
    bash-only prefix, a hyphen/underscore mismatch) never silently yields zero reports.
    """
    exists = s3_prefix_exists if exists is None else exists
    assets = read_metadata(sub_dir).get("assets") or {}
    if not isinstance(assets, dict):
        raise ValueError("submission metadata assets must be a mapping")
    repo = assets.get("repo")
    if isinstance(repo, str) and "github.com" in repo:
        return {"kind": "github", "repo": repo.rstrip("/"), "rule": "assets.repo"}
    candidates: list[tuple[str, str]] = []
    logs, trajs = assets.get("logs"), assets.get("trajs")
    if isinstance(logs, str) and logs.startswith("s3://"):
        logs = logs.rstrip("/")
        if not logs.endswith("/logs"):  # one entry names the submission root instead of its logs/ prefix
            candidates.append((logs + "/logs", "assets.logs + /logs"))
        candidates.append((logs, "assets.logs"))
        parent = logs.removesuffix("/logs").rsplit("/", 1)[0]
        candidates.append((f"{parent}/{sub_dir.name}/logs", "folder name under the assets.logs parent prefix"))
    if isinstance(trajs, str) and trajs.startswith("s3://"):
        candidates.append((trajs.rstrip("/").rsplit("/", 1)[0] + "/logs", "logs sibling of assets.trajs"))
    candidates.append((f"s3://{S3_BUCKET}/{split}/{sub_dir.name}/logs", "folder name under split"))
    tried: list[str] = []
    for url, rule in candidates:
        if url not in tried:
            tried.append(url)
            if exists(url):
                return {"kind": "s3", "logs": url, "rule": rule}
    return {"kind": "none", "rule": "no S3 logs prefix found", "tried": tried}


def install_predictions(pending: Path, dest: Path) -> None:
    """Validate a downloaded ``all_preds.jsonl`` and move it into place as JSON Lines; an invalid file is discarded.

    Two submissions publish the predictions as one JSON array; they are rewritten line by line. A truncated or
    malformed file must never be read as "no generation" for its missing rows.
    """
    try:
        text = pending.read_text()
        rows = json.loads(text) if text.lstrip().startswith("[") else [json.loads(line) for line in text.splitlines() if line.strip()]
        prediction_patch_presence(rows)
    except (ValueError, UnicodeDecodeError) as exc:
        pending.unlink(missing_ok=True)
        raise ValueError(f"predictions discarded ({exc}); submission stays unmeasured where reports are missing") from exc
    pending.write_text("".join(json.dumps(r) + "\n" for r in rows))
    pending.replace(dest / "all_preds.jsonl")


def count_reports(dest: Path) -> int:
    return len(list((dest / "logs").glob("*/report.json")))


def sync_s3(logs_url: str, dest: Path) -> int:
    """Download a submission's report.json files and all_preds.jsonl with unsigned S3 access; return the report count."""
    logs_url = logs_url.rstrip("/")
    root = logs_url.rsplit("/", 1)[0]
    sync = ["aws", "s3", "sync", *UNSIGNED, logs_url + "/", str(dest / "logs"), "--exclude", "*", "--include", "*/report.json"]
    subprocess.run(sync, check=True)
    # A failed cp may leave a truncated file; never interpret its missing task rows as no generation.
    pending = dest / "all_preds.jsonl.partial"
    result = subprocess.run(["aws", "s3", "cp", *UNSIGNED, f"{root}/all_preds.jsonl", str(pending)], check=False)
    if result.returncode == 0:
        install_predictions(pending, dest)
    else:
        pending.unlink(missing_ok=True)
    return count_reports(dest)


def sync_github(repo: str, dest: Path, clone_root: Path | None = None) -> tuple[int, str]:
    """Blobless depth-1 sparse clone of a self-hosted submission repository; copy its report.json files and predictions.

    The repository layout is the one ``swebench submit package`` writes: ``all_preds.jsonl`` at the root and
    ``logs/<instance_id>/report.json`` per evaluated instance. Returns the report count and the cloned commit.
    """
    if clone_root is not None:
        clone_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=clone_root) as tmp:
        clone = Path(tmp) / "repo"
        git = ["git", "-C", str(clone)]
        subprocess.run(["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", "--depth", "1", repo, str(clone)], check=True)
        subprocess.run([*git, "sparse-checkout", "init", "--no-cone"], check=True, capture_output=True)
        subprocess.run([*git, "sparse-checkout", "set", "/all_preds.jsonl", "/logs/*/report.json"], check=True, capture_output=True)
        subprocess.run([*git, "checkout", "--quiet", "HEAD"], check=True)
        commit = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
        for report in sorted((clone / "logs").glob("*/report.json")) if (clone / "logs").is_dir() else []:
            target = dest / "logs" / report.parent.name / "report.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(report, target)
        if (clone / "all_preds.jsonl").is_file():
            pending = dest / "all_preds.jsonl.partial"
            shutil.copy(clone / "all_preds.jsonl", pending)
            install_predictions(pending, dest)
    return count_reports(dest), commit


def fetch_submission(args: argparse.Namespace, name: str) -> dict:
    """Copy a submission's committed metadata, locate its logs and download the reports; one inventory row."""
    sub_dir = args.experiments_repo / "evaluation" / args.split / name
    dest = args.out / "submissions" / name
    entry = {"submission": name, "source": "unresolved", "source_rule": "source resolution failed", "reports": 0, "error": None}
    try:
        dest.mkdir(parents=True, exist_ok=True)
        for rel in COPIED_METADATA:
            if (sub_dir / rel).is_file():
                shutil.copy(sub_dir / rel, dest / Path(rel).name)
        source = resolve_source(sub_dir, args.split)
        entry.update(source=source["kind"], source_rule=source["rule"])
        if source["kind"] == "s3":
            entry["source"] = f"s3:{source['logs']}"
            entry.update(logs_layout(source["logs"]))
            entry["reports"] = sync_s3(source["logs"], dest)
        elif source["kind"] == "github":
            entry["source"] = f"github:{source['repo']}"
            entry["reports"], entry["repo_commit"] = sync_github(source["repo"], dest, args.out / "tmp_clones")
        else:
            entry["error"] = "no public logs located; tried " + ", ".join(source["tried"])
    except (subprocess.CalledProcessError, ValueError, OSError) as exc:
        entry["reports"] = count_reports(dest)
        entry["error"] = f"{type(exc).__name__}: {exc}"
    print(json.dumps(entry), flush=True)
    return entry


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--experiments-repo", type=Path, required=True, help="clone of SWE-bench/experiments at the pinned commit")
    ap.add_argument("--split", default="verified")
    ap.add_argument("--out", type=Path, required=True, help="raw data root on the host (not committed)")
    ap.add_argument("--gold-dataset", default="princeton-nlp/SWE-bench_Verified")
    ap.add_argument("--gold-revision", required=True, help="exact Hugging Face dataset revision (commit sha)")
    ap.add_argument("--jobs", type=int, default=8, help="concurrent submission downloads")
    ap.add_argument("--only", nargs="*", default=None, help="refetch only these submissions (identical download; inventory rows of the others are kept)")
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

    inventory_path = args.out / "inventory.json"
    previous = {row["submission"]: row for row in json.loads(inventory_path.read_text())} if inventory_path.is_file() else {}
    todo = sorted(names) if args.only is None else sorted(set(args.only))
    if unknown := set(todo) - set(names):
        raise ValueError(f"--only names outside the pinned inventory: {sorted(unknown)}")
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        fetched = {row["submission"]: row for row in pool.map(partial(fetch_submission, args), todo)}
    inventory = []
    for name in sorted(names):
        if name in fetched:
            inventory.append(fetched[name])
        elif name in previous:
            inventory.append(previous[name])
        else:
            raise ValueError(f"no inventory row for {name}; run without --only first")
    pending_inventory = args.out / "inventory.json.partial"
    pending_inventory.write_text(json.dumps(inventory, indent=1) + "\n")
    pending_inventory.replace(inventory_path)


if __name__ == "__main__":
    main()
