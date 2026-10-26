"""TLDR: Verify complete stub execution, immutable stage order, crash recovery, and stop without resampling."""
import json
from pathlib import Path
import pytest
from common import digest, write_new
from runner import Runner, STAGES
from stage_ledger import Ledger, RecoveryRequired
from stub_engine import StubEngine
from recovery import inspect
from test_contracts import admission_fixture


def setup(tmp_path,**kw):
    root,path=admission_fixture(tmp_path)
    return Runner(tmp_path/'run',path,StubEngine(**kw))


def test_full_stage_sequence_extends_all_six_and_binds_receipts(tmp_path):
    run=setup(tmp_path)
    with pytest.raises(ValueError,match='predecessor'):run.run('G0_GENERATE')
    for stage in STAGES:
        r=run.run(stage)
        assert r['status']=='PASS' and r['synthetic'] and r['admission_sha256']==digest(run.admission)
    assert run.result('T5_30')['decision']['action']=='EXTEND_ALL_SIX'
    assert run.result('T5_60')['decision']['action']=='MAIN_RESOURCE_CHECK'
    rows=run.result('PILOT30')['rows']+run.result('PILOT60')['rows']
    assert len(rows)==360 and {(r['arm'],r['seed']) for r in rows}=={(a,s) for a in 'ABP' for s in (1301,1302)}
    assert all(r['optimizer_steps']==0 and r['synthetic_transition'] for r in rows)
    assert all('top_token_ids' not in r['receipt'][0] for r in rows)
    assert run.result('T5_60')['token_budget']['slots']==15360
    before=digest(run.work/'T1/receipt.json');run.run('T1');assert digest(run.work/'T1/receipt.json')==before
    # Mutated predecessor artifacts prevent all downstream progress, even for
    # an already completed result.
    (run.work/'T1/statistic.json').write_text('{}')
    with pytest.raises(ValueError,match='artifact changed'):run.run('G0_GENERATE')


def test_zero_generation_crash_recovery_and_attempt_cap(tmp_path):
    run=setup(tmp_path,crash='probe')
    with pytest.raises(RuntimeError,match='simulated'):run.run('T1')
    assert inspect(run.work)['action']=='RETRY_EMPTY'
    with pytest.raises(RecoveryRequired):run.run('T1')
    assert run.run('T1',recover=True)['status']=='PASS'
    assert len(list((run.work/'T1/probe').glob('attempt_*')))==2
    capped=tmp_path/'cap';ledger=Ledger(capped,run.admission,synthetic=True)
    def failed(path,data):
        write_new(path/'infrastructure_failure.json',{'generated_responses':0,'optimizer_started':False,'statistics_started':False})
        raise RuntimeError('infrastructure')
    for i in range(3):
        with pytest.raises(RuntimeError,match='infrastructure'):ledger.operation('T1','probe',{},failed,recover=i>0)
    with pytest.raises(RecoveryRequired,match='cap'):ledger.operation('T1','probe',{},failed,recover=True)
    assert inspect(capped)['action']=='STOP_A4_CAP'


def test_partial_generation_never_retried_even_with_recover(tmp_path):
    run=setup(tmp_path)
    def partial(path,data):
        write_new(path/'generation.json',{'tokens':[1]})
        raise RuntimeError('killed after response')
    with pytest.raises(RuntimeError):run.ledger.operation('T1','probe',{},partial)
    with pytest.raises(RecoveryRequired,match='partial effects'):run.ledger.operation('T1','probe',{},partial,recover=True)
    assert inspect(run.work)['action']=='STOP_PARTIAL'
    assert len(list((run.work/'T1/probe').glob('attempt_*')))==1


def test_statistic_crash_is_terminal_but_completed_operation_is_accounted(tmp_path):
    run=setup(tmp_path);run.ledger.begin('T1',[])
    calls=[]
    def action(path,data):calls.append(1);return {'ok':True}
    run.ledger.operation('T1','op',{},action)
    run.ledger.operation('T1','op',{},action,recover=True);assert len(calls)==1
    def broken():raise RuntimeError('crashed statistic')
    with pytest.raises(RuntimeError):run.ledger.statistic('T1',broken)
    with pytest.raises(FileExistsError):run.ledger.statistic('T1',lambda:{'status':'PASS'})
    assert inspect(run.work)['action']=='STOP_STATISTIC'


def test_t2_stop_has_no_update_refit_or_resampling(tmp_path):
    run=setup(tmp_path,no_signal=True)
    for stage in STAGES[:4]:run.run(stage)
    assert run.run('T2')['status']=='STOP_NO_SIGNAL'
    assert not (run.work/'T2/update').exists() and not (run.work/'T2/refit').exists()
    with pytest.raises(ValueError,match='predecessor'):run.run('T3')
    assert run.run('T2',recover=True)['status']=='STOP_NO_SIGNAL'


def test_lease_checks_admission_before_gpu_probe(tmp_path):
    from device_lease import allocation
    def blocked():raise ValueError('admission blocked')
    def forbidden():raise AssertionError('GPU probe forbidden')
    with pytest.raises(ValueError,match='admission'):
        with allocation(tmp_path,blocked,probe=forbidden):pass


def test_lease_mocked_idle_guard_and_environment_restore(tmp_path,monkeypatch):
    import os
    from device_lease import allocation
    def probe():return {0:'GPU-test'},[]
    v3=tmp_path/'v3';(v3/'phase2').mkdir(parents=True);(v3/'gpu_0.lock').touch()
    ticks=[0.0]
    def sleep(seconds):ticks[0]+=seconds
    with allocation(tmp_path,lambda:None,probe=probe,host='skampere1',v3_work=v3,
                    clock=lambda:ticks[0],sleep=sleep) as p:
        assert os.environ['CUDA_VISIBLE_DEVICES']=='0'
        assert json.loads(p.read_text())['owner']=='e13v4'
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and p.with_suffix('.end.json').exists()


def test_local_engine_never_substitutes_stub(tmp_path):
    from local_engine import LocalEngine
    engine=LocalEngine(tmp_path,'admission')
    assert not engine.synthetic
    assert len(engine.train_ids())==539
    assert not list(tmp_path.iterdir())


def test_controller_watchdog_does_not_restart_failed_gate(tmp_path,monkeypatch):
    import autoresume_watchdog as wd
    from common import object_digest
    admission=tmp_path/'admission.json';write_new(admission,{'fixture':True})
    work=tmp_path/'run';ledger=Ledger(work,admission,synthetic=False)
    ledger.begin('T1',[]);ledger.finish('T1',{'status':'FAIL'})
    plan={'kind':'stage-controller','admission':str(admission),'work':str(work),
          'session':'rl4cv-e13v4-stages','resume_argv':['forbidden']}
    monkeypatch.setattr(wd,'live',lambda *a,**kw:False)
    result=wd.tick(plan,admission_check=lambda *a,**kw:{'watchdog_plan_sha256':object_digest(plan)})
    assert result['status']=='STOPPED'


def test_controller_watchdog_dry_run_never_starts_command(tmp_path,monkeypatch):
    import autoresume_watchdog as wd
    from common import object_digest
    admission=tmp_path/'admission.json';write_new(admission,{'fixture':True})
    plan={'kind':'stage-controller','admission':str(admission),'work':str(tmp_path/'run'),
          'session':'rl4cv-e13v4-stages','resume_argv':['forbidden']}
    monkeypatch.setattr(wd,'live',lambda *a,**kw:False)
    def forbidden(*a,**kw):raise AssertionError('must not execute')
    result=wd.tick(plan,run=forbidden,admission_check=lambda *a,**kw:{'watchdog_plan_sha256':object_digest(plan)})
    assert result['status']=='DRY_RUN'


def test_controller_watchdog_releases_runner_fence_before_spawn(tmp_path,monkeypatch):
    import fcntl
    from types import SimpleNamespace
    import autoresume_watchdog as wd
    from common import object_digest
    admission=tmp_path/'admission.json';write_new(admission,{'fixture':True})
    work=tmp_path/'run'
    plan={'kind':'stage-controller','admission':str(admission),'work':str(work),
          'session':'rl4cv-e13v4-stages','resume_argv':['fake-launch']}
    monkeypatch.setattr(wd,'live',lambda *a,**kw:False)
    def spawn(*a,**kw):
        with (work/'controller.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return SimpleNamespace(returncode=0,stdout='synthetic spawn check only')
    r=wd.tick(plan,dry_run=False,run=spawn,
              admission_check=lambda *a,**kw:{'watchdog_plan_sha256':object_digest(plan)})
    assert r['status']=='DISPATCHED'


def test_t1_denominator_comes_from_saved_response_lengths(tmp_path):
    run=setup(tmp_path)
    original=run.engine.measure
    def missing_position(op,path,payload):
        data=original(op,path,payload)
        if op=='probe':data['rows'][0]['output_token_ids'].append(99)
        return data
    run.engine.measure=missing_position
    with pytest.raises(ValueError,match='full declared token denominator'):run.run('T1')
    assert not (run.work/'T1/receipt.json').exists()
