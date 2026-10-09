"""TLDR: Mask, sparse-support and gradient controls for the prospective NeMo loss."""
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip('torch')
pytest.importorskip('nemo_rl')
E = Path(__file__).resolve().parents[1] / 'experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/expt_v1'
sys.path.insert(0, str(E))
from filtered_policy import selected_logprobs, SupportMismatch
from filtered_loss import FilteredGRPOLoss


def fixture():
    scaled = torch.linspace(-5, 5, 50).repeat(2, 6, 1).requires_grad_()
    ids = torch.tensor([[0, 49, 48, 0, 49, 47], [0, 49, 48, 0, 49, 47]])
    mask = torch.tensor([[0, 1, 1, 0, 1, 1]]).repeat(2, 1)
    q = selected_logprobs(scaled[:, :-1], ids[:, 1:], mask[:, 1:]).detach()
    padded = torch.cat((torch.zeros(2, 1), q), dim=1)
    data = dict(input_ids=ids, token_mask=mask, sample_mask=torch.ones(2),
                advantages=torch.tensor([[1.] * 6, [-1.] * 6]),
                prev_logprobs=padded.clone(), generation_logprobs=padded.clone())
    cfg = dict(reference_policy_kl_penalty=0, token_level_loss=True,
               use_importance_sampling_correction=False, ratio_clip_c=None,
               ratio_clip_min=.2, ratio_clip_max=.2)
    return scaled, data, FilteredGRPOLoss(cfg)


def test_assistant_only_gradient_and_no_masked_nan():
    scaled, data, loss_fn = fixture()
    for key in ('prev_logprobs', 'generation_logprobs'):
        data[key][~data['token_mask'].bool()] = float('nan')
    loss, metrics = loss_fn(scaled, data, torch.tensor(2), torch.tensor(8))
    assert torch.isfinite(loss)
    loss.backward()
    assert torch.isfinite(scaled.grad).all()
    assert torch.all(scaled.grad[:, 2] == 0)  # Predicts user-feedback target.
    assert torch.all(scaled.grad[:, 5] == 0)  # Last position has no next token.
    assert scaled.grad[:, 0].abs().sum() > 0
    assert metrics['e09_generation_logprob_max_error'] == 0


@pytest.mark.parametrize('failure', ['generation', 'current', 'support', 'sample_drop', 'nonfinite'])
def test_probability_and_support_negative_controls(failure):
    scaled, data, loss_fn = fixture()
    if failure == 'generation':
        data['generation_logprobs'][0, 1] += .2
    elif failure == 'current':
        data['prev_logprobs'][0, 1] += .02
        data['generation_logprobs'][0, 1] += .02
    elif failure == 'support':
        data['input_ids'][0, 1] = 0
    elif failure == 'sample_drop':
        data['sample_mask'][0] = 0
    else:
        data['generation_logprobs'][0, 1] = -float('inf')
    with pytest.raises((SupportMismatch, AssertionError)):
        loss_fn(scaled, data, torch.tensor(2), torch.tensor(8))


def test_chunked_probabilities_and_gradients_match_dense():
    from filtered_policy import filtered_logprobs
    z = torch.randn(2, 5, 70, requires_grad=True)
    targets = z.detach().argmax(-1)
    mask = torch.ones_like(targets)
    sparse = selected_logprobs(z, targets, mask, chunk_size=2)
    dense = filtered_logprobs(z.reshape(-1, 70), already_scaled=True).gather(1, targets.reshape(-1, 1)).reshape(2, 5)
    assert torch.allclose(sparse, dense, atol=1e-6)
    gs = torch.autograd.grad(sparse.sum(), z, retain_graph=True)[0]
    gd = torch.autograd.grad(dense.sum(), z)[0]
    assert torch.allclose(gs, gd, atol=1e-6)


def test_read_only_probability_replay_cannot_enter_optimizer(monkeypatch):
    scaled, data, loss_fn = fixture()
    monkeypatch.setenv('E09_PROB_DIAGNOSTIC_DIR', '/unused/deterministic-test')
    with pytest.raises(AssertionError, match='must never optimize'):
        loss_fn(scaled, data, torch.tensor(2), torch.tensor(8))
