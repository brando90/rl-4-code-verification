"""TLDR: Unit tests for experiment 20's GRPO objective: group advantages are zero for constant groups and standardized otherwise, the importance weight is truncated at 2 and detached, the clipped surrogate matches the asymmetric clip by hand, token normalization sums over micro-batches, and the truncated-support recomputation reproduces temperature/top-k/top-p log-probabilities and flags out-of-support tokens."""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/expt_v1/loss_e20.py"
spec = importlib.util.spec_from_file_location("loss_e20", SRC)
L = importlib.util.module_from_spec(spec)
sys.modules["loss_e20"] = L
spec.loader.exec_module(L)


def test_group_advantages():
    r = torch.tensor([[0., 0., 0., 0.], [1., 0., 0., 0.], [1., 1., 1., 1.]])
    a = L.group_advantages(r)
    assert torch.all(a[0] == 0) and torch.all(a[2] == 0)
    assert a[1, 0] > 0 and torch.all(a[1, 1:] < 0) and abs(float(a[1].sum())) < 1e-5


def test_importance_weights_truncated_and_detached():
    lt = torch.tensor([0.0, -1.0, -3.0], requires_grad=True)
    ls = torch.tensor([-1.0, -1.0, -1.0])
    w = L.importance_weights(lt, ls)
    assert torch.allclose(w, torch.tensor([2.0, 1.0, math.exp(-2.0)])) and not w.requires_grad


def test_clipped_surrogate_asymmetric():
    logp_old = torch.zeros(4)
    logp = torch.log(torch.tensor([0.5, 1.0, 1.5, 1.2]))
    adv = torch.tensor([1.0, 1.0, 1.0, -1.0])
    s = L.clipped_surrogate(logp, logp_old, adv)
    # ratio 0.5 with A>0: min(0.5, 0.8) = 0.5; ratio 1.5 with A>0: min(1.5, 1.28) = 1.28; ratio 1.2 with A<0: min(-1.2, -1.2) = -1.2
    assert torch.allclose(s, torch.tensor([0.5, 1.0, 1.28, -1.2]), atol=1e-6)


def test_token_normalized_loss_adds_over_micro_batches():
    sur = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    w = torch.ones_like(sur)
    mask = torch.tensor([[1.0, 1.0], [1.0, 0.0]])
    total = float(mask.sum())
    whole = L.token_normalized_loss(sur, w, mask, total)
    parts = L.token_normalized_loss(sur[:1], w[:1], mask[:1], total) + L.token_normalized_loss(sur[1:], w[1:], mask[1:], total)
    assert torch.allclose(whole, parts) and abs(float(whole) + 6.0 / 3.0) < 1e-6


def test_truncated_logprobs_matches_hand_computation():
    logits = torch.tensor([[2.0, 1.0, 0.0, -5.0]])
    T, k, p = 0.5, 3, 0.9
    z = logits / T
    full = torch.log_softmax(z, -1)[0]
    out = L.truncated_logprobs(logits, torch.tensor([1]), T, k, p)
    assert torch.allclose(out["logp_full"], full[1:2])
    # top-3 = tokens 0,1,2 (z = 4, 2, 0): probs within top-3
    pr = torch.softmax(z[0, :3], -1)
    cum = pr.cumsum(0)
    keep = (cum - pr) < p
    expected = math.log(float(pr[1])) - math.log(float((pr * keep).sum()))
    assert keep[1] and abs(float(out["logp_truncated"][0]) - expected) < 1e-6 and bool(out["in_support"][0])
    out2 = L.truncated_logprobs(logits, torch.tensor([3]), T, k, p)  # token 3 is outside the top-k
    assert not bool(out2["in_support"][0]) and float(out2["logp_truncated"][0]) == float("-inf")
    summary = L.mismatch_summary(torch.tensor([-1.0, -2.0, -3.0]), torch.tensor([-1.0, -2.1, -3.0]), torch.tensor([True, True, False]))
    assert summary["abs_delta_gt_tol"] == 1 and summary["outside_support"] == 1 and abs(summary["share_gt_tol"] - 2 / 3) < 1e-9
