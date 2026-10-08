#!/usr/bin/env python3
"""TLDR: Turn one experiment 08 SFT run's TensorBoard event files into the committed per-step CSV (step, loss, learning rate, loss tokens this step, cumulative assistant tokens) and a summary JSON, and compare the cumulative loss-token log with the precomputed schedule (`results/sft_schedule.json`); a mismatch across sizes blocks selection (PROTOCOL § 8). Runs with the NeMo RL interpreter; zero model calls."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
TAGS = {"loss": ("train/loss",), "lr": ("train/lr",), "valid_toks": ("train/global_valid_toks",), "grad_norm": ("train/grad_norm",), "tokens_per_sec": ("train/tokens_per_sec_per_gpu",)}


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_scalars(tb_dir: Path) -> dict[str, dict[int, float]]:
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

    out: dict[str, dict[int, float]] = {}
    for ev in sorted(tb_dir.rglob("events.out.tfevents.*")):
        acc = EventAccumulator(str(ev), size_guidance={"scalars": 0})
        acc.Reload()
        for tag in acc.Tags().get("scalars", []):
            d = out.setdefault(tag, {})
            for s in acc.Scalars(tag):
                d[int(s.step)] = float(s.value)   # a later segment's value for the same step wins (resume re-logs nothing before its first step)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tb-dir", type=Path, required=True)
    ap.add_argument("--size", required=True)
    ap.add_argument("--schedule", type=Path, default=EXP / "results" / "sft_schedule.json")
    ap.add_argument("--out-csv", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    a = ap.parse_args(argv)
    scalars = load_scalars(a.tb_dir)
    tags_present = sorted(scalars)
    def pick(name):
        for t in TAGS[name]:
            if t in scalars:
                return scalars[t]
        return {}
    loss, lr, toks, gn = pick("loss"), pick("lr"), pick("valid_toks"), pick("grad_norm")
    steps = sorted(set(loss) | set(toks))
    cum, rows = 0, []
    for s in steps:
        cum += int(round(toks.get(s, 0)))
        rows.append({"step": s, "loss": loss.get(s), "lr": lr.get(s), "loss_tokens_step": int(round(toks.get(s, 0))) if s in toks else None, "cumulative_assistant_tokens": cum,
                     "grad_norm": gn.get(s)})
    a.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with a.out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["step", "loss", "lr", "loss_tokens_step", "cumulative_assistant_tokens", "grad_norm"])
        w.writeheader()
        w.writerows(rows)
    sched = json.loads(a.schedule.read_text()) if a.schedule.exists() else None
    cmp = None
    if sched:
        expected = sched["cumulative_assistant_tokens_per_step"]
        got = [r["cumulative_assistant_tokens"] for r in rows]
        n = min(len(expected), len(got))
        mism = [i + 1 for i in range(n) if expected[i] != got[i]]
        cmp = {"n_steps_logged": len(got), "n_steps_scheduled": len(expected), "n_compared": n, "first_mismatch_step": mism[0] if mism else None, "n_mismatch": len(mism),
               "matches_schedule": not mism and len(got) >= len(expected), "checkpoint_steps": {f: v["step"] for f, v in sched["checkpoints"].items()},
               "cumulative_at_checkpoints_logged": {f: (got[v["step"] - 1] if v["step"] - 1 < len(got) else None) for f, v in sched["checkpoints"].items()}}
    out = {"written_utc": stamp(), "size": a.size, "tb_dir": str(a.tb_dir), "tags_present": tags_present, "n_steps": len(rows), "first_loss": rows[0]["loss"] if rows else None,
           "last_loss": rows[-1]["loss"] if rows else None, "mean_loss_first_10": (sum(r["loss"] for r in rows[:10] if r["loss"] is not None) / max(1, len([r for r in rows[:10] if r["loss"] is not None]))) if rows else None,
           "mean_loss_last_10": (sum(r["loss"] for r in rows[-10:] if r["loss"] is not None) / max(1, len([r for r in rows[-10:] if r["loss"] is not None]))) if rows else None,
           "total_loss_tokens": rows[-1]["cumulative_assistant_tokens"] if rows else 0, "schedule_comparison": cmp, "csv": str(a.out_csv), "csv_sha256": hashlib.sha256(a.out_csv.read_bytes()).hexdigest()}
    a.out_json.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: out[k] for k in ("size", "n_steps", "first_loss", "last_loss", "total_loss_tokens")} | {"schedule": (cmp or {}).get("matches_schedule")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
