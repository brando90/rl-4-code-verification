"""Reject evaluation snapshots from a different main run or a method introduced after learning."""
from pathlib import Path
import importlib.util,json,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));spec=importlib.util.spec_from_file_location('e13_evaluation_authority',PHASE/'evaluation_authority.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(tmp_path,monkeypatch):
    root=tmp_path/'evaluation/A/13011/validation_b1';(root/'freeze').mkdir(parents=True)
    manifest=root/'freeze/manifest.json';manifest.write_text('{}')
    run={'phase':'main','arm':'A','run_seed':13011,'LP':{'sha256':'LP'},'execution_lock':{'sha256':'L2'},'repository':'authored'}
    execution={'bindings':[{'path':str(PHASE/name),'sha256':m.digest(PHASE/name)} for name in m.SOURCES]}
    config={'evaluation':{'root':str(tmp_path/'evaluation'),'allowlists':{'validation':{'path':'authored-ids'}}}}
    main={'condition':'v2-S2','stage':'MAIN_TRAINING','status':'COMPLETE','arm':'A','run_seed':13011,
          'L2_sha256':'L2','boundaries_accounted':4,'cleanup_unresolved':0,
          'boundaries':{'1':{'path':'boundary','sha256':'boundary-sha'}}}
    snapshot={'gate':'EVALUATION_SNAPSHOT','condition':'v2-S2','status':'FROZEN','arm':'A','run_seed':13011,
        'purpose':'validation','boundary':1,'LP_sha256':'LP','L2_sha256':'L2','model':'authored-model',
        'model_binding_sha256':'model-sha','boundary_receipt_sha256':'boundary-sha','main_result':{'name':'main'},
        'bindings':execution['bindings']+[{'path':str(manifest),'sha256':m.digest(manifest)}],
        'configuration':{'root':str(root),'manifest':str(manifest),'allowlist':'authored-ids','learning_configuration':'config'}}
    values={'snapshot':snapshot,'main':main}
    monkeypatch.setattr(m,'learning_authority',lambda _ : ({},execution,config))
    monkeypatch.setattr(m,'published',lambda ref,_:values[ref['name']])
    monkeypatch.setattr(m,'read',lambda _:{'model':'authored-model'})
    monkeypatch.setattr(m,'checkpoint',lambda *_:'model-sha')
    return {'learning':{'run':run,'configuration':'config'},'snapshot_lock':{'name':'snapshot'}},snapshot,execution


def test_snapshot_must_match_its_pre_main_execution_and_model(tmp_path,monkeypatch):
    plan,snapshot,execution=fixture(tmp_path,monkeypatch)
    assert m.authorize(plan)[3] is snapshot
    snapshot['L2_sha256']='other-main'
    with pytest.raises(ValueError,match='another main execution'):m.authorize(plan)
    snapshot['L2_sha256']='L2';snapshot['model_binding_sha256']='other-model'
    with pytest.raises(ValueError,match='selected main boundary'):m.authorize(plan)


def test_method_absent_before_learning_cannot_admit_evaluation(tmp_path,monkeypatch):
    plan,snapshot,execution=fixture(tmp_path,monkeypatch);execution['bindings']=execution['bindings'][1:]
    with pytest.raises(ValueError,match='not bound before main'):m.authorize(plan)


def test_changed_manifest_or_unfrozen_execution_root_is_refused(tmp_path,monkeypatch):
    plan,snapshot,execution=fixture(tmp_path,monkeypatch)
    snapshot['configuration']['root']=str(tmp_path/'different')
    with pytest.raises(ValueError,match='moved from its pre-main'):m.authorize(plan)
    manifest=Path(snapshot['configuration']['manifest']);manifest.write_text('{"changed":true}')
    with pytest.raises(ValueError,match='snapshot binding changed'):m.authorize(plan)
