"""Tests for the VeriBench adapters: experiment 103 prompt/extraction reuse, job layout, collection, probe tables."""

import csv
import json
import os
from pathlib import Path

import pytest

from rl4cv.probe import measure_channel
from rl4cv.veribench.collect import collect
from rl4cv.veribench.jobs import materialize_jobs
from rl4cv.veribench.pack import load_pack, longest_python_block
from rl4cv.veribench.summarize import summarize

INSTRUCTION = """# Task (VeriBench agent-spec v6)

Translate this Python program.

```python
def my_add(a, b):
    return a + b
```

Write your answer to `/home/user/lean_project/Veribench/1_MyAdd.lean`.
"""


def _root():
    for cand in (os.environ.get("VERIBENCH_ROOT"), "/home/user/veribench", str(Path(__file__).resolve().parents[1] / "external" / "veribench")):
        if cand and (Path(cand) / "experiments").is_dir():
            try:
                from rl4cv.veribench.exp103 import veribench_root

                return str(veribench_root(cand))
            except FileNotFoundError:
                continue
    return None


needs_vb = pytest.mark.skipif(_root() is None, reason="no VeriBench checkout with experiment 103")


@needs_vb
def test_prompt_matches_experiment_103_hashes():
    from rl4cv.veribench.exp103 import build_prompt

    p = build_prompt(INSTRUCTION, root=_root())
    assert p.required_paths == ("/home/user/lean_project/Veribench/1_MyAdd.lean",)
    # Experiment 103 PROTOCOL.md records these two hashes for the delivered addendum and system prompt.
    assert p.addendum_sha256 == "a7a0fc1b7be6b4ede41fd6b31e1e1dcae3d2fd320a6cddf9b311cf55855a18f5"
    assert p.system_prompt_sha256 == "dc051963de1199dd4f77c9f8f96218eb45be331c819b8e76693b063b206143cd"
    assert p.user.startswith(INSTRUCTION.rstrip() + "\n\n---\n\n")


@needs_vb
def test_extraction_uses_file_marker_then_longest_block():
    from rl4cv.veribench.exp103 import extract_lean

    path = ("/home/user/lean_project/Veribench/1_MyAdd.lean",)
    marked = "Plan...\nFILE: /home/user/lean_project/Veribench/1_MyAdd.lean\n```lean\ndef myAdd (a b : Nat) := a + b\n```\n"
    assert extract_lean(marked, path, root=_root()).lean.strip() == "def myAdd (a b : Nat) := a + b"
    two = "```lean\nx\n```\ntext\n```lean\nlonger body\n```\n"
    e = extract_lean(two, path, root=_root())
    assert e.lean.strip() == "longer body" and e.method == "longest_bare_block"
    assert extract_lean("no code here", path, root=_root()).lean is None


def test_pack_loader(tmp_path):
    d = tmp_path / "pack" / "easy_set__my_add"
    d.mkdir(parents=True)
    (d / "instruction.md").write_text(INSTRUCTION)
    tasks = load_pack(tmp_path / "pack")
    assert tasks[0].task_id == "easy_set__my_add" and tasks[0].agent_spec_version == 6
    assert "def my_add" in longest_python_block(INSTRUCTION)


def _gen_rows():
    rows = []
    for k in range(2):
        for tid, lean in (("t1", "theorem a : 1 = 1 := rfl"), ("t2", None)):
            rows.append({
                "task_id": tid, "sample_idx": k, "label": "m", "model": "m", "revision": "r",
                "generated_tokens": 100 + k, "admitted": True, "truncated": False, "measured": True,
                "extraction": "single_bare_block" if lean else "no_lean_block", "lean": lean,
            })
    return rows


def test_materialize_collect_probe_summarize(tmp_path):
    rows = _gen_rows()
    jobs = materialize_jobs(rows, tmp_path / "jobs", "m")
    assert sorted(jobs) == [0, 1]
    cfg = json.loads((jobs[0] / "t1" / "config.json").read_text())
    assert cfg["task"]["path"] == "tasks/t1"
    assert (jobs[0] / "t2" / "verifier" / "solution.lean").read_text() == ""
    with pytest.raises(FileExistsError):
        materialize_jobs(rows, tmp_path / "jobs", "m")
    gen = tmp_path / "gen.jsonl"
    gen.write_text("".join(json.dumps(r) + "\n" for r in rows))
    for k in range(2):
        out = tmp_path / "scores" / f"m_s{k}"
        out.mkdir(parents=True)
        with (out / f"m_s{k}_per_task.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["task", "split", "IC_tests", "IC_proofs", "agent_compiles", "agent_n_ex", "agent_n_thm", "kernel_n_theorems", "kernel_n_honest"])
            w.writeheader()
            # t1 compiles in sample 0 only; t2 never compiles.
            w.writerow({"task": "t1", "split": "easy", "IC_tests": 1.0 if k == 0 else 0.0, "IC_proofs": 1.0 if k == 0 else 0.0,
                        "agent_compiles": k == 0, "agent_n_ex": 1, "agent_n_thm": 1, "kernel_n_theorems": 1, "kernel_n_honest": 1 if k == 0 else 0})
            w.writerow({"task": "t2", "split": "easy", "IC_tests": 0.0, "IC_proofs": 0.0, "agent_compiles": False,
                        "agent_n_ex": 0, "agent_n_thm": 0, "kernel_n_theorems": 0, "kernel_n_honest": 0})
    scored = collect(gen, tmp_path / "scores", "m")
    assert len(scored) == 4 and all(r["status"] == "scored" for r in scored)
    t1s0 = next(r for r in scored if r["task_id"] == "t1" and r["sample_idx"] == 0)
    assert t1s0["rewards"]["kernel_binary"] == 1.0
    assert t1s0["rewards"]["scsc"] is None  # IC > 0 but no judge score: unmeasured, not zero
    table = measure_channel(scored, "kernel_binary")
    assert table["all"]["n_groups"] == 2 and table["all"]["q_mixed_empirical"] == pytest.approx(0.5)
    assert measure_channel(scored, "scsc")["all"]["n_groups_excluded_unmeasured"] == 1
    summ = summarize(scored)["m"]
    assert summ["cells_declared"] == 4 and summ["probe_k"] == 2
    assert summ["probe"]["kernel_binary"]["pass_at_k_any_positive"] == pytest.approx(0.5)


def test_split_helpers_and_stratified_subset():
    from rl4cv.veribench.pack import is_core, split_of, stratified_subset

    ids = [f"easy_set__{i}_x" for i in range(10)] + [f"aerospace_set_real__t{i}" for i in range(10)]
    assert split_of(ids[0]) == "easy_set" and is_core(ids[0]) and not is_core(ids[-1])
    sub = stratified_subset(ids, 3)
    assert len(sub) == 6 and sub == stratified_subset(list(reversed(ids)), 3)
    assert len(stratified_subset(ids, 3, splits=("easy_set",))) == 3
