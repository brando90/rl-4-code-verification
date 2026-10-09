"""TLDR: Declared-cell coverage, endpoint isolation, adjacent H and missingness controls."""
import sys
from pathlib import Path

import pytest

E = Path(__file__).resolve().parents[1] / 'experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/expt_v1'
sys.path.insert(0, str(E))
import matrix_e09 as matrix


def declared():
    return matrix.manifest({'validation': [f'v{i}' for i in range(135)],
                            'test': [f't{i}' for i in range(222)]})


def test_complete_null_matrix_and_before_after_denominators():
    rows = declared()
    summary = matrix.summarize(rows)
    assert summary['counts']['validation'] == {'declared': 945, 'measured': 0, 'missing': 945}
    assert summary['counts']['test'] == {'declared': 1554, 'measured': 0, 'missing': 1554}
    assert len(summary['before_after']) == 2142
    assert matrix.FIELDS.index('H') == matrix.FIELDS.index('S') + 1
    assert all(r['H'] is None and r['FSC'] is None for r in rows)
    assert summary['paired_H'][0]['per_seed']['20261008']['full_denominator_missingness_bounds'] == [-1, 1]


def test_unfrozen_endpoint_and_duplicate_cells_rejected():
    rows = declared()
    row = {**rows[0], 'checkpoint_sha256': 'not_frozen', 'status': 'measured', 'H': 0, 'S': 0}
    with pytest.raises(ValueError, match='Endpoint not frozen'):
        matrix.reconcile(rows, [row])
    rows[0]['checkpoint_sha256'] = 'frozen'
    row['checkpoint_sha256'] = 'frozen'
    assert matrix.reconcile(rows, [row])[0]['H'] == 0
    with pytest.raises(ValueError, match='Duplicate'):
        matrix.reconcile(rows, [row, row])


def test_regression_and_zero_to_one_are_distinct():
    rows = declared()
    baseline = next(r for r in rows if r['policy'] == 'baseline')
    endpoint = next(r for r in rows if r['policy'] == 'A_20261008')
    baseline['H'], endpoint['H'] = 1, 0
    result = matrix.before_after(rows)[0]
    assert result['regression'] is True and result['H_transition'] == '1->0'
