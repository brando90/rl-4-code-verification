"""V27 SFT data-size ablation: expt_v4's hash-verified train-only SFT of Qwen3-1.7B-Base on the ladder's nested subsets.

The training loop is expt_v4/train_sherlock.py's (as reused by V26). Differences: a run table (fraction x seed, runs.tsv),
each run trains on the first n examples of S in manifest order (the examples experiment 08's ladder rung had seen), for
ceil(n/2) updates with the v4 warmup and a cosine to zero at the run's own end. See PROTOCOL.md.
"""
from __future__ import annotations

import argparse
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

ROOT = Path(__file__).resolve().parent
DATA_SHA = "885d4ae2d6cf193bddc43df6ad6274cacfa8c98a5e5ecd63bd2519472f5e7354"
MANIFEST_SHA = "06d15adc7d8599bda2dd976da475b231e9120e08a7a9ccaf4a4cdbc577220314"  # ../expt_v4/token_manifest.jsonl, copied into the package
LOSS_TOKENS = 5752936
N_EXAMPLES = 1315
WARMUP = 20
# fraction label -> (examples = 2 x ladder rung step, loss tokens = ladder rung cumulative tokens; expt_v1 PROTOCOL § 8)
SUBSETS = {"f0p125": (164, 720775), "f0p25": (328, 1442549), "f0p5": (668, 2884708)}
MODEL = "Qwen/Qwen3-1.7B-Base"
REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
LFS_SHA256 = {"model.safetensors": "6df85b39330e5a425ee36253d0f894e4387e4f0a15b9c53cb467d668e6b3a841"}
SCRATCH = Path(os.environ.get("SCRATCH", "/scratch/users/brando9"))
DATA_SOURCES = [SCRATCH / "rl4cv_sherlock/expt_v4/data/s_v1.jsonl",
                Path("/home/groups/sanmi/brando9/rl4cv_sherlock/expt_v4/data/s_v1.jsonl")]
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


def read_runs():
    """runs.tsv: index, fraction, seed, run, label (the single source of the six runs for every chain step)."""
    rows = list(csv.DictReader((ROOT / "runs.tsv").open(), delimiter="\t"))
    assert [int(r["index"]) for r in rows] == list(range(len(rows)))
    for r in rows:
        assert r["fraction"] in SUBSETS and r["run"] == f"{r['fraction']}_s{r['seed']}" and r["label"] == f"v27_{r['run']}"
    return rows


def subset_indices(fraction):
    """The ladder's subset: the first n examples of S in manifest order (nested across fractions)."""
    return list(range(SUBSETS[fraction][0]))


def run_order(fraction, seed):
    order = subset_indices(fraction)
    random.Random(seed).shuffle(order)
    return order


def n_steps(n_examples):
    return math.ceil(n_examples / 2)


def make_optimizer(model):
    import torch
    return torch.optim.AdamW(model.parameters(), lr=2e-5, betas=(0.9, 0.98), eps=1e-5, weight_decay=0.1,
                             foreach=False, fused=False)


def make_scheduler(optimizer, steps):
    """expt_v4's schedule shape at this run's length: 20-step linear warmup from 5%, cosine to 0 over the rest."""
    import torch
    return torch.optim.lr_scheduler.SequentialLR(optimizer, [
        torch.optim.lr_scheduler.LinearLR(optimizer, start_factor=0.05, total_iters=WARMUP),
        torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=steps - WARMUP, eta_min=0.0)], milestones=[WARMUP])


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
    assert len(rows) == len(manifest) == N_EXAMPLES
    model_path = snapshot_download(MODEL, revision=REVISION, allow_patterns=["*.json", "*.safetensors", "merges.txt", "*.model"])
    files = {p.name: digest(p) for p in sorted(Path(model_path).iterdir()) if p.is_file()}
    for name, sha in LFS_SHA256.items():
        assert files.get(name) == sha, f"{name} hash {files.get(name)} != Hub LFS {sha}"
    tok = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    tokens = []
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
        tokens.append({"index": index, "ids": pids + aids, "prompt": len(pids), "loss_tokens": len(aids)})
    assert sum(r["loss_tokens"] for r in tokens) == LOSS_TOKENS
    torch.save(tokens, ROOT / "data/tokens.pt")
    subsets = {}
    for fraction, (n, loss_tokens) in SUBSETS.items():
        idx = subset_indices(fraction)
        assert sum(tokens[i]["loss_tokens"] for i in idx) == loss_tokens, f"{fraction} is not the ladder rung's subset"
        subsets[fraction] = {"examples": n, "loss_tokens": loss_tokens, "indices_sha256": ids_digest(idx),
                             "task_ids_sha256": ids_digest([rows[i]["task_id"] for i in idx]), "steps": n_steps(n)}
    runs = read_runs()
    for r in runs:
        order = run_order(r["fraction"], int(r["seed"]))
        r["order_sha256"] = ids_digest(order)
    write_json(ROOT / "data/subsets.json", {"subsets": subsets, "runs": runs})
    receipt = {"status": "PASS", "examples": len(tokens), "loss_tokens": LOSS_TOKENS, "model": MODEL, "revision": REVISION,
        "model_path": model_path, "file_sha256": files, "token_gate": "PASS", "subsets": subsets, "runs": runs,
        "data_sha256": DATA_SHA, "token_manifest_sha256": MANIFEST_SHA, "tokens_sha256": digest(ROOT / "data/tokens.pt"),
        "code_sha256": digest(__file__), "runs_tsv_sha256": digest(ROOT / "runs.tsv"),
        "maximum_sequence_tokens": max(len(r["ids"]) for r in tokens), "vllm_image_sha256": sif_sha,
        "chain_inputs_present": [str(p) for p in NEEDED], "host": socket.gethostname(),
        "job_id": os.environ.get("SLURM_JOB_ID"), "torch": torch.__version__}
    write_json(ROOT / "prepare_receipt.json", receipt)
    print(json.dumps(receipt), flush=True)


def run_steps(model, optimizer, scheduler, rows, order, out, identity, device="cuda", save_every=100):
    """expt_v4's update loop: batches of two in `order`, token-normalized assistant loss, clip 1.0, one epoch."""
    import torch
    steps = n_steps(len(order))
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
                ids = torch.tensor([row["ids"]], dtype=torch.long, device=device)
                labels = ids.clone()
                labels[:, :row["prompt"]] = -100
                with torch.autocast(device, dtype=torch.bfloat16):
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
            peak = torch.cuda.max_memory_allocated() / 2**30 if device == "cuda" else 0.0
            metrics = dict(zip(fields, [step, min(offset + 2, len(order)), consumed, total_loss, float(grad),
                learning_rate, time.monotonic() - started, peak], strict=True))
            writer.writerow(metrics)
            write_json(out / "progress.json", {**identity, **metrics, "status": "RUNNING"})
            print(json.dumps(metrics), flush=True)
            if step % save_every == 0 or step == steps:
                tmp = out / "training_state.tmp.pt"
                state = {"step": step, "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                    "scheduler": scheduler.state_dict(), "identity": identity, "order": order, "cpu_rng": torch.get_rng_state()}
                if device == "cuda":
                    state["cuda_rng"] = torch.cuda.get_rng_state_all()
                torch.save(state, tmp)
                tmp.replace(out / "training_state.pt")
    assert step == steps
    return metrics, consumed


def train(index):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    spec = read_runs()[index]
    fraction, seed = spec["fraction"], int(spec["seed"])
    n, loss_tokens = SUBSETS[fraction]
    assert os.environ.get("SLURM_JOB_ID"), "use the declared scheduler job"
    assert os.environ.get("CUDA_VISIBLE_DEVICES") and torch.cuda.device_count() == 1
    receipt = json.loads((ROOT / "prepare_receipt.json").read_text())
    assert receipt["status"] == "PASS" and receipt["data_sha256"] == DATA_SHA and receipt["revision"] == REVISION
    assert receipt["code_sha256"] == digest(__file__), "source changed after admission"
    assert receipt["runs_tsv_sha256"] == digest(ROOT / "runs.tsv"), "run table changed after admission"
    assert receipt["tokens_sha256"] == digest(ROOT / "data/tokens.pt")
    assert torch.cuda.is_bf16_supported()
    rows = torch.load(ROOT / "data/tokens.pt", weights_only=True)
    order = run_order(fraction, seed)
    assert len(order) == n and ids_digest(sorted(order)) == receipt["subsets"][fraction]["indices_sha256"]
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.set_num_threads(int(os.environ.get("SLURM_CPUS_PER_TASK", "4")))
    torch.backends.cuda.matmul.allow_tf32 = False
    out = ROOT / "runs" / spec["run"]
    out.mkdir(parents=True, exist_ok=True)
    if (out / "result.json").exists() or (out / "steps.csv").exists():
        raise RuntimeError("existing trajectory: preserve evidence; do not silently restart")
    model_path = receipt["model_path"]
    model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True,
        torch_dtype=torch.float32, attn_implementation="sdpa").cuda()
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.train()
    steps = n_steps(n)
    optimizer = make_optimizer(model)
    scheduler = make_scheduler(optimizer, steps)
    identity = {"index": index, "fraction": fraction, "seed": seed, "run": spec["run"], "label": spec["label"],
        "model": MODEL, "revision": REVISION, "host": socket.gethostname(), "job_id": os.environ["SLURM_JOB_ID"],
        "array_task": os.environ.get("SLURM_ARRAY_TASK_ID"), "torch": torch.__version__,
        "transformers": transformers.__version__, "gpu": torch.cuda.get_device_name(),
        "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"], "data_sha256": DATA_SHA,
        "subset_indices_sha256": receipt["subsets"][fraction]["indices_sha256"], "order_sha256": ids_digest(order),
        "code_sha256": digest(__file__), "declared_examples": n, "declared_steps": steps, "declared_loss_tokens": loss_tokens,
        "warmup_steps": WARMUP, "cosine_steps": steps - WARMUP, "parameter_dtype": "float32", "autocast_dtype": "bfloat16",
        "backend": "transformers-sdpa", "n_parameters": sum(p.numel() for p in model.parameters())}
    write_json(out / "identity.json", identity)
    metrics, consumed = run_steps(model, optimizer, scheduler, rows, order, out, identity)
    assert consumed == loss_tokens
    model.save_pretrained(out / "hf")
    AutoTokenizer.from_pretrained(model_path, local_files_only=True).save_pretrained(out / "hf")
    files = {p.name: digest(p) for p in sorted((out / "hf").iterdir()) if p.is_file()}
    write_json(out / "weights_manifest.json", files)
    write_json(out / "result.json", {**identity, **metrics, "status": "COMPLETE", "export_files": len(files),
        "validation": "measured by the gen/score steps of this chain", "test": "unopened", "provider_spend_usd": 0})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "train"])
    parser.add_argument("--index", type=int, help="row of runs.tsv (the Slurm array task id)")
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        train(args.index)
