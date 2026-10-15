"""Verify paired-seed inference, multiplicity and full-denominator missingness on authored outcomes."""
import importlib.util
from pathlib import Path
import sys
import numpy as np
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
spec=importlib.util.spec_from_file_location('e13_selected_test_analysis',PHASE/'selected_test_analysis.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_exact_seed_resolution_and_frozen_holm_family():
    assert m.sign_swap([.1,.1,.1])['p_value']==.25
    assert m.sign_swap([0,0,0])['p_value']==1
    assert m.holm({'B-A':.25,'C-A':.5})=={'B-A':.5,'C-A':.5}
    assert m.holm({'B-A':.25,'C-A':None})=={'B-A':.5,'C-A':None}
    assert m.holm({'B-A':.25})=={'B-A':.25}
    with pytest.raises(ValueError):m.sign_swap([.1,.2])


def test_unbiased_pass_k_and_missing_outcomes_keep_declared16():
    assert m.pass_k(1,4)==.25 and m.pass_k(1,16)==1 and m.pass_k(0,16)==0
    values=np.zeros((3,222,16));values[:,:,0]=1
    result=m.summarize(values,list(range(222)))
    assert result['pass_at_k']['1']['mean']==1/16 and result['pass_at_k']['4']['mean']==.25
    values[0,0,0]=np.nan;missing=m.summarize(values,list(range(222)))
    assert missing['missing']==1 and missing['declared']==3*222*16 and missing['strict_mean'] is None
    assert missing['strict_mean_bounds'][1]==1/16 and missing['pass_at_k']['16']['mean'] is None


def test_shared_pairing_cancels_task_difficulty_in_bootstrap():
    tasks=[{'group_id':'same' if i<2 else 'other'} for i in range(3)]
    right=np.zeros((3,3,16));right[:,0,:]=1
    left=right+.125
    result=m.contrast(left,right,tasks,[0,1,2],bootstrap_seed=1302301)
    assert result['mean_difference']==.125 and result['confidence_interval_95']==[.125,.125]
    assert result['p_value']==.25 and result['bootstrap_draws']==10000
    assert result['paired_task_seed_improvements']==9


def test_missing_pair_keeps_sharp_bounds_without_a_fabricated_p_value():
    left=np.ones((3,2,16));right=np.zeros_like(left);left[0,0,0]=np.nan
    result=m.contrast(left,right,[{'group_id':'a'},{'group_id':'b'}],[0,1],bootstrap_seed=1302301)
    assert result['paired_common_cohort_mean']==1 and result['paired_observed']==95
    assert result['full_manifest_difference_bounds']==[95/96,1]
    assert result['p_value'] is None and result['confidence_interval_95'] is None


def full_fixture():
    tasks=[{'task_id':f'authored_{i}','group_id':f'group_{i//2}','domain':'core' if i<152 else 'IndustrySet','split':'test'} for i in range(222)]
    rows=[{'condition':'v2-S2','split':'test','arm':arm,'run_seed':seed,'boundary':4,
           'task_id':task['task_id'],'sample_idx':sample,'strict':sample%2}
          for arm in ['A','B','P'] for seed in m.SEEDS for task in tasks for sample in range(16)]
    return tasks,rows


def test_every_slot_is_required_and_one_selected_checkpoint_per_run():
    tasks,rows=full_fixture();values=m.validate(rows,tasks,['A','B','P'])
    assert set(values)=={'A','B','P'} and values['A'].shape==(3,222,16)
    with pytest.raises(ValueError,match='terminal receipt'):m.validate(rows[:-1],tasks,['A','B','P'])
    rows[1]['boundary']=3
    with pytest.raises(ValueError,match='multiple selected'):m.validate(rows,tasks,['A','B','P'])


def test_full_report_retains_domains_gated_C_and_failed_point_forecast():
    tasks,rows=full_fixture();result=m.evaluate(rows,tasks,['A','B','P'])
    assert result['primary_contrasts']==['B-A'] and not result['confirmatory_claim_admitted']
    assert result['populations']['core']['arms']['A']['tasks']==152
    assert result['populations']['IndustrySet']['arms']['A']['tasks']==70
    assert result['populations']['pooled']['arms']['A']['confidence_interval_95']==[.5,.5]
    assert result['populations']['pooled']['contrasts']['B-A']['holm_adjusted_p']==1
    assert result['F3']['B-A']['observed_minus_prediction']==-.02
    assert result['F3']['C-A']['status']=='UNAVAILABLE' and result['H5'].startswith('unresolved')


def test_failed_run_without_selection_remains_fully_declared_and_unmeasured():
    tasks,rows=full_fixture()
    for row in rows:
        if row['arm']=='B' and row['run_seed']==13011:
            row.update(boundary=None,strict=None,status='not_evaluated',reason='main run halted before checkpoint selection')
    values=m.validate(rows,tasks,['A','B','P'])
    assert np.isnan(values['B'][0]).all() and np.isfinite(values['B'][1:]).all()
    summary=m.summarize(values['B'],list(range(222)))
    assert summary['declared']==10656 and summary['missing']==3552 and summary['strict_mean'] is None
    rows[3]['boundary']=None
    with pytest.raises(ValueError,match='identity changed'):m.validate(rows,tasks,['A','B','P'])
