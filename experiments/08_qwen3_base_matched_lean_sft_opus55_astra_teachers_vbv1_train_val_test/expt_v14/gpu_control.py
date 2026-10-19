"""Run a bounded disposable GB10 CUDA forward/backward control without downloading a model."""
import argparse
import json
from pathlib import Path
import platform
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = {'observed_unix': time.time(), 'host': platform.node(), 'machine': platform.machine(),
              'status': 'FAILED', 'model_training_started': False, 'model_downloaded': False}
    try:
        import torch
        result.update(torch_version=torch.__version__, cuda_runtime=torch.version.cuda,
                      cuda_available=torch.cuda.is_available(), compiled_arches=torch.cuda.get_arch_list())
        assert result['cuda_available'], 'CUDA unavailable'
        result.update(device=torch.cuda.get_device_name(0), capability=torch.cuda.get_device_capability(0))
        assert tuple(result['capability']) == (12, 1), 'Unexpected GPU; this control is for GB10'
        torch.manual_seed(0)
        start = time.monotonic()
        x = torch.randn((512, 512), device='cuda', dtype=torch.bfloat16, requires_grad=True)
        weight = torch.nn.Parameter(torch.randn((512, 512), device='cuda', dtype=torch.bfloat16))
        optimizer = torch.optim.AdamW([weight], lr=1e-4)
        before = weight.detach().float().clone()
        loss = (x @ weight).float().square().mean()
        loss.backward()
        assert torch.isfinite(loss) and torch.isfinite(x.grad).all() and torch.isfinite(weight.grad).all()
        optimizer.step()
        torch.cuda.synchronize()
        assert not torch.equal(before, weight.detach().float()), 'Optimizer did not modify weights'
        result.update(status='PASS', forward_backward_optimizer=True, loss=float(loss.detach()),
                      elapsed_seconds=time.monotonic()-start,
                      peak_allocated_bytes=torch.cuda.max_memory_allocated())
    except Exception as exc:
        result['error'] = f'{type(exc).__name__}: {exc}'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result['status']=='PASS' else 1)


if __name__ == '__main__':
    main()
