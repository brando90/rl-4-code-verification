"""TLDR: Test fail-closed GPU ownership, bounded v4 restarts, cron isolation and the launch-only probe."""
from pathlib import Path
from types import SimpleNamespace
import json
import pytest
from device_guard import eligible,ensure_idle,census,check,Busy
from autoresume_watchdog import decide,live,trajectory_state,tick,ProbeError
from install_watchdog import cron_text
from maximum_length_probe import probe


@pytest.mark.parametrize('host,index,expected',[('skampere1',0,True),('skampere1',5,True),('skampere1',7,True),
    ('skampere1',1,False),('skampere2',4,True),('skampere3',7,True),('other',0,False)])
def test_authorized_devices(host,index,expected):assert eligible(host,index)==expected


def test_idle_means_no_process_even_same_user_or_zero_memory():
    assert ensure_idle('skampere1',0,{0:'GPU-a'},[])=='GPU-a'
    with pytest.raises(Busy):ensure_idle('skampere1',0,{0:'GPU-a'},[('GPU-a',1)])
    with pytest.raises(Busy):ensure_idle('skampere1',0,{0:'GPU-a'},[],reservations=[{'status':'ACTIVE','index':0}],now=1)


@pytest.mark.parametrize('stdout,code',[('bad',0),('',1),('0, GPU-a\n0, GPU-a',0)])
def test_probe_fails_closed(stdout,code):
    with pytest.raises(Busy):census(lambda *a,**kw:SimpleNamespace(returncode=code,stdout=stdout,stderr='error'))


def test_guard_owned_only_and_unreadable_foreign_is_busy(tmp_path,monkeypatch):
    lease={'owner':'e13v4','host':'skampere3','status':'ACTIVE','index':2,'uuid':'GPU-a','id':'v4-test','expires_unix':100}
    path=tmp_path/'lease.json';path.write_text(json.dumps(lease))
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','2');monkeypatch.setenv('E13V4_EXECUTION_ID','v4-test');monkeypatch.setenv('HF_HUB_OFFLINE','1')
    def run(cmd,**kw):return SimpleNamespace(returncode=0,stdout='2, GPU-a' if '--query-gpu=index,uuid' in cmd else 'GPU-a, 123',stderr='')
    assert check({'lease_path':path},host='skampere3',now=2,run=run,read_environment=lambda pid:b'E13V4_EXECUTION_ID=v4-test\0')==lease
    with pytest.raises(Busy):check({'lease_path':path},host='skampere3',now=2,run=run,read_environment=lambda pid:b'E13_EXECUTION_ID=v3\0')
    def denied(pid):raise PermissionError()
    with pytest.raises(Busy):check({'lease_path':path},host='skampere3',now=2,run=run,read_environment=denied)


def test_watchdog_transitions_no_resampling():
    args=dict(live=False,complete=False,partials=[],restarts={},next_update=1)
    assert decide(**args)==('launch',1)
    args['live']=True;assert decide(**args)==('skip',None);args['live']=False
    p={'update':1,'generations':1,'scored':False,'optimizer_result':False,'pre_state_bound':False}
    args['partials']=[p];assert decide(**args)==('diagnose',1)
    p['generations']=0;assert decide(**args)==('archive_then_launch',1)
    p.update(generations=256,scored=True,pre_state_bound=True)
    assert decide(**args)==('replay_saved_then_launch',1)
    p['optimizer_result']=True;assert decide(**args)==('account_then_launch',1)
    args['restarts']={'1':3};assert decide(**args)==('diagnose',1)


def test_watchdog_unknown_tmux_is_not_dead(tmp_path):
    def error(*a,**kw):return SimpleNamespace(returncode=1,stdout='',stderr='error connecting permission denied')
    with pytest.raises(ProbeError):live(tmp_path,'rl4cv-e13v4-pilot-A-1301',error)
    with pytest.raises(ProbeError):live(tmp_path,'rl4cv-e13v3-pilot-A-1301',error)


def test_extended_horizon_does_not_stop_at_result30(tmp_path):
    for i in range(1,31):
        p=tmp_path/f'update_{i:05d}';p.mkdir();(p/'summary.json').write_text('{}')
    (tmp_path/'result_30.json').write_text('{}')
    assert trajectory_state(tmp_path,30)['complete']
    assert not trajectory_state(tmp_path,60)['complete']
    assert trajectory_state(tmp_path,60)['next_update']==31


def test_cron_preserves_v3_lines_and_is_idempotent():
    old='1 * * * * v3 # e13v3-autoresume\n2 * * * * unrelated\n'
    new=cron_text(old,'/python','/v4/watchdog.py','/v4/plan.json','/v4/watchdog.log')
    assert new.startswith(old) and new.count('# e13v4-autoresume')==1
    assert cron_text(new,'/python','/v4/watchdog.py','/v4/plan.json','/v4/watchdog.log')==new


def test_maximum_length_probe_checks_admission_before_touching_worker():
    calls=[]
    def blocked():calls.append('admission');raise ValueError('not admitted')
    with pytest.raises(ValueError):probe(None,maximum_train_prompt=7753,response_cap=12288,admission_check=blocked,lease_check=lambda:calls.append('lease'))
    assert calls==['admission']


def test_watchdog_reserves_attempt_durably_before_failed_repair(tmp_path,monkeypatch):
    import autoresume_watchdog as wd
    from common import object_digest
    plan={'admission':str(tmp_path/'admission.json'),'work':str(tmp_path),'trajectories':[
        {'arm':'A','seed':1301,'horizon':30,'commands':{'launch':['owned-v4-runner']}}]}
    monkeypatch.setattr(wd,'live',lambda *a,**kw:False)
    def run(cmd,**kw):
        state=json.loads((tmp_path/'autoresume_state.json').read_text())
        assert state['A_1301']['1']==1
        return SimpleNamespace(returncode=1,stdout='failed before generation')
    result=tick(plan,dry_run=False,run=run,admission_check=lambda *a,**kw:{'watchdog_plan_sha256':object_digest(plan)})
    assert result['trajectories']['A_1301']['returncode']==1


def test_watchdog_rechecks_liveness_before_mutation(tmp_path,monkeypatch):
    import autoresume_watchdog as wd
    from common import object_digest
    plan={'admission':str(tmp_path/'admission.json'),'work':str(tmp_path),'trajectories':[
        {'arm':'A','seed':1301,'horizon':30,'commands':{'launch':['owned-v4-runner']}}]}
    states=iter([False,True]);monkeypatch.setattr(wd,'live',lambda *a,**kw:next(states))
    def forbidden(*a,**kw):raise AssertionError('must not launch')
    tick(plan,dry_run=False,run=forbidden,admission_check=lambda *a,**kw:{'watchdog_plan_sha256':object_digest(plan)})
    assert not (tmp_path/'autoresume_state.json').exists()


def test_synthetic_probe_batch_allows_embedding_backward_without_index_mutation(monkeypatch):
    import torch
    from maximum_length_probe import synthetic_batch
    from nemo_objective import FilteredClippedPGLossFn
    monkeypatch.setattr(torch.Tensor,'cuda',lambda self,*a,**kw:self)
    embedding=torch.nn.Embedding(32,8);head=torch.nn.Linear(8,32)
    ids=torch.full((1,8),3,dtype=torch.long);before=ids.clone()
    logits=head(embedding(ids));data=synthetic_batch(logits,ids,3)
    loss,_=FilteredClippedPGLossFn()(logits.float()/.6,data,torch.tensor(1.),data['token_mask'].sum())
    loss.backward()
    assert torch.equal(ids,before)
    assert embedding.weight.grad is not None and torch.isfinite(embedding.weight.grad).all()
