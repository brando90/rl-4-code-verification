"""Keep real training identities, frozen oracle behavior and durable scoring receipts."""
import importlib.util,json,os,sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));spec=importlib.util.spec_from_file_location('e13_training_scoring',PHASE/'score_training.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(tmp_path):
 ids=tmp_path/'train.txt';ids.write_text('authored\n');generation=tmp_path/'generation';generation.mkdir()
 cell={'cell_id':'authored/0','task_id':'authored','split':'train','sample':0,'arm':'B','run_seed':1301,'update':1,'group_index':0}
 config={'train_ids':str(ids),'root':str(tmp_path/'scores'),'generation_root':str(generation)}
 return cell,config,generation/'00000.generation.json'


def test_completed_training_score_is_recovered_without_second_measurement(tmp_path):
 cell,config,path=fixture(tmp_path);path.write_text(json.dumps(cell));bound={str(path):m.digest(path)};calls=[]
 def execute(job,root,marker,slots):
  calls.append(job);result={**job['identity'],'status':'measured','strict':1,'cleanup_verified':True}
  m.write_new(root/'result.json',result);return result
 first=m.score_cell(cell,0,config,bound,'fixed-execution',None,executor=execute)
 assert first==m.score_cell(cell,0,config,bound,'fixed-execution',None,executor=lambda *args:pytest.fail('rescore'))
 assert len(calls)==1 and first['arm']=='B' and 'policy' not in first
 with pytest.raises(ValueError,match='binding changed'):m.score_cell(cell,0,config,bound,'changed',None)
 path.write_text('{}')
 with pytest.raises(ValueError,match='changed rollout'):m.score_cell(cell,0,config,bound,'fixed-execution',None)


def test_missing_generation_stays_missing_and_cannot_be_replaced(tmp_path):
 cell,config,path=fixture(tmp_path);result=m.score_cell(cell,0,config,{},'fixed',None)
 assert result['status']=='missing_generation' and 'strict' not in result
 path.write_text(json.dumps(cell))
 with pytest.raises(ValueError,match='cannot be replaced'):m.score_cell(cell,0,config,{str(path):m.digest(path)},'fixed',None)


def test_heldout_cell_refused_before_extraction(tmp_path,monkeypatch):
 cell,config,path=fixture(tmp_path);cell['split']='test'
 import rl4cv.veribench.exp103 as extraction
 monkeypatch.setattr(extraction,'extract_lean',lambda *a,**k:pytest.fail('held-out source read'))
 with pytest.raises(ValueError,match='train-only'):m.score_one(cell,tmp_path,config)


def test_real_frozen_scorer_keeps_capped_training_success(tmp_path):
 required=('VERIBENCH_ROOT','E13_LAKE_DIR','E13_SCORER_ROOT')
 if not all(os.environ.get(k) and Path(os.environ[k]).exists() for k in required):
  if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION')=='1':pytest.fail('required Lean routes missing')
  pytest.skip('pinned Lean routes unavailable')
 cell,config,path=fixture(tmp_path)
 authored=ROOT/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/R0_attempt_2/fixtures/valid.lean'
 cell.update(completion='```lean\n'+authored.read_text()+'\n```',required_paths=['solution.lean'],at_token_cap=True)
 config.update(veribench=os.environ['VERIBENCH_ROOT'],lake=os.environ['E13_LAKE_DIR'],scorer=os.environ['E13_SCORER_ROOT'])
 result=m.score_one(cell,tmp_path,config)
 assert result['status']=='measured' and result['strict']==1 and result['at_token_cap']
 assert result['p']['numerator']==result['p']['denominator']>0
