"""TLDR: Verify the designated pause, timing, process races and three-device pilot preflight without GPUs."""
import fcntl
import json
import signal
from pathlib import Path
import pytest
from common import write_new
from operational_pause import CONFIG,RECORD,selection
from pause_v3 import pause,boundary_probe,VETO_END
from admission import launch_timing,check_admission
from test_contracts import admission_fixture


def setup_pause(tmp_path):
    _,admission=admission_fixture(tmp_path)
    work=tmp_path/'v3';(work/'phase2/pilot').mkdir(parents=True)
    runner={'kind':'runner','pid':123456789,'pgid':123456789,'start_ticks':'123','start_unix':1}
    snap={'trajectory':'A_1302','pane_text':'waiting for an idle GPU','processes':[runner],'leases':[]}
    signals=[];seen=[]
    def probe(key,work):seen.append(key);return snap
    kwargs=dict(work=work,veto_not_issued=True,now=VETO_END+1,probe=probe,
                inspect=lambda pid:runner,kill=lambda pgid,sig:signals.append(sig))
    return admission,work,runner,snap,signals,seen,kwargs


def test_selection_is_exactly_one():
    assert selection()==('A_1302',)


@pytest.mark.parametrize('key',['A_1301','B_1302','P_1301','P_1302','B_1301'])
def test_refuse_non_designated_before_probe(tmp_path,key):
    admission,work,_,_,signals,seen,kw=setup_pause(tmp_path)
    with pytest.raises(ValueError,match='non-designated'):pause(admission,trajectory=key,**kw)
    assert not signals and not seen and not (work/'phase2/autoresume.lock').exists()


@pytest.mark.parametrize('targets',[[],['B_1301'],['A_1301'],['A_1302','B_1302']])
def test_invalid_operational_selection(tmp_path,targets):
    p=tmp_path/'operation.json';write_new(p,{'mode':'single','trajectories':targets,'record':RECORD})
    with pytest.raises(ValueError,match='only A_1302'):selection(p)


def test_admission_binds_operational_json_and_markdown(tmp_path):
    root,admission=admission_fixture(tmp_path)
    record=check_admission(admission)
    assert {RECORD,'phase2/operational_pause.json'}<={r['path'] for r in record['bindings']}
    (root/'phase2/operational_pause.json').write_text(CONFIG.read_text()+'\n')
    with pytest.raises(ValueError,match='bound v4 file changed'):check_admission(admission)


def test_pause_wait_then_atomic_single_pause_and_idempotence(tmp_path):
    admission,work,runner,snap,signals,seen,kw=setup_pause(tmp_path)
    snap['processes'].append({'kind':'stage'})
    assert pause(admission,**kw)=={'A_1302':'WAIT_STAGE_RUNNING'}
    assert not signals and not (work/'phase2/autoresume_paused.json').exists()
    snap['processes']=[runner]
    assert pause(admission,**kw)=={'A_1302':'PAUSED'}
    assert signals==[signal.SIGSTOP,signal.SIGTERM,signal.SIGCONT]
    state=json.loads((work/'phase2/autoresume_paused.json').read_text())
    assert set(state['trajectories'])=={'A_1302'} and not (work/'phase2/.autoresume_paused.tmp').exists()
    assert pause(admission,**kw)=={'A_1302':'ALREADY_PAUSED'}
    assert seen==['A_1302']*3 and len(signals)==3


def test_boundary_probe_is_read_only_before_window(tmp_path):
    admission,work,_,_,signals,seen,kw=setup_pause(tmp_path)
    assert boundary_probe(admission,work=work,probe=kw['probe'])['A_1302']['status']=='READY'
    assert seen==['A_1302'] and not signals
    assert sorted(p.name for p in (work/'phase2').iterdir())==['pilot']


def test_stop_recheck_race_resumes_without_pause(tmp_path):
    admission,work,_,snap,signals,_,kw=setup_pause(tmp_path)
    def kill(pgid,sig):
        signals.append(sig)
        if sig==signal.SIGSTOP:snap['leases']=['raced']
    kw['kill']=kill
    assert pause(admission,**kw)=={'A_1302':'WAIT_RACE'}
    assert signals==[signal.SIGSTOP,signal.SIGCONT]
    assert not (work/'phase2/autoresume_paused.json').exists()


@pytest.mark.parametrize('after_stop',[False,True])
def test_pid_reuse_never_signals_replacement(tmp_path,after_stop):
    admission,work,runner,_,signals,_,kw=setup_pause(tmp_path)
    kw['inspect']=lambda pid:{**runner,'start_ticks':'reused' if signals or not after_stop else '123'}
    with pytest.raises(ValueError,match='PID reused'):pause(admission,**kw)
    assert signals==([signal.SIGSTOP] if after_stop else [])
    assert not (work/'phase2/autoresume_paused.json').exists()


def test_watchdog_lock_prevents_any_probe_or_signal(tmp_path):
    admission,work,_,_,signals,seen,kw=setup_pause(tmp_path)
    with (work/'phase2/autoresume.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert pause(admission,**kw)=={'A_1302':'WAIT_WATCHDOG_LOCK'}
    assert not signals and not seen


def test_gate_one_pause_and_pilot_still_waits_for_b1301(tmp_path):
    pilot=tmp_path/'phase2/pilot';pilot.mkdir(parents=True)
    def timing(**kw):return launch_timing(pilot,now=VETO_END+1,veto_not_issued=True,**kw)
    assert not timing()['released']
    write_new(pilot.parent/'autoresume_paused.json',{'trajectories':{'A_1302':{'pid':123}}})
    assert timing()['released'] and timing()['designated_pause_recorded']
    assert not launch_timing(pilot,now=VETO_END-1,veto_not_issued=True)['released']
    assert not launch_timing(pilot,now=VETO_END+1)['released']
    assert not timing(phase='pilot')['released']
    write_new(pilot/'B_1301/T5_30.json',{'status':'EXTEND_TO_60'})
    write_new(pilot/'B_1301/update_00030/generation_lease.json',{'status':'ACTIVE'})
    assert not timing(phase='pilot')['released'] and timing()['released']
    write_new(pilot/'B_1301/update_00030/generation_lease_end.json',{'status':'RELEASED'})
    assert timing(phase='pilot')['released']


@pytest.mark.parametrize('paused',[{}, {'B_1302':{'pid':123}}, {'A_1302':{}}, ['A_1302']])
def test_no_designated_receipt_does_not_release(tmp_path,paused):
    pilot=tmp_path/'phase2/pilot';pilot.mkdir(parents=True)
    write_new(pilot.parent/'autoresume_paused.json',{'trajectories':paused})
    assert not launch_timing(pilot,now=VETO_END+1,veto_not_issued=True)['released']


def test_cpu_dry_run_single_pause(tmp_path):
    _,admission=admission_fixture(tmp_path)
    from dry_run import single_pause
    result=single_pause(tmp_path/'dry',admission)
    assert result['gates_released']==[False,False,True] and result['real_signals']==0


def test_runner_enforces_single_pause_and_pilot_prerequisites(tmp_path,monkeypatch):
    from runner import Runner
    from stub_engine import StubEngine
    import admission as adm
    import device_lease
    _,admission=admission_fixture(tmp_path)
    pilot=tmp_path/'v3/phase2/pilot';pilot.mkdir(parents=True)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','')
    monkeypatch.setenv('E13V4_A3_NO_VETO','1')
    monkeypatch.setattr(adm,'launch_timing',lambda path,**kw:launch_timing(pilot,now=VETO_END+1,**kw))
    capacity=[];monkeypatch.setattr(device_lease,'pilot_capacity',lambda *a:capacity.append(3))
    engine=StubEngine();runner=Runner(tmp_path/'run',admission,engine)
    engine.synthetic=False # Exercise measured schedule guards with a strictly synthetic backend.
    with pytest.raises(ValueError,match='schedule'):runner.run('T1')
    write_new(pilot.parent/'autoresume_paused.json',{'trajectories':{'A_1302':{'pid':123}}})
    assert runner.run('T1')['status']=='PASS'
    with pytest.raises(ValueError,match='schedule'):runner.run('PILOT30')
    assert not capacity
    write_new(pilot/'B_1301/T5_30.json',{'status':'PASS'})
    with pytest.raises(ValueError,match='predecessor'):runner.run('PILOT30')
    assert capacity==[3]


def test_controller_propagates_verified_veto_flag_to_tmux(tmp_path,monkeypatch):
    import launch_control
    from common import object_digest
    from types import SimpleNamespace
    plan={'admission':'fixture','v3_pilot_read_only':'fixture',
          'session':'rl4cv-e13v4-fixture','sequence_argv':['python','runner.py','sequence'],
          'checkout':str(tmp_path)}
    monkeypatch.setattr(launch_control,'check_admission',lambda *a,**kw:{'root':str(tmp_path),'launch_plan_sha256':object_digest(plan)})
    monkeypatch.setattr(launch_control,'launch_timing',lambda *a,**kw:{'released':kw['veto_not_issued']})
    calls=[]
    def run(argv,**kw):
        calls.append(argv)
        return SimpleNamespace(returncode=1,stderr="can't find session")
    monkeypatch.delenv('E13V4_A3_NO_VETO',raising=False)
    with pytest.raises(ValueError,match='release condition'):launch_control.launch(plan,run=run)
    assert not calls
    monkeypatch.setenv('E13V4_A3_NO_VETO','1')
    assert launch_control.launch(plan,run=run)['status']=='STARTED'
    assert calls[1][:5]==['tmux','new-session','-d','-e','E13V4_A3_NO_VETO=1']


def test_pilot_requires_three_idle_unlocked_devices_and_leaves_no_reservation(tmp_path):
    from device_lease import pilot_capacity
    from device_guard import Busy
    leases=tmp_path/'leases';v3=tmp_path/'v3';v3.mkdir()
    devices={i:f'GPU-{i}' for i in (0,5,7)}
    probe=lambda:(devices,[])
    kw=dict(probe=probe,host='skampere1',v3_work=v3)
    with (v3/'gpu_5.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(Busy,match='3 idle'):pilot_capacity(leases,**kw)
    with pytest.raises(Busy):pilot_capacity(leases,**{**kw,'probe':lambda:(devices,[('GPU-5',123)])})
    assert pilot_capacity(leases,**kw)['idle_authorized_devices']==[0,5,7]
    for path in [*leases.glob('*.lock'),*v3.glob('*.lock')]:
        with path.open('a') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(tmp_path.glob('**/*lease.json'))
    write_new(v3/'phase2/pilot/B_1301/stage_lease.json',{'status':'ACTIVE','index':5})
    with pytest.raises(Busy,match='reservation'):pilot_capacity(leases,**kw)
