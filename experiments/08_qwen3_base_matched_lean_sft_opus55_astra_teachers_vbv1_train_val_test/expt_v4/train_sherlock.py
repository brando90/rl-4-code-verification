"""Run two separately labelled Sherlock training replications with hash-verified train-only tokens."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import random
import socket
import time

ROOT = Path(__file__).resolve().parent
MODEL = "Qwen/Qwen3-1.7B-Base"
REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
DATA_SHA = "885d4ae2d6cf193bddc43df6ad6274cacfa8c98a5e5ecd63bd2519472f5e7354"
SEEDS = (20260830, 20260831)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def ids_digest(ids):
    return hashlib.sha256(json.dumps(ids).encode()).hexdigest()


def write_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def prepare():
    import torch
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer

    data = ROOT / "data/s_v1.jsonl"
    assert digest(data) == DATA_SHA, "training corpus hash mismatch"
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    manifest = [json.loads(line) for line in (ROOT / "token_manifest.jsonl").read_text().splitlines()]
    assert len(rows) == len(manifest) == 1315
    model_path = snapshot_download(MODEL, revision=REVISION,
        allow_patterns=["*.json", "*.safetensors", "merges.txt", "*.model"])
    tok = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    prepared = []
    for index, (row, expected) in enumerate(zip(rows, manifest, strict=True)):
        assert row["index"] == expected["index"] == index
        assert row["task_id"] == expected["task_id"] and expected["ok"]
        roles = {m["role"]: m["content"] for m in row["messages"]}
        prefix = tok.apply_chat_template([
            {"role": "system", "content": roles["system"]},
            {"role": "user", "content": roles["user"]}],
            tokenize=False, add_generation_prompt=True, enable_thinking=True)
        pids = tok.encode(prefix, add_special_tokens=False)
        aids = tok.encode("<think>\n\n</think>\n\n" + roles["assistant"] +
                          "<|im_end|>\n" + tok.eos_token, add_special_tokens=False)
        assert ids_digest(pids) == expected["prompt_ids_sha256"], index
        assert ids_digest(aids) == expected["assistant_ids_sha256"], index
        assert len(aids) == expected["n_assistant_tokens_loss"] > 0
        assert len(pids) + len(aids) == expected["n_total_tokens"] <= 16384
        prepared.append({"index": index, "ids": pids + aids, "prompt": len(pids), "loss_tokens": len(aids)})
    assert sum(r["loss_tokens"] for r in prepared) == 5752936
    torch.save(prepared, ROOT / "data/tokens.pt")
    receipt = {"status": "PASS", "examples": len(prepared), "loss_tokens": 5752936,
        "model": MODEL, "revision": REVISION, "model_path": model_path,
        "data_sha256": DATA_SHA, "token_manifest_sha256": digest(ROOT / "token_manifest.jsonl"),
        "tokens_sha256": digest(ROOT / "data/tokens.pt"), "code_sha256": digest(__file__),
        "maximum_sequence_tokens": max(len(r["ids"]) for r in prepared)}
    write_json(ROOT / "prepare_receipt.json", receipt)
    print(json.dumps(receipt), flush=True)


def train(seed):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    assert seed in SEEDS and os.environ.get("SLURM_JOB_ID"), "use the declared scheduler job"
    assert os.environ.get("CUDA_VISIBLE_DEVICES") and torch.cuda.device_count() == 1
    receipt = json.loads((ROOT / "prepare_receipt.json").read_text())
    assert receipt["status"] == "PASS" and receipt["data_sha256"] == DATA_SHA
    assert receipt["code_sha256"] == digest(__file__), "source changed after admission"
    assert receipt["tokens_sha256"] == digest(ROOT / "data/tokens.pt")
    assert torch.cuda.is_bf16_supported()
    rows = torch.load(ROOT / "data/tokens.pt", weights_only=True)
    order = list(range(len(rows)))
    random.Random(seed).shuffle(order)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.set_num_threads(int(os.environ.get("SLURM_CPUS_PER_TASK", "4")))
    torch.backends.cuda.matmul.allow_tf32 = False
    model = AutoModelForCausalLM.from_pretrained(receipt["model_path"], local_files_only=True,
        torch_dtype=torch.float32, attn_implementation="sdpa").cuda()
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, betas=(0.9, 0.98),
        eps=1e-5, weight_decay=0.1, foreach=False, fused=False)
    scheduler = torch.optim.lr_scheduler.SequentialLR(optimizer, [
        torch.optim.lr_scheduler.LinearLR(optimizer, start_factor=0.05, total_iters=20),
        torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=638, eta_min=0.0)], milestones=[20])
    out = ROOT / "runs" / str(seed)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "result.json").exists() or (out / "steps.csv").exists():
        raise RuntimeError("existing trajectory: preserve evidence; do not silently restart")
    identity = {"seed": seed, "model": MODEL, "revision": REVISION, "host": socket.gethostname(),
        "job_id": os.environ["SLURM_JOB_ID"], "torch": torch.__version__, "transformers": transformers.__version__,
        "gpu": torch.cuda.get_device_name(), "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"],
        "data_sha256": DATA_SHA, "order_sha256": ids_digest(order), "code_sha256": digest(__file__),
        "declared_examples": 1315, "declared_steps": 658, "declared_loss_tokens": 5752936,
        "parameter_dtype": "float32", "autocast_dtype": "bfloat16", "backend": "transformers-sdpa"}
    write_json(out / "identity.json", identity)
    started = time.monotonic()
    consumed = 0
    fields = ["step", "examples", "loss_tokens", "train_loss", "grad_norm", "learning_rate", "elapsed_seconds", "peak_gpu_gib"]
    with (out / "steps.csv").open("x", buffering=1) as log:
        writer = csv.DictWriter(log, fieldnames=fields)
        writer.writeheader()
        for offset in range(0, len(order), 2):
            batch = [rows[i] for i in order[offset:offset + 2]]
            denominator = sum(row["loss_tokens"] for row in batch)
            optimizer.zero_grad(set_to_none=True)
            total_loss = 0.0
            for row in batch:
                ids = torch.tensor([row["ids"]], dtype=torch.long, device="cuda")
                labels = ids.clone()
                labels[:, :row["prompt"]] = -100
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    loss = model(input_ids=ids, labels=labels).loss
                assert bool(torch.isfinite(loss)), "nonfinite loss"
                weight = row["loss_tokens"] / denominator
                (loss * weight).backward()
                total_loss += float(loss.detach()) * weight
                del loss, ids, labels
            grad = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
            assert float(grad) > 0, "zero gradient"
            learning_rate = optimizer.param_groups[0]["lr"]
            optimizer.step()
            scheduler.step()
            consumed += denominator
            step = offset // 2 + 1
            metrics = dict(zip(fields, [step, min(offset + 2, len(order)), consumed, total_loss, float(grad),
                learning_rate, time.monotonic() - started, torch.cuda.max_memory_allocated() / 2**30], strict=True))
            writer.writerow(metrics)
            write_json(out / "progress.json", {**identity, **metrics, "status": "RUNNING"})
            print(json.dumps(metrics), flush=True)
            if step % 100 == 0 or step == 658:
                tmp = out / "training_state.tmp.pt"
                torch.save({"step": step, "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                    "scheduler": scheduler.state_dict(), "identity": identity, "order": order,
                    "cpu_rng": torch.get_rng_state(), "cuda_rng": torch.cuda.get_rng_state_all()}, tmp)
                tmp.replace(out / "training_state.pt")
    assert consumed == 5752936 and step == 658
    model.save_pretrained(out / "hf")
    AutoTokenizer.from_pretrained(receipt["model_path"], local_files_only=True).save_pretrained(out / "hf")
    files = {p.name: digest(p) for p in sorted((out / "hf").iterdir()) if p.is_file()}
    write_json(out / "weights_manifest.json", files)
    write_json(out / "result.json", {**identity, **metrics, "status": "COMPLETE", "export_files": len(files),
        "validation": "not measured", "test": "unopened", "provider_spend_usd": 0})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "train"])
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        train(args.seed)
