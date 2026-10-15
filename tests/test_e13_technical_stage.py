"""Keep technical-stage launches numeric, unique, bounded and cleaned without gate comparisons."""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0, str(PHASE))
spec = importlib.util.spec_from_file_location('e13_technical_stage', PHASE/'technical_stage.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def fixture(tmp_path, monkeypatch):
    lp = {'path': 'authored-LP', 'sha256': 'lp-sha', 'revision': 'authored-revision'}
    source_paths = [PHASE/'technical_stage.py', PHASE/'technical_supervisor.py', PHASE/'technical_runtime.py',
                    PHASE.parent/'phase1/device_binding.py', PHASE.parent/'phase1/lp1.py', PHASE.parent/'phase1/anchor_lease.py']
    ledger = tmp_path/'ledger'
    lock = {'configuration': {'technical_ledger': str(ledger)},
            'bindings': [{'path': str(p), 'sha256': m.digest(p)} for p in source_paths]}
    monkeypatch.setattr(m, 'pilot_lock', lambda *args: (lock, 'science-sha'))
    lease = {'id': 'authored-lease', 'owner': 'e13v2', 'status': 'ACTIVE', 'host': m.socket.gethostname().split('.')[0],
             'phase': 'v2-S2-technical', 'started_unix': 100, 'expires_unix': 700}
    lease_root = tmp_path/'leases'; lease_root.mkdir()
    lease_path = lease_root/'authored-lease.json'; lease_path.write_text(json.dumps(lease))
    config_path = tmp_path/'config.json'; config = {'condition': 'v2-S2', 'stage': 'preflight',
        'lease_path': str(lease_path), 'lease_id': lease['id'], 'bindings': []}
    config_path.write_text(json.dumps(config))
    kwargs = {'LP': lp, 'repository': tmp_path, 'gate': 'T1', 'stage_key': 'preflight',
              'config_path': config_path, 'maximum_seconds': 600, 'preparation_root': tmp_path/'preflight-stage'}
    return kwargs, config, lease_root, ledger


def admission(ledger):
    root = ledger/'T1/attempt_1'; root.mkdir(parents=True)
    path = root/'attempt.json'
    path.write_text(json.dumps({'gate': 'T1', 'status': 'ADMITTED', 'LP_sha256': 'lp-sha', 'science_sha256': 'science-sha', 'attempt': 1}))
    return path


def test_preflight_is_attempt_zero_then_numbered_stage_is_unique(tmp_path, monkeypatch):
    kwargs, config, lease_root, ledger = fixture(tmp_path, monkeypatch)
    plan_path = m.prepare(**kwargs)
    plan = json.loads(plan_path.read_text()); execution = json.loads(Path(plan['execution']).read_text())
    assert execution['attempt'] == 0 and execution['status'] == 'PREFLIGHT_RESERVED'
    assert not ledger.exists()
    path = admission(ledger)
    config['stage'] = 'generate'; kwargs['config_path'].write_text(json.dumps(config))
    monkeypatch.setattr(m, 'check_preflight', lambda x: {'status': 'PASS'})
    kwargs.update(stage_key='generate', preparation_root=tmp_path/'generation-stage', attempt_path=path,
                  preflight={'path': 'authored-health', 'sha256': 'health-sha'})
    result = m.prepare(**kwargs)
    record = json.loads(Path(json.loads(result.read_text())['execution']).read_text())
    assert record['status'] == 'ADMITTED' and record['attempt'] == 1
    kwargs['preparation_root'] = tmp_path/'other-folder'
    with pytest.raises(FileExistsError): m.prepare(**kwargs)
    assert not (tmp_path/'other-folder').exists()


def test_closed_gate_or_changed_duration_cannot_prepare_another_stage(tmp_path, monkeypatch):
    kwargs, config, lease_root, ledger = fixture(tmp_path, monkeypatch)
    kwargs['maximum_seconds'] = 601
    with pytest.raises(ValueError, match='duration'): m.prepare(**kwargs)
    kwargs['maximum_seconds'] = 600
    path = admission(ledger); (path.parent/'evaluation_attempt.json').write_text('{}')
    config['stage'] = 'generate'; kwargs['config_path'].write_text(json.dumps(config))
    kwargs.update(stage_key='generate', attempt_path=path)
    with pytest.raises(ValueError, match='closed or evaluated'): m.prepare(**kwargs)


def launched_fixture(tmp_path, monkeypatch):
    kwargs, config, lease_root, ledger = fixture(tmp_path, monkeypatch)
    plan_path = m.prepare(**kwargs); plan = json.loads(plan_path.read_text())
    import technical_supervisor
    monkeypatch.setattr(technical_supervisor, 'authorize', lambda p: (plan, config))
    calls = []
    def environment(lease, purpose, env):
        calls.append(('numeric-launch', purpose))
        return {**env, 'CUDA_VISIBLE_DEVICES': '7', 'E13_EXECUTION_ID': lease['id']}
    monkeypatch.setattr(m, 'launch_environment', environment)
    monkeypatch.setattr(m, 'cleanup', lambda marker: (calls.append(('cleanup', marker)) or {'verified': True, 'signals': []}))
    monkeypatch.setattr(m, 'release', lambda root, marker, cleanup_verified: (calls.append(('release', cleanup_verified)) or {'status': 'RELEASED'}))
    return plan_path, plan, lease_root, calls


def test_local_launch_uses_fresh_numeric_environment_and_releases(tmp_path, monkeypatch):
    path, plan, leases, calls = launched_fixture(tmp_path, monkeypatch)
    def execute(argv, **kwargs):
        assert kwargs['env']['CUDA_VISIBLE_DEVICES'] == '7' and kwargs['start_new_session']
        assert kwargs['timeout'] == 630
        root = Path(plan['supervisor_root']); root.mkdir()
        (root/'result.json').write_text(json.dumps({'status': 'RUNTIME_EXITED_ZERO'}))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(m.subprocess, 'run', execute)
    result = m.launch_local(path, lease_root=leases, route_environment={})
    assert result['status'] == 'RUNTIME_FINISHED' and not result['admission_statistics_computed']
    assert calls == [('numeric-launch', 'T1'), ('cleanup', 'authored-lease'), ('release', True)]
    with pytest.raises(RuntimeError, match='already dispatched'):
        m.launch_local(path, lease_root=leases, route_environment={})


def test_supervisor_timeout_retains_evidence_and_releases_without_retry(tmp_path, monkeypatch):
    path, plan, leases, calls = launched_fixture(tmp_path, monkeypatch)
    def execute(argv, **kwargs): raise m.subprocess.TimeoutExpired(argv, kwargs['timeout'])
    monkeypatch.setattr(m.subprocess, 'run', execute)
    result = m.launch_local(path, lease_root=leases, route_environment={})
    assert result['status'] == 'INCOMPLETE_INFRA' and result['error_type'] == 'TimeoutExpired'
    assert calls[-2:] == [('cleanup', 'authored-lease'), ('release', True)]


def test_uncertain_cleanup_keeps_the_lease_reserved(tmp_path, monkeypatch):
    path, plan, leases, calls = launched_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(m.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=1))
    monkeypatch.setattr(m, 'cleanup', lambda marker: {'verified': False, 'signals': []})
    monkeypatch.setattr(m, 'release', lambda root, marker, cleanup_verified:
                        {'status': 'RELEASED' if cleanup_verified else 'CLEANUP_REQUIRED'})
    result = m.launch_local(path, lease_root=leases, route_environment={})
    assert result['status'] == result['released']['status'] == 'CLEANUP_REQUIRED'
    assert result['cleanup_verified'] is False


def test_T4_requires_its_distinct_nonprobe_engine_preflight(tmp_path,monkeypatch):
    kwargs,config,lease_root,ledger=fixture(tmp_path,monkeypatch);kwargs['gate']='T4'
    with pytest.raises(ValueError,match='evaluation-context'):m.prepare(**kwargs)
    config['stage']='evaluation_preflight';kwargs['config_path'].write_text(json.dumps(config))
    plan_path=m.prepare(**kwargs);plan=json.loads(plan_path.read_text())
    execution=json.loads(Path(plan['execution']).read_text())
    assert execution['gate']=='T4' and execution['attempt']==0 and execution['status']=='PREFLIGHT_RESERVED'
    assert not ledger.exists()
    kwargs['gate']='T1';kwargs['preparation_root']=tmp_path/'wrong'
    with pytest.raises(ValueError,match='evaluation-context'):m.prepare(**kwargs)
