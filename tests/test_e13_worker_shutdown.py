"""Reproduce the real exited-worker environment error and preserve the unchanged device ownership guard."""
from pathlib import Path
import json,os,sys,time
from types import SimpleNamespace
import pytest
P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P));sys.path.insert(0,str(P.parent/'phase1'))
import worker_shutdown as m
import runtime


def test_real_zombie_environment_error_then_census_clear(tmp_path,monkeypatch):
    pid=os.fork()
    if pid==0:os._exit(0)
    try:
        deadline=time.monotonic()+5
        while m.process_identity(pid)['state']!='Z':
            assert time.monotonic()<deadline
            time.sleep(.01)
        birth=m.process_identity(pid)
        # This is the actual host kernel error, not a patched read_bytes call.
        with pytest.raises(PermissionError):Path('/proc',str(pid),'environ').read_bytes()
        path=tmp_path/'lease.json';path.write_text(json.dumps({'id':'authored','uuid':'GPU-authored'}))
        monkeypatch.setattr(runtime,'check_visible_device',lambda _:None)
        visible={pid}
        monkeypatch.setattr(runtime.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout=''.join(f'GPU-authored, {p}\n'for p in visible)))
        with pytest.raises(PermissionError):runtime.check_lease({'lease_path':str(path)})
        calls=[]
        def census():
            calls.append(True)
            if len(calls)>1:visible.clear()
            return set(visible)
        result=m.wait_for_workers([birth],query=census,sleep=lambda _:None)
        assert result['status']=='PASS' and result['polls']==2
        assert result['owned_workers_exited'] and result['no_owned_gpu_processes']
        runtime.check_lease({'lease_path':str(path)})
        # The original guard still rejects a live foreign execution.
        visible.add(os.getpid())
        with pytest.raises(RuntimeError,match='another execution'):runtime.check_lease({'lease_path':str(path)})
    finally:os.waitpid(pid,0)


@pytest.mark.parametrize('state,visible',[('S',set()),('Z',{123}),('S',{123})])
def test_handoff_requires_both_exit_and_no_device_entry(state,visible):
    with pytest.raises(TimeoutError,match='handoff'):
        m.wait_for_workers([{'pid':123,'start_ticks':1}],identity=lambda _:dict(pid=123,start_ticks=1,state=state),
            query=lambda:visible,clock=lambda:0,timeout=0,sleep=lambda _:pytest.fail('deadline ignored'))


def test_pid_reuse_is_not_killed_or_accepted_while_in_census():
    with pytest.raises(TimeoutError):
        m.wait_for_workers([{'pid':123,'start_ticks':1}],identity=lambda _:dict(pid=123,start_ticks=2,state='S'),
            query=lambda:{123},clock=lambda:0,timeout=0)
    result=m.wait_for_workers([{'pid':123,'start_ticks':1}],identity=lambda _:None,query=lambda:set())
    assert result['status']=='PASS'


@pytest.mark.parametrize('identities',[[],[{'pid':0,'start_ticks':1}],[{'pid':1,'start_ticks':0}],
    [{'pid':1,'start_ticks':1},{'pid':1,'start_ticks':1}]])
def test_identity_required(identities):
    with pytest.raises(ValueError):m.wait_for_workers(identities,query=lambda:pytest.fail('invalid identity queried'))
