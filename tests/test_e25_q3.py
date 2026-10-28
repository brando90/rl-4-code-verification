"""Unit tests for experiment 25's Q3 (P8) curve-extrapolation script and P6 helper on synthetic curves; CPU only."""
import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip('scipy')
_P = Path(__file__).resolve().parents[1] / 'experiments/25_checkpoint_reuse_for_rho_h_law/expt_v2'
sys.path.insert(0, str(_P))
import q3_p8 as q  # noqa: E402


def test_sigmoid_curve_is_extrapolated_well():
    t = np.arange(1, 101, dtype=float)
    y = q.sigmoid(t, 0.8, np.log(15.0), 0.7)
    r = q.evaluate(t, y)
    assert r['mae_over_range_sigmoid'] <= 0.10
    assert r['n_fit'] >= 4 and r['n_test'] >= 4


def test_flat_curve_returns_none():
    t = np.arange(1, 101, dtype=float)
    assert q.evaluate(t, np.full(100, 0.3)) is None


def test_shift_handles_negative_rewards():
    t = np.arange(1, 101, dtype=float)
    y = q.sigmoid(t, 0.8, np.log(15.0), 0.7) - 1.0
    assert q.evaluate(t, y, shift=True)['mae_over_range_sigmoid'] <= 0.10


def test_saturating_fit_recovers_form():
    t = np.arange(5, 55, dtype=float)
    a, t0 = q.fit_sat(t, 0.6 * t / (t + 9.0))
    assert abs(a - 0.6) < 0.02 and abs(t0 - 9.0) < 1.0
