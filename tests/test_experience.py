"""Tests for rho/H measurement: the paper's identities (Eq. 2-9) and basic invariances."""

import math

import numpy as np
import pytest

from rl4cv.experience import (
    Response,
    binary_raw_mass,
    effective_coverage,
    group_masses,
    groups_from_records,
    loo_advantages,
    measure_environment,
    q_mixed,
    top_decile_share,
)


def test_loo_advantages_sum_to_zero_and_match_definition():
    r = [1.0, 0.0, 0.0, 1.0, 0.5]
    a = loo_advantages(r)
    assert a.sum() == pytest.approx(0.0, abs=1e-12)
    for i, ri in enumerate(r):
        others = [x for j, x in enumerate(r) if j != i]
        assert a[i] == pytest.approx(ri - np.mean(others))


@pytest.mark.parametrize("G", [2, 4, 8, 16])
def test_binary_raw_mass_identity_eq8(G):
    for k in range(G + 1):
        group = [Response(1.0 if i < k else 0.0, 100) for i in range(G)]
        raw, adm, _ = group_masses(group)
        assert raw == pytest.approx(binary_raw_mass(k, G))
        assert adm == pytest.approx(raw)
    assert binary_raw_mass(0, G) == 0.0 and binary_raw_mass(G, G) == 0.0


def test_expected_raw_mass_is_2Gp1mp():
    G, p = 8, 0.3
    expected = sum(math.comb(G, k) * p**k * (1 - p) ** (G - k) * binary_raw_mass(k, G) for k in range(G + 1))
    assert expected == pytest.approx(2 * G * p * (1 - p))


def test_q_mixed_eq3():
    assert q_mixed(0.5, 8) == pytest.approx(1 - 2 / 256)
    assert q_mixed(0.0, 8) == 0.0 and q_mixed(1.0, 8) == 0.0
    p = np.array([0.1, 0.5])
    assert np.allclose(q_mixed(p, 8), 1 - p**8 - (1 - p) ** 8)


def test_capped_response_stays_in_baseline_but_loses_loss_weight():
    group = [Response(1.0, 12288, admitted=False)] + [Response(0.0, 500) for _ in range(7)]
    raw, adm, tok = group_masses(group)
    # Success advantage = 1 - 0 = 1 (masked); each failure = 0 - 1/7.
    assert raw == pytest.approx(1 + 7 * (1 / 7))
    assert adm == pytest.approx(7 * (1 / 7))
    assert tok == pytest.approx(7 * (1 / 7) * 500)


def test_effective_coverage_bounds_and_invariance():
    assert effective_coverage([1, 1, 1, 1]) == pytest.approx(1.0)
    assert effective_coverage([5, 0, 0, 0]) == pytest.approx(0.25)
    assert effective_coverage([0, 0, 0]) == 0.0
    m = np.array([0.2, 3.0, 1.0, 0.0, 0.7])
    h = effective_coverage(m)
    assert 1 / m.size <= h <= 1
    assert effective_coverage(7.5 * m) == pytest.approx(h)


def test_top_decile_share():
    assert top_decile_share([10] + [0] * 19) == pytest.approx(1.0)
    assert top_decile_share([1] * 20) == pytest.approx(0.1)


def test_measure_environment_rho_H_and_eq9_decomposition():
    groups = [
        [Response(1, 1000), Response(0, 2000), Response(0, 3000, admitted=False), Response(1, 1000)],
        [Response(0, 500), Response(0, 500), Response(0, 500), Response(0, 500)],
        [Response(1, 800), Response(1, 800), Response(0, 1200), Response(1, 800, admitted=False)],
    ]
    m = measure_environment(groups)
    raws, adms = zip(*[group_masses(g)[:2] for g in groups])
    tokens = sum(r.generated_tokens for g in groups for r in g)
    assert m.rho == pytest.approx(1e6 * sum(adms) / tokens)
    assert m.rho_raw == pytest.approx(1e6 * sum(raws) / tokens)
    assert m.rho == pytest.approx(m.rho_raw * m.advantage_survival)  # Eq. 9
    assert m.H == pytest.approx(effective_coverage(adms))
    assert m.q_mixed_empirical == pytest.approx(2 / 3)
    assert m.admission_rate == pytest.approx(10 / 12)
    assert m.n_groups == 3 and m.n_responses == 12


def test_groups_from_records_preserves_order_and_fields():
    recs = [
        {"task_id": "b", "reward": 1, "generated_tokens": 10, "admitted": True},
        {"task_id": "a", "reward": 0, "generated_tokens": 20, "admitted": False},
        {"task_id": "b", "reward": 0, "generated_tokens": 30},
    ]
    groups = groups_from_records(recs)
    assert [len(g) for g in groups] == [2, 1]
    assert groups[1][0].admitted is False and groups[0][1].admitted is True
