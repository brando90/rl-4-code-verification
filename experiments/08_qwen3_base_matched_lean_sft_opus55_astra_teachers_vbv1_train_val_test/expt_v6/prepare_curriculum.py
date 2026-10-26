"""Add an executable example alias to each tiny answer, then repeat all compilation and admission checks."""
from __future__ import annotations

import concurrent.futures
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
RUN = Path(os.environ["TINY_RUN_ROOT"])
REPO = HERE.parents[2]
OLD = HERE.parent / "expt_v5"
SOURCE_SHA = "8c493b9f1e1acf43b21d244b36f44647059b9de5dc8d1cb2785b7c3ba58ac5ad"


def main():
    root = RUN / "curriculum"
    root.mkdir(parents=True, exist_ok=True)
    os.environ.update(TINY_ROOT=str(root), TINY_REPO_ROOT=str(REPO))
    sys.path.insert(0, str(REPO / "src"))
    spec = importlib.util.spec_from_file_location("tiny_checker_v5", OLD / "check_example.py")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    from transformers import AutoTokenizer
    from rl4cv.screens import screen

    original = OLD / "dataset/training.jsonl"
    assert hashlib.sha256(original.read_bytes()).hexdigest() == SOURCE_SHA
    source_rows = [json.loads(line) for line in original.read_text().splitlines()]
    tasks = [json.loads(line) for line in (OLD / "manifest.jsonl").read_text().splitlines()]
    assert len(tasks) == len(source_rows) == 500
    by_id = {r["task_id"]: r for r in source_rows}
    tok = AutoTokenizer.from_pretrained(
        "/lfs/skampere1/0/brando9/rl4cv_e08/cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
        local_files_only=True)
    pool, transformed = {}, []
    for task in tasks:
        tid = task["task_id"]
        source = (OLD / "dataset/examples" / tid / "Solution.lean").read_text()
        assert hashlib.sha256(source.encode()).hexdigest() == by_id[tid]["lean_sha256"]
        match = re.search(r"^theorem\s+(test_\w+)\s*:\s*(.*?)\s*:=", source, re.M | re.S)
        assert match and len(match.group(2)) < 500 and source.count("\nend Tiny\n") == 1
        alias = f"example : {match.group(2).strip()} := {match.group(1)}\n"
        lean = source.replace("\nend Tiny\n", "\n" + alias + "end Tiny\n")
        assert len(re.findall(r"^\s*example\b", lean, re.M)) >= 1
        folder = root / "examples" / tid
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "Solution.lean").write_text(lean)
        transformed.append((task, folder))
    def verify(pair):
        task, folder = pair
        receipt = checker.validate(task, folder, tok)
        print(json.dumps({"task_id": task["task_id"], "accepted": receipt["accepted"],
            "error": receipt.get("error")}), flush=True)
        return receipt
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        receipts = list(executor.map(verify, transformed))
    (root / "verification.json").write_text(json.dumps(receipts, indent=2) + "\n")
    assert all(r["accepted"] for r in receipts), "new-source verification failed; retain all receipts"
    admitted = []
    for task, folder in transformed:
        row = json.loads((folder / "training.json").read_text())
        row["source"] = "tiny_curriculum_v6_executable_example"
        row["derivation"] = {"source_training_sha256": SOURCE_SHA,
            "transformation": "one anonymous executable example aliases the first existing named concrete test theorem"}
        admitted.append(row)
        tid = task["task_id"]
        pool[tid + "/python"] = task["python"]
        pool[tid + "/lean"] = (folder / "Solution.lean").read_text()
        pool[tid + "/assistant"] = row["messages"][-1]["content"]
    # Protected references are used only by admission, never by the trainer or solver.
    protected = {}
    split = HERE.parent / "expt_v1/results/split/vbv1_split_manifest.csv"
    for row in csv.DictReader(split.open()):
        if row["split"] in ("validation", "test"):
            protected[row["task_id"] + "/python"] = (checker.VB / "veribench_dataset/py_src" / row["py_relpath"]).read_text()
            protected[row["task_id"] + "/lean"] = (checker.VB / "veribench_dataset/lean_src/veribench" / row["gold_relpath"]).read_text()
    assert len(protected) == 714
    report = screen(pool, protected, n=5, threshold=0.7)
    (root / "contamination.json").write_text(json.dumps(report, indent=2) + "\n")
    assert not report["exact"] and not report["near"], "new derived pool has protected overlap"
    output = root / "training.jsonl"
    output.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in admitted))
    receipt = {"status": "PASS", "source_sha256": SOURCE_SHA,
        "training_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "examples": len(admitted), "anonymous_examples": 500, "compiled": 500,
        "differential_cases": sum(len(t["tests"]) for t in tasks), "protected_reference_hits": 0,
        "max_assistant_tokens": max(r["n_assistant_tokens"] for r in admitted),
        "total_assistant_tokens": sum(r["n_assistant_tokens"] for r in admitted),
        "checker_sha256": hashlib.sha256((OLD / "check_example.py").read_bytes()).hexdigest(),
        "derivation_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (root / "admission.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
