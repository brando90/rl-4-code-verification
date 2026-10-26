"""Route learning stages through the admitted numerical runtime and bound token-prefix state."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_learning_runtime',PHASE/'learning_runtime.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_bound_main_prefix_and_pilot_dispatch_preserve_same_runtime(tmp_path,monkeypatch):
    calls=[]
    monkeypatch.setattr(m,'bound',lambda config,path:Path(path))
    monkeypatch.setattr(m,'verify',lambda config,stage:calls.append(('verify',stage)))
    monkeypatch.setattr(m,'generate',lambda config,cells,**kw:kw)
    cells=tmp_path/'cells.json';cells.write_text(json.dumps([{'arm':'A','run_seed':13011,'update':1}]))
    state=tmp_path/'state.json';state.write_text(json.dumps({'generated_tokens':1,'next_target':10}))
    config={'learning_phase':'main','arm':'A','run_seed':13011,'update':1,'cells_path':str(cells),
            'budget_state':str(state),'stage_root':str(tmp_path/'generation')}
    result=m.run(config,'generate')
    assert result['budget_state']=={'generated_tokens':1,'next_target':10} and calls==[('verify','generate')]
    config['learning_phase']='pilot'
    with pytest.raises(ValueError,match='no token boundary'):m.run(config,'generate')
    config.pop('budget_state');assert m.run(config,'generate')['budget_state'] is None
    config['arm']='B'
    with pytest.raises(ValueError,match='another learning'):m.run(config,'generate')


def test_partial_complete_group_update_uses_same_installed_trainer_path(tmp_path,monkeypatch):
    calls=[]
    monkeypatch.setattr(m,'bound',lambda config,path:Path(path));monkeypatch.setattr(m,'verify',lambda *_:None)
    monkeypatch.setattr(m,'technical_run',lambda config,stage:calls.append(stage))
    groups=tmp_path/'groups.json';groups.write_text(json.dumps([{'group_index':0,'rows':[]}]))
    config={'learning_phase':'main','arm':'B','groups_path':str(groups)}
    m.run(config,'update');assert calls==['update']
    groups.write_text('[]')
    with pytest.raises(ValueError,match='complete prompt groups'):m.run(config,'update')
    assert calls==['update']
