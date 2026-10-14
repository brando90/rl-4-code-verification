"""Refuse changed runtime inputs and incomplete cleanup before admitting LP-1."""
import importlib.metadata
import json
import os
from pathlib import Path
import socket
import sys
import time
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1'
sys.path.insert(0, str(ROOT))
import runtime
import lp1


def test_runtime_requires_every_export_input_and_exact_version(tmp_path):
    model = tmp_path/'model'; model.mkdir(); (model/'weights.bin').write_bytes(b'not a real model')
    files = [ROOT/name for name in ('runtime.py','panel.py','probability.py','lp1.py','device_binding.py')]
    config = {'model':str(model), 'runtime_versions':{'numpy':importlib.metadata.version('numpy')}}
    for name in ('manifest','train_ids','policy_config'):
        path=tmp_path/name; path.write_text('synthetic'); config[name]=str(path); files.append(path)
    files.append(model/'weights.bin')
    config['bindings']=[{'path':str(p),'sha256':runtime.digest(p)} for p in files]
    runtime.check_bindings(config)
    missing = {**config,'bindings':config['bindings'][:-1]}
    with pytest.raises(ValueError,match='omits required'): runtime.check_bindings(missing)
    (model/'weights.bin').write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash mismatch'): runtime.check_bindings(config)
    (model/'weights.bin').write_bytes(b'not a real model')
    config['runtime_versions']['numpy']='not-the-installed-version'
    with pytest.raises(ValueError,match='version mismatch'): runtime.check_bindings(config)


def test_foreign_process_on_target_uuid_refuses_model_call(tmp_path, monkeypatch):
    lease = tmp_path/'lease.json'
    lease.write_text(json.dumps({'status':'ACTIVE','owner':'e13v2','host':socket.gethostname().split('.')[0],
                                'expires_unix':time.time()+100,'uuid':'GPU-fixture','index':0,'id':'synthetic-execution'}))
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','0')
    monkeypatch.setenv('E13_EXECUTION_ID','synthetic-execution')
    monkeypatch.setattr(runtime,'check_visible_device',lambda _:None)
    monkeypatch.setattr(runtime.subprocess,'run',lambda *args,**kw: SimpleNamespace(stdout=f'GPU-fixture, {os.getpid()}\n'))
    with pytest.raises(RuntimeError,match='another execution'):
        runtime.check_lease({'lease_path':str(lease)})


def test_cleanup_failure_cannot_leave_a_passed_admission(tmp_path, monkeypatch):
    generation = tmp_path/'generation'; generation.mkdir()
    for i in range(8):
        row={'cell_id':str(i),'split':'train','prompt_token_ids':[1],'output_token_ids':[2],
             'trainer_input_ids':[1,2],'trainer_token_mask':[0,1],'finish_reason':'stop',
             'generation_logprobs':[-1.],'trainer_logprobs':[0.,-1.]}
        (generation/f'{i:05d}.probability.json').write_text(json.dumps(row))
    lease=tmp_path/'lease.json';lease.write_text(json.dumps({'id':'fixture','expires_unix':time.time()+100}))
    manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps({'terminal_token_ids':[2]}))
    config={'lease_path':str(lease),'manifest':str(manifest),'generation_root':str(generation),
            'attempt_root':str(tmp_path/'attempt'),'maximum_seconds':100,'python':'fixture','route':'synthetic'}
    path=tmp_path/'config.json';path.write_text(json.dumps(config))
    monkeypatch.setenv('E13_EXECUTION_ID','fixture')
    monkeypatch.setattr(lp1,'check_bindings',lambda _:None)
    monkeypatch.setattr(lp1,'check_lease',lambda _:None)
    def stage(*args, **kwargs):
        if args[0][-1] == 'preflight':
            (tmp_path/'attempt/preflight.json').write_text('{"status":"PASS"}')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(lp1.subprocess,'run',stage)
    clean=iter([True,True,True,False])
    monkeypatch.setattr(lp1,'cleanup',lambda _: {'verified':next(clean),'signals':[]})
    result=lp1.run(path)
    assert result['status']=='INCOMPLETE' and result['probability_status']=='PASS'
    with pytest.raises(FileExistsError):lp1.run(path)
