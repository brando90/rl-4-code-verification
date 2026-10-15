"""Check prompt pairing, replay and boundary overshoot against the frozen complete-group rules."""
from pathlib import Path
import importlib.util
import pytest

PATH=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2/schedule.py'
spec=importlib.util.spec_from_file_location('e13_phase2_schedule',PATH);schedule=importlib.util.module_from_spec(spec);spec.loader.exec_module(schedule)


def test_uniform_epochs_and_resume_are_independent_of_arm_update_partitions():
    tasks=[f'fixture_{i}' for i in range(19)]
    stream=[schedule.uniform_task(tasks,13011,i) for i in range(57)]
    for i in range(3):assert set(stream[19*i:19*(i+1)])==set(tasks)
    assert stream[7:44]==[schedule.uniform_task(reversed(tasks),13011,i) for i in range(7,44)]
    assert stream!=[schedule.uniform_task(tasks,13012,i) for i in range(57)]
    assert schedule.rollout_seed(13011,11,3)==schedule.rollout_seed(13011,11,3)
    assert len({schedule.rollout_seed(13011,g,s) for g in range(100) for s in range(8)})==800


def test_zero_information_falls_back_to_same_uniform_stream():
    tasks=['a','b','c'];information=dict.fromkeys(tasks,0.)
    assert [schedule.information_task(tasks,information,3,i) for i in range(20)]==[
        schedule.uniform_task(tasks,3,i) for i in range(20)]
    with pytest.raises(ValueError):schedule.information_task(tasks,{'a':1.},3,0)
    with pytest.raises(ValueError):schedule.information_task(tasks,dict(a=1,b=-1,c=0),3,0)


def test_budget_uses_all_lengths_and_refuses_missing_or_short_matching_budget():
    result=schedule.pilot_token_budget([1000,1001,3000])
    assert result['ceiling_mean_length']==1667 and result['T']==42675200
    assert result['targets']==[10668800,21337600,32006400,42675200]
    assert result['one_percent_matching_feasible']
    assert not schedule.pilot_token_budget([10,20])['one_percent_matching_feasible']
    with pytest.raises(ValueError):schedule.pilot_token_budget([10,None,20])


def test_crossing_group_is_kept_in_full_and_stops_a_partial_update():
    state={'generated_tokens':9999,'next_target':10000,'update_groups':2,'group_index':2}
    result=schedule.advance_group(state,[8192]*8)
    assert result['generated_tokens']==75535 and result['overshoot']==65535
    assert result['update_groups']==3 and result['boundary_crossed'] and result['update_due']
    assert state['generated_tokens']==9999
    with pytest.raises(ValueError):schedule.advance_group(result,[1]*8)
    with pytest.raises(ValueError):schedule.advance_group(state,[1]*7)


def test_ordinary_updates_close_at_32_groups_even_with_no_boundary():
    state={'generated_tokens':100,'next_target':1000000,'update_groups':31,'group_index':31}
    result=schedule.advance_group(state,[1]*8)
    assert result['update_due'] and not result['boundary_crossed'] and result['update_groups']==32
    with pytest.raises(ValueError):schedule.advance_group(result,[1]*8)


def test_actual_matching_requires_every_arm_boundary_and_one_percent():
    assert schedule.boundary_agreement(100000,dict(A=100000,B=100999,P=100050))['matched']
    assert not schedule.boundary_agreement(100000,dict(A=100000,B=101001))['matched']
    with pytest.raises(ValueError):schedule.boundary_agreement(100000,dict(A=99999,B=100001))
