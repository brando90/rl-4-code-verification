"""Verify that A6 feasibility reads B's actual reward slots and cannot swap in strict labels."""
from pathlib import Path
import importlib.machinery,importlib.util,sys
import pytest
P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P))
import a6_t5_driver as m

def fixture():
 entries=[]
 for update in range(1,31):
  cells=[];files=[];own=[]
  for index in range(256):
   identity={'cell_id':f'1301/{update}/{index}','task_id':f'authored_{index//8}','sample':index%8,'group_index':index//8,'split':'train','arm':'B','run_seed':1301,'update':update}
   score={**identity,'status':'measured','strict':0,'cleanup_verified':True,'e':True,'n_examples':1,'raw_vacuity_hits':0,'d':{'numerator':0,'denominator':1},'p':{'numerator':0,'denominator':1},'t':1.}
   cells.append(score);files.append({'value':{**identity,'output_token_ids':[1,2]}})
   own.append({**identity,'score_status':'measured','reward':m.family_reward(score,0)})
  scoring={'value':{'rows':cells}};groups={'value':[{'rows':own[i:i+8]}for i in range(0,256,8)]}
  entries.append({'seed':1301,'update':update,'scoring':scoring,'generation_files':files,
    'summary':{'value':{'arm':'B','seed':1301,'update':update,'split':'train','declared':256,'status':'ACCOUNTED','measured':256,'strict_successes':0,'generated_tokens':512,'scoring':scoring,'groups':groups}},
    'generation':{'value':{'status':'COMPLETE','completed':256,'generated_tokens':512}},
    'opportunity':{'value':{'status':'ACCOUNTED','arm':'B','run_seed':1301,'update':update,'optimizer_updates':1}},
    'closed_stages':{stage:{'value':{'status':'RUNTIME_EXITED_ZERO','cleanup_verified':True,'arm':'B','run_seed':1301,'update':update}}for stage in ('generate','update','export')}})
 return entries

def test_own_partial_credit_is_used_when_strict_is_zero(monkeypatch):
 monkeypatch.setattr(m,'read',lambda ref:ref['value']);rows,lengths=m.validate_updates(fixture(),30)
 assert len(rows)==30 and len(lengths)==7680
 assert all(r['strict_successes']==0 and all(v>0 for v in r['rewards'])for r in rows)

def test_corrupted_reward_or_stage_cleanup_is_rejected(monkeypatch):
 monkeypatch.setattr(m,'read',lambda ref:ref['value']);entries=fixture()
 own=entries[0]['summary']['value']['groups']['value'][0]['rows'][0];old=own['reward'];own['reward']=0
 with pytest.raises(ValueError,match='own reward differs'):m.validate_updates(entries,30)
 own['reward']=old;entries[0]['closed_stages']['update']['value']['cleanup_verified']=False
 with pytest.raises(ValueError,match='not cleanly closed'):m.validate_updates(entries,30)


def gate_fixture(tmp_path,monkeypatch,horizon=30):
 def put(path,value):
  path.parent.mkdir(parents=True,exist_ok=True);path.write_text(__import__('json').dumps(value));return {'path':str(path),'sha256':m.digest(path)}
 state=put(tmp_path/'state.json',{'condition':'v2-S2','arm':'B','run_seed':1301,'phase':'pilot','status':'WAIT_FOR_T5','completed_updates':horizon,'execution_sha256':'pilot'})
 inputs=put(tmp_path/'inputs.json',{'states':{'1301':state},'updates':[]})
 pilot={'gate':'LEARNING_PILOT','condition':'v2-S2','status':'FROZEN','LP_sha256':'lp','bindings':[{'path':str(p),'sha256':m.digest(p)}for p in (Path(m.__file__).resolve(),P/'a6_t5_measurement.py',P/'schedule.py',P.parent/'reproduction/cell_worker.py')]}
 lock={'gate':'T5_INPUTS','condition':'v2-S2','status':'FROZEN','pilot_execution_lock':{'name':'pilot','sha256':'pilot'},'configuration':{'root':str(tmp_path/'result'),'horizon':horizon,'inputs':inputs},'bindings':[inputs,state]}
 values={'lock':lock,'pilot':pilot,'prior':{'gate':'T5','status':'EXTEND_TO_60','horizon':30,'pilot_execution_sha256':'pilot','arm':'B','seeds':[1301],'metric':'own train reward'}}
 if horizon==60:lock['extension_admission']={'name':'prior'}
 monkeypatch.setattr(m,'published',lambda ref,repo:values[ref['name']])
 rows=[{'arm':'B','seed':1301,'update':i,'split':'train','rewards':[.1 if i<=10 else .12]*256}for i in range(1,horizon+1)]
 monkeypatch.setattr(m,'validate_updates',lambda *args:(rows,[2048]*(horizon*256)))
 return {'repository':'authored','lock':{'name':'lock','sha256':'inputs'}},values


def test_b_gate_is_final_and_never_sets_budget_from_b_lengths(tmp_path,monkeypatch):
 plan,_=gate_fixture(tmp_path,monkeypatch);r=m.run(plan)
 assert r['status']=='PASS'and r['arm']=='B'and r['pilot_slots']==7680 and r['token_budget']is None
 monkeypatch.setattr(m,'t5',lambda *args,**kw:pytest.fail('gate recomputed'))
 with pytest.raises(FileExistsError):m.run(plan)


def test_extension_requires_the_same_b_own_reward_decision(tmp_path,monkeypatch):
 plan,values=gate_fixture(tmp_path,monkeypatch,60);values['prior']['arm']='A'
 with pytest.raises(ValueError,match='extension was not admitted'):m.run(plan)
 assert not (tmp_path/'result').exists()


def test_b_reward_function_source_is_bound_before_learning(tmp_path,monkeypatch):
 plan,values=gate_fixture(tmp_path,monkeypatch)
 values['pilot']['bindings']=[b for b in values['pilot']['bindings']if b['path']!=str(P.parent/'reproduction/cell_worker.py')]
 with pytest.raises(ValueError,match='before learning'):m.run(plan)
 assert not (tmp_path/'result').exists()
