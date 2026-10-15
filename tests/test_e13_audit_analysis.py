"""Retain fixed train mutations, missing coverage and every actual reward increase in audit summaries."""
import copy
import importlib.util
from pathlib import Path
import sys

import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_audit_analysis',PHASE/'audit_analysis.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture():
    cells=[];cpu=[];coverage=[]
    for index in range(32):
        for variant in m.VARIANTS:
            cell={'cell_id':f'{index}/{variant}','audit_id':str(index),'task_id':f'authored_{index}','split':'train','variant':variant}
            cells.append(cell)
            parts={'e':1,'n_examples':1,'raw_vacuity_hits':[],'d':{'numerator':1,'denominator':2},
                   't':1,'p':{'numerator':1,'denominator':2}}
            if variant=='padding':parts.update(d={'numerator':9,'denominator':10},p={'numerator':9,'denominator':10})
            cpu.append({**cell,'strict_status':'measured','strict':0,'components':parts,
                        'hidden_test_coverage':.5,'cleanup_verified':True})
            coverage.append({**cell,'formal_specification_coverage':.5 if variant=='original' else .4})
    return {'condition':'v2-S2','declared_tasks':32,'cells':cells},cpu,coverage


def test_all_reward_increases_are_reported_with_strict_and_coverage_changes():
    inputs,cpu,coverage=fixture();weights={c['task_id']:[1/3]*3 for c in inputs['cells']}
    result=m.evaluate(inputs,cpu,coverage,C_weights=weights)
    assert len(result['comparisons'])==96 and len(result['reward_increasing_mutations'])==64
    for row in result['reward_increasing_mutations']:
        assert row['variant']=='padding' and row['arm'] in ('B','C') and row['strict']==0
        assert row['formal_specification_coverage']==pytest.approx(-.1) and row['theorem_count']==8
    assert not result['learning_admitted'] and not result['independent_checks_functioning']


def test_missing_outcomes_remain_declared_and_do_not_fabricate_a_reward_delta():
    inputs,cpu,coverage=fixture();cpu[0].update(strict_status='unresolved',strict=None,components=None,hidden_test_coverage=None)
    coverage[0]['formal_specification_coverage']=None
    result=m.evaluate(inputs,cpu,coverage)
    assert result['declared']==128 and len(result['reward_increasing_mutations'])==31 and not result['C_evaluated']
    first=result['comparisons'][0]
    assert first['reward_changes']['B'] is None and first['formal_specification_coverage'] is None
    original=result['by_variant']['original']['formal_specification_coverage']
    assert original['measured']==31 and original['missing']==1 and original['mean_bounds']==[15.5/32,16.5/32]


def test_wrong_identity_or_duplicate_inventory_cannot_be_joined():
    inputs,cpu,coverage=fixture();coverage[0]['task_id']='wrong'
    with pytest.raises(ValueError,match='identity'):m.evaluate(inputs,cpu,coverage)
    inputs,cpu,coverage=fixture()
    with pytest.raises(ValueError,match='inventories'):m.evaluate(inputs,cpu,coverage+[coverage[0]])


def test_cleanup_and_C_availability_remain_explicit():
    inputs,cpu,coverage=fixture();cpu[1]['cleanup_verified']=False
    result=m.evaluate(inputs,cpu,coverage)
    assert result['cleanup_unresolved']==1 and not result['C_evaluated']
    with pytest.raises(ValueError,match='exactly'):m.evaluate(inputs,cpu,coverage,C_weights={})


def test_claimed_measured_components_require_the_actual_strict_label():
    inputs,cpu,coverage=fixture();cpu[0]['strict']=None
    with pytest.raises(ValueError,match='invalid strict'):m.evaluate(inputs,cpu,coverage)
