"""Never impute unknown coverage; allow only mathematically identified composites."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'phase2'))
from scsc_bounds import bounds
from scsc_bounds import attach
import hashlib
import json


def test_known_zero_determines_composite_without_imputing_coverage():
    assert bounds(0, 1, None) == [0., 0.]
    assert bounds(1, 0, None) == [0., 0.]
    assert bounds(None, None, 0) == [0., 0.]


def test_positive_local_factors_do_not_determine_unknown_coverage():
    assert bounds(1, 1, None) == [0., 1.]
    assert bounds(1, .125, None) == [0., .5]
    assert bounds(None, None, None) == [0., 1.]


def test_fully_observed_product():
    assert bounds(1, .5, .25) == [.5, .5]


@pytest.mark.parametrize('bad', [True, -1, 1.01, float('nan'), float('inf')])
def test_invalid_factor_rejected(bad):
    with pytest.raises(ValueError): bounds(1, bad, None)


def fixture(root):
    attempt = root / '00000/attempt_1'
    oracle = attempt / 'evidence/oracle'
    mechanical = oracle / 'ladder/train/scored'
    mechanical.mkdir(parents=True)
    source = b'example : True := True.intro\n'
    sha = hashlib.sha256(source).hexdigest()
    (attempt / 'solution.lean').write_bytes(source)
    (oracle / 'oracle.json').write_text(json.dumps({'compile': True, 'source_sha256': sha}))
    (mechanical / 'scored_fixture_g8.jsonl').write_text(json.dumps({'status': 'scored', 'IC_tests': 1, 'IC_proofs': .125}))
    return {'rows': [{'status': 'measured', 'attempts': 1, 'compile': True, 'source_sha256': sha},
                     {'status': 'deterministic_resource_limit'}]}


def test_bound_evidence_retains_unknown_cells(tmp_path):
    result = attach(fixture(tmp_path), tmp_path)
    assert result['official_SCSC_summary']['mean_bounds'] == [0, .75]
    assert result['official_SCSC_summary']['mean'] is None
    assert result['official_SCSC_summary']['known_composites'] == 0
    assert result['rows'][0]['official_factor_evidence']['oracle_sha256']


def test_changed_candidate_cannot_supply_official_factors(tmp_path):
    scores = fixture(tmp_path)
    (tmp_path / '00000/attempt_1/solution.lean').write_text('changed')
    with pytest.raises(ValueError): attach(scores, tmp_path)
