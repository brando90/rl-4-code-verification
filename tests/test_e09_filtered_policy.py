"""TLDR: Numerical controls for exact native sampling, support failure, and masked gradients."""
import ast
import importlib.util
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
E = Path(__file__).resolve().parents[1] / "experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/expt_v1"
spec = importlib.util.spec_from_file_location("filtered_policy", E / "filtered_policy.py")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


def native_filter():
    # Repository checkout and runtime are siblings, not committed dependencies.
    path = Path(__file__).resolve().parents[2] / "nemo_rl/.venv/lib/python3.12/site-packages/vllm/v1/sample/ops/topk_topp_sampler.py"
    if not path.is_file():
        pytest.skip("pinned vLLM runtime unavailable")
    tree = ast.parse(path.read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "apply_top_k_top_p")
    env = {"torch": torch, "Optional": __import__('typing').Optional}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(path), "exec"), env)
    return env[fn.name]


def test_exact_native_support_and_probabilities():
    torch.manual_seed(191)
    cases = [torch.randn(5, 97), torch.zeros(2, 97),
             torch.arange(97).float().repeat(2, 1) * 100,
             torch.full((1, 97), -1000.),
             torch.cat((torch.zeros(1, 80), torch.ones(1, 17)), dim=1)]
    native = native_filter()
    for raw in cases:
        scaled = raw.float() / .6
        before = raw.clone()
        rng = torch.random.get_rng_state().clone()
        expected = native(scaled.clone(), torch.full((len(raw),), 20),
                          torch.full((len(raw),), .95)).log_softmax(-1)
        actual = policy.filtered_logprobs(raw)
        assert torch.equal(torch.isfinite(actual), torch.isfinite(expected))
        assert torch.equal(actual, expected)
        assert torch.equal(before, raw)
        assert torch.equal(rng, torch.random.get_rng_state())
        assert torch.allclose(actual.exp().sum(-1), torch.ones(len(raw)))


def test_support_disagreement_blocks_and_inactive_values_are_finite():
    logits = torch.arange(25.).repeat(1, 3, 1).requires_grad_()
    ids = torch.tensor([[24, 0, 24]])
    mask = torch.tensor([[1, 0, 1]])
    got = policy.selected_logprobs(logits, ids, mask)
    assert got[0, 1] == 0 and torch.isfinite(got).all()
    got.sum().backward()
    assert torch.equal(logits.grad[0, 1], torch.zeros(25))
    assert torch.isfinite(logits.grad).all()
    with pytest.raises(policy.SupportMismatch):
        policy.selected_logprobs(logits, ids, torch.ones_like(mask))


def test_piecewise_gradient_matches_finite_difference():
    z = torch.linspace(-4, 4, 50).reshape(1, 50).requires_grad_()
    logq = policy.filtered_logprobs(z)[0, 49]
    logq.backward()
    eps = .001
    for j in (0, 38, 49):
        plus, minus = z.detach().clone(), z.detach().clone()
        plus[0, j] += eps
        minus[0, j] -= eps
        numerical = (policy.filtered_logprobs(plus)[0, 49] - policy.filtered_logprobs(minus)[0, 49]) / (2 * eps)
        assert torch.allclose(z.grad[0, j], numerical, atol=.002, rtol=.002)


def test_temperature_exactly_once_and_dynamic_support():
    z = torch.linspace(-1, 1, 51).reshape(1, 51)
    once = policy.filtered_logprobs(z)
    twice = policy.filtered_logprobs(z / .6)
    assert not torch.equal(once, twice)
    changed = z.clone()
    changed[0, 50] = -10
    assert torch.isfinite(once[0, 50])
    assert not torch.isfinite(policy.filtered_logprobs(changed)[0, 50])


def test_sampler_profile_exemption_cannot_leak_to_real_requests(monkeypatch):
    import sys
    path = E / 'adapters/vllm_v010_sampler.py'
    tree = ast.parse(path.read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_e09_profile_call')
    env = {'sys': sys}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(path), 'exec'), env)
    monkeypatch.setenv('E09_ENGINE_INITIALIZING', '1')
    assert not env['_e09_profile_call']()
    code = 'def _dummy_sampler_run():\n    return _e09_profile_call()\n'
    exec(compile(code, '/test/vllm/v1/worker/gpu_model_runner.py', 'exec'), env)
    assert env['_dummy_sampler_run']()
    exec(compile(code, '/test/not_the_native_runner.py', 'exec'), env)
    assert not env['_dummy_sampler_run']()
