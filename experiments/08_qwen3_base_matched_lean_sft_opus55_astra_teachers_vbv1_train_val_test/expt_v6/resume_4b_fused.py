"""Continue a saved 4B trajectory with CPU fused AdamW, preserving float32 masters and moments."""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import socket
import time

import experiment as original


class FusedCpuAdamW(original.CpuAdamW):
    """Restore authoritative float32 weights rather than reconstructing them from bf16 shadows."""
    def __init__(self, parameters, torch, saved):
        self.torch = torch
        self.parameters = list(parameters)
        assert len(self.parameters) == len(saved["master_weights"])
        self.masters = [torch.nn.Parameter(value.detach().to(device="cpu", dtype=torch.float32).clone())
            for value in saved["master_weights"]]
        self.inner = torch.optim.AdamW(self.masters, lr=original.learning_rate(0), betas=(0.9, 0.98),
            eps=1e-5, weight_decay=0.1, foreach=False, fused=True)
        self.inner.load_state_dict(saved["optimizer"])
        for group in self.inner.param_groups:
            group.update(fused=True, foreach=False)
        self.param_groups = self.inner.param_groups


def control():
    import torch
    torch.set_num_threads(4)
    torch.manual_seed(original.SEED)
    parameters = [torch.nn.Parameter(torch.randn(shape, dtype=torch.bfloat16))
        for shape in ((19,), (127, 89), (250003,))]
    unfused = original.CpuAdamW(parameters, torch)
    for _ in range(5):
        for p in parameters:
            p.grad = torch.randn_like(p)
        unfused.step()
    # Round-trip the same schema used by the full training checkpoint.
    import io
    buffer = io.BytesIO()
    torch.save(unfused.state_dict(), buffer)
    buffer.seek(0)
    saved = torch.load(buffer, map_location="cpu", weights_only=True)
    shadows = [torch.nn.Parameter(p.detach().clone()) for p in parameters]
    fused = FusedCpuAdamW(shadows, torch, saved)
    for old, new in zip(unfused.masters, fused.masters, strict=True):
        assert torch.equal(old, new)
        for key in ("step", "exp_avg", "exp_avg_sq"):
            assert torch.equal(unfused.inner.state[old][key], fused.inner.state[new][key])
    maxima = dict(weights=0.0, first_moment=0.0, second_moment=0.0)
    for step in range(5):
        unfused.zero_grad(); fused.zero_grad()
        for old, new in zip(parameters, shadows, strict=True):
            gradient = torch.randn_like(old)
            old.grad, new.grad = gradient, gradient.clone()
        for opt in (unfused, fused):
            opt.param_groups[0]["lr"] = 2e-5 * (step + 1) / 5
            opt.step()
        for old, new, shadow in zip(unfused.masters, fused.masters, shadows, strict=True):
            for key, a, b in (("weights", old, new),
                ("first_moment", unfused.inner.state[old]["exp_avg"], fused.inner.state[new]["exp_avg"]),
                ("second_moment", unfused.inner.state[old]["exp_avg_sq"], fused.inner.state[new]["exp_avg_sq"])):
                maxima[key] = max(maxima[key], float((a - b).abs().max()))
                torch.testing.assert_close(a, b, rtol=2e-6, atol=1e-7)
            assert torch.equal(shadow, new.detach().to(torch.bfloat16))
    print(json.dumps({"status": "PASS", "restored_master_weights_and_moments_bitwise": True,
        "updates_before_save": 5, "updates_after_restore": 5, "max_absolute_differences": maxima,
        "bf16_shadows_match_own_masters": True, "torch": torch.__version__}, indent=2))


def inspect_checkpoint(path, expected_step):
    import torch
    torch.set_num_threads(4)
    root = original.ROOT
    # This is our own checkpoint; its recorded TorchVersion object needs the full loader.
    state = torch.load(path, map_location="cpu", weights_only=False)
    receipt = json.loads((root / "prepare_receipt.json").read_text())
    batches = json.loads((root / "data/schedule_mixed.json").read_text())
    assert state["step"] == expected_step
    assert state["consumed"] == batches[expected_step - 1]["cumulative_loss_tokens"]
    identity = state["identity"]
    assert identity["size"] == "4B" and identity["condition"] == "mixed"
    assert identity["code_sha256"] == receipt["code_sha256"] == original.digest(original.__file__)
    assert identity["initial_manifest_sha256"] == receipt["initial_manifest_sha256"]
    optimizer = state["optimizer"]
    masters = optimizer["master_weights"]
    opt = optimizer["optimizer"]
    param_ids = [i for group in opt["param_groups"] for i in group["params"]]
    assert len(masters) == len(param_ids)
    assert all(master.dtype == torch.float32 for master in masters)
    assert all(int(opt["state"][i]["step"].item()) == expected_step for i in param_ids)
    assert state["cpu_rng"].dtype == torch.uint8 and len(state["cuda_rng"]) == 1
    return {"status": "PASS", "step": expected_step, "consumed": state["consumed"],
        "checkpoint": str(path), "checkpoint_sha256": original.digest(path),
        "parameter_tensors": len(masters), "parameter_count": sum(p.numel() for p in masters),
        "master_dtype": "float32", "all_optimizer_steps_match": True}


def train(checkpoint, expected_step):
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    root = original.ROOT
    out = root / "runs/mixed"
    assert os.environ["CUDA_VISIBLE_DEVICES"] == "6" and torch.cuda.device_count() == 1
    torch.set_num_threads(4)
    torch.backends.cuda.matmul.allow_tf32 = False
    receipt = json.loads((root / "prepare_receipt.json").read_text())
    inspection = json.loads((original.ROOT.parent / "fused_handoff/checkpoint_inspection.json").read_text())
    assert inspection["status"] == "PASS" and inspection["step"] == expected_step
    assert inspection["checkpoint_sha256"] == original.digest(checkpoint)
    assert receipt["code_sha256"] == original.digest(original.__file__)
    assert receipt["tokens_sha256"] == original.digest(root / "data/tokens.pt")
    assert receipt["schedules"]["mixed"]["schedule_sha256"] == original.digest(root / "data/schedule_mixed.json")
    batches = json.loads((root / "data/schedule_mixed.json").read_text())
    tokens = torch.load(root / "data/tokens.pt", weights_only=True)
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    assert state["step"] == expected_step and state["consumed"] == inspection["consumed"]
    rows = list(csv.DictReader((out / "steps.csv").open()))
    assert [int(row["step"]) for row in rows] == list(range(1, expected_step + 1))
    assert int(rows[-1]["loss_tokens"]) == state["consumed"]
    previous_elapsed = float(rows[-1]["elapsed_seconds"])
    previous_peak = float(rows[-1]["peak_gpu_gib"])
    model = AutoModelForCausalLM.from_pretrained(root / "initial", local_files_only=True,
        torch_dtype=torch.bfloat16, attn_implementation="sdpa").cuda()
    loaded = model.load_state_dict(state["model"], strict=True)
    assert not loaded.missing_keys and not loaded.unexpected_keys
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.train()
    optimizer = FusedCpuAdamW(model.parameters(), torch, state["optimizer"])
    for parameter, master in zip(optimizer.parameters, optimizer.masters, strict=True):
        assert torch.equal(parameter.detach().cpu(), master.detach().to(torch.bfloat16)), "shadow/master mismatch"
    torch.set_rng_state(state["cpu_rng"])
    torch.cuda.set_rng_state_all(state["cuda_rng"])
    consumed = state["consumed"]
    identity = {**state["identity"], "pid": os.getpid(), "host": socket.gethostname(),
        "torch": torch.__version__, "transformers": transformers.__version__,
        "optimizer_location": "cpu-float32-master-weights-fused",
        "continuation_source_sha256": original.digest(__file__), "resumed_after_step": expected_step,
        "resumed_checkpoint_sha256": inspection["checkpoint_sha256"],
        "kernel_change": "fused=True; float32 masters, moments, hyperparameters and schedule restored",
        "numerical_limit": "same AdamW formula; different floating-point kernel, not bitwise-equivalent trajectory"}
    original.write(out / "identity.json", identity)
    original.write(root.parent / "fused_handoff/restore_verified.json", {"status": "PASS", "step": expected_step,
        "master_and_moment_restore": "exact", "bf16_shadows_match_masters": True,
        "cpu_cuda_rng_restored": True, "pid": os.getpid(), "verified_unix": time.time()})
    del state, rows
    started = time.monotonic()
    fields = ["step", "loss_tokens", "tiny_batch", "train_loss", "grad_norm", "learning_rate", "elapsed_seconds", "peak_gpu_gib"]
    with (out / "steps.csv").open("a", buffering=1) as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        for step in range(expected_step + 1, len(batches) + 1):
            spec = batches[step - 1]
            batch = [tokens[i] for i in spec["indices"]]
            denominator = sum(row["loss_tokens"] for row in batch)
            lr = original.learning_rate(consumed)
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
            assert consumed == spec["cumulative_loss_tokens"]
            metrics = dict(zip(fields, [step, consumed, spec["tiny"], total_loss, float(grad), lr,
                previous_elapsed + time.monotonic() - started,
                max(previous_peak, torch.cuda.max_memory_allocated() / 2**30)], strict=True))
            writer.writerow(metrics)
            original.write(out / "progress.json", {**metrics, "status": "RUNNING", "condition": "mixed", "optimizer_fused": True})
            print(json.dumps(metrics), flush=True)
            if step % 100 == 0 or step == len(batches):
                temporary = out / "training_state.tmp.pt"
                torch.save({"step": step, "consumed": consumed, "model": model.state_dict(),
                    "optimizer": optimizer.state_dict(), "identity": identity,
                    "cpu_rng": torch.get_rng_state(), "cuda_rng": torch.cuda.get_rng_state_all()}, temporary)
                temporary.replace(out / "training_state.pt")
    assert consumed == receipt["schedules"]["mixed"]["loss_tokens"]
    model.save_pretrained(out / "hf", safe_serialization=True)
    AutoTokenizer.from_pretrained(root / "initial", local_files_only=True).save_pretrained(out / "hf")
    model.generation_config.save_pretrained(out / "hf")
    hashes = {p.name: original.digest(p) for p in sorted((out / "hf").iterdir()) if p.is_file()}
    original.write(out / "weights_manifest.json", hashes)
    (out / "hf/SHA256SUMS").write_text("".join(f"{h}  {name}\n" for name, h in hashes.items()))
    original.write(out / "result.json", {**identity, **metrics, "status": "COMPLETE", "test_split_opened": False})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("control", "inspect", "train"))
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--step", type=int, default=100)
    args = parser.parse_args()
    if args.mode == "control":
        control()
    elif args.mode == "inspect":
        print(json.dumps(inspect_checkpoint(args.checkpoint, args.step), indent=2))
    else:
        train(args.checkpoint, args.step)
