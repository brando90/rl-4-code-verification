"""Retain exact failed and missing validation cells without changing gate cohorts."""
import importlib.util
from pathlib import Path
import sys
import pytest

HERE = Path(__file__).resolve().parents[1] / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3'
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('e08_coverage', HERE / 'analyze_validation.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def test_partial_coverage_keeps_known_failed_and_missing_cells():
    rows = [{'task_id': 't', 'sample_idx': 0, 'status': 'scored'},
            {'task_id': 't', 'sample_idx': 1, 'status': 'failed', 'error': 'native timeout'}]
    cells = m.coverage_rows(rows, ['t'])
    assert len(cells) == 8 and sum(c['known'] for c in cells) == 1
    assert cells[1]['status'] == 'failed' and cells[1]['error'] == 'native timeout'
    assert all(c['status'] == 'missing' and not c['known'] for c in cells[2:])


@pytest.mark.parametrize('rows', [
    [{'task_id': 't', 'sample_idx': 0}] * 2,
    [{'task_id': 'foreign', 'sample_idx': 0}],
    [{'task_id': 't', 'sample_idx': 8}],
])
def test_coverage_rejects_duplicates_and_extras(rows):
    with pytest.raises(ValueError, match='Duplicate or extra'):
        m.coverage_rows(rows, ['t'])
