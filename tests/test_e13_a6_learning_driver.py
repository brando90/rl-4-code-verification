"""Route A6 feasibility through B once while retaining A/P horizons, monitor stops and no replay."""
from pathlib import Path
import sys
import pytest
P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P))
import a6_learning_driver as m
import test_e13_learning_driver as original_tests

def fixture(tmp_path,monkeypatch,arm='B'):
 monkeypatch.setattr(original_tests,'m',m)
 return original_tests.fixture(tmp_path,monkeypatch,arm)

def allow_monitors(plan,config,decisions,points):
 plan['monitor_results']={str(i):{'name':'monitor'+str(i)}for i in points}
 decisions.update({'monitor'+str(i):original_tests.monitor_value(plan,config,i)for i in points})

@pytest.mark.parametrize('arm',['A','P'])
def test_a_and_p_finish_their_30_update_pilots_without_a_t5_gate(tmp_path,monkeypatch,arm):
 plan,config,root,events,decisions=fixture(tmp_path,monkeypatch,arm)
 state=m.tick(plan)
 assert state['status']=='COMPLETE'and state['completed_updates']==30 and 'T5_final'not in state
 assert len([e for e in events if e[1]=='update'])==30
 before=list(events);assert m.tick(plan)==state and events==before

def test_b_waits_at_30_and_extends_only_once_with_monitoring_through_60(tmp_path,monkeypatch):
 plan,config,root,events,decisions=fixture(tmp_path,monkeypatch)
 allow_monitors(plan,config,decisions,range(0,61,10))
 state=m.tick(plan);assert state['status']=='WAIT_FOR_T5'and state['completed_updates']==30
 plan['T5_results']={'30':{'name':'extend'}}
 decisions['extend']={'condition':'v2-S2','gate':'T5','horizon':30,'pilot_execution_sha256':'execution-sha',
  'admission_statistics_computed':True,'arm':'B','seeds':[1301],'metric':'own train reward','status':'EXTEND_TO_60'}
 state=m.tick(plan);assert state['status']=='WAIT_FOR_T5'and state['completed_updates']==60
 assert set(state['monitor_receipts'])=={str(i)for i in range(0,61,10)}
 assert len([e for e in events if e[1]=='update'])==60
 plan['T5_results']['60']={'name':'final'};decisions['final']={**decisions['extend'],'horizon':60,'status':'FAIL'}
 state=m.tick(plan);assert state['status']=='COMPLETE'and state['T5_final']=={'name':'final'}
 before=list(events);assert m.tick(plan)==state and events==before

def test_a_strict_gate_cannot_extend_b(tmp_path,monkeypatch):
 plan,config,root,events,decisions=fixture(tmp_path,monkeypatch)
 allow_monitors(plan,config,decisions,range(0,31,10));m.tick(plan);before=list(events)
 plan['T5_results']={'30':{'name':'wrong'}}
 decisions['wrong']={'condition':'v2-S2','gate':'T5','horizon':30,'pilot_execution_sha256':'execution-sha',
  'admission_statistics_computed':True,'arm':'A','seeds':[1301,1302],'metric':'strict','status':'EXTEND_TO_60'}
 with pytest.raises(ValueError,match='fixed pilot'):m.tick(plan)
 assert events==before

def test_original_monitor_stop_and_cleanup_guards_remain(tmp_path,monkeypatch):
 monkeypatch.setattr(original_tests,'m',m)
 original_tests.test_B_cannot_start_before_own_baseline_and_stops_after_monitor10(tmp_path/'monitor',monkeypatch)
 original_tests.test_zero_exit_with_unresolved_cleanup_halts_before_prefix(tmp_path/'cleanup',monkeypatch)
