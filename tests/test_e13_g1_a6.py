"""Check that A6 waives only batch 2 while preserving G1's immutable fitting body and single attempt."""
from pathlib import Path
import json,sys
import pytest
P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1'
sys.path.insert(0,str(P))
import g1_a6 as a6


def refs(tmp_path):
    values={'lp1':{'status':'PASS','admission_statistics_computed':True},
        'calibration':{'status':'FROZEN','F2':.75,'g1_lock_sha256':'original','strict_forecast_admitted':False,'C_calibration_admitted':False},
        'h2_f2_a6':{'condition':'v2-S2','H2':{'status':'UNAVAILABLE','predictor':None,'auc':None},
            'F2':{'status':'UNAVAILABLE','prospectively_frozen_value':.75,'observed':None},
            'batch2':{'status':'SKIPPED_A6','responses':0,'armed':False},'disable_arm_C':True}}
    result={}
    for name,value in values.items():
        if name=='h2_f2_a6':value['calibration_sha256']=result['calibration']['sha256']
        p=tmp_path/(name+'.json');p.write_text(json.dumps(value));result[name]={'path':str(p),'sha256':a6.digest(p)}
    return result


def test_waiver_accepts_null_forecast_without_a_batch(tmp_path):
    r=refs(tmp_path);assert a6.check_order(r,{'self_sha256':'original'})['h2_f2_a6']['H2']['predictor']is None


@pytest.mark.parametrize('name,key,value',[('lp1','status','FAIL'),('calibration','F2',.6),
    ('calibration','strict_forecast_admitted',True),('calibration','C_calibration_admitted',True),
    ('h2_f2_a6','disable_arm_C',False),('h2_f2_a6','batch2',{'status':'COMPLETE','responses':4312,'armed':True})])
def test_waiver_cannot_change_science_or_reenable_C(tmp_path,name,key,value):
    r=refs(tmp_path);p=Path(r[name]['path']);v=json.loads(p.read_text());v[key]=value;p.write_text(json.dumps(v));r[name]['sha256']=a6.digest(p)
    with pytest.raises(ValueError):a6.check_order(r,{'self_sha256':'original'})


def test_fit_body_is_identical_to_frozen_driver():
    def body(name):
        s=(P/name).read_text();return s[s.index('    root=Path(root);root.mkdir'):s.index("\n\nif __name__")].strip()
    assert body('g1_a6.py')==body('g1_driver.py')


def test_partial_forecast_and_attempt_are_retained_once(tmp_path,monkeypatch):
    meta=tmp_path/'metadata';meta.write_text('{"systems":[]}');features=tmp_path/'features';features.write_text('{"t":{"group_id":"g","features":{}}}')
    lock={'self_sha256':'old','input_bindings':{},'bootstrap':{'draws':10000}}
    monkeypatch.setattr(a6,'verify',lambda *args:({'prerequisites':{}},lock,{'policy_metadata':meta,'validation_features':features}))
    monkeypatch.setattr(a6,'load',lambda *args:([{}],set(),{'t':'g'}));calls=[]
    def fail(*args,**kw):
        calls.append(1);kw['forecast_sink']({'scheme':'grouped_tasks'});raise RuntimeError('authored interruption')
    monkeypatch.setattr(a6,'run_forecast',fail)
    root=tmp_path/'fit'
    with pytest.raises(RuntimeError):a6.run('lock',tmp_path,'revision',root)
    assert (root/'grouped_tasks.forecasts.json').exists()
    assert json.loads((root/'result.json').read_text())['status']=='INCONCLUSIVE'
    with pytest.raises(FileExistsError):a6.run('lock',tmp_path,'revision',root)
    assert len(calls)==1
