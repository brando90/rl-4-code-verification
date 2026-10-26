"""Admit unchanged technical execution only with a published sound A6 result and the exact null-predictor waiver."""
from pathlib import Path
import inspect,json,sys
import pytest
P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P))
import a6_technical_driver as m
import technical_driver as original
from test_e13_a6_phase2_admission import fixture as gates


def fixture(tmp_path,monkeypatch):
    probe=tmp_path/'probe.json';probe.write_text('[]')
    config={'condition':'v2-S2','host':m.socket.gethostname().split('.')[0],'runtime':{},
        'probability_probe':m.reference(probe),'update_probe':m.reference(probe)}
    path=tmp_path/'config.json';path.write_text(json.dumps(config))
    paths=[path,P/'a6_technical_driver.py',P/'a6_phase2_admission.py',P/'technical_resources.py',
        P/'technical_stage.py',P/'technical_measurements.py',P/'rollout_groups.py',P/'costs.py']
    lock={'bindings':m.bindings(paths),'science':{k:config[k]for k in ('probability_probe','update_probe')},
        'phase1_results':dict(zip(('G0','LP1','calibration','G1','H2','A6'),gates())),
        'eligible_arms':['A','B','P']}
    monkeypatch.setattr(m,'pilot_lock',lambda *a:(lock,'authored-science'))
    monkeypatch.setattr(m,'published',lambda ref,repo:ref)
    import resource_lease
    monkeypatch.setattr(resource_lease,'verify_allocation',lambda p:({'routes':{config['host']:{}}},'authored-allocation'))
    plan={'LP':{},'repository':str(tmp_path),'configuration':str(path),'gate':'T1',
        'resource_plan':{'allocation_plan':{}},'prerequisites':{}}
    return plan,lock


def test_sound_a6_admits_technical_preparation_without_fabricating_h2(tmp_path,monkeypatch):
    plan,lock=fixture(tmp_path,monkeypatch)
    result,_,science=m.authorize(plan)
    assert result is lock and science=='authored-science'
    assert result['phase1_results']['H2']['status']=='UNAVAILABLE'


def test_unsound_or_absent_diagnostic_blocks_even_when_eligible_arms_match(tmp_path,monkeypatch):
    plan,lock=fixture(tmp_path,monkeypatch);lock['phase1_results']['A6']['status']='UNSOUND'
    with pytest.raises(ValueError,match='sound'):m.authorize(plan)
    del lock['phase1_results']['A6']
    with pytest.raises(KeyError):m.authorize(plan)


def test_admission_source_must_be_frozen_in_the_pilot_lock(tmp_path,monkeypatch):
    plan,lock=fixture(tmp_path,monkeypatch)
    lock['bindings']=[b for b in lock['bindings']if b['path']!=str(P/'a6_phase2_admission.py')]
    with pytest.raises(ValueError,match='not bound'):m.authorize(plan)


def test_gate_measurement_and_execution_functions_are_identical_to_frozen_predecessor():
    # This is the protocol's preservation check: A6 changes prerequisites,
    # never technical thresholds, stage chronology or missingness handling.
    names=[name for name,value in vars(original).items()if inspect.isfunction(value)
        and value.__module__==original.__name__ and name!='authorize']
    assert names
    for name in names:assert inspect.getsource(getattr(m,name))==inspect.getsource(getattr(original,name))
    assert m.ORDER==original.ORDER and m.KINDS==original.KINDS
