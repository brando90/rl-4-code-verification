"""Measure CPU AdamW kernels without modifying training processes or allocating a GPU."""
import json
import statistics
import time

import torch


def main():
    torch.set_num_threads(4)
    torch.manual_seed(20261019)
    ordinary = [torch.nn.Parameter(torch.randn(shape)) for shape in ((17,), (123, 91), (250003,))]
    fused = [torch.nn.Parameter(p.detach().clone()) for p in ordinary]
    options = dict(lr=2e-5, betas=(0.9, 0.98), eps=1e-5, weight_decay=0.1, foreach=False)
    optimizers = [torch.optim.AdamW(ordinary, **options, fused=False),
                  torch.optim.AdamW(fused, **options, fused=True)]
    max_differences = {}
    for step in range(5):
        for left, right in zip(ordinary, fused, strict=True):
            gradient = torch.randn_like(left)
            left.grad, right.grad = gradient, gradient.clone()
        for opt in optimizers:
            opt.param_groups[0]["lr"] = 2e-5 * (step + 1) / 5
            opt.step()
        for left, right in zip(ordinary, fused, strict=True):
            for name, x, y in (("weights", left, right),
                ("first_moment", optimizers[0].state[left]["exp_avg"], optimizers[1].state[right]["exp_avg"]),
                ("second_moment", optimizers[0].state[left]["exp_avg_sq"], optimizers[1].state[right]["exp_avg_sq"])):
                max_differences[name] = max(max_differences.get(name, 0), float((x - y).abs().max()))
                torch.testing.assert_close(x, y, rtol=2e-6, atol=1e-7)
    del ordinary, fused, optimizers
    measurements = []
    for use_fused in (False, True):
        parameter = torch.nn.Parameter(torch.full((50_000_000,), 0.5))
        parameter.grad = torch.full_like(parameter, 0.125)
        optimizer = torch.optim.AdamW([parameter], **options, fused=use_fused)
        durations = []
        for _ in range(4):
            start = time.perf_counter()
            optimizer.step()
            durations.append(time.perf_counter() - start)
        measurements.append({"parameters": parameter.numel(), "fused": use_fused,
            "seconds": durations, "steady_median_seconds": statistics.median(durations[1:])})
        del optimizer, parameter
    print(json.dumps({"status": "PASS", "torch": torch.__version__, "cpu_threads": 4,
        "numerical_control_updates": 5, "max_absolute_differences": max_differences,
        "benchmark": measurements,
        "training_processes_modified": False, "cuda_allocated": False,
        "limits": "CPU kernel only; excludes transfers, model compute and checkpoint handoff. Floating-point agreement does not imply bitwise-equivalent future training."}, indent=2))


if __name__ == "__main__":
    main()
