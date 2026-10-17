"""Check complete pilot resource denominators and a ceiling independent of outcomes."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'phase2'))
from resource_plan import project


def test_full_paired_and_extension_projection():
    result = project(2., .5, .01, 40e9, 9e9, 100e6)
    assert result['maximum_updates'] == 240
    assert result['maximum_validation_cells'] == 8640
    assert result['projected_device_hours'] == (240 * 2.5 + 1080 * .01) * 1.25
    assert result['device_hour_budget'] == 2100
    assert result['projected_storage_bytes'] == (18 * 40e9 + 9 * 9e9 + 240 * 100e6) * 1.25
    assert result['api_spend_usd'] == 0


def test_ceiling_does_not_increase_to_fit_a_slow_measurement():
    result = project(10., 2., 1., 1, 1, 1)
    assert result['projected_device_hours'] > result['device_hour_budget'] == 2100


@pytest.mark.parametrize('missing', [None, float('nan'), float('inf'), 0, -1, True])
def test_missing_or_invalid_cost_is_not_zero(missing):
    with pytest.raises(ValueError): project(missing, .5, .01, 40e9, 9e9, 100e6)
