#!/usr/bin/env python3
"""TLDR: Derive experiment 08's NeMo RL SFT configs `configs/e08_sft_<size>.yaml` from Varun's committed production config byte-for-byte copy (`configs/varun_phase1c_production_sft.yaml`), changing only what PROTOCOL § 8 allows (run-specific inputs and output dirs, the step / warmup / cosine schedule and checkpoint handling from `results/sft_schedule.json`, SFT-time validation and Weights & Biases off, the declared rendering/mask flags, and the per-size GPU layout), and write a complete diff report of every changed key with its reason (`results/sft_config_diff.{json,md}`; zero model calls)."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
CONFIGS = EXP / "configs"
VARUN_YAML = CONFIGS / "varun_phase1c_production_sft.yaml"
VARUN_SHA256 = "8e45b9f5605dbd5eeaf448bc1e0088760d572b0eecebeb9908d1eaacbdf9a290"
SIZES = ("1.7B", "4B", "8B", "14B")
# GPU layout per size (PROTOCOL § 8: the only thing that may differ by size). Tensor parallel keeps data parallel = 1 everywhere, so the
# global batch of 2 sequences is consumed identically (2 micro-batches of 1) at every size.
GPU_LAYOUT = {"1.7B": {"gpus": 1, "tp": 1}, "4B": {"gpus": 2, "tp": 2}, "8B": {"gpus": 4, "tp": 4}, "14B": {"gpus": 8, "tp": 8}}
SAVE_PERIOD_NEVER = 1_000_000   # checkpoints come from segment ends (is_last_step), see results/sft_schedule.json and launch_sft_e08.sh


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def flatten(d, prefix=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flatten(v, f"{prefix}{k}."))
    else:
        out[prefix[:-1]] = d
    return out


def build(size: str, varun: dict, sched: dict) -> tuple[dict, list[dict]]:
    import copy

    cfg = copy.deepcopy(varun)
    changes = []

    def setk(path: str, value, reason: str):
        node = cfg
        parts = path.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        old = node.get(parts[-1], "<absent>")
        node[parts[-1]] = value
        if old != value:
            changes.append({"key": path, "varun": old, "e08": value, "reason": reason})

    def delk(path: str, reason: str):
        node = cfg
        parts = path.split(".")
        for p in parts[:-1]:
            node = node.get(p, {})
        if parts[-1] in node:
            changes.append({"key": path, "varun": node[parts[-1]], "e08": "<removed>", "reason": reason})
            del node[parts[-1]]

    steps, W = sched["steps"], sched["warmup_steps_W"]
    # sft
    setk("sft.max_num_steps", steps, "step schedule: ⌈|S| / 2⌉ steps over S in the frozen order (PROTOCOL § 8); per-segment overrides stop at each checkpoint step")
    setk("sft.val_period", 0, "SFT-time validation off (PROTOCOL § 8); the § 9 ladder selects checkpoints")
    setk("sft.val_batches", 0, "SFT-time validation off")
    setk("sft.val_at_start", False, "SFT-time validation off")
    # checkpointing
    setk("checkpointing.checkpoint_dir", "${oc.env:E08_CHECKPOINT_DIR}", "run-specific output directory")
    setk("checkpointing.metric_name", None, "no validation metric; checkpoints are kept by step, never by score")
    setk("checkpointing.keep_top_k", None, "keep every token-fraction checkpoint")
    setk("checkpointing.save_period", SAVE_PERIOD_NEVER, "checkpoints at the precomputed token-fraction steps: each training segment ends (is_last_step) at one of them and the next segment resumes from it")
    # policy
    setk("policy.model_name", "${oc.env:E08_MODEL_PATH}", "run-specific input: the pinned Base snapshot for this size")
    setk("policy.dtensor_cfg.tensor_parallel_size", GPU_LAYOUT[size]["tp"], f"GPU layout for {size}: {GPU_LAYOUT[size]['gpus']} GPU(s), tensor parallel {GPU_LAYOUT[size]['tp']}, data parallel 1")
    setk("policy.make_sequence_length_divisible_by", GPU_LAYOUT[size]["tp"], "GPU layout: sequence length divisible by the tensor-parallel size (padding only, no loss)")
    setk("policy.scheduler", [{"name": "torch.optim.lr_scheduler.LinearLR", "kwargs": {"start_factor": 1.0 / W, "end_factor": 1.0, "total_iters": W}},
                              {"name": "torch.optim.lr_scheduler.CosineAnnealingLR", "kwargs": {"T_max": steps - W, "eta_min": 0.0}},
                              {"milestones": [W]}], f"Varun's schedule form with W = ⌈0.03 × {steps}⌉ = {W} warmup updates then cosine over {steps - W}")
    # data
    setk("data.dataset_name", "openai_format", "dataset adapter: system + user + assistant messages (Varun's ResponseDataset has no system message)")
    setk("data.train_data_path", "${oc.env:E08_TRAIN_JSONL}", "run-specific input: S in NeMo RL openai_format (host only)")
    setk("data.val_data_path", "${oc.env:E08_VAL_JSONL}", "loader requirement only: a 2-example file never evaluated (val_period 0, val_at_start false)")
    setk("data.chat_key", "messages", "openai_format adapter key")
    setk("data.system_key", None, "openai_format adapter: the system message is inside messages")
    setk("data.system_prompt", None, "openai_format adapter")
    setk("data.tool_key", None, "openai_format adapter: no tools")
    setk("data.use_preserving_dataset", False, "openai_format adapter")
    setk("data.add_generation_prompt", True, "rendering/mask (declared difference): the generation prompt `<|im_start|>assistant\\n` belongs to the prompt (no loss), so the loss span is exactly what the policy generates at evaluation (PROTOCOL § 7)")
    delk("data.input_key", "ResponseDataset-only key")
    delk("data.output_key", "ResponseDataset-only key")
    # logger
    setk("logger.log_dir", "${oc.env:E08_LOG_DIR}", "run-specific output directory")
    setk("logger.wandb_enabled", False, "Weights & Biases off (PROTOCOL § 8)")
    setk("logger.tensorboard.log_dir", "${oc.env:E08_TENSORBOARD_DIR}", "run-specific output directory")
    setk("logger.wandb", {"project": "rl4cv-e08-sft", "name": "${oc.env:E08_RUN_NAME}"}, "run name (W&B disabled)")
    setk("logger.mlflow", {"experiment_name": "rl4cv-e08-sft", "run_name": "${oc.env:E08_RUN_NAME}"}, "run name (MLflow disabled)")
    # cluster
    setk("cluster.gpus_per_node", GPU_LAYOUT[size]["gpus"], f"GPU layout for {size}")
    return cfg, changes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--schedule", type=Path, default=EXP / "results" / "sft_schedule.json")
    ap.add_argument("--out-dir", type=Path, default=CONFIGS)
    ap.add_argument("--report", type=Path, default=EXP / "results" / "sft_config_diff.json")
    a = ap.parse_args(argv)
    import yaml

    raw = VARUN_YAML.read_bytes()
    if sha(raw) != VARUN_SHA256:
        raise RuntimeError("Varun's config copy does not match its recorded SHA-256")
    varun = yaml.safe_load(raw)
    sched = json.loads(a.schedule.read_text())
    report = {"written_utc": stamp(), "source": {"path": str(VARUN_YAML.relative_to(EXP)), "sha256": VARUN_SHA256}, "schedule_sha256": sha(a.schedule.read_bytes()),
              "steps": sched["steps"], "warmup_steps_W": sched["warmup_steps_W"], "checkpoints": sched["checkpoints"], "sizes": {}}
    md = ["| Key | Varun | Experiment 08 | Reason |", "|---|---|---|---|"]
    for size in SIZES:
        cfg, changes = build(size, varun, sched)
        out = a.out_dir / f"e08_sft_{size}.yaml"
        header = (f"# TLDR: experiment 08 matched SFT config for Qwen3-{size}-Base, derived from Varun's phase-1c production config (SHA-256 {VARUN_SHA256[:16]}…) by "
                  f"scripts/make_sft_configs_e08.py; every difference is listed in results/sft_config_diff.md.\n")
        out.write_text(header + yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        unchanged = {k: v for k, v in flatten(varun).items() if flatten(cfg).get(k, "<absent>") == v}
        report["sizes"][size] = {"config": str(out.relative_to(EXP)), "sha256": sha(out.read_bytes()), "n_changes": len(changes), "changes": changes, "n_unchanged_keys": len(unchanged),
                                 "gpu_layout": GPU_LAYOUT[size]}
        if size == SIZES[0]:
            for c in changes:
                md.append(f"| `{c['key']}` | `{c['varun']}` | `{c['e08']}` | {c['reason']} |")
    md.append("")
    md.append("Per-size differences are only `policy.dtensor_cfg.tensor_parallel_size`, `policy.make_sequence_length_divisible_by` and `cluster.gpus_per_node` (GPU layout): " +
              "; ".join(f"{s}: {GPU_LAYOUT[s]['gpus']} GPU(s), TP {GPU_LAYOUT[s]['tp']}" for s in SIZES) + ".")
    unchanged_keys = sorted(k for k in flatten(varun) if all(flatten(yaml.safe_load((a.out_dir / f'e08_sft_{s}.yaml').read_text())).get(k, "<absent>") == flatten(varun)[k] for s in SIZES))
    report["unchanged_keys_all_sizes"] = unchanged_keys
    md.append(f"\nUnchanged in every size ({len(unchanged_keys)} keys): optimizer (AdamW lr 2e-5, betas 0.9/0.98, eps 1e-5, weight decay 0.1), max_grad_norm 1.0, global batch 2, micro-batch 1, "
              "max sequence length 16,384, bf16, no sequence packing, no dynamic batching, activation checkpointing, seed 20260830, one epoch, shuffle off, add_bos / add_eos on.")
    a.report.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    a.report.with_suffix(".md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({s: {"n_changes": v["n_changes"], "sha256": v["sha256"][:16]} for s, v in report["sizes"].items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
