"""Exercise exact complete-group boundaries with authored generation only."""
from pathlib import Path
from importlib.util import spec_from_file_location,module_from_spec
from types import SimpleNamespace
import json,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=spec_from_file_location('e13_learning_generation',PHASE/'learning_generation.py')
m=module_from_spec(spec);spec.loader.exec_module(m)

def setup(tmp_path,monkeypatch,bad=False):
 train=tmp_path/'train';train.write_text('authored\n');seen=[]
 config={'train_ids':str(train),'batch_size':32,'terminal_token_ids':[1],'tokenizer':'authored','model':'authored'}
 cells=[{'cell_id':f'authored/{i}','task_id':'authored','split':'train','sample':i%8,'group_index':i//8,
  'seed':i,'prompt_token_ids':[3,4],'arm':'A','run_seed':13011,'update':1} for i in range(256)]
 class Engine:
  def generate(self,prompts,sampling,use_tqdm):
   seen.append(len(prompts));result=[]
   for i,p in enumerate(prompts):
    tokens=[5,2 if bad and i==1 else 1]
    result.append(SimpleNamespace(prompt_token_ids=p['prompt_token_ids'],outputs=[SimpleNamespace(
      token_ids=tokens,logprobs=[{5:SimpleNamespace(logprob=-.2)},{tokens[-1]:SimpleNamespace(logprob=-.1)}],finish_reason='stop')]))
   return result
 monkeypatch.setattr(m,'check_lease',lambda c:None);monkeypatch.setattr(m,'numerical_dtype',lambda c:'float16')
 monkeypatch.setattr(m,'build_engine',lambda *a:Engine());monkeypatch.setattr(m,'sampler',lambda *a:a)
 monkeypatch.setitem(sys.modules,'transformers',SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a,**k:SimpleNamespace(decode=lambda *a,**k:'authored'))))
 return config,cells,seen

def test_crossing_group_is_retained_and_no_later_group_generated(tmp_path,monkeypatch):
 config,cells,seen=setup(tmp_path,monkeypatch)
 state={'generated_tokens':95,'next_target':100,'update_groups':0,'group_index':0}
 result=m.generate(config,cells,root=tmp_path/'run',budget_state=state)
 assert seen==[8] and result['declared']==8 and result['generated_tokens']==16
 assert result['budget_state_after']['overshoot']==11 and result['ungenerated_prefix_tail']==248
 assert state['generated_tokens']==95
 assert len(json.loads((tmp_path/'run/cells.json').read_text()))==8
 with pytest.raises(FileExistsError):m.generate(config,cells,root=tmp_path/'run',budget_state=state)
 assert seen==[8]

def test_pilot_and_far_target_keep_full_32_groups(tmp_path,monkeypatch):
 config,cells,seen=setup(tmp_path,monkeypatch)
 result=m.generate(config,cells,root=tmp_path/'pilot')
 assert seen==[32]*8 and result['declared']==256
 seen.clear()
 result=m.generate(config,cells,root=tmp_path/'main',budget_state={'generated_tokens':0,'next_target':10**6,'update_groups':0,'group_index':0})
 assert seen==[32]*8 and result['complete_groups']==32 and result['budget_state_after']['update_due']
 assert not result['budget_state_after']['boundary_crossed']

def test_failed_slot_preserves_neighbors_without_refill(tmp_path,monkeypatch):
 config,cells,seen=setup(tmp_path,monkeypatch,bad=True)
 with pytest.raises(ValueError,match='incomplete group'):m.generate(config,cells,root=tmp_path/'run',budget_state={'generated_tokens':0,'next_target':5,'update_groups':0,'group_index':0})
 assert seen==[8] and len(list((tmp_path/'run').glob('*.generation.json')))==7
 assert json.loads((tmp_path/'run/error.json').read_text())['unknown_tokens_not_imputed']

def test_changed_group_or_heldout_refused_before_engine(tmp_path,monkeypatch):
 config,cells,seen=setup(tmp_path,monkeypatch);cells[1]['group_index']=1
 with pytest.raises(ValueError,match='group identity'):m.generate(config,cells,root=tmp_path/'run')
 assert not seen and not (tmp_path/'run').exists()
 cells[1]['group_index']=0;cells[0]['split']='test'
 with pytest.raises(ValueError,match='held-out'):m.generate(config,cells,root=tmp_path/'run')
