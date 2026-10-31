"""V28 model-family replicate: expt_v4's hash-verified train-only SFT recipe at Llama-3.2-1B/3B (Gemma-3 prepared, not launched).

The training loop is expt_v26/train_v26.py's. Differences: the Qwen3 chat format and expt_v4 token manifest cannot apply to
another tokenizer, so each family has its own prompt format (FAMILIES) and prepare writes that family's own token manifest
(same corpus, same hashes of the source text); three seeds per size; a --smoke mode that trains a few steps on the longest
examples to measure peak GPU memory and checks the export. See PROTOCOL.md.
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
STEPS = 658
MAX_SEQ = 16384
SCRATCH = Path(os.environ.get("SCRATCH", "/scratch/users/brando9"))
DATA_SOURCES = [SCRATCH / "rl4cv_sherlock/expt_v4/data/s_v1.jsonl",
                Path("/home/groups/sanmi/brando9/rl4cv_sherlock/expt_v4/data/s_v1.jsonl")]
SEEDS = (20260830, 20260831, 20260832)
# Public unsloth mirrors of the gated official repos (same weights), pinned by revision and by Hub LFS sha256.
ARMS = {
    "llama1b": {"family": "llama3", "model": "unsloth/Llama-3.2-1B", "revision": "9535bd9b1d1dea6acafbdc4813b728796aeb28da",
                "seeds": SEEDS, "host_optimizer": False, "enabled": True,
                "lfs_sha256": {"model.safetensors": "68a2e4be76fa709455a60272fba8e512c02d81c46e6c671cc9449e374fd6809a",
                               "tokenizer.json": "6b9e4e7fb171f92fd137b777cc2714bf87d11576700a1dcd7a399e7bbe39537b"}},
    "llama3b": {"family": "llama3", "model": "unsloth/Llama-3.2-3B", "revision": "d4446454d87d51aa42e1fb174f25acc5f8762331",
                "seeds": SEEDS, "host_optimizer": True, "enabled": True,
                "lfs_sha256": {"model-00001-of-00002.safetensors": "584d8d3e3f82f7964955174dfe5e3b1cf117a9d859f022cfdf7fcb884856e002",
                               "model-00002-of-00002.safetensors": "4719a04514ec2f060240711b7c33ab21187cac730ecaba3040b7a0fd95a9cefb",
                               "tokenizer.json": "6b9e4e7fb171f92fd137b777cc2714bf87d11576700a1dcd7a399e7bbe39537b"}},
    # Prepared, not launched (enabled False): turned on by editing this table in the Gemma addendum to PROTOCOL.md.
    "gemma1b": {"family": "gemma3", "model": "unsloth/gemma-3-1b-pt", "revision": "34a98bf3eaecc08c699516f625eb5e56e4c5d99d",
                "seeds": SEEDS, "host_optimizer": False, "enabled": False,
                "lfs_sha256": {"model.safetensors": "ee5250f6eb1aa7cfb729dfd4dc8d9964fd772324776c6d00bf2bc674c069cb27",
                               "tokenizer.json": "4667f2089529e8e7657cfb6d1c19910ae71ff5f28aa7ab2ff2763330affad795"}},
    "gemma4b": {"family": "gemma3", "model": "unsloth/gemma-3-4b-pt", "revision": "52aba93981c6ad7712b030eb6dd496ece1d279d6",
                "seeds": SEEDS, "host_optimizer": True, "enabled": False,
                "lfs_sha256": {"model-00001-of-00002.safetensors": "8f5b423a203c41b5655b2e1b4c58be262cb0e403048c8116e100bdac91318320",
                               "model-00002-of-00002.safetensors": "d3d22b1ab51a03678f95f7d5e60f703a50e6554e4c731c884fc0fbf05e6e3f47",
                               "tokenizer.json": "4667f2089529e8e7657cfb6d1c19910ae71ff5f28aa7ab2ff2763330affad795"}},
}
# Prompt formats. The prefix is the chat template's output for (system, user) with the generation prompt, WITHOUT the BOS
# text (the tokenizer adds BOS once, in training and in vLLM generation alike); the assistant ids are the content plus the
# turn-end token plus the tokenizer's EOS. The same template string is saved with every checkpoint so vLLM generation uses it.
FAMILIES = {
    "llama3": {
        "template": ("{% for m in messages %}{{ '<|start_header_id|>' + m['role'] + '<|end_header_id|>\n\n' + m['content'] + '<|eot_id|>' }}"
                     "{% endfor %}{% if add_generation_prompt %}{{ '<|start_header_id|>assistant<|end_header_id|>\n\n' }}{% endif %}"),
        "turn_end": "<|eot_id|>", "stop_tokens": ["<|eot_id|>", "<|end_of_text|>"]},
    "gemma3": {
        # Gemma has no system role: the system text opens the first user turn, as in Google's own template.
        "template": ("{% set sys = messages[0]['content'] if messages[0]['role'] == 'system' else '' %}"
                     "{% for m in messages %}{% if m['role'] == 'user' %}{{ '<start_of_turn>user\n' + (sys + '\n\n' if sys and loop.index0 == 1 else '') + m['content'] + '<end_of_turn>\n' }}"
                     "{% elif m['role'] == 'assistant' %}{{ '<start_of_turn>model\n' + m['content'] + '<end_of_turn>\n' }}{% endif %}{% endfor %}"
                     "{% if add_generation_prompt %}{{ '<start_of_turn>model\n' }}{% endif %}"),
        "turn_end": "<end_of_turn>\n", "stop_tokens": ["<end_of_turn>", "<eos>"]},
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


def format_ids(tok, family, roles):
    """(prompt ids, assistant ids) for one corpus row under the family's format; BOS is added once by the tokenizer."""
    spec = FAMILIES[family]
    prefix = tok.apply_chat_template([{"role": "system", "content": roles["system"]},
                                      {"role": "user", "content": roles["user"]}],
                                     tokenize=False, add_generation_prompt=True, chat_template=spec["template"])
    pids = tok.encode(prefix, add_special_tokens=True)
    aids = tok.encode(roles["assistant"] + spec["turn_end"] + tok.eos_token, add_special_tokens=False)
    return pids, aids


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
    rows = [json.loads(line) for line in data.read_text().splitlines()]
    assert len(rows) == 1315
    models, family_tokens = {}, {}
    for arm, spec in ARMS.items():
        if not spec["enabled"]:
            continue
        fam = spec["family"]
        model_path = snapshot_download(spec["model"], revision=spec["revision"],
            allow_patterns=["*.json", "*.safetensors", "merges.txt", "*.model"])
        files = {p.name: digest(p) for p in sorted(Path(model_path).iterdir()) if p.is_file()}
        for name, sha in spec["lfs_sha256"].items():
            assert files.get(name) == sha, f"{arm} {name} hash {files.get(name)} != Hub LFS {sha}"
        tok = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        prepared, manifest = [], []
        for index, row in enumerate(rows):
            assert row["index"] == index
            roles = {m["role"]: m["content"] for m in row["messages"]}
            pids, aids = format_ids(tok, fam, roles)
            assert len(aids) > 0 and pids[0] == tok.bos_token_id and pids.count(tok.bos_token_id) == 1, (arm, index)
            prepared.append({"index": index, "ids": pids + aids, "prompt": len(pids), "loss_tokens": len(aids)})
            manifest.append({"index": index, "task_id": row["task_id"], "prompt_ids_sha256": ids_digest(pids),
                             "assistant_ids_sha256": ids_digest(aids), "n_prompt_tokens": len(pids),
                             "n_assistant_tokens_loss": len(aids), "n_total_tokens": len(pids) + len(aids)})
        longest = max(m["n_total_tokens"] for m in manifest)
        over = [m["index"] for m in manifest if m["n_total_tokens"] > MAX_SEQ]
        assert not over, f"{arm}: {len(over)} sequences above {MAX_SEQ} tokens (longest {longest}); first {over[:5]}"
        if fam in family_tokens:  # same family, same tokenizer files: tokens must agree (checked, not assumed)
            assert family_tokens[fam]["tokens"] == prepared, f"{arm} tokens differ from the family's first arm"
        else:
            family_tokens[fam] = {"tokens": prepared, "manifest": manifest}
        models[arm] = {"model": spec["model"], "revision": spec["revision"], "family": fam, "model_path": model_path,
                       "file_sha256": files, "token_gate": "PASS", "longest_sequence_tokens": longest,
                       "loss_tokens": sum(r["loss_tokens"] for r in prepared)}
    receipt_tokens = {}
    for fam, t in family_tokens.items():
        torch.save(t["tokens"], ROOT / f"data/tokens_{fam}.pt")
        with (ROOT / f"token_manifest_{fam}.jsonl").open("w") as f:
            for m in t["manifest"]:
                f.write(json.dumps(m) + "\n")
        receipt_tokens[fam] = {"tokens_sha256": digest(ROOT / f"data/tokens_{fam}.pt"),
                               "manifest_sha256": digest(ROOT / f"token_manifest_{fam}.jsonl"),
                               "loss_tokens": sum(r["loss_tokens"] for r in t["tokens"])}
    receipt = {"status": "PASS", "examples": len(rows), "models": models, "families": receipt_tokens,
        "data_sha256": DATA_SHA, "code_sha256": digest(__file__), "vllm_image_sha256": sif_sha,
        "chain_inputs_present": [str(p) for p in NEEDED], "host": socket.gethostname(),
        "job_id": os.environ.get("SLURM_JOB_ID"), "torch": torch.__version__}
    write_json(ROOT / "prepare_receipt.json", receipt)
    print(json.dumps(receipt), flush=True)


def train(arm, seed, smoke_steps=0, host_override=None):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    spec = ARMS[arm]
    smoke = smoke_steps > 0
    assert spec["enabled"] and seed in spec["seeds"] and os.environ.get("SLURM_JOB_ID"), "use the declared scheduler job"
    assert os.environ.get("CUDA_VISIBLE_DEVICES") and torch.cuda.device_count() == 1
    fam = spec["family"]
    receipt = json.loads((ROOT / "prepare_receipt.json").read_text())
    assert receipt["status"] == "PASS" and receipt["data_sha256"] == DATA_SHA
    assert receipt["code_sha256"] == digest(__file__), "source changed after admission"
    assert receipt["families"][fam]["tokens_sha256"] == digest(ROOT / f"data/tokens_{fam}.pt")
    assert receipt["models"][arm]["revision"] == spec["revision"]
    loss_tokens = receipt["families"][fam]["loss_tokens"]
    assert torch.cuda.is_bf16_supported()
    rows = torch.load(ROOT / f"data/tokens_{fam}.pt", weights_only=True)
    order = list(range(len(rows)))
    random.Random(seed).shuffle(order)
    if smoke:  # the longest examples first: peak GPU memory at the worst case, a few steps only
        order = sorted(order, key=lambda i: -len(rows[i]["ids"]))[:2 * smoke_steps]
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.set_num_threads(int(os.environ.get("SLURM_CPUS_PER_TASK", "4")))
    torch.backends.cuda.matmul.allow_tf32 = False
    model_path = receipt["models"][arm]["model_path"]
    host = spec["host_optimizer"] if host_override is None else host_override
    model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True,
        torch_dtype=torch.float32, attn_implementation="sdpa").cuda()
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.train()
    optimizer = make_optimizer(model, host)
    scheduler = make_scheduler(optimizer)
    out = ROOT / ("runs_smoke" if smoke else "runs") / f"{arm}_s{seed}"
    out.mkdir(parents=True, exist_ok=True)
    if (out / "result.json").exists() or (out / "steps.csv").exists():
        raise RuntimeError("existing trajectory: preserve evidence; do not silently restart")
    identity = {"arm": arm, "seed": seed, "model": spec["model"], "revision": spec["revision"], "family": fam,
        "host": socket.gethostname(), "job_id": os.environ["SLURM_JOB_ID"], "torch": torch.__version__,
        "transformers": transformers.__version__, "gpu": torch.cuda.get_device_name(),
        "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"], "data_sha256": DATA_SHA,
        "order_sha256": ids_digest(order), "code_sha256": digest(__file__), "declared_examples": len(order),
        "declared_steps": smoke_steps if smoke else STEPS, "declared_loss_tokens": None if smoke else loss_tokens,
        "parameter_dtype": "float32", "autocast_dtype": "bfloat16", "backend": "transformers-sdpa", "smoke": smoke,
        "optimizer_device": "cpu (HostAdamW, float32 master + moments)" if host else "cuda",
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
            if not smoke and (step % 100 == 0 or step == STEPS):
                tmp = out / "training_state.tmp.pt"
                torch.save({"step": step, "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                    "scheduler": scheduler.state_dict(), "identity": identity, "order": order,
                    "cpu_rng": torch.get_rng_state(), "cuda_rng": torch.cuda.get_rng_state_all()}, tmp)
                tmp.replace(out / "training_state.pt")
    if not smoke:
        assert consumed == loss_tokens and step == STEPS
    model.save_pretrained(out / "hf")
    tok = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    tok.chat_template = FAMILIES[fam]["template"]  # generation reads the format from the checkpoint's tokenizer
    tok.save_pretrained(out / "hf")
    files = {p.name: digest(p) for p in sorted((out / "hf").iterdir()) if p.is_file()}
    write_json(out / "weights_manifest.json", files)
    write_json(out / "result.json", {**identity, **metrics, "status": "COMPLETE", "export_files": len(files),
        "stop_tokens": FAMILIES[fam]["stop_tokens"],
        "validation": "measured by the gen/score steps of this chain", "test": "unopened", "provider_spend_usd": 0})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "train", "smoke"])
    parser.add_argument("--arm", choices=sorted(ARMS))
    parser.add_argument("--seed", type=int)
    parser.add_argument("--steps", type=int, default=4, help="smoke: number of updates on the longest examples")
    parser.add_argument("--host-optimizer", choices=["auto", "on", "off"], default="auto", help="smoke only")
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    elif args.mode == "smoke":
        train(args.arm, args.seed, smoke_steps=args.steps,
              host_override={"auto": None, "on": True, "off": False}[args.host_optimizer])
    else:
        train(args.arm, args.seed)
