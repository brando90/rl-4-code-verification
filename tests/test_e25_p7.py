"""Tests for experiment 25 expt_v2/p7_stats.py: Spearman helper and the ladder logic on synthetic measurement files."""
import importlib.util
import json
import math
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[1] / 'experiments' / '25_checkpoint_reuse_for_rho_h_law' / 'expt_v2' / 'p7_stats.py'


def _load():
    spec = importlib.util.spec_from_file_location('p7_stats', P)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _cell(q, rho, h):
    return {'q_mixed_empirical': q, 'rho': rho, 'H': h}


def test_spearman_monotone_and_constant():
    m = _load()
    assert m.spearman([1, 2, 3, 4], [10, 20, 35, 90]) == pytest.approx(1.0)
    assert m.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert m.spearman([1, 2, 3], [5, 5, 5]) is None


def test_ladder_lists_below_bar_and_never_fits_them(tmp_path):
    m = _load()
    m.R = tmp_path
    tags = [t for lad in m.LADDERS.values() for t, _ in lad['cells']]
    for i, t in enumerate(sorted(set(tags))):
        env = {'good': _cell(0.5, math.exp(5 + i), 0.1 * (i + 1)), 'floor': _cell(0.05, 10.0, 0.01)}
        (tmp_path / f'{t}_measure.json').write_text(json.dumps({'envs': env}))
    m.main()
    out = json.loads((tmp_path / 'p7_q2.json').read_text())
    d = out['D_at_fixed_N_3.4B']['envs']
    assert d['floor']['n_measurable'] == 0 and len(d['floor']['below_bar_cells']) == 5
    assert 'log_rho' not in d['floor']
    assert d['good']['n_measurable'] == 5
    assert out['D_at_fixed_N_3.4B']['cells_not_run'] == []


def test_missing_checkpoint_reported_not_run(tmp_path):
    m = _load()
    m.R = tmp_path
    (tmp_path / 'q1_3p4b_base_measure.json').write_text(json.dumps({'envs': {'good': _cell(0.5, 100.0, 0.3)}}))
    m.main()
    out = json.loads((tmp_path / 'p7_q2.json').read_text())
    assert 'q2a_25b' in out['N_at_compute_optimal_D']['cells_not_run']
