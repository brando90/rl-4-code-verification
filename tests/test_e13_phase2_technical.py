"""Check unchanged technical thresholds, delayed comparisons and full-denominator pilot bounds."""
from pathlib import Path
import importlib.util,copy,sys
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_technical_measurements',PHASE/'technical_measurements.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def rows():
    return [{'cell_id':f'authored_{i}','split':'train','prompt_token_ids':[3,4],
        'output_token_ids':[5]*99+[1],'generation_logprobs':[-1.]*100,'finish_reason':'stop',
        'trainer_input_ids':[3,4]+[5]*99+[1],'trainer_token_mask':[0,0]+[1]*100,
        'trainer_logprobs':[0.,0.]+[-1.]*100} for i in range(8)]


def source_update():
    return {'condition':'v2-S2','status':'MEASURED','optimizer_updates':1,'counts':{'declared_slots':256},
        'before_parameters':[{'sha256':'0'*64,'elements':10,'state_tensors':2}],
        'after_parameters':[{'sha256':'1'*64,'elements':10,'state_tensors':2}],
        'batch_sha256':'2'*64,'metrics':{'loss':[.5]}}


def test_t1_reuses_exact_frozen_probability_gate_and_requires_all_cells():
    data=rows();expected=[r['cell_id'] for r in data]
    result=m.t1(data,expected_cells=expected,eos_token_ids=[1]);assert result['status']=='PASS'
    assert result['generated_tokens']==800 and result['eos_tokens_in_mask']==8
    data[0]['generation_logprobs'][0]=None
    assert m.t1(data,expected_cells=expected,eos_token_ids=[1])['status']=='FAIL'
    with pytest.raises(ValueError,match='incomplete'):m.t1(data[:-1],expected_cells=expected,eos_token_ids=[1])


def test_t2_needs_weight_change_and_median_not_an_added_tail_threshold():
    data=rows();expected=[r['cell_id'] for r in data]
    for row in data:row['trainer_logprobs'][2:12]=[-.5]*10
    assert m.t1(data,expected_cells=expected,eos_token_ids=[1])['status']=='FAIL'
    update=source_update()
    result=m.t2(update,data,expected_cells=expected,eos_token_ids=[1])
    assert result['status']=='PASS' and result['refit_probability']['p99_absolute_logprob_error']==.5
    update['after_parameters']=copy.deepcopy(update['before_parameters'])
    assert m.t2(update,data,expected_cells=expected,eos_token_ids=[1])['status']=='FAIL'
    update['after_parameters'][0]['elements']+=1
    with pytest.raises(ValueError,match='dimensions'):m.t2(update,data,expected_cells=expected,eos_token_ids=[1])


def test_t3_exact_source_and_batch_precede_loss_gate_end_hash_is_descriptive():
    original=source_update();replay={'condition':'v2-S2','status':'MEASURED','diagnostic_replay_updates':1,
        'continued_learning_updates':0,'pre_update_state_verified':True,'batch_sha256':'2'*64,
        'source_result_sha256':'3'*64,'metrics':{'loss':[.5009]},'parameters':[{'sha256':'4'*64}]}
    result=m.t3(original,replay,source_result_sha256='3'*64)
    assert result['status']=='PASS' and not result['post_replay_parameter_digest_equal']
    replay['metrics']['loss']=[.5011]
    assert m.t3(original,replay,source_result_sha256='3'*64)['status']=='FAIL'
    replay['batch_sha256']='5'*64
    with pytest.raises(ValueError,match='exact saved'):m.t3(original,replay,source_result_sha256='3'*64)


def pilot(horizon,late_successes=0):
    data=[{'arm':'A','split':'train','seed':seed,'update':u,'declared':256,'measured':256,'strict_successes':0}
          for seed in (1301,1302) for u in range(1,horizon+1)]
    late=[r for r in data if r['update']>horizon-10]
    for row in late:
        take=min(256,late_successes);row['strict_successes']=take;late_successes-=take
    assert late_successes==0
    return data


def test_t5_uses_both_paired_seeds_all_slots_and_one_predeclared_extension():
    # 2% of 5,120 fixed slots is 102.4; 102 successes do not pass, 103 do.
    assert m.t5(pilot(30,102),horizon=30)['status']=='EXTEND_TO_60'
    assert m.t5(pilot(30,103),horizon=30)['status']=='PASS'
    assert m.t5(pilot(60,102),horizon=60)['status']=='FAIL'
    assert m.t5(pilot(60,103),horizon=60)['status']=='PASS'
    with pytest.raises(ValueError,match='every scheduled'):m.t5(pilot(30)[:-1],horizon=30)
    heldout=pilot(30);heldout[0]['split']='validation'
    with pytest.raises(ValueError,match='accounting'):m.t5(heldout,horizon=30)


def test_t5_missing_outcomes_remain_in_full_denominator_and_can_be_inconclusive():
    data=pilot(60,100)
    next(r for r in data if r['seed']==1302 and r['update']==60)['measured']=246
    result=m.t5(data,horizon=60)
    assert result['status']=='INCONCLUSIVE' and result['final']['declared']==5120
    assert result['final']['measured']==5110 and result['final']['strict_successes']==100
    assert result['improvement_bounds'][0]<.02<result['improvement_bounds'][1]
