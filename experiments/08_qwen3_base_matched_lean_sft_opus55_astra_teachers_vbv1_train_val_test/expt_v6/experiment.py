"""Prepare and run a matched 1.7B continuation with and without the 500-example curriculum."""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import socket
import time

ROOT = Path(os.environ.get("TINY_TRAIN_ROOT", Path(__file__).resolve().parent))
SOURCE = Path("/lfs/skampere1/0/brando9/rl4cv_e08")
TINY = Path("/lfs/skampere1/0/eth127/rl4cv_tiny_curriculum/final/training.jsonl")
START = SOURCE / "sft_v3/ckpt/v3_E_1p7b/hf/step_667"
CORPUS_SHA = "7fa0255741a2b6046ceda0dfda43664334ca603a0aeca9fc2424af43c849726b"
TINY_SHA = "8c493b9f1e1acf43b21d244b36f44647059b9de5dc8d1cb2785b7c3ba58ac5ad"
TARGET = 5752936
SEED = 20261019
REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
FOUR_REVISION = "906bfd4b4dc7f14ee4320094d8b41684abff8539"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def schedule(tokens, condition):
    """Use identical old-data order; insert each tiny pair after two old-data pairs."""
    old = [i for i, r in enumerate(tokens) if not r["tiny"]]
    tiny = [i for i, r in enumerate(tokens) if r["tiny"]]
    random.Random(SEED).shuffle(old)
    random.Random(SEED + 1).shuffle(tiny)
    total, cursor, since_tiny, tiny_cursor = 0, 0, 0, 0
    batches = []
    while total < TARGET:
        take_tiny = condition == "mixed" and tiny_cursor < len(tiny) and since_tiny == 2
        if take_tiny:
            batch = tiny[tiny_cursor:tiny_cursor + 2]
            tiny_cursor += len(batch)
            since_tiny = 0
        else:
            batch = [old[(cursor + j) % len(old)] for j in range(2)]
            cursor += 2
            since_tiny += 1
        total += sum(tokens[i]["loss_tokens"] for i in batch)
        batches.append({"indices": batch, "tiny": take_tiny, "cumulative_loss_tokens": total})
    if condition == "mixed":
        assert tiny_cursor == len(tiny) == 500, "budget failed to expose every tiny example"
    return batches


def prepare(size):
    import torch
    from transformers import AutoTokenizer

    data = ROOT / "data"
    data.mkdir(parents=True, exist_ok=True)
    existing = SOURCE / "sft_v3/s_v3_candidates.jsonl"
    curriculum = ROOT.parent / "curriculum"
    admission = json.loads((curriculum / "admission.json").read_text())
    tiny_source = curriculum / "training.jsonl"
    assert admission["status"] == "PASS" and admission["compiled"] == admission["examples"] == 500
    assert digest(existing) == CORPUS_SHA and digest(TINY) == TINY_SHA
    assert admission["source_sha256"] == TINY_SHA and digest(tiny_source) == admission["training_sha256"]
    for source, name in ((existing, "existing.jsonl"), (tiny_source, "tiny.jsonl")):
        shutil.copy2(source, data / name)
        assert digest(source) == digest(data / name)
    checkpoint = ROOT / "initial"
    checkpoint.mkdir(exist_ok=True)
    start = START if size == "1.7B" else SOURCE / "sft_v3/ckpt/v3_E_4b/hf/step_667"
    expected = {}
    for line in (start / "SHA256SUMS").read_text().splitlines():
        h, name = line.split(maxsplit=1)
        name = name.lstrip("*")
        assert Path(name).name == name
        assert digest(start / name) == h, name
        shutil.copy2(start / name, checkpoint / name)
        assert digest(checkpoint / name) == h, name
        expected[name] = h
    write(data / "initial_manifest.json", expected)
    tok = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)
    base_tok = AutoTokenizer.from_pretrained(
        SOURCE / f"cache/huggingface/hub/models--Qwen--Qwen3-{size}-Base/snapshots" / (REVISION if size == "1.7B" else FOUR_REVISION),
        local_files_only=True)
    encoded, manifest = [], []
    for is_tiny, path in ((False, data / "existing.jsonl"), (True, data / "tiny.jsonl")):
        source_rows = rows(path)
        assert len(source_rows) == (500 if is_tiny else 2585)
        for row in source_rows:
            messages = row["messages"]
            assert [m["role"] for m in messages] == ["system", "user", "assistant"]
            prefix = tok.apply_chat_template(messages[:2], tokenize=False,
                add_generation_prompt=True, enable_thinking=True)
            assert prefix == base_tok.apply_chat_template(messages[:2], tokenize=False,
                add_generation_prompt=True, enable_thinking=True)
            pids = tok.encode(prefix, add_special_tokens=False)
            response = "<think>\n\n</think>\n\n" + messages[2]["content"] + "<|im_end|>\n"
            rendered_aids = tok.encode(response, add_special_tokens=False)
            aids = tok.encode(response + tok.eos_token, add_special_tokens=False)
            assert rendered_aids == base_tok.encode(response, add_special_tokens=False)
            assert len(rendered_aids) == row["n_assistant_tokens"], row["task_id"]
            assert len(pids) + len(aids) <= 16384
            assert len(aids) == len(rendered_aids) + 1
            if is_tiny:
                assert len(aids) < 1000
            index = len(encoded)
            encoded.append({"index": index, "task_id": row["task_id"], "tiny": is_tiny,
                "source": row["source"], "ids": pids + aids, "prompt": len(pids),
                "loss_tokens": len(aids)})
            manifest.append({k: v for k, v in encoded[-1].items() if k != "ids"})
            manifest[-1]["ids_sha256"] = hashlib.sha256(json.dumps(pids + aids).encode()).hexdigest()
    torch.save(encoded, data / "tokens.pt")
    write(data / "token_manifest.json", manifest)
    schedules = {}
    for condition in (("control", "mixed") if size == "1.7B" else ("mixed",)):
        batches = schedule(encoded, condition)
        write(data / f"schedule_{condition}.json", batches)
        consumed = [encoded[i] for b in batches for i in b["indices"]]
        schedules[condition] = {"steps": len(batches), "loss_tokens": batches[-1]["cumulative_loss_tokens"],
            "overshoot": batches[-1]["cumulative_loss_tokens"] - TARGET,
            "examples": len(consumed), "unique_tiny": len({r["task_id"] for r in consumed if r["tiny"]}),
            "by_source": dict(collections.Counter(r["source"] for r in consumed)),
            "tiny_loss_tokens": sum(r["loss_tokens"] for r in consumed if r["tiny"]),
            "schedule_sha256": digest(data / f"schedule_{condition}.json")}
    receipt = {"status": "PASS", "size": size, "seed": SEED, "target_loss_tokens": TARGET,
        "existing_sha256": CORPUS_SHA, "tiny_source_sha256": TINY_SHA,
        "tiny_training_sha256": admission["training_sha256"], "initial": str(checkpoint),
        "initial_manifest_sha256": digest(data / "initial_manifest.json"),
        "tokens_sha256": digest(data / "tokens.pt"), "code_sha256": digest(__file__),
        "schedules": schedules, "test_split_opened": False}
    write(ROOT / "prepare_receipt.json", receipt)
    print(json.dumps(receipt), flush=True)


def learning_rate(consumed):
    progress = min(consumed / TARGET, 1.0)
    if progress < 0.03:
        return 2e-5 * (0.05 + 0.95 * progress / 0.03)
    return 2e-5 * 0.5 * (1.0 + math.cos(math.pi * (progress - 0.03) / 0.97))


class CpuAdamW:
    """Keep full-parameter float32 master weights and Adam moments in host RAM for 4B."""
    def __init__(self, parameters, torch):
        self.torch = torch
        self.parameters = list(parameters)
        self.masters = [torch.nn.Parameter(p.detach().to(device="cpu", dtype=torch.float32).clone()) for p in self.parameters]
        self.inner = torch.optim.AdamW(self.masters, lr=learning_rate(0), betas=(0.9, 0.98),
            eps=1e-5, weight_decay=0.1, foreach=False, fused=False)
        self.param_groups = self.inner.param_groups

    def zero_grad(self, set_to_none=True):
        self.inner.zero_grad(set_to_none=set_to_none)
        for p in self.parameters:
            p.grad = None

    def step(self):
        for p, master in zip(self.parameters, self.masters, strict=True):
            master.grad = None if p.grad is None else p.grad.detach().to(device="cpu", dtype=self.torch.float32)
        self.inner.step()
        with self.torch.no_grad():
            for p, master in zip(self.parameters, self.masters, strict=True):
                p.copy_(master)

    def state_dict(self):
        return {"optimizer": self.inner.state_dict(), "master_weights": [p.detach() for p in self.masters]}


def train(condition, smoke=False):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    assert os.environ.get("CUDA_VISIBLE_DEVICES") and torch.cuda.device_count() == 1
    receipt = json.loads((ROOT / "prepare_receipt.json").read_text())
    assert receipt["status"] == "PASS" and receipt["code_sha256"] == digest(__file__)
    assert receipt["tokens_sha256"] == digest(ROOT / "data/tokens.pt")
    batches = json.loads((ROOT / "data" / f"schedule_{condition}.json").read_text())
    assert digest(ROOT / "data" / f"schedule_{condition}.json") == receipt["schedules"][condition]["schedule_sha256"]
    tokens = torch.load(ROOT / "data/tokens.pt", weights_only=True)
    size = receipt["size"]
    out = ROOT / ("smoke" if smoke else "runs") / condition
    out.mkdir(parents=True, exist_ok=True)
    assert not (out / "steps.csv").exists(), "existing trajectory; preserve evidence"
    torch.set_num_threads(4)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cuda.matmul.allow_tf32 = False
    for name, h in json.loads((ROOT / "data/initial_manifest.json").read_text()).items():
        assert digest(ROOT / "initial" / name) == h
    model = AutoModelForCausalLM.from_pretrained(ROOT / "initial", local_files_only=True,
        torch_dtype=torch.float32 if size == "1.7B" else torch.bfloat16, attn_implementation="sdpa").cuda()
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.train()
    optimizer = (torch.optim.AdamW(model.parameters(), lr=learning_rate(0), betas=(0.9, 0.98),
        eps=1e-5, weight_decay=0.1, foreach=False, fused=False) if size == "1.7B" else CpuAdamW(model.parameters(), torch))
    identity = {"size": size, "condition": condition, "host": socket.gethostname(), "pid": os.getpid(),
        "gpu": torch.cuda.get_device_name(), "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"],
        "torch": torch.__version__, "transformers": transformers.__version__, "seed": SEED,
        "initial_manifest_sha256": receipt["initial_manifest_sha256"], "code_sha256": digest(__file__),
        "planned": receipt["schedules"][condition], "smoke": smoke,
        "parameter_dtype": "float32" if size == "1.7B" else "bfloat16",
        "optimizer_location": "cuda" if size == "1.7B" else "cpu-float32-master-weights",
        "autocast_dtype": "bfloat16", "attention": "sdpa"}
    write(out / "identity.json", identity)
    if smoke:
        # Stress the longest real sequence, then the short-example path in one disposable update.
        longest = max(range(len(tokens)), key=lambda i: len(tokens[i]["ids"]))
        tiny = next(i for i, r in enumerate(tokens) if r["tiny"])
        batches = [{"indices": [longest, tiny], "tiny": False}]
    started, consumed = time.monotonic(), 0
    fields = ["step", "loss_tokens", "tiny_batch", "train_loss", "grad_norm", "learning_rate", "elapsed_seconds", "peak_gpu_gib"]
    with (out / "steps.csv").open("x", buffering=1) as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for step, batch_spec in enumerate(batches, 1):
            batch = [tokens[i] for i in batch_spec["indices"]]
            denominator = sum(r["loss_tokens"] for r in batch)
            lr = learning_rate(consumed)
            for group in optimizer.param_groups:
                group["lr"] = lr
            optimizer.zero_grad(set_to_none=True)
            total_loss = 0.0
            for row in batch:
                ids = torch.tensor([row["ids"]], dtype=torch.long, device="cuda")
                labels = ids.clone()
                labels[:, :row["prompt"]] = -100
                assert int((labels != -100).sum()) == row["loss_tokens"]
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    loss = model(input_ids=ids, labels=labels).loss
                assert bool(torch.isfinite(loss)), "nonfinite loss"
                weight = row["loss_tokens"] / denominator
                (loss * weight).backward()
                total_loss += float(loss.detach()) * weight
                del loss, ids, labels
            grad = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
            assert float(grad) > 0, "zero gradient"
            optimizer.step()
            consumed += denominator
            if not smoke:
                assert consumed == batch_spec["cumulative_loss_tokens"]
            metrics = dict(zip(fields, [step, consumed, batch_spec["tiny"], total_loss, float(grad), lr,
                time.monotonic() - started, torch.cuda.max_memory_allocated() / 2**30], strict=True))
            writer.writerow(metrics)
            write(out / "progress.json", {**metrics, "status": "RUNNING", "condition": condition})
            print(json.dumps(metrics), flush=True)
            if not smoke and (step % 100 == 0 or step == len(batches)):
                tmp = out / "training_state.tmp.pt"
                torch.save({"step": step, "consumed": consumed, "model": model.state_dict(),
                    "optimizer": optimizer.state_dict(), "identity": identity,
                    "cpu_rng": torch.get_rng_state(), "cuda_rng": torch.cuda.get_rng_state_all()}, tmp)
                tmp.replace(out / "training_state.pt")
    if not smoke:
        assert consumed == receipt["schedules"][condition]["loss_tokens"]
        model.save_pretrained(out / "hf", safe_serialization=True)
        AutoTokenizer.from_pretrained(ROOT / "initial", local_files_only=True).save_pretrained(out / "hf")
        model.generation_config.save_pretrained(out / "hf")
        files = {p.name: digest(p) for p in sorted((out / "hf").iterdir()) if p.is_file()}
        write(out / "weights_manifest.json", files)
        (out / "hf/SHA256SUMS").write_text("".join(f"{h}  {n}\n" for n, h in files.items()))
    write(out / "result.json", {**identity, **metrics, "status": "COMPLETE", "test_split_opened": False})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "train", "smoke"))
    parser.add_argument("--condition", choices=("control", "mixed"), default="mixed")
    parser.add_argument("--size", choices=("1.7B", "4B"), default="1.7B")
    args = parser.parse_args()
    prepare(args.size) if args.mode == "prepare" else train(args.condition, args.mode == "smoke")
