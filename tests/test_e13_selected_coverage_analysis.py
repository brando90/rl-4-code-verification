"""Preserve continuous coverage, independent missingness and unbounded theorem-count uncertainty on authored data."""
from pathlib import Path
import sys
import numpy as np
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
import selected_coverage_analysis as m


def test_actual_paired_group_bootstrap_preserves_constant_continuous_difference():
    tasks=[{'group_id':'first'},{'group_id':'first'},{'group_id':'second'}]
    right=np.array([[.1,.4,.6],[.2,.5,.7],[.3,.6,.8]])
    result=m.difference(right+.125,right,tasks,[0,1,2],bounded=True,bootstrap_seed=1302301)
    assert result['confidence_interval_95']==[.125,.125]
    assert result['mean_difference']==.125 and result['paired_observed']==9
    assert result['noninferiority_established'] is False


def fixture(monkeypatch):
    tasks=[{'task_id':f'authored_{i}','group_id':f'group_{i//2}','split':'test','domain':'core' if i<152 else 'IndustrySet'} for i in range(222)]
    rows=[{'condition':'v2-S2','split':'test','arm':arm,'run_seed':seed,'task_id':task['task_id'],
        'sample_idx':0,'boundary':4,'formal_specification_coverage':.375 if arm=='B' else .25,
        'hidden_test_coverage':.25 if arm=='B' else .5,'theorem_count':2 if arm=='B' else 3}
        for arm in ['A','B','P'] for seed in m.SEEDS for task in tasks]
    monkeypatch.setattr(m,'bootstrap_means',lambda values,*a,**kw:[float(values.mean())]*2)
    return rows,tasks


def test_continuous_means_and_opposite_independent_effects_do_not_claim_noninferiority(monkeypatch):
    rows,tasks=fixture(monkeypatch);out=m.evaluate(rows,tasks,['A','B','P'])
    formal=out['populations']['pooled']['formal_specification_coverage'];hidden=out['populations']['pooled']['hidden_test_coverage']
    assert formal['arms']['B']['full_manifest_mean']==.375
    assert formal['contrasts']['B-A']['mean_difference']==.125
    assert hidden['contrasts']['B-A']['mean_difference']==-.25
    assert out['populations']['pooled']['theorem_count']['contrasts']['B-A']['mean_difference']==-1
    assert not out['noninferiority_established'] and not formal['contrasts']['B-A']['noninferiority_established']
    assert formal['arms']['A']['declared']==666 and out['populations']['IndustrySet']['hidden_test_coverage']['arms']['A']['declared']==210


def test_missing_formal_route_does_not_erase_hidden_measurement_or_fill_with_zero(monkeypatch):
    rows,tasks=fixture(monkeypatch)
    for row in rows:row['formal_specification_coverage']=None
    out=m.evaluate(rows,tasks,['A','B','P']);formal=out['populations']['pooled']['formal_specification_coverage']
    assert formal['arms']['A']['full_manifest_mean'] is None and formal['arms']['A']['full_manifest_mean_bounds']==[0,1]
    assert formal['contrasts']['B-A']['full_manifest_difference_bounds']==[-1,1]
    assert formal['contrasts']['B-A']['confidence_interval_95'] is None
    assert out['populations']['pooled']['hidden_test_coverage']['contrasts']['B-A']['mean_difference']==-.25


def test_missing_theorem_counts_have_no_invented_finite_upper_bound(monkeypatch):
    rows,tasks=fixture(monkeypatch)
    for row in rows:
        if row['arm']=='B':row['theorem_count']=None
    out=m.evaluate(rows,tasks,['A','B','P'])['populations']['pooled']['theorem_count']
    assert out['arms']['B']['full_manifest_mean_bounds']==[0,None] and out['arms']['B']['upper_bound_unbounded']
    assert out['contrasts']['B-A']['full_manifest_difference_bounds']==[-3,None]
    assert out['contrasts']['B-A']['upper_bound_unbounded'] and out['contrasts']['B-A']['paired_observed']==0
    values=m.validate(rows,tasks,['A','B','P'])['theorem_count']
    reverse=m.difference(values['A'],values['B'],tasks,list(range(222)),bounded=False,bootstrap_seed=1302301)
    assert reverse['full_manifest_difference_bounds']==[None,3] and reverse['lower_bound_unbounded']


@pytest.mark.parametrize('changed',['sample','duplicate','missing_metric','checkpoint','fraction'])
def test_changed_sample_identity_or_population_cannot_be_analyzed(monkeypatch,changed):
    rows,tasks=fixture(monkeypatch)
    if changed=='sample':rows[0]['sample_idx']=1
    elif changed=='duplicate':rows[-1]=dict(rows[0])
    elif changed=='missing_metric':rows[0].pop('hidden_test_coverage')
    elif changed=='checkpoint':rows[0]['boundary']=3
    else:rows[0]['formal_specification_coverage']=1.1
    with pytest.raises(ValueError):m.evaluate(rows,tasks,['A','B','P'])


def test_failed_run_retains_all_222_fixed_samples_and_no_inferential_estimate(monkeypatch):
    rows,tasks=fixture(monkeypatch)
    for row in rows:
        if row['arm']=='A' and row['run_seed']==13011:
            row.update(boundary=None,status='not_evaluated',reason='authored failed run')
            row.update(dict.fromkeys(m.METRICS))
    out=m.evaluate(rows,tasks,['A','B','P'])['populations']['pooled']['formal_specification_coverage']
    assert out['arms']['A']['declared']==666 and out['arms']['A']['missing']==222
    assert out['contrasts']['B-A']['paired_observed']==444 and out['contrasts']['B-A']['mean_difference'] is None
