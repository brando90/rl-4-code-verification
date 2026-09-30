"""Enumerate VeriBench tasks from a generated Harbor task pack (one directory per task with instruction.md)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

PY_BLOCK = re.compile(r"^```python[^\n]*\n(?P<body>.*?)^```", re.S | re.M)
AGENT_SPEC = re.compile(r"agent-spec v(?P<v>\d+)")


@dataclass(frozen=True)
class Task:
    task_id: str
    task_dir: Path
    instruction: str
    python_source: str | None
    agent_spec_version: int | None

    @property
    def instruction_sha256(self) -> str:
        return hashlib.sha256(self.instruction.encode("utf-8")).hexdigest()


def longest_python_block(instruction: str) -> str | None:
    """The Python source shown to the solver (experiment 103's judge uses the longest python block too)."""
    blocks = [m.group("body") for m in PY_BLOCK.finditer(instruction)]
    return max(blocks, key=len) if blocks else None


def load_pack(pack_dir: str | Path, task_ids: list[str] | None = None) -> list[Task]:
    """Load tasks in `task_ids` order (or sorted directory order); every task needs an instruction.md."""
    pack = Path(pack_dir)
    if not pack.is_dir():
        raise FileNotFoundError(pack)
    ids = task_ids if task_ids is not None else sorted(p.name for p in pack.iterdir() if (p / "instruction.md").is_file())
    tasks = []
    for tid in ids:
        d = pack / tid
        inst_path = d / "instruction.md"
        if not inst_path.is_file():
            raise FileNotFoundError(f"task {tid} has no instruction.md under {d}")
        text = inst_path.read_text(encoding="utf-8")
        m = AGENT_SPEC.search(text)
        tasks.append(Task(tid, d, text, longest_python_block(text), int(m.group("v")) if m else None))
    return tasks


def read_task_ids(path: str | Path) -> list[str]:
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


CORE_SPLITS = ("easy_set", "cs_set", "humaneval_set", "realcode_set", "security_set")


def split_of(task_id: str) -> str:
    """VeriBench task ids are the lowercased py_src path with '__' separators, so the split is the first part."""
    return task_id.split("__", 1)[0]


def is_core(task_id: str) -> bool:
    """Core VeriBench (614 tasks) versus VeriBench-IndustrySet (282 tasks, *_set_real / *_set_synthetic)."""
    return split_of(task_id) in CORE_SPLITS


def stratified_subset(task_ids: list[str], per_split: int, *, salt: str = "rl4cv-probe-v1", splits: tuple[str, ...] | None = None) -> list[str]:
    """Deterministic, outcome-blind subset: the first `per_split` ids of each split in sha256(salt:id) order."""
    by_split: dict[str, list[str]] = {}
    for tid in task_ids:
        s = split_of(tid)
        if splits is None or s in splits:
            by_split.setdefault(s, []).append(tid)
    out = []
    for s in sorted(by_split):
        ranked = sorted(by_split[s], key=lambda t: hashlib.sha256(f"{salt}:{t}".encode()).hexdigest())
        out.extend(ranked[:per_split])
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI: write an outcome-blind stratified probe subset of a task-id list."""
    import argparse

    ap = argparse.ArgumentParser(description="Write a deterministic stratified subset of VeriBench task ids")
    ap.add_argument("--task-ids", required=True, type=Path)
    ap.add_argument("--per-split", required=True, type=int)
    ap.add_argument("--salt", default="rl4cv-probe-v1")
    ap.add_argument("--core-only", action="store_true")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    ids = read_task_ids(args.task_ids)
    sub = stratified_subset(ids, args.per_split, salt=args.salt, splits=CORE_SPLITS if args.core_only else None)
    args.out.write_text("".join(t + "\n" for t in sub), encoding="utf-8")
    print(f"{len(sub)} of {len(ids)} task ids -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
