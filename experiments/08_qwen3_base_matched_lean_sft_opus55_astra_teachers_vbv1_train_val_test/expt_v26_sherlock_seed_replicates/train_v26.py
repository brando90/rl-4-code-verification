"""V26 Sherlock seed replicates: expt_v4's hash-verified train-only SFT at a third 1.7B seed and at Qwen3-4B-Base.

The training loop is expt_v4/train_sherlock.py's. Differences: an arm table (model, revision, seeds), a preparation step
that downloads and hashes both models and runs the v4 token gate with each tokenizer, and for the 4B arm the same AdamW
run on float32 host copies of the parameters (HostAdamW) because float32 parameters, gradients and moments do not fit
one 80 GB H100 together with activations. See PROTOCOL.md.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import socket
import time

ROOT = Path(__file__).resolve().parent
DATA_SHA = "885d4ae2d6cf193bddc43df6ad6274cacfa8c98a5e5ecd63bd2519472f5e7354"
MANIFEST_SHA = "06d15adc7d8599bda2dd976da475b231e9120e08a7a9ccaf4a4cdbc577220314"  # ../expt_v4/token_manifest.jsonl, copied into the package
LOSS_TOKENS = 5752936
STEPS = 658
SCRATCH = Path(os.environ.get("SCRATCH", "/scratch/users/brando9"))
DATA_SOURCES = [SCRATCH / "rl4cv_sherlock/expt_v4/data/s_v1.jsonl",
                Path("/home/groups/sanmi/brando9/rl4cv_sherlock/expt_v4/data/s_v1.jsonl")]
ARMS = {
    "1p7b": {"model": "Qwen/Qwen3-1.7B-Base", "revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
             "seeds": (20260832,), "host_optimizer": False,
             "lfs_sha256": {"model.safetensors": "6df85b39330e5a425ee36253d0f894e4387e4f0a15b9c53cb467d668e6b3a841"}},
    "4b": {"model": "Qwen/Qwen3-4B-Base", "revision": "906bfd4b4dc7f14ee4320094d8b41684abff8539",
           "seeds": (20260830, 20260831), "host_optimizer": True,
           "lfs_sha256": {"model-00001-of-00003.safetensors": "4c807e2503d68ae373d508689d00a41f4b33f33c2536da97ab81a20caddc1241",
                          "model-00002-of-00003.safetensors": "f4707585548b2fc75a6b1d732e8465c62040a8699903c32850781beeb9b27826",
                          "model-00003-of-00003.safetensors": "c7b1aa8fb672de2e00423c99876926022e50b18d4f0d140670788510a27f9965"}},
}
# Inputs the later chain steps read; prep fails early if one is missing instead of the chain failing hours later.
V4V = SCRATCH / "rl4cv_sherlock/v4_validation"
SIF = SCRATCH / "rl4cv_sherlock/containers/vllm-openai_v0.30.0.sif"
SIF_SHA_PREFIX, SIF_SHA_SUFFIX = "5fec93bd16e7", "139b"
NEEDED = [V4V / "rl4cv_gen/src/rl4cv/veribench/generate.py", V4V / "run/validation_pack",
          V4V / "rl4cv_gen/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split/vbv1_validation_task_ids.txt",
          SCRATCH / "rl4cv_sherlock/grading/READY", SCRATCH / "rl4cv_sherlock/grading/score_sherlock.sh",
          SCRATCH / "rl4cv_sherlock/grading/rl4cv/src/rl4cv/veribench/jobs.py"]


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


class HostAdamW:
    """torch.optim.AdamW stepping float32 host copies of device parameters; the device parameters get the result back.

    Gradients are computed and clipped on the device as in expt_v4, copied into host buffers, the unchanged AdamW step
    runs on the host copies (moments live on the host), and the updated values are copied back, so device and host
    parameters are equal after every step.
    """

    def __init__(self, params, pin=False, **kwargs):
        import torch
        self.torch = torch
        self.params = list(params)
        self.master = []
        for p in self.params:
            m = p.detach().to("cpu", copy=True)
            self.master.append(torch.nn.Parameter(m.pin_memory() if pin else m))
        self.pin = pin
        self.optimizer = torch.optim.AdamW(self.master, **kwargs)
        self.param_groups = self.optimizer.param_groups

    def step(self):
        torch = self.torch
        for p, m in zip(self.params, self.master, strict=True):
            if p.grad is None:
                m.grad = None
                continue
            if m.grad is None:
                m.grad = torch.empty(m.shape, dtype=m.dtype, pin_memory=self.pin)
            m.grad.copy_(p.grad, non_blocking=self.pin)
        if self.params[0].is_cuda:
            torch.cuda.synchronize()
        self.optimizer.step()
        with torch.no_grad():
            for p, m in zip(self.params, self.master, strict=True):
                p.copy_(m, non_blocking=self.pin)
        if self.params[0].is_cuda:
            torch.cuda.synchronize()

    def state_dict(self):
        return self.optimizer.state_dict()


def make_optimizer(model, host):
    import torch
    kwargs = dict(lr=2e-5, betas=(0.9, 0.98), eps=1e-5, weight_decay=0.1, foreach=False, fused=False)
    if host:
        return HostAdamW(model.parameters(), pin=torch.cuda.is_available(), **kwargs)
    return torch.optim.AdamW(model.parameters(), **kwargs)


def make_scheduler(optimizer):
    import torch
    optimizer = getattr(optimizer, "optimizer", optimizer)
    return torch.optim.lr_scheduler.SequentialLR(optimizer, [
        torch.optim.lr_scheduler.LinearLR(optimizer, start_factor=0.05, total_iters=20),
        torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=638, eta_min=0.0)], milestones=[20])


def prepare():
    import torch
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer

    missing = [str(p) for p in NEEDED if not p.exists()]
    assert not missing, f"chain inputs missing: {missing}"
    sif_sha = digest(SIF)
    assert sif_sha.startswith(SIF_SHA_PREFIX) and sif_sha.endswith(SIF_SHA_SUFFIX), f"vLLM image hash {sif_sha}"
    data = ROOT / "data/s_v1.jsonl"
    data.parent.mkdir(exist_ok=True)
    if not data.exists():
        source = next(p for p in DATA_SOURCES if p.exists())
        shutil.copyfile(source, data)
    assert digest(data) == DATA_SHA, "training corpus hash mismatch"
    assert digest(ROOT / "token_manifest.jsonl") == MANIFEST_SHA, "token manifest is not expt_v4's"
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    manifest = [json.loads(line) for line in (ROOT / "token_manifest.jsonl").read_text().splitlines()]
    assert len(rows) == len(manifest) == 1315
    models, tokens = {}, None
    for arm, spec in ARMS.items():
        model_path = snapshot_download(spec["model"], revision=spec["revision"],
            allow_patterns=["*.json", "*.safetensors", "merges.txt", "*.model"])
        files = {p.name: digest(p) for p in sorted(Path(model_path).iterdir()) if p.is_file()}
        for name, sha in spec["lfs_sha256"].items():
            assert files.get(name) == sha, f"{arm} {name} hash {files.get(name)} != Hub LFS {sha}"
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
            assert ids_digest(pids) == expected["prompt_ids_sha256"], (arm, index)
            assert ids_digest(aids) == expected["assistant_ids_sha256"], (arm, index)
            assert len(aids) == expected["n_assistant_tokens_loss"] > 0
            assert len(pids) + len(aids) == expected["n_total_tokens"] <= 16384
            prepared.append({"index": index, "ids": pids + aids, "prompt": len(pids), "loss_tokens": len(aids)})
        assert sum(r["loss_tokens"] for r in prepared) == LOSS_TOKENS
        assert tokens is None or tokens == prepared, f"{arm} tokens differ from the first arm's"
        tokens = prepared
        models[arm] = {"model": spec["model"], "revision": spec["revision"], "model_path": model_path,
                       "file_sha256": files, "token_gate": "PASS"}
    torch.save(tokens, ROOT / "data/tokens.pt")
    receipt = {"status": "PASS", "examples": len(tokens), "loss_tokens": LOSS_TOKENS, "models": models,
        "data_sha256": DATA_SHA, "token_manifest_sha256": MANIFEST_SHA,
        "tokens_sha256": digest(ROOT / "data/tokens.pt"), "code_sha256": digest(__file__),
        "maximum_sequence_tokens": max(len(r["ids"]) for r in tokens), "vllm_image_sha256": sif_sha,
        "chain_inputs_present": [str(p) for p in NEEDED], "host": socket.gethostname(),
        "job_id": os.environ.get("SLURM_JOB_ID"), "torch": torch.__version__}
    write_json(ROOT / "prepare_receipt.json", receipt)
    print(json.dumps(receipt), flush=True)


def train(arm, seed):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    spec = ARMS[arm]
    assert seed in spec["seeds"] and os.environ.get("SLURM_JOB_ID"), "use the declared scheduler job"
    assert os.environ.get("CUDA_VISIBLE_DEVICES") and torch.cuda.device_count() == 1
    receipt = json.loads((ROOT / "prepare_receipt.json").read_text())
    assert receipt["status"] == "PASS" and receipt["data_sha256"] == DATA_SHA
    assert receipt["code_sha256"] == digest(__file__), "source changed after admission"
    assert receipt["tokens_sha256"] == digest(ROOT / "data/tokens.pt")
    assert receipt["models"][arm]["revision"] == spec["revision"]
    assert torch.cuda.is_bf16_supported()
    rows = torch.load(ROOT / "data/tokens.pt", weights_only=True)
    order = list(range(len(rows)))
    random.Random(seed).shuffle(order)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.set_num_threads(int(os.environ.get("SLURM_CPUS_PER_TASK", "4")))
    torch.backends.cuda.matmul.allow_tf32 = False
    model_path = receipt["models"][arm]["model_path"]
    model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True,
        torch_dtype=torch.float32, attn_implementation="sdpa").cuda()
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.train()
    optimizer = make_optimizer(model, spec["host_optimizer"])
    scheduler = make_scheduler(optimizer)
    out = ROOT / "runs" / f"{arm}_s{seed}"
    out.mkdir(parents=True, exist_ok=True)
    if (out / "result.json").exists() or (out / "steps.csv").exists():
        raise RuntimeError("existing trajectory: preserve evidence; do not silently restart")
    identity = {"arm": arm, "seed": seed, "model": spec["model"], "revision": spec["revision"],
        "host": socket.gethostname(), "job_id": os.environ["SLURM_JOB_ID"], "torch": torch.__version__,
        "transformers": transformers.__version__, "gpu": torch.cuda.get_device_name(),
        "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"], "data_sha256": DATA_SHA,
        "order_sha256": ids_digest(order), "code_sha256": digest(__file__), "declared_examples": 1315,
        "declared_steps": STEPS, "declared_loss_tokens": LOSS_TOKENS, "parameter_dtype": "float32",
        "autocast_dtype": "bfloat16", "backend": "transformers-sdpa",
        "optimizer_device": "cpu (HostAdamW, float32 master + moments)" if spec["host_optimizer"] else "cuda",
        "n_parameters": sum(p.numel() for p in model.parameters())}
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
            model.zero_grad(set_to_none=True)
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
            if step % 100 == 0 or step == STEPS:
                tmp = out / "training_state.tmp.pt"
                torch.save({"step": step, "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                    "scheduler": scheduler.state_dict(), "identity": identity, "order": order,
                    "cpu_rng": torch.get_rng_state(), "cuda_rng": torch.cuda.get_rng_state_all()}, tmp)
                tmp.replace(out / "training_state.pt")
    assert consumed == LOSS_TOKENS and step == STEPS
    model.save_pretrained(out / "hf")
    AutoTokenizer.from_pretrained(model_path, local_files_only=True).save_pretrained(out / "hf")
    files = {p.name: digest(p) for p in sorted((out / "hf").iterdir()) if p.is_file()}
    write_json(out / "weights_manifest.json", files)
    write_json(out / "result.json", {**identity, **metrics, "status": "COMPLETE", "export_files": len(files),
        "validation": "measured by the gen/score steps of this chain", "test": "unopened", "provider_spend_usd": 0})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "train"])
    parser.add_argument("--arm", choices=sorted(ARMS))
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        train(args.arm, args.seed)
