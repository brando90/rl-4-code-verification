"""TLDR: Stage 2a helpers for the checkpoint-reuse plan (experiment 25, plan section 6): constant or cosine learning rate with the
learning-rate fraction, one per-step record of the run's own rollouts (task id, group rewards, tokens, admitted flag, advantage, lr) from which rolling
rho/H are measured on the 25 steps before a checkpoint, and a keep-all checkpoint check. Pure Python, no torch, so it is unit-tested locally."""
from __future__ import annotations

import json
import math
from pathlib import Path

CKPT_STEPS = (16, 32, 48, 64, 96, 128)  # the 02B ladder; every checkpoint is kept, none is overwritten or deleted
WINDOW_STEPS = 25  # plan section 6 (R3): 25 steps x 16 groups = 400 groups before each checkpoint


def lr_at(update: int, lr0: float, schedule: str, horizon: int) -> float:
    """Learning rate used by the (1-based) `update`-th optimizer step; t = update - 1 steps are already done."""
    if schedule == "constant":
        return lr0
    if schedule == "cosine":
        return lr0 * 0.5 * (1.0 + math.cos(math.pi * (update - 1) / horizon))
    raise ValueError(f"unknown schedule {schedule!r}")


def lr_fraction_after(done_updates: int, schedule: str, horizon: int) -> float:
    """lr(t) / lr0 with t = number of completed updates (the plan's cosine lr0 * (1 + cos(pi t / T)) / 2); 1.0 for a constant rate."""
    if schedule == "constant":
        return 1.0
    if schedule == "cosine":
        return 0.5 * (1.0 + math.cos(math.pi * done_updates / horizon))
    raise ValueError(f"unknown schedule {schedule!r}")


def _group_advantages(row: list[float], eps: float = 1e-4) -> list[float]:
    """Same formula as loss_e20.group_advantages: (r - mean) / (population std + eps)."""
    mean = sum(row) / len(row)
    std = math.sqrt(sum((x - mean) ** 2 for x in row) / len(row))
    return [(x - mean) / (std + eps) for x in row]


def build_step_record(update: int, task_ids: list[str], strict: list[list[float]], reward: list[list[float]], tokens: list[list[int]],
                      lr: float, lr_fraction: float) -> dict:
    """One JSON line per optimizer step. `strict` is the strict 0/1 matrix (groups x G), `reward` the matrix the trainer's advantage uses
    (strict in arm A, smooth in arm B), `tokens` the completion lengths. The advantage is the trainer's own group-normalized one."""
    n = len(task_ids)
    if not (len(strict) == len(reward) == len(tokens) == n):
        raise ValueError("task_ids, strict, reward and tokens must have one row per group")
    groups = []
    for i in range(n):
        if not (len(strict[i]) == len(reward[i]) == len(tokens[i])):
            raise ValueError(f"group {i}: strict, reward and tokens differ in length")
        adv = _group_advantages([float(x) for x in reward[i]])
        s = int(round(sum(strict[i])))
        groups.append({"task_id": task_ids[i], "strict": [float(x) for x in strict[i]], "rewards": [float(x) for x in reward[i]],
                       "tokens": [int(x) for x in tokens[i]], "advantages": adv, "strict_successes": s,
                       "active_strict": 1 <= s <= len(strict[i]) - 1, "admitted": any(abs(a) > 0 for a in adv)})
    return {"update": int(update), "lr": lr, "lr_fraction": lr_fraction, "n_groups": n, "n_admitted": sum(g["admitted"] for g in groups),
            "tokens": sum(sum(g["tokens"]) for g in groups), "groups": groups}


def read_steps(path: Path) -> dict[int, dict]:
    out = {}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["update"]] = r
    return out


def window_groups(path: Path, upto: int, window: int = WINDOW_STEPS) -> list[dict]:
    """The group records of steps (upto - window, upto] (fewer when upto < window), each tagged with its update; a missing step raises."""
    steps = read_steps(path)
    lo = max(1, upto - window + 1)
    groups = []
    for u in range(lo, upto + 1):
        if u not in steps:
            raise ValueError(f"missing step {u} in {path}")
        groups += [{**g, "update": u} for g in steps[u]["groups"]]
    return groups


def check_checkpoints(run_dir: Path, expected=CKPT_STEPS) -> dict:
    """present = DONE marker and a safetensors file; incomplete = directory exists without both; missing = no directory."""
    present, missing, incomplete = [], [], []
    for s in expected:
        d = Path(run_dir) / f"ckpt_u{s:03d}"
        if not d.exists():
            missing.append(s)
        elif (d / "DONE").exists() and any((d / "model").glob("*.safetensors")):
            present.append(s)
        else:
            incomplete.append(s)
    return {"present": present, "missing": missing, "incomplete": incomplete}
