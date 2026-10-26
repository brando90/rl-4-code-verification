"""TLDR: Exercise sustained idle admission and pre-engine refusal using only CPU fakes and temporary locks."""
import fcntl
import json
from pathlib import Path

import pytest

from common import write_new
from device_guard import Busy, check
from device_lease import allocation


class FakeClock:
    def __init__(self):self.now=0.0;self.waits=[]
    def __call__(self):return self.now
    def sleep(self,seconds):self.waits.append(seconds);self.now+=seconds


@pytest.fixture
def lease_fixture(tmp_path):
    v3=tmp_path/'v3';(v3/'phase2').mkdir(parents=True)
    (v3/'gpu_7.lock').write_text('existing v3 lock; preserve bytes\n')
    clock=FakeClock()
    return tmp_path/'leases',v3,clock


def idle():return {7:'GPU-seven'},[]


def lease(work,v3,clock,probe=idle,**kwargs):
    return allocation(work,lambda:None,host='skampere1',v3_work=v3,
                      clock=clock,sleep=clock.sleep,probe=probe,**kwargs)


def test_two_complete_observations_hold_locks_for_sixty_seconds(lease_fixture):
    work,v3,clock=lease_fixture;seen=[]
    before=(v3/'gpu_7.lock').read_bytes()
    def probe():seen.append(clock());return idle()
    with lease(work,v3,clock,probe) as path:
        row=json.loads(path.read_text())
        assert seen==[0,0,60] and clock.waits==[60]
        assert [r['monotonic'] for r in row['idle_observations']]==[0,60]
        with (v3/'gpu_7.lock').open('r') as contender:
            with pytest.raises(BlockingIOError):fcntl.flock(contender,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert check({'lease_path':path},pre_engine=True,probe=idle,v3_work=v3)==row
    assert path.with_suffix('.end.json').exists()
    assert (v3/'gpu_7.lock').read_bytes()==before
    with (v3/'gpu_7.lock').open('r') as available:fcntl.flock(available,fcntl.LOCK_EX|fcntl.LOCK_NB)


def test_foreign_process_flapping_resets_the_entire_idle_wait(lease_fixture):
    work,v3,clock=lease_fixture
    observations=iter([idle(),idle(),({7:'GPU-seven'},[('GPU-seven',701)]),
                       idle(),idle(),({7:'GPU-seven'},[('GPU-seven',702)]),
                       idle(),idle(),idle()])
    probe=lambda:next(observations)
    for expected in (60,120):
        with pytest.raises(Busy,match='two idle observations'):
            with lease(work,v3,clock,probe):pytest.fail('flapping process leased')
        assert clock()==expected and not list(work.glob('*.lease.json'))
    with lease(work,v3,clock,probe) as path:
        assert [r['monotonic'] for r in json.loads(path.read_text())['idle_observations']]==[120,180]
    assert clock.waits==[60,60,60]


def test_busy_first_observation_never_waits_or_leases(lease_fixture):
    work,v3,clock=lease_fixture
    probe=lambda:({7:'GPU-seven'},[('GPU-seven',700)])
    with pytest.raises(Busy):
        with lease(work,v3,clock,probe):pytest.fail('busy process leased')
    assert not clock.waits and not list(work.glob('*.lease.json'))


def test_v3_lease_appearing_during_wait_refuses_device(lease_fixture):
    work,v3,clock=lease_fixture
    original=clock.sleep
    def sleep(seconds):
        original(seconds)
        write_new(v3/'phase2/run/stage_lease.json',{'status':'ACTIVE','index':7})
    clock.sleep=sleep
    with pytest.raises(Busy):
        with lease(work,v3,clock):pytest.fail('reserved process leased')
    assert not list(work.glob('*.lease.json'))


def test_busy_v3_lock_never_leases_and_preserves_file(lease_fixture):
    work,v3,clock=lease_fixture
    with (v3/'gpu_7.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(Busy):
            with lease(work,v3,clock):pytest.fail('v3 lock ignored')
    assert not clock.waits and not list(work.glob('*.lease.json'))


def test_missing_v3_lock_is_not_created(lease_fixture):
    work,v3,clock=lease_fixture;(v3/'gpu_7.lock').unlink()
    with pytest.raises(Busy):
        with lease(work,v3,clock):pytest.fail('missing v3 lock ignored')
    assert not (v3/'gpu_7.lock').exists() and not clock.waits


def test_changed_device_mapping_during_wait_refuses(lease_fixture):
    work,v3,clock=lease_fixture
    observations=iter([idle(),idle(),({7:'GPU-replaced'},[])])
    with pytest.raises(Busy):
        with lease(work,v3,clock,lambda:next(observations)):pytest.fail('changed device leased')
    assert not list(work.glob('*.lease.json'))


def test_shortened_wait_does_not_satisfy_sixty_second_contract(lease_fixture):
    work,v3,clock=lease_fixture;clock.sleep=lambda _:setattr(clock,'now',59)
    with pytest.raises(Busy):
        with lease(work,v3,clock):pytest.fail('short idle interval accepted')
    assert not list(work.glob('*.lease.json'))


@pytest.mark.parametrize('foreign_pid',[123,456])
def test_pre_engine_rejects_any_new_process_without_reading_its_environment(lease_fixture,foreign_pid):
    work,v3,clock=lease_fixture
    def forbidden(pid):pytest.fail('pre-engine guard read a process environment')
    with lease(work,v3,clock) as path:
        probe=lambda:({7:'GPU-seven'},[('GPU-seven',foreign_pid)])
        with pytest.raises(Busy,match='compute process'):
            check({'lease_path':path},pre_engine=True,probe=probe,v3_work=v3,read_environment=forbidden)


def test_pre_engine_rechecks_v3_reservations_after_lease(lease_fixture):
    work,v3,clock=lease_fixture
    with lease(work,v3,clock) as path:
        write_new(v3/'phase2/run/stage_lease.json',{'status':'ACTIVE','index':7})
        with pytest.raises(Busy,match='reservation'):
            check({'lease_path':path},pre_engine=True,probe=idle,v3_work=v3)


def test_pre_engine_fails_if_allocator_dropped_shared_lock(lease_fixture):
    work,v3,clock=lease_fixture
    with lease(work,v3,clock) as path:
        row=json.loads(path.read_text())
        fcntl.flock(row['shared_locks'][1]['fd'],fcntl.LOCK_UN)
        with pytest.raises(Busy,match='shared lock ownership'):
            check({'lease_path':path},pre_engine=True,probe=idle,v3_work=v3)


def test_pre_engine_fails_closed_when_owned_lock_evidence_is_unreadable(lease_fixture,monkeypatch):
    work,v3,clock=lease_fixture
    with lease(work,v3,clock) as path:
        original=Path.read_text
        def denied(self,*args,**kwargs):
            if 'fdinfo' in self.parts:raise PermissionError('owned lock evidence unavailable')
            return original(self,*args,**kwargs)
        monkeypatch.setattr(Path,'read_text',denied)
        with pytest.raises(Busy,match='shared lock ownership'):
            check({'lease_path':path},pre_engine=True,probe=idle,v3_work=v3)


def test_admission_is_rechecked_after_idle_observations(lease_fixture):
    work,v3,clock=lease_fixture;calls=[]
    def admit():
        calls.append(clock())
        if len(calls)==2:raise ValueError('admission changed while waiting')
    with pytest.raises(ValueError,match='admission changed'):
        with allocation(work,admit,host='skampere1',v3_work=v3,probe=idle,
                        clock=clock,sleep=clock.sleep):pytest.fail('changed admission accepted')
    assert calls==[0,60] and not list(work.glob('*.lease.json'))


@pytest.mark.parametrize('reservation',[{'status':'ACTIVE','index':7,'expires_unix':float('nan')},
                                        {'status':'ACTIVE','index':'7'}, {'status':'ACTIVE'}])
def test_incomplete_or_invalid_reservation_prevents_idle_proof(lease_fixture,reservation):
    work,v3,clock=lease_fixture
    path=v3/'phase2/run/stage_lease.json';path.parent.mkdir()
    path.write_text(json.dumps(reservation))
    with pytest.raises(Busy):
        with lease(work,v3,clock):pytest.fail('unreadable reservation accepted')
    assert not clock.waits and not list(work.glob('*.lease.json'))


def test_expired_unfinished_v3_lease_requires_end_receipt(lease_fixture):
    work,v3,clock=lease_fixture
    path=v3/'phase2/run/stage_lease.json'
    write_new(path,{'status':'ACTIVE','index':7,'expires_unix':0})
    with pytest.raises(Busy):
        with lease(work,v3,clock):pytest.fail('unfinished v3 lease ignored after expiry')
    assert not clock.waits and not list(work.glob('*.lease.json'))
    write_new(path.with_name('stage_lease_end.json'),{'status':'RELEASED'})
    with lease(work,v3,clock) as admitted:
        assert check({'lease_path':admitted},pre_engine=True,probe=idle,v3_work=v3)['index']==7


def test_pre_engine_refuses_expired_v3_lease_without_end_receipt(lease_fixture):
    work,v3,clock=lease_fixture
    with lease(work,v3,clock) as path:
        write_new(v3/'phase2/run/stage_lease.json',{'status':'ACTIVE','index':7,'expires_unix':0})
        with pytest.raises(Busy,match='reservation'):
            check({'lease_path':path},pre_engine=True,probe=idle,v3_work=v3)
