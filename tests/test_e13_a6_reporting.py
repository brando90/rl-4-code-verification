"""Check descriptive A gradients and the independent unchanged A token budget on authored evidence."""
from pathlib import Path
import importlib.machinery,importlib.util,json,sys
import pytest
R=Path(__file__).resolve().parents[1]
P=R/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P))
import a6_gradient_reporting as gradient
import a6_learning_report as report
import a6_a_budget_driver as budget
import test_e13_t5_driver as old_budget
import test_e13_learning_report as old_report

def budget_fixture(tmp_path,monkeypatch):
 monkeypatch.setattr(old_budget,'m',budget)
 plan,values=old_budget.fixture(tmp_path,monkeypatch)
 values['lock']['gate']='A6_A_BUDGET_INPUTS'
 refs=[]
 for seed in (1301,1302):
  p=tmp_path/f'{seed}.json';v=json.loads(p.read_text());v['status']='COMPLETE';refs.append(old_budget.put(p,v))
 inputs=old_budget.put(tmp_path/'inputs.json',{'states':dict(zip(('1301','1302'),refs)),'updates':[]})
 values['lock']['configuration']['inputs']=inputs;values['lock']['bindings']=[inputs,*refs]
 values['pilot']['bindings']=[{'path':str(p),'sha256':budget.digest(p)}for p in (Path(budget.__file__).resolve(),P/'t5_driver.py',P/'schedule.py')]
 return plan,values

def test_a_budget_uses_both_thirty_update_pilots_independent_of_strict_improvement(tmp_path,monkeypatch):
 plan,values=budget_fixture(tmp_path,monkeypatch)
 monkeypatch.setattr(budget,'validate_updates',lambda *_:([{'strict_successes':0}]*60,[2048]*15360))
 out=budget.run(plan)
 assert out['status']=='FROZEN'and out['token_budget']['T']==25600*2048 and out['pilot_slots']==15360
 assert out['gate']=='A_PILOT_TOKEN_BUDGET'and out['feasibility_gate']is False
 with pytest.raises(FileExistsError):budget.run(plan)

@pytest.mark.parametrize('change',['B','horizon','missing_state'])
def test_cannot_derive_budget_from_b_or_extended_or_missing_a_pilot(tmp_path,monkeypatch,change):
 plan,values=budget_fixture(tmp_path,monkeypatch)
 if change=='horizon':values['lock']['configuration']['horizon']=60
 else:
  p=tmp_path/'1301.json';v=json.loads(p.read_text());v['arm'if change=='B'else 'status']='B'if change=='B'else 'HALTED'
  changed=old_budget.put(p,v);inputs=json.loads((tmp_path/'inputs.json').read_text());inputs['states']['1301']=changed
  ref=old_budget.put(tmp_path/'inputs.json',inputs);values['lock']['configuration']['inputs']=ref
  values['lock']['bindings']=[ref,changed,inputs['states']['1302']]
 with pytest.raises(ValueError):budget.run(plan)
 assert not (tmp_path/'result/evaluation_attempt.json').exists()

def test_a_report_counts_actual_gradient_separately_and_retains_partial_rollout_cost(tmp_path):
 state=old_report.fixture(tmp_path,count=2);state.update(status='HALTED',failed_stage='update')
 for i,norm in enumerate((0.,.3),1):
  old_report.put(tmp_path/f'update_{i:05d}/update/output/result.json',{'condition':'v2-S2','status':'MEASURED','optimizer_updates':1,
   'counts':{'usable_groups':1,'nonzero_advantage_slots':int(norm>0)*8},'metrics':{'grad_norm':[norm]}})
 old_report.put(tmp_path/'update_00003/generate/output/00000.generation.json',{'output_token_ids':[1,2,3]})
 value,sources=report.summarize(tmp_path,state,{},'execution',{})
 assert value['gradient_signal']['nonzero_gradient_updates']==1 and value['gradient_signal']['zero_gradient_updates']==1
 assert value['optimizer_updates']==2 and value['partial_opportunity_tokens']==3 and value['status']=='HALTED'
 assert len([p for p in sources if str(p).endswith('update/output/result.json')])==2

def test_changed_gradient_receipt_count_is_rejected(tmp_path):
 state=old_report.fixture(tmp_path)
 old_report.put(tmp_path/'update_00001/update/output/result.json',{'condition':'v2-S2','status':'UNMEASURED','optimizer_updates':0})
 with pytest.raises(ValueError,match='count differs'):report.summarize(tmp_path,state,{},'execution',{})

@pytest.mark.parametrize('terminal_receipt',[True,False])
def test_partial_training_gradient_is_retained_or_explicitly_unknown(tmp_path,terminal_receipt):
 state=old_report.fixture(tmp_path,count=0);state.update(status='HALTED',failed_stage='export'if terminal_receipt else 'update')
 root=tmp_path/'update_00001/update/output'
 old_report.put(root/'attempt.json',{'provenance':'authored training attempt'})
 if terminal_receipt:
  old_report.put(root/'result.json',{'condition':'v2-S2','status':'MEASURED','optimizer_updates':1,
   'counts':{'usable_groups':1,'nonzero_advantage_slots':8},'metrics':{'grad_norm':[.5]}})
 value,sources=report.summarize(tmp_path,state,{},'execution',{})
 signal=value['gradient_signal']
 assert value['completed_opportunities']==0
 assert signal['nonzero_gradient_updates']==int(terminal_receipt)
 assert signal['partial_opportunity_receipts']==int(terminal_receipt)
 assert signal['incomplete_training_attempts_without_result']==int(not terminal_receipt)
 assert signal['nonzero_gradient_count_is_lower_bound']is not terminal_receipt
