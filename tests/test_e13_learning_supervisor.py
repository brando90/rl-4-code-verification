"""Check canonical learning reservations and bounded child cleanup without graphics-device work."""
from pathlib import Path
import importlib.util
import json
import socket
import sys
import time

import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_learning_supervisor',PHASE/'learning_supervisor.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(tmp_path,monkeypatch):
    ledger=tmp_path/'ledger';root=ledger/'pilot/B/1301';(root/'update_00001').mkdir(parents=True)
    run={'phase':'pilot','arm':'B','run_seed':1301,'execution_lock':{'sha256':'lock-sha'}}
    (root/'admission.json').write_text(json.dumps({**{k:run[k] for k in ('phase','arm','run_seed')},'status':'ADMITTED','execution_lock_sha256':'lock-sha'}))
    lease={'id':'owned','phase':'v2-S2-learning-pilot','owner':'e13v2','status':'ACTIVE',
           'host':socket.gethostname().split('.')[0],'started_unix':time.time(),'expires_unix':time.time()+1000}
    lease_root=tmp_path/'leases';lease_root.mkdir();lease_path=lease_root/'owned.json';lease_path.write_text(json.dumps(lease))
    config={'stage':'generate','arm':'B','run_seed':1301,'learning_phase':'pilot','condition':'v2-S2','update':1,
            'lease_path':str(lease_path),'lease_id':'owned','python':sys.executable}
    cp=tmp_path/'config.json';cp.write_text(json.dumps(config))
    reservation=root/'update_00001/generate.json'
    reservation.write_text(json.dumps({'execution_sha256':'lock-sha','stage':'generate','update':1,
        'inputs':{'configuration_sha256':m.digest(cp),'lease_id':'owned','maximum_seconds':300}}))
    deps=[PHASE/'learning_supervisor.py',PHASE/'learning_runtime.py',PHASE.parent/'phase1/device_binding.py',
          PHASE.parent/'phase1/lp1.py',PHASE.parent/'phase1/anchor_lease.py']
    execution={'bindings':[{'path':str(p),'sha256':m.digest(p)} for p in deps],'configuration':{'ledger':str(ledger)}}
    monkeypatch.setattr(m,'verify_learning',lambda _:({},execution,'science'))
    plan={'run':run,'stage':'generate','config':str(cp),'reservation':str(reservation),'lease_root':str(lease_root),
          'maximum_seconds':300,'dispatch_root':str(tmp_path/'dispatch'),'environment':{}}
    return plan,config,lease,root


def test_exclusive_reservation_and_canonical_local_lease_required(tmp_path,monkeypatch):
    plan,config,lease,root=fixture(tmp_path,monkeypatch)
    assert m.authorize(plan)[1]==lease
    cp=Path(plan['config']);config['run_seed']=1302;cp.write_text(json.dumps(config))
    with pytest.raises(ValueError,match='identity changed'):m.authorize(plan)
    config['run_seed']=1301;cp.write_text(json.dumps(config))
    (root/'terminal.json').write_text('{}')
    with pytest.raises(ValueError,match='already terminal'):m.authorize(plan)


def test_missing_run_admission_and_altered_resource_reservation_refused(tmp_path,monkeypatch):
    plan,config,lease,root=fixture(tmp_path,monkeypatch)
    admission=root/'admission.json';saved=admission.read_text();admission.write_text('{}')
    with pytest.raises(ValueError,match='immutable admission'):m.authorize(plan)
    admission.write_text(saved);plan['maximum_seconds']=301
    with pytest.raises(ValueError,match='resource reservation changed'):m.authorize(plan)


def test_real_child_failure_retains_receipts_and_releases_only_after_verified_cleanup(tmp_path,monkeypatch):
    plan,config,lease,root=fixture(tmp_path,monkeypatch)
    # Exercise a real non-GPU subprocess; the dummy runtime fails immediately.
    dummy=tmp_path/'runtime';dummy.mkdir();(dummy/'learning_runtime.py').write_text('raise SystemExit(7)\n')
    monkeypatch.setattr(m,'authorize',lambda _: (config,lease,{}));monkeypatch.setattr(m,'HERE',dummy)
    monkeypatch.setattr(m,'launch_environment',lambda *_:{'CUDA_VISIBLE_DEVICES':'2'})
    calls=[]
    monkeypatch.setattr(m,'cleanup',lambda marker:calls.append(('cleanup',marker)) or {'verified':True,'signals':[]})
    monkeypatch.setattr(m,'release',lambda root,marker,**kw:calls.append(('release',marker,kw['cleanup_verified'])) or True)
    result=m.launch(plan)
    assert result['status']=='INCOMPLETE_INFRA' and result['worker_exit_code']==7 and result['released']
    assert calls==[('cleanup','owned'),('release','owned',True)]
    dispatch=Path(plan['dispatch_root'])
    assert json.loads((dispatch/'launch.json').read_text())['visible_index']=='2'
    assert (dispatch/'process.json').exists() and (dispatch/'cleanup.json').exists()
    with pytest.raises(FileExistsError):m.launch(plan)


def test_expired_lease_cleanup_failure_keeps_reservation_unreleased(tmp_path,monkeypatch):
    plan,config,lease,root=fixture(tmp_path,monkeypatch);lease['expires_unix']=time.time()-1
    monkeypatch.setattr(m,'authorize',lambda _: (config,lease,{}))
    monkeypatch.setattr(m,'launch_environment',lambda *_:{'CUDA_VISIBLE_DEVICES':'4'})
    monkeypatch.setattr(m,'cleanup',lambda _: {'verified':False,'signals':[]})
    monkeypatch.setattr(m,'release',lambda root,marker,**kw:False if not kw['cleanup_verified'] else pytest.fail('unsafe release'))
    result=m.launch(plan)
    assert result['status']=='CLEANUP_REQUIRED' and not result['released'] and result['error_type']=='TimeoutError'
    assert not (Path(plan['dispatch_root'])/'process.json').exists()
