"""Verify A6's B extension preserves monitor inputs, scoring, stops and publication chronology."""
from pathlib import Path
import ast
import copy
import json
import sys
import pytest

P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P))
import a6_monitor_points as points
import a6_monitor_preparation as preparation
import a6_monitor_runtime as runtime
import a6_monitor_snapshot as snapshot
import a6_monitor_decision as decision
import a6_monitor_measurements as measurements
import test_e13_monitor_preparation as old_preparation
import test_e13_monitor_runtime as old_runtime
import test_e13_monitor_snapshot as old_snapshot
import test_e13_monitor_decision as old_decision


def test_all_seven_checkpoints_keep_the_same_cohort_prompts_and_paired_seeds():
    tasks,cohort,prompts,_=old_preparation.fixture()
    baseline=None
    for update in range(0,61,10):
        value=preparation.prepare(cohort,prompts,tasks,arm='B',run_seed=1301,update=update)
        if update<=30:
            assert value==old_preparation.m.prepare(cohort,prompts,tasks,arm='B',run_seed=1301,update=update)
        paired=[{k:v for k,v in c.items() if k not in ('cell_id','update')} for c in value['cells']]
        if baseline is None:baseline=paired
        assert paired==baseline and value['learning_rollout_tokens']==0
        assert runtime.validate(value,{'arm':'B','run_seed':1301,'update':update})==value['cells']
    for arm,seed,update in [('C',1301,0),('A',1301,40),('B',1302,40),('B',1301,70),('B',1301,40.)]:
        with pytest.raises(ValueError,match='undeclared'):
            preparation.prepare(cohort,prompts,tasks,arm=arm,run_seed=seed,update=update)


def test_extension_requires_published_b_own_reward_decision_for_same_execution(monkeypatch):
    value={'condition':'v2-S2','gate':'T5','arm':'B','seeds':[1301],'metric':'own train reward',
           'horizon':30,'status':'EXTEND_TO_60','admission_statistics_computed':True,'pilot_execution_sha256':'execution'}
    calls=[]
    monkeypatch.setattr(points,'published',lambda ref,repo:(calls.append((ref,repo)) or value))
    points.require_extension(30,None,'repo','execution');assert not calls
    with pytest.raises(ValueError,match='published'):points.require_extension(40,None,'repo','execution')
    for update in (40,50,60):points.require_extension(update,{'name':'extension'},'repo','execution')
    for key,bad in [('arm','A'),('metric','strict'),('horizon',60),('status','PASS'),('pilot_execution_sha256','other')]:
        prior=value[key];value[key]=bad
        with pytest.raises(ValueError,match='differs'):points.require_extension(40,{},'repo','execution')
        value[key]=prior


def test_extension_snapshot_freezes_once_and_cannot_generate_without_decision(tmp_path,monkeypatch):
    monkeypatch.setattr(old_snapshot,'m',snapshot)
    plan,config,root,state=old_snapshot.fixture(tmp_path,monkeypatch)
    plan['learning']['run']['repository']='authored'
    state['completed_updates']=40;old_snapshot.put(root/'state.json',state)
    with pytest.raises(ValueError,match='published'):snapshot.freeze(plan)
    assert not (root/'monitors').exists()
    state['T5_extension']={'name':'extension'};old_snapshot.put(root/'state.json',state)
    monkeypatch.setattr(points,'published',lambda *_:{'condition':'v2-S2','gate':'T5','arm':'B','seeds':[1301],
        'metric':'own train reward','horizon':30,'status':'EXTEND_TO_60','admission_statistics_computed':True,
        'pilot_execution_sha256':'execution'})
    result=snapshot.freeze(plan);lock=json.loads(Path(result['lock']).read_text())
    assert lock['update']==40 and result['model_calls']==0
    assert lock['controller_state_sha256']==snapshot.digest(root/'state.json')
    with pytest.raises(FileExistsError):snapshot.freeze(plan)


def test_original_generator_and_changed_input_guards_remain(tmp_path,monkeypatch):
    monkeypatch.setattr(old_runtime,'m',runtime)
    for name in ('test_monitor_uses_unchanged_generator_and_zero_learning_tokens',
                 'test_modified_cells_rejected_before_generator_or_device_verification'):
        root=tmp_path/name;root.mkdir();getattr(old_runtime,name)(root,monkeypatch)


def test_extension_measurements_preserve_original_statistics_and_stop_rule(tmp_path,monkeypatch):
    # Source identity checks below also establish that baseline/measurement functions are unchanged.
    monkeypatch.setattr(old_decision,'join',measurements)
    _,base=old_decision.fixture(tmp_path/'base',update=0)
    _,current=old_decision.fixture(tmp_path/'current',update=60,denominator=1)
    rows=decision.read_checked(current['rows'])
    monkeypatch.setattr(decision,'published',lambda *_:current)
    assert decision.measurement({},'authored',execution_sha='execution',arm='B',run_seed=1301,update=60)[1]==rows
    initial=decision.read_checked(base['rows'])
    manifest=[{k:r[k] for k in ('audit_id','task_id','group_id','split')} for r in initial]
    availability={k:{'baseline':decision.read_checked(base['availability'])[k],
                    'current':decision.read_checked(current['availability'])[k]} for k in decision.COVERAGE}
    value=decision.evaluate(initial,rows,manifest,arm='B',run_seed=1301,update=60,coverage_availability=availability)
    assert value['status']=='STOP_ARM' and 'theorem_count' in value['stop_metrics']


def test_scientific_scoring_and_unchanged_controller_functions_are_preserved():
    changed={'monitor_preparation':{'prepare'},'monitor_runtime':{'validate','run'},
             'monitor_snapshot':{'freeze'},'monitor_supervisor':{'authorize','launch'},
             'monitor_coverage':{'helper','validate'},'monitor_decision':{'run'},
             'monitor_hosted':{'load'},'monitor_publication':{'decision_lock'}}
    for name in ('monitor_preparation','monitor_runtime','monitor_snapshot','monitor_supervisor',
                 'monitor_coverage','monitor_decision','monitor_hosted','monitor_measurements',
                 'monitor_processing','monitor_driver','monitor_publication'):
        before=ast.parse((P/(name+'.py')).read_text());after=ast.parse((P/('a6_'+name+'.py')).read_text())
        old={n.name:ast.dump(n,include_attributes=False) for n in before.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        new={n.name:ast.dump(n,include_attributes=False) for n in after.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        assert old.keys()==new.keys()
        for key in old.keys()-changed.get(name,set()):
            # A renamed import inside a function changes routing only, not its body operations.
            normalized=new[key].replace('a6_monitor_', 'monitor_').replace('a6_learning_', 'learning_')
            assert old[key]==normalized,(name,key)
