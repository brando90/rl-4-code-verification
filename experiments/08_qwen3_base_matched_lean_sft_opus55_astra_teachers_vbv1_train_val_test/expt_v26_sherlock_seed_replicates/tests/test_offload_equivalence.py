"""HostAdamW (the 4B arm's optimizer path) must give bit-identical parameters to in-place AdamW on the same device.

Runs on CPU: a tiny tied-embedding language model, expt_v4's AdamW hyperparameters, warmup+cosine schedule, token-weighted
two-microbatch loss and clipping, 60 updates. On Sherlock the only further difference is CPU vs CUDA elementwise rounding.
usage: python -m pytest tests/test_offload_equivalence.py   (or python tests/test_offload_equivalence.py)
"""
from pathlib import Path
import sys

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import train_v26  # noqa: E402


class Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.emb = torch.nn.Embedding(50, 16)
        self.mix = torch.nn.Linear(16, 16)
        self.norm = torch.nn.LayerNorm(16)

    def forward(self, ids, labels):
        h = self.norm(torch.tanh(self.mix(self.emb(ids))))
        logits = h @ self.emb.weight.T
        return torch.nn.functional.cross_entropy(logits[:-1], labels[1:], ignore_index=-100)


def run(host):
    torch.manual_seed(0)
    model = Tiny()
    optimizer = train_v26.make_optimizer(model, host)
    scheduler = train_v26.make_scheduler(optimizer)
    data = torch.Generator().manual_seed(1)
    lrs, norms = [], []
    for _ in range(60):
        model.zero_grad(set_to_none=True)
        batch = [torch.randint(0, 50, (int(torch.randint(5, 12, (1,), generator=data)),), generator=data) for _ in range(2)]
        prompts = [int(torch.randint(1, 4, (1,), generator=data)) for _ in range(2)]
        denominator = sum(len(ids) - p for ids, p in zip(batch, prompts))
        for ids, p in zip(batch, prompts):
            labels = ids.clone()
            labels[:p] = -100
            (model(ids, labels) * ((len(ids) - p) / denominator)).backward()
        norms.append(float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)))
        lrs.append(optimizer.param_groups[0]["lr"])
        optimizer.step()
        scheduler.step()
    return model, optimizer, lrs, norms


def test_host_adamw_bit_identical():
    ref, _, lrs_ref, norms_ref = run(host=False)
    off, opt, lrs_off, norms_off = run(host=True)
    assert lrs_ref == lrs_off and norms_ref == norms_off
    for (name, a), b in zip(ref.named_parameters(), off.parameters()):
        assert torch.equal(a, b), name
    for p, m in zip(opt.params, opt.master):
        assert torch.equal(p.detach(), m.detach()) and p.data_ptr() != m.data_ptr()
    assert lrs_ref[0] == 2e-5 * 0.05 and abs(lrs_ref[20] - 2e-5) < 1e-12


if __name__ == "__main__":
    test_host_adamw_bit_identical()
    print("PASS test_host_adamw_bit_identical")
