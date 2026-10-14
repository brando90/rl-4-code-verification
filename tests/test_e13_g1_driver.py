"""Fence G1 fitting behind published methods, immutable inputs and independent-batch chronology."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1'
sys.path.insert(0,str(ROOT))
import g1_driver as driver


def publish(path):
    subprocess.run(['git','init','-q',str(path.parent)],check=True)
    subprocess.run(['git','add',path.name],cwd=path.parent,check=True)
    subprocess.run(['git','-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid',
                    'commit','-qm','method'],cwd=path.parent,check=True)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=path.parent,text=True).strip()
    subprocess.run(['git','update-ref','refs/remotes/origin/main',revision],cwd=path.parent,check=True)
    return revision


def test_changed_method_or_feature_sources_rejected_before_fit(tmp_path):
    source=tmp_path/'feature.txt';source.write_text('synthetic source')
    sources=tmp_path/'sources.json';sources.write_text(json.dumps([{'path':str(source),'sha256':driver.digest(source)}]))
    lock={'gate':'G1','status':'FROZEN','completion_refits':False,'bootstrap':{'draws':10000},
          'library_versions':{'python':platform.python_version(),'numpy':importlib.metadata.version('numpy')},
          'bindings':[{'path':str(ROOT/n),'sha256':driver.digest(ROOT/n)}
                      for n in ['g1_driver.py','g1_inputs.py','nested_a3.py','g1_bounds.py']],
          'input_bindings':{'source_features':{'path':str(sources),'sha256':driver.digest(sources)}}}
    path=tmp_path/'lock.json';path.write_text(json.dumps(lock));revision=publish(path)
    driver.verify_fit_lock(path,tmp_path,revision)
    source.write_text('changed')
    with pytest.raises(ValueError,match='feature source'):driver.verify_fit_lock(path,tmp_path,revision)
    source.write_text('synthetic source');path.write_text(path.read_text()+' ')
    with pytest.raises(ValueError,match='published bytes'):driver.verify_fit_lock(path,tmp_path,revision)


def prerequisites(tmp_path):
    objects={'lp1':{'status':'PASS','admission_statistics_computed':True},
             'calibration':{'status':'FROZEN','F2':.6,'g1_lock_sha256':'method'},
             'batch2':{'status':'COMPLETE','batch':'full2','declared':4312,'accounted':4312}}
    bindings={}
    for name,obj in objects.items():
        if name=='batch2':obj['calibration_sha256']=bindings['calibration']['sha256']
        p=tmp_path/(name+'.json');p.write_text(json.dumps(obj))
        bindings[name]={'path':str(p),'sha256':driver.digest(p)}
    return bindings


@pytest.mark.parametrize('defect',['lp1_preflight_only','unfrozen_F2','wrong_calibration','incomplete_accounting'])
def test_chronology_refuses_unadmitted_fit(tmp_path,defect):
    bindings=prerequisites(tmp_path);driver.check_order(bindings,{'self_sha256':'method'})
    name='lp1' if defect=='lp1_preflight_only' else 'calibration' if defect=='unfrozen_F2' else 'batch2'
    p=Path(bindings[name]['path']);obj=json.loads(p.read_text())
    if defect=='lp1_preflight_only':obj['admission_statistics_computed']=False
    if defect=='unfrozen_F2':obj.pop('F2')
    if defect=='wrong_calibration':obj['calibration_sha256']='other'
    if defect=='incomplete_accounting':obj['accounted']=4311
    p.write_text(json.dumps(obj));bindings[name]['sha256']=driver.digest(p)
    with pytest.raises(ValueError):driver.check_order(bindings,{'self_sha256':'method'})


def test_accounted_missing_H2_cells_do_not_suppress_independent_G1(tmp_path):
    bindings=prerequisites(tmp_path);p=Path(bindings['batch2']['path']);obj=json.loads(p.read_text())
    obj.update(status='INCOMPLETE',measured=4311,missing=1);p.write_text(json.dumps(obj));bindings['batch2']['sha256']=driver.digest(p)
    assert driver.check_order(bindings,{'self_sha256':'method'})['batch2']['missing']==1


def test_partial_fit_remains_one_attempt_and_retains_forecasts(tmp_path,monkeypatch):
    method=tmp_path/'method.json';method.write_text('{}')
    metadata=tmp_path/'metadata.json';metadata.write_text('{"systems":[]}')
    features=tmp_path/'features.json';features.write_text('{"t":{"group_id":"g","features":{}}}')
    prereqs=tmp_path/'prerequisites.json';prereqs.write_text('{}')
    lock={'input_bindings':{},'bootstrap':{'draws':10000}}
    monkeypatch.setattr(driver,'verify_fit_lock',lambda *a:(lock,{'policy_metadata':metadata,'validation_features':features}))
    monkeypatch.setattr(driver,'check_order',lambda *a:None)
    monkeypatch.setattr(driver,'load',lambda *a:([{}],set(),{'t':'g'}))
    calls=[]
    def fail(*a,**kw):
        calls.append(1);kw['forecast_sink']({'scheme':'grouped_tasks','predictions':{'M0':[.5]}})
        raise RuntimeError('synthetic fit interruption')
    monkeypatch.setattr(driver,'run_forecast',fail)
    root=tmp_path/'run'
    with pytest.raises(RuntimeError):driver.run(method,tmp_path,'fixed',prereqs,root)
    assert (root/'grouped_tasks.forecasts.json').exists()
    assert json.loads((root/'result.json').read_text())['status']=='INCONCLUSIVE'
    with pytest.raises(FileExistsError):driver.run(method,tmp_path,'fixed',prereqs,root)
    assert len(calls)==1
