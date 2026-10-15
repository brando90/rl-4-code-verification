"""Keep diagnostic generation fixed to its own 32 train cells and separate from learning-token accounting."""
import importlib.util
import json
from pathlib import Path
import sys
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));spec=importlib.util.spec_from_file_location('e13_monitor_runtime',PHASE/'monitor_runtime.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(tmp_path):
    cells=[{'cell_id':str(i),'audit_id':str(i),'task_id':f'authored_{i}','group_id':str(i),
            'split':'train','arm':'B','run_seed':1301,'update':10,'sample':0} for i in range(32)]
    snapshot={'condition':'v2-S2','stage':'PILOT_MONITOR_SNAPSHOT','declared':32,'frozen_before_generation':True,
              'arm':'B','run_seed':1301,'update':10,'cells':cells}
    path=tmp_path/'snapshot.json';path.write_text(json.dumps(snapshot))
    cell_path=tmp_path/'cells.json';cell_path.write_text(json.dumps(cells))
    config={'arm':'B','run_seed':1301,'update':10,'stage':'monitor_generate','snapshot':str(path),
            'cells_path':str(cell_path),'stage_root':str(tmp_path/'generated')}
    return snapshot,config


def test_monitor_never_admits_another_arm_seed_or_nontrain_cell(tmp_path):
    snapshot,config=fixture(tmp_path)
    assert len(m.validate(snapshot,config))==32
    config['run_seed']=13011
    with pytest.raises(ValueError,match='undeclared'):m.validate(snapshot,config)
    snapshot,config=fixture(tmp_path);snapshot['cells'][0]['split']='test'
    with pytest.raises(ValueError,match='identity'):m.validate(snapshot,config)
    snapshot,config=fixture(tmp_path);snapshot['cells'].pop()
    with pytest.raises(ValueError,match='population'):m.validate(snapshot,config)


def test_monitor_uses_unchanged_generator_and_zero_learning_tokens(tmp_path,monkeypatch):
    snapshot,config=fixture(tmp_path);calls=[]
    monkeypatch.setattr(m,'bound',lambda config,path:Path(path))
    monkeypatch.setattr(m,'verify',lambda config,stage:calls.append(('verify',stage,config['stage'])))
    def generate(config,cells,root):
        calls.append(('generate',len(cells),config['stage']));Path(root).mkdir()
        return {'condition':'v2-S2','status':'COMPLETE','generated_tokens':123,'completed':32,'optimizer_updates':0}
    monkeypatch.setattr(m,'generate',generate)
    result=m.run(config,'monitor_generate')
    assert calls==[('verify','generate','generate'),('generate',32,'generate')]
    assert result['learning_rollout_tokens']==0 and result['diagnostic_generated_tokens']==123
    assert result['optimizer_updates']==0
    assert json.loads((Path(config['stage_root'])/'monitor_result.json').read_text())==result


def test_modified_cells_rejected_before_generator_or_device_verification(tmp_path,monkeypatch):
    snapshot,config=fixture(tmp_path);cells=snapshot['cells'];cells[0]['cell_id']='replaced'
    Path(config['cells_path']).write_text(json.dumps(cells))
    monkeypatch.setattr(m,'bound',lambda config,path:Path(path))
    monkeypatch.setattr(m,'verify',lambda *a:pytest.fail('changed snapshot reached device verification'))
    monkeypatch.setattr(m,'generate',lambda *a,**kw:pytest.fail('changed snapshot generated'))
    with pytest.raises(ValueError,match='pre-response freeze'):m.run(config,'monitor_generate')
