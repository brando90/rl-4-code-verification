"""Experiment 16: GINC-style generator and exact verifier (numpy only, no torch)."""

import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "16_toy_env_generation_ginc_hmm_rho_h_law" / "expt_v1"))

from ginc_toy import V, EnvSpec, make_concept, make_prompts, next_symbol_dist, sample_sequences  # noqa: E402

from rl4cv.experience import Response, measure_environment  # noqa: E402


def brute_force_next(c, x):
    """p(x_{l+1} | x_{1:l}) by summing over every hidden path."""
    l = len(x)
    joint = np.zeros(V)
    for h in itertools.product(range(c.S), repeat=l):
        p = c.pi[h[0]] * c.B[h[0], x[0]]
        for t in range(1, l):
            p *= c.T[h[t - 1], h[t]] * c.B[h[t], x[t]]
        joint += p * (c.T[h[-1]] @ c.B)
    return joint / joint.sum()


def test_forward_matches_brute_force():
    c = make_concept(3, 4.0, seed=5)
    rng = np.random.default_rng(0)
    x = sample_sequences(c, 4, 5, rng)
    fast = next_symbol_dist(c, x)
    for i in range(4):
        np.testing.assert_allclose(fast[i], brute_force_next(c, x[i]), rtol=1e-9, atol=1e-12)


def test_sampler_matches_emission_marginal():
    c = make_concept(4, 2.0, seed=1)
    x = sample_sequences(c, 50_000, 1, np.random.default_rng(1))
    empirical = np.bincount(x[:, 0], minlength=V) / x.shape[0]
    np.testing.assert_allclose(empirical, c.pi @ c.B, atol=0.01)


def test_prompts_are_deterministic_and_labels_are_bayes_argmax():
    spec = EnvSpec("t", 4, 4.0, 3, 6)
    a, b = make_prompts(spec, 200, seed=3), make_prompts(spec, 200, seed=3)
    assert (a.x == b.x).all() and (a.y == b.y).all()
    assert a.x.shape == (200, 6) and a.y.min() >= 0 and a.y.max() < V
    assert ((a.bayes_acc > 0) & (a.bayes_acc <= 1)).all()


def test_rho_h_plumbing_for_one_token_binary_groups():
    groups = [[Response(r, 1, True) for r in row] for row in ([1, 0, 0, 0], [1, 1, 0, 0], [0, 0, 0, 0])]
    m = measure_environment(groups)
    assert m.q_mixed_empirical == 2 / 3
    assert 0 < m.H < 1 and m.rho > 0

# Night 2 lives in a separate module namespace so Night 1 evidence is unchanged.
from importlib import import_module
v2 = import_module('experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v2.ginc')


def test_multitoken_forward_matches_hidden_path_enumeration():
    c = v2.make_concept(2, 2., 17)
    x = np.array([[1, 3]])
    y = np.array([[2, 4, 1, 0]])
    conditional, logjoint = v2.forward_scores(c, x, y)
    prefix = x[0].tolist()
    for t in range(4):
        expected = brute_force_next(c, prefix)[y[0,t]]
        np.testing.assert_allclose(conditional[0,t], expected, rtol=1e-10)
        prefix.append(int(y[0,t]))
    np.testing.assert_allclose(np.exp(logjoint[0]), conditional.prod(), rtol=1e-12)
    labels, lp = v2.oracle_continuation(c, x)
    assert labels.shape == (1,4)
    np.testing.assert_allclose(lp, v2.forward_scores(c, x, labels)[1])


def test_mixture_determinism_and_entropy_does_not_change_data():
    a = v2.EnvSpec('a', 2, 2., 3, 5)
    b = v2.EnvSpec('b', 3, 4., 2, 5)
    m = v2.Mixture('m', (a,b), (.3,.7))
    p = v2.make_prompts(m, 100, 81, entropy=True)
    q = v2.make_prompts(m, 100, 81, entropy=False)
    np.testing.assert_array_equal(p.x, q.x)
    np.testing.assert_array_equal(p.y, q.y)
    np.testing.assert_array_equal(p.concept_idx, q.concept_idx)
    assert np.isfinite(p.entropy_mc).all()
    assert np.all(p.oracle_logprob <= 0)
    assert (p.concept_idx < 3).any() and (p.concept_idx >= 3).any()


def test_four_token_reward_and_token_accounting():
    labels = np.array([[1,2,3,4]])
    actions = np.array([[[1,2,3,4],[1,2,0,0],[0,0,0,0]]])
    partial, joint = v2.rewards(actions, labels)
    np.testing.assert_array_equal(partial, [[1.,.5,0.]])
    np.testing.assert_array_equal(joint, [[1.,0.,0.]])
    m = measure_environment([[Response(float(r),4,True) for r in partial[0]]])
    assert m.total_generated_tokens == 12


def test_exact_kl_value_gradient_and_reference_frozen():
    import pytest
    torch = pytest.importorskip('torch')
    pol = import_module('experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v2.policy')
    logits = torch.tensor([[.3,-.7,1.1]], dtype=torch.float64, requires_grad=True)
    ref = torch.tensor([[-.2,.4,.8]], dtype=torch.float64, requires_grad=True)
    kl = pol.exact_kl(logits,ref).sum()
    p, q = logits.softmax(-1), ref.softmax(-1)
    torch.testing.assert_close(kl, (p * (p.log()-q.log())).sum())
    assert torch.autograd.gradcheck(lambda z: pol.exact_kl(z,ref), (logits,))
    kl.backward()
    assert ref.grad is None and logits.grad.abs().sum() > 0
    same = logits.detach().clone().requires_grad_()
    zero = pol.exact_kl(same,same.detach()).sum()
    zero.backward()
    assert abs(zero.item()) < 1e-12 and same.grad.abs().max() < 1e-12


def test_multitoken_grpo_has_policy_gradient_and_kl_at_all_positions():
    import pytest
    torch = pytest.importorskip('torch')
    from copy import deepcopy
    pol = import_module('experiments.16_toy_env_generation_ginc_hmm_rho_h_law.expt_v2.policy')
    torch.set_num_threads(1)
    torch.manual_seed(3)
    model = pol.TinyLM(*pol.SCALES['n1'])
    ref = deepcopy(model)
    for p in ref.parameters(): p.requires_grad_(False)
    prompts = v2.make_prompts(v2.BASE[0], 3, 17)
    actions = pol.generate(model,prompts.x,4,torch.Generator().manual_seed(5))
    actions[:,0] = prompts.y
    reward,_ = v2.rewards(actions,prompts.y)
    loss,kl = pol.rollout_loss(model,ref,prompts.x,actions,reward)
    assert abs(kl.item()) < 1e-6
    loss.backward()
    assert sum(p.grad.abs().sum() for p in model.parameters()) > 0
    assert all(p.grad is None for p in ref.parameters())


def test_mixture_proposals_depend_only_on_stable_probe_order():
    rows=[{'env':s.name,'rho':100.+i,'H':.5+i/50} for i,s in enumerate(v2.BASE)]
    a=v2.propose_mixtures(rows)
    b=v2.propose_mixtures(list(reversed(rows)))
    assert [m.to_dict() for m in a] == [m.to_dict() for m in b]
    assert [m.name for m in a] == ['m00','m01','m02','m03']
    assert [len(m.components) for m in a] == [3,5,8,12]
    assert all(np.isclose(sum(m.weights),1.) for m in a)
    assert all(c.length != 10 and c.n_concepts == 64 for m in a for c in m.components)
