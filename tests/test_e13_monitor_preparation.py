"""Check the monitor's separate paired seeds, fixed train cohort and pre-response C weights."""
import importlib.machinery
import importlib.util
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_monitor_preparation',PHASE/'monitor_preparation.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture():
    tasks=[f'authored_{i:02d}' for i in range(40)]
    cohort={'condition':'v2-S2','cells':[{'audit_id':str(i),'task_id':task,'group_id':str(i),'split':'train'} for i,task in enumerate(tasks[:32])]}
    prompts={task:{'task_id':task,'split':'train','prompt_token_ids':[12,13],'required_paths':['solution.lean']} for task in tasks}
    models={key:{'a':[1.]*40,'b':[.1*i]*40} for i,key in enumerate(('d','t','p'))}
    return tasks,cohort,prompts,models


def test_separate_monitor_randomness_is_paired_across_arms_and_checkpoints():
    tasks,cohort,prompts,models=fixture();snapshots=[]
    for arm,update in [('B',0),('B',10),('C',0),('C',20)]:
        value=m.prepare(cohort,prompts,tasks,arm=arm,run_seed=1301,update=update,models=models,abilities=[0,0,0])
        snapshots.append(value)
    assert len({tuple(c['seed'] for c in s['cells']) for s in snapshots})==1
    assert len({tuple(c['cell_id'] for c in s['cells']) for s in snapshots})==4
    for cell in snapshots[-1]['cells']:
        assert len(cell['weights'])==3 and min(cell['weights'])>0 and sum(cell['weights'])==pytest.approx(1)
    assert all(s['learning_rollout_tokens']==0 and s['frozen_before_generation'] for s in snapshots)


def test_monitor_never_substitutes_missing_rewards_or_fits_to_its_outputs():
    tasks,cohort,prompts,models=fixture()
    snapshot=m.prepare(cohort,prompts,tasks,arm='C',run_seed=1301,update=10,models=models,abilities=[0,0,0])
    rows=[{**c,'status':'measured','strict':0,'cleanup_verified':True,'e':1,'n_examples':1,'raw_vacuity_hits':[],
           'd':{'numerator':1,'denominator':2},'t':1,'p':{'numerator':1,'denominator':2}} for c in snapshot['cells']]
    rows[0].update(status='unresolved_measurement',strict=None)
    result=m.reward_rows(snapshot,rows)
    assert result[0]['reward'] is None and result[0]['theorem_count'] is None
    assert all(r['formal_specification_coverage'] is None and r['hidden_test_coverage'] is None for r in result)
    assert result[1]['reward']==m.weighted_reward(rows[1],snapshot['cells'][1]['weights'],0)


def test_changed_cohort_and_unresolved_cleanup_are_rejected():
    tasks,cohort,prompts,models=fixture();cohort['cells'][0]['split']='test'
    with pytest.raises(ValueError,match='train split'):m.prepare(cohort,prompts,tasks,arm='B',run_seed=1301,update=0)
    tasks,cohort,prompts,models=fixture();snapshot=m.prepare(cohort,prompts,tasks,arm='B',run_seed=1301,update=0)
    rows=[{**c,'status':'unresolved_measurement','cleanup_verified':False} for c in snapshot['cells']]
    with pytest.raises(ValueError,match='cleanup'):m.reward_rows(snapshot,rows)
