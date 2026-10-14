"""Exercise publication fencing, automatic dispatch and release without model calls."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1'
sys.path.insert(0, str(ROOT))
import dispatch


def test_lock_must_be_the_published_blob_and_bind_configuration(tmp_path):
    subprocess.run(['git','init','-q',str(tmp_path)], check=True)
    data = tmp_path/'input'; data.write_text('fixed')
    config = tmp_path/'config.json'; config.write_text('{"routes":[]}')
    g0 = tmp_path/'g0.json'; g0.write_text('{"status":"PASS"}')
    lock = tmp_path/'lock.json'
    lock.write_text(json.dumps({'gate':'LP1','status':'FROZEN','G0_result':str(g0),
                                'bindings':[{'path':str(data), 'sha256':dispatch.digest(data)},
                                            {'path':str(g0),'sha256':dispatch.digest(g0)}],
                                'configuration_sha256':dispatch.digest(config)}))
    subprocess.run(['git','add','lock.json'],cwd=tmp_path,check=True)
    subprocess.run(['git','-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid',
                    'commit','-qm','fixture'],cwd=tmp_path,check=True)
    revision = subprocess.check_output(['git','rev-parse','HEAD'],cwd=tmp_path,text=True).strip()
    subprocess.run(['git','update-ref','refs/remotes/origin/main',revision],cwd=tmp_path,check=True)
    plan = {'repository':str(tmp_path),'lock':str(lock),'published_revision':revision,'configuration':str(config)}
    assert dispatch.published(plan) == {'routes':[]}
    data.write_text('changed')
    with pytest.raises(RuntimeError,match='input changed'): dispatch.published(plan)
    data.write_text('fixed'); config.write_text('{}')
    with pytest.raises(RuntimeError,match='configuration'): dispatch.published(plan)
    config.write_text('{"routes":[]}'); lock.write_text(lock.read_text()+' ')
    with pytest.raises(RuntimeError,match='published revision'): dispatch.published(plan)


@pytest.mark.parametrize('exit_code,clean', [(0,True),(1,True),(1,False)])
def test_single_automatic_attempt_and_remote_lease_retirement(tmp_path, monkeypatch, exit_code, clean):
    root = tmp_path/'state'; registry = tmp_path/'leases'; registry.mkdir()
    (registry/'registry.json').write_text(json.dumps({'owner':'e13v2','leases':[],'device_hours':0}))
    plan_path = tmp_path/'plan.json'
    plan = {'state_root':str(root),'lease_root':str(registry),'watchdog_root':str(tmp_path/'watch'),
            'watchdog_run':'fixture','published_revision':'fixed'}
    plan_path.write_text(json.dumps(plan))
    config = {'routes':[{'host':'fixture','storage_required_bytes':1,'minimum_memory_mib':1,
                         'runtime':{'python':'fixture-python','attempt_root':'fixture-result'},
                         'lease_path':'fixture-lease','config_path':'fixture-config','lp1_script':'fixture-script',
                         'environment':{}}], 'foreign_registries':[], 'reservation_bindings':[],
              'maximum_seconds':1800, 'cumulative_limit_hours':1.}
    inventory = {'host':'fixture','inventory_complete':True,'idle_device_indices':[0],
                 'local_storage':{'available_bytes':100},'devices':[{'index':0,'uuid':'GPU-fixture','memory_mib':81920}]}
    calls = []; retired = []
    monkeypatch.setattr(dispatch,'published',lambda _: config)
    monkeypatch.setattr(dispatch,'observe',lambda _: inventory)
    monkeypatch.setattr(dispatch.subprocess,'run',lambda *a,**kw: SimpleNamespace(returncode=0))
    def command(host, argv, **kw):
        calls.append(argv)
        if argv[0] == 'env': return SimpleNamespace(returncode=exit_code)
        return SimpleNamespace(stdout=json.dumps({'status':'PASS','cleanup_verified':clean}),returncode=0)
    monkeypatch.setattr(dispatch,'command',command)
    monkeypatch.setattr(dispatch,'retire_remote_lease',lambda *args: retired.append(args))
    receipt = dispatch.dispatch(plan_path)
    assert receipt['status'] == ('PASS' if exit_code == 0 else 'INCOMPLETE')
    assert bool(retired) == clean
    assert json.loads((registry/'registry.json').read_text())['leases'][0]['status'] == ('RELEASED' if clean else 'CLEANUP_REQUIRED')
    assert dispatch.dispatch(plan_path)['status'] == 'ATTEMPT_ALREADY_RECORDED_NO_RETRY'
    assert sum(argv[0] == 'env' for argv in calls) == 1
