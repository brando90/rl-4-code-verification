#!/usr/bin/env python3
"""TLDR: One-device read-only Qwen/NeMo preflight for experiment09 before any rollout or optimizer update."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = Path("/lfs/skampere1/0/brando9/rl4cv_e08/ckpt/1.7B/hf/step_658")
OUT = Path("/lfs/skampere1/0/brando9/rl4cv_e09/receipts/gpu_preflight_e09.json")


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "3":
        raise SystemExit("preflight requires the explicit GPU-3 lease visibility")
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise SystemExit("expected exactly one leased visible CUDA device")
    before = torch.cuda.mem_get_info()
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    messages = [{"role": "user", "content": "Verifier feedback: write a complete replacement Lean solution."}]
    rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    encoded = tokenizer(rendered, add_special_tokens=False, return_tensors="pt").input_ids.to("cuda")
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.bfloat16, local_files_only=True).to("cuda").eval()
    with torch.inference_mode():
        logits = model(input_ids=encoded).logits
    after = torch.cuda.mem_get_info()
    receipt = {
        "written_utc": stamp(), "model": str(MODEL), "read_only": True,
        "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"], "device_name": torch.cuda.get_device_name(0),
        "torch": torch.__version__, "transformers": __import__("transformers").__version__,
        "model_type": model.config.model_type, "max_position_embeddings": getattr(model.config, "max_position_embeddings", None),
        "tokenizer_class": type(tokenizer).__name__, "rendered_feedback_sha256": hashlib.sha256(rendered.encode()).hexdigest(),
        "feedback_token_count": int(encoded.shape[1]), "forward_logits_shape": list(logits.shape),
        "parameters": sum(p.numel() for p in model.parameters()),
        "memory_free_before_bytes": before[0], "memory_total_bytes": before[1], "memory_free_after_bytes": after[0],
        "verdict": "PASS",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: receipt[k] for k in ("verdict", "model_type", "max_position_embeddings", "feedback_token_count", "forward_logits_shape", "parameters")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
