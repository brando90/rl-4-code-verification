"""Authored end-to-end controller sequencing without scientific measurements or device calls."""
import copy
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys

import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_learning_driver',PHASE/'learning_driver.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(tmp_path,monkeypatch,arm='A',phase='pilot'):
    run={'phase':phase,'arm':arm,'run_seed':1301 if phase=='pilot' else 13011,'execution_lock':{'sha256':'execution-sha'},'repository':'authored'}
    ledger=tmp_path/'ledger';root=ledger/phase/arm/str(run['run_seed']);root.mkdir(parents=True)
    config_path=tmp_path/'configuration.json';config_path.write_text('{}')
    theta=tmp_path/'theta.json';theta.write_text('[0,0,0]')
    config={'runtime':{'initial_model':'authored-model'},'initial_model_manifest':{'sha256':'initial-sha'},
            'initial_abilities':m.reference(theta),'stage_seconds':dict.fromkeys(m.DEVICE,300),'environment':{}}
    execution={'configuration':{'ledger':str(ledger)}}
    leases=tmp_path/'leases';leases.mkdir();events=[];count=[0];decisions={}
    plan={'run':run,'configuration':str(config_path),'resources':{'lease_root':str(leases)},'watchdog_root':'authored','watchdog_run':'authored'}
    monkeypatch.setattr(m,'authorize',lambda _:({},execution,config));monkeypatch.setattr(m,'admit',lambda _:None)
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**k:None);monkeypatch.setattr(m,'snapshot',lambda _: {})
    monkeypatch.setattr(m,'stage_cost',lambda *a,**k:{'stage':k['stage'],'authored':True})
    monkeypatch.setattr(m,'check_preflight',lambda _:None)
    monkeypatch.setattr(m,'published',lambda ref,repo:decisions[ref['name']])
    def reserve(plan,*,update,stage_key,seconds):
        count[0]+=1;lease={'id':str(count[0]),'status':'RELEASED'}
        (leases/(lease['id']+'.json')).write_text(json.dumps(lease));events.append((update,stage_key))
        return {'status':'RESERVED','lease':lease}
    monkeypatch.setattr(m,'reserve',reserve)
    def materialize(config,state,run,root,key,lease):
        d=Path(root)/key;d.mkdir();(d/'health').mkdir();(d/'health/preflight.json').write_text('{}')
        (d/'runtime.json').write_text('{}');(d/'output').mkdir()
        if key=='update':(d/'output/result.json').write_text('{"status":"MEASURED"}')
        return d/'runtime.json'
    monkeypatch.setattr(m,'materialize',materialize)
    monkeypatch.setattr(m,'reserve_stage',lambda root,**kw:Path(root)/'authored-reservation')
    monkeypatch.setattr(m,'launch',lambda _: {'status':'RUNTIME_EXITED_ZERO','cleanup_verified':True})
    monkeypatch.setattr(m,'retire',lambda *a,**k:events.append((a[1]['completed_updates'],'retention')))
    monkeypatch.setattr(m,'prefix',lambda config,state,run,root:events.append((state['update'],'prefix')))
    monkeypatch.setattr(m,'score',lambda config,run,root:events.append((int(Path(root).name.split('_')[1]),'score')))
    monkeypatch.setattr(m,'ability',lambda *a:{'admitted':True,'abilities':[0,0,0]})
    def finish(state,run,root):
        state=dict(state);state['completed_updates']=state['update'];state['generated_tokens']+=512
        state['optimizer_updates']+=1;state['group_index']+=32
        if run['phase']=='main':state['boundary_index']+=1
        return state
    monkeypatch.setattr(m,'finish',finish)
    return plan,config,root,events,decisions


def monitor_value(plan,config,update,status='CONTINUE'):
    return {'condition':'v2-S2','gate':'PILOT_MONITOR','arm':plan['run']['arm'],'run_seed':plan['run']['run_seed'],
            'update':update,'execution_sha256':'execution-sha','model_binding_sha256':'initial-sha','status':status}


def test_A_pilot_waits_at30_and_only_published_T5_can_extend_once_to60(tmp_path,monkeypatch):
    plan,config,root,events,decisions=fixture(tmp_path,monkeypatch)
    state=m.tick(plan)
    assert state['status']=='WAIT_FOR_T5' and state['completed_updates']==30
    assert len([r for r in events if r[1]=='update'])==30 and not (root/'terminal.json').exists()
    plan['T5_results']={'30':{'name':'extension'}}
    decisions['extension']={'condition':'v2-S2','gate':'T5','horizon':30,'pilot_execution_sha256':'execution-sha',
                            'admission_statistics_computed':True,'status':'EXTEND_TO_60'}
    state=m.tick(plan);assert state['status']=='WAIT_FOR_T5' and state['completed_updates']==60
    assert len([r for r in events if r[1]=='update'])==60
    plan['T5_results']['60']={'name':'final'};decisions['final']={**decisions['extension'],'horizon':60,'status':'FAIL'}
    state=m.tick(plan);assert state['status']=='COMPLETE' and (root/'terminal.json').exists()
    before=list(events);assert m.tick(plan)==state and events==before


def test_B_cannot_start_before_own_baseline_and_stops_after_monitor10(tmp_path,monkeypatch):
    plan,config,root,events,decisions=fixture(tmp_path,monkeypatch,'B')
    state=m.tick(plan);assert state['status']=='WAIT_FOR_MONITOR' and events==[(0,'preflight')]
    plan['monitor_results']={'0':{'name':'baseline'}};decisions['baseline']=monitor_value(plan,config,0)
    state=m.tick(plan);assert state['status']=='WAIT_FOR_MONITOR' and state['completed_updates']==10
    plan['monitor_results']['10']={'name':'stop'};decisions['stop']=monitor_value(plan,config,10,'STOP_ARM')
    state=m.tick(plan);assert state['status']=='HALTED' and (root/'terminal.json').exists()
    assert len([r for r in events if r[1]=='update'])==10


def test_C_failed_refit_stops_before_generation11_with_no_stale_weights(tmp_path,monkeypatch):
    plan,config,root,events,decisions=fixture(tmp_path,monkeypatch,'C')
    plan['monitor_results']={str(i):{'name':str(i)} for i in (0,10)}
    decisions.update({str(i):monitor_value(plan,config,i) for i in (0,10)})
    monkeypatch.setattr(m,'ability',lambda *a:{'admitted':False,'abilities':None})
    state=m.tick(plan)
    assert state['status']=='HALTED' and state['completed_updates']==10
    assert (11,'generate') not in events and (11,'prefix') not in events


def test_main_closes_at_four_common_token_boundaries_and_does_not_replay(tmp_path,monkeypatch):
    plan,config,root,events,decisions=fixture(tmp_path,monkeypatch,phase='main')
    state=m.tick(plan)
    assert state['status']=='COMPLETE' and state['boundary_index']==4 and state['next_stage']=='evaluation_pending'
    before=list(events);assert m.tick(plan)==state and events==before


def test_interrupted_running_stage_requires_receipt_recovery_not_redispatch(tmp_path,monkeypatch):
    plan,config,root,events,decisions=fixture(tmp_path,monkeypatch,'B')
    state=m.tick(plan);state['status']='RUNNING';(root/'state.json').write_text(json.dumps(state));before=list(events)
    result=m.tick(plan);assert result['status']=='RECOVERY_REQUIRED' and events==before


def test_zero_exit_with_unresolved_cleanup_halts_before_prefix(tmp_path,monkeypatch):
    plan,config,root,events,decisions=fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(m,'launch',lambda _: {'status':'RUNTIME_EXITED_ZERO','cleanup_verified':False})
    state=m.tick(plan)
    assert state['status']=='HALTED' and state['failed_stage']=='preflight'
    assert events==[(0,'preflight')] and (root/'terminal.json').exists()


def test_monitor_from_another_export_cannot_authorize_next_update(tmp_path,monkeypatch):
    plan,config,root,events,decisions=fixture(tmp_path,monkeypatch,'B')
    state=m.tick(plan);before=list(events)
    plan['monitor_results']={'0':{'name':'wrong'}}
    decisions['wrong']={**monitor_value(plan,config,0),'model_binding_sha256':'different-export'}
    with pytest.raises(ValueError,match='another checkpoint'):m.tick(plan)
    assert events==before and json.loads((root/'state.json').read_text())['status']=='WAIT_FOR_MONITOR'
