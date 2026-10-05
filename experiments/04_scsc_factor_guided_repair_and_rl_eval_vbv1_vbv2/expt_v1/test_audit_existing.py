"""Check missing-data, declared-denominator, duplicate-cell and immutable-input safeguards."""
import json
from pathlib import Path
import pytest
from audit_existing import read_inputs, summarize

DECLARED={'condition':'original','models':{'model_a':{},'absent_model':{}}}

def row(**kwargs):
    return dict(benchmark='vbv1_896', model='model_a', task='easy_set__t', cell_status='measured', **kwargs)

def test_missing_is_not_zero_and_absent_models_remain():
    gs=summarize([row(IC_tests=None,IC_proofs=None,FSC=None)],DECLARED)
    target=next(g for g in gs if g['model']=='model_a' and g['panel']=='core_614')
    assert target['known_zero_per_artifact_product']==0
    assert target['absent_from_snapshot']==613
    assert sum(g['absent_from_snapshot'] for g in gs)==1791

def test_observed_zero_does_not_invent_other_factors():
    g=next(g for g in summarize([row(IC_tests=0,IC_proofs=None,FSC=None)],DECLARED) if g['saved_rows'])
    assert g['known_zero_per_artifact_product']==1
    assert g['all_factors_present']==0
    assert g['supplied_scsc_present']==0

def test_duplicates_rejected_but_recovery_separate():
    r=row(IC_tests=1,IC_proofs=1,FSC=1)
    with pytest.raises(ValueError,match='Duplicate'): summarize([r,r],DECLARED)
    groups=summarize([r,dict(r,condition='recovery_1')],DECLARED)
    assert len([g for g in groups if g['saved_rows']])==2

def test_out_of_range_scores_rejected():
    with pytest.raises(ValueError,match='Invalid'): summarize([row(FSC=5)],DECLARED)

def test_changed_input_rejected(tmp_path):
    (tmp_path/'input_manifest.json').write_text(json.dumps({'inputs':[{'name':'x','snapshot':'x.json','sha256':'incorrect'}]}))
    (tmp_path/'x.json').write_text('{}')
    with pytest.raises(ValueError,match='hash mismatch'): read_inputs(tmp_path)
