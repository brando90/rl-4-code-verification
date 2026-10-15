"""Check disjoint A5 selection, exact numerical scope and single measured finality."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1'
sys.path.insert(0, str(ROOT))
from a5_admission import qualifies, ordered_selection, numerical_policy
from panel import development_tasks, validate_manifest, cell_seed
from runtime import numerical_dtype

CANDIDATES = [{'id':'C1','dtype':'float16'}, {'id':'C2','dtype':'float32'}]


def result(**changes):
    return {'candidate':'C1','a5_stage':'development','responses':8,'status':'PASS',
            'admission_statistics_computed':True,'unsupported_tokens':0,
            'median_absolute_logprob_error':.008,'p99_absolute_logprob_error':.08,
            'importance_truncation_fraction':.008,'cleanup_verified':True, **changes}


def test_margin_and_original_pass_are_distinct():
    assert qualifies(result())
    for key, value in [('median_absolute_logprob_error',.008001),
                       ('p99_absolute_logprob_error',.080001),
                       ('importance_truncation_fraction',.008001),('unsupported_tokens',1),
                       ('responses',7),('cleanup_verified',False),
                       ('admission_statistics_computed',False),('p99_absolute_logprob_error',float('nan'))]:
        assert not qualifies(result(**{key:value}))


def test_first_qualifier_order_and_finality():
    fail=result(p99_absolute_logprob_error=.09)
    assert ordered_selection(CANDIDATES,[])['id']=='C1'
    assert ordered_selection(CANDIDATES,[fail])['id']=='C2'
    assert ordered_selection(CANDIDATES,[result()],confirmation=True)['id']=='C1'
    assert ordered_selection(CANDIDATES,[fail,result(candidate='C2')],confirmation=True)['id']=='C2'
    for receipts, confirmation in [([result()],False),([result(candidate='C2')],True),
        ([fail],True),([result(),result(candidate='C2')],True),
        ([result(admission_statistics_computed=False)],False)]:
        with pytest.raises(ValueError):ordered_selection(CANDIDATES,receipts,confirmation=confirmation)


@pytest.mark.parametrize('dtype',['float16','float32'])
def test_identical_dtype_and_no_other_scientific_change(tmp_path,dtype):
    old={'precision':'bfloat16','generation':{'vllm_cfg':{'precision':'bfloat16'},'temperature':1.},'seed':17}
    new=deepcopy(old);new['precision']=dtype;new['generation']['vllm_cfg']['precision']=dtype
    numerical_policy(old,new,dtype)
    p=tmp_path/'policy.json';p.write_text(json.dumps(new))
    assert numerical_dtype({'policy_config':str(p),'numerical_dtype':dtype})==dtype
    bad=deepcopy(new);bad['generation']['temperature']=.5
    with pytest.raises(ValueError):numerical_policy(old,bad,dtype)
    bad=deepcopy(new);bad['generation']['vllm_cfg']['precision']='bfloat16';p.write_text(json.dumps(bad))
    with pytest.raises(ValueError):numerical_dtype({'policy_config':str(p),'numerical_dtype':dtype})


def test_seeded_probe_disjoint_original_and_fixed_sample_seeds():
    import hashlib
    train=[f'synthetic-{i}' for i in range(539)]
    original=sorted(train,key=lambda t:hashlib.sha256(('e13v2-lp1\0'+t).encode()).hexdigest())[:8]
    chosen=development_tasks(train)
    assert len(set(chosen))==8 and not set(original)&set(chosen)
    assert development_tasks(list(reversed(train)))==chosen
    m={'batch':'lp1_a5_dev','max_model_len':8193,'cells':[
        {'task_id':t,'cell_id':f'lp1_a5_dev/{t}/0','sample':0,'split':'train',
         'seed':cell_seed('lp1',t,0),'prompt_token_ids':[1]} for t in chosen]}
    assert len(validate_manifest(m,train))==8
    bad=deepcopy(m);bad['cells'][0].update(task_id=original[0],cell_id=f'lp1_a5_dev/{original[0]}/0',seed=cell_seed('lp1',original[0],0))
    with pytest.raises(ValueError):validate_manifest(bad,train)


def test_scope_guard_rejects_sampler_versions_weights_and_budget_drift():
    from a5_admission import unchanged_science
    runtime={'model':'fixed','manifest':'original','policy_config':'old-policy','batch_size':32,
             'runtime_versions':{'vllm':'0.10.0'},'bindings':[{'path':'weights','sha256':'fixed'}]}
    old={'maximum_seconds':1800,'foreign_registries':[],'reservation_bindings':[],
         'cumulative_limit_hours':.6,'routes':[{'host':'fixture','runtime':runtime}]}
    new=deepcopy(old);new['cumulative_limit_hours']=3.1
    new['routes'][0]['runtime'].update(manifest='development',policy_config='new-policy',
                                      numerical_dtype='float16',a5_stage='development')
    unchanged_science(old,new,'float16','development')
    for key,value in [('model','other'),('batch_size',8),('runtime_versions',{'vllm':'0.11'})]:
        bad=deepcopy(new);bad['routes'][0]['runtime'][key]=value
        with pytest.raises(ValueError):unchanged_science(old,bad,'float16','development')
    bad=deepcopy(new);bad['routes'][0]['runtime']['bindings'][0]['sha256']='changed'
    with pytest.raises(ValueError):unchanged_science(old,bad,'float16','development')
    bad=deepcopy(new);bad['maximum_seconds']=1801
    with pytest.raises(ValueError):unchanged_science(old,bad,'float16','development')
    with pytest.raises(ValueError):unchanged_science(old,new,'float16','confirmation')
