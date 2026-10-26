"""Cover NeMo's actual single-rank gradient receipt representation and malformed alternatives."""
import importlib.util
from pathlib import Path
import pytest

PATH = Path(__file__).resolve().parents[1] / 'phase2/gates.py'
spec = importlib.util.spec_from_file_location('v3_gates', PATH)
gates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gates)


@pytest.mark.parametrize('value, expected', [([0.0], 0.0), ([.125], .125), (.25, .25)])
def test_actual_rank_receipts(value, expected):
    assert gates.single_rank_gradient(value) == expected


@pytest.mark.parametrize('value', [[], [1, 2], [[1]], None, True, float('nan'), [float('inf')], -1])
def test_invalid_gradients(value):
    with pytest.raises(ValueError): gates.single_rank_gradient(value)
