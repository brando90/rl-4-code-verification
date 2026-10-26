"""Preserve full evaluation denominators, frozen scoring configuration and completed parent writes."""
from pathlib import Path
import json,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));sys.path.insert(0,str(Path(__file__).parent))
import evaluation_processing as m
from evaluation_contract import identities


def fixture(tmp_path,monkeypatch):
    cells=identities([f'authored_{i:03d}' for i in range(135)],'validation',arm='A',run_seed=13011,boundary=1)
    manifest={'cells':cells};value={'generation':{c['cell_id']:None for c in cells}}
    root=tmp_path/'evaluation';root.mkdir();(root/'generation_terminal.json').write_text(json.dumps(value))
    snapshot={'purpose':'validation','arm':'A','run_seed':13011,'boundary':1,'LP_sha256':'LP','L2_sha256':'L2',
        'model_binding_sha256':'model','boundary_receipt_sha256':'boundary','evaluation_contract_sha256':'contract',
        'configuration':{'allowlist':'authored-allowlist'}}
    config={'scoring':{'lake':'authored-lake','scorer':'authored-scorer','veribench':'authored-veribench','controller_fence':'authored-fence'}}
    inputs=root/'inputs.json';inputs.write_text(json.dumps({'snapshot_sha256':'snapshot','generation':value['generation']}))
    lock={'gate':'EVALUATION_SCORE_INPUTS','condition':'v2-S2','status':'FROZEN','snapshot_sha256':'snapshot',
        **{k:snapshot[k] for k in ('arm','run_seed','boundary','purpose','L2_sha256')},
        'configuration':{**config['scoring'],'root':str(root/'strict/cells'),'allowlist':'authored-allowlist','split':'validation','purpose':'validation'},
        'generation_inputs':str(inputs),'bindings':[{'path':str(inputs),'sha256':m.digest(inputs)}]}
    plan={'learning':{'run':{'repository':'authored'}},'snapshot_lock':{'sha256':'snapshot'},'score_lock':{'sha256':'score'}}
    monkeypatch.setattr(m,'context',lambda _:(snapshot,config,root,manifest,value))
    monkeypatch.setattr(m,'published',lambda *_:lock)
    measured=[]
    def scorer(manifest,config,generations,sha):
        path=Path(config['root'])/'result.json'
        if path.exists():return json.loads(path.read_text())
        rows=[{**c,'strict':None if i==0 else int(i==1)} for i,c in enumerate(cells)]
        result={'rows':rows,'cleanup_unresolved':0,'identical_retries':1}
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result));measured.append(True);return result
    monkeypatch.setattr(m,'score_manifest',scorer)
    return plan,lock,root,measured


def test_missing_evaluation_cell_remains_in_full_denominator_and_result_is_recovered(tmp_path,monkeypatch):
    plan,lock,root,measured=fixture(tmp_path,monkeypatch)
    result=m.score(plan);assert result['status']=='INCOMPLETE' and result['summary']['declared']==1080
    assert result['summary']['missing']==1 and result['summary']['measured']==1079
    assert result['summary']['strict_mean_bounds']==[1/1080,2/1080]
    assert result['identical_retries']==1 and m.score(plan)==result and len(measured)==1


def test_changed_scorer_path_cannot_use_a_post_outcome_lock(tmp_path,monkeypatch):
    plan,lock,root,measured=fixture(tmp_path,monkeypatch);lock['configuration']['scorer']='different'
    with pytest.raises(ValueError,match='pre-main settings'):m.score(plan)
    assert not measured


def test_interrupted_terminal_write_recovers_saved_measurements_and_cost(tmp_path,monkeypatch):
    plan,lock,root,measured=fixture(tmp_path,monkeypatch);real=m.write_new
    def fail(path,value):
        if path.name=='terminal.json':raise InterruptedError('authored parent interruption')
        return real(path,value)
    monkeypatch.setattr(m,'write_new',fail)
    with pytest.raises(InterruptedError):m.score(plan)
    before=(root/'strict/cost.json').read_bytes();monkeypatch.setattr(m,'write_new',real)
    result=m.score(plan)
    assert result['summary']['declared']==1080 and len(measured)==1 and (root/'strict/cost.json').read_bytes()==before


def test_scoring_snapshot_cannot_cross_main_runs(tmp_path,monkeypatch):
    plan,lock,root,measured=fixture(tmp_path,monkeypatch);lock['run_seed']=13012
    with pytest.raises(ValueError,match='another snapshot'):m.score(plan)
    assert not measured
