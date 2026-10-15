"""Verify S2 anchor resume, missing-cell retry limits and concurrent lease accounting."""
from pathlib import Path
import json
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1'
sys.path.insert(0,str(ROOT))
import anchor_panel
import anchor_lease
from panel import cell_seed
from lease import release


def manifest():
    train=[f'synthetic_anchor_{i}' for i in range(539)]
    return {'batch':'base','max_model_len':8193,'terminal_token_ids':[2],'cells':[
        {'cell_id':f'base/{task}/{sample}','task_id':task,'sample':sample,'split':'train',
         'seed':cell_seed('base',task,sample),'prompt_token_ids':[1]}
        for task in train for sample in range(8)]},train


def generate(cells):
    return [{'prompt_token_ids':c['prompt_token_ids'],'output_token_ids':[2],
             'generation_logprobs':[-.1],'finish_reason':'stop','completion':'synthetic'} for c in cells]


def run(root,segment,callback=generate,maximum=256):
    m,train=manifest()
    return anchor_panel.run_segment(m,train,root,generate_batch=callback,lease_check=lambda:None,
        prerequisites={'lp1':{'status':'PASS'}},segment_id=segment,lease_id=f'lease-{segment}',maximum_cells=maximum)


def test_resume_never_regenerates_completed_cells(tmp_path):
    calls=[]
    def callback(cells):calls.extend(c['cell_id'] for c in cells);return generate(cells)
    first=run(tmp_path,0,callback);original=(tmp_path/'00000.generation.json').read_bytes()
    second=run(tmp_path,1,callback)
    assert first['declared']==4312 and first['completed']==256 and first['status']=='CHECKPOINT'
    assert second['completed']==512 and len(calls)==len(set(calls))==512
    assert (tmp_path/'00000.generation.json').read_bytes()==original
    assert not (tmp_path/'00000.attempt2.json').exists()


def test_one_identical_retry_and_exhausted_cells_stay_missing(tmp_path):
    def failed(cells):raise RuntimeError('synthetic infrastructure failure')
    with pytest.raises(RuntimeError):run(tmp_path,0,failed,32)
    retry=run(tmp_path,1,maximum=32)
    assert retry['completed']==32 and (tmp_path/'00000.attempt2.json').exists()
    for segment in (2,3):
        with pytest.raises(RuntimeError):run(tmp_path,segment,failed,32)
    seen=[]
    def callback(cells):seen.extend(c['cell_id'] for c in cells);return generate(cells)
    result=run(tmp_path,4,callback,32)
    m,train=manifest();state=anchor_panel.inventory(m,train,tmp_path)
    assert result['completed']==64 and result['exhausted']==32
    assert state['exhausted']==list(range(32,64))
    assert seen==[c['cell_id'] for c in m['cells'][64:96]]
    assert not (tmp_path/'00032.attempt3.json').exists()


def test_invalid_batch_member_does_not_discard_other_complete_rows(tmp_path):
    def partly_bad(cells):
        rows=generate(cells);rows[0]['finish_reason']='length';return rows
    with pytest.raises(ValueError):run(tmp_path,0,partly_bad,32)
    m,train=manifest();state=anchor_panel.inventory(m,train,tmp_path)
    assert len(state['completed'])==31 and state['pending'][0][0]==0
    result=run(tmp_path,1,maximum=1)
    assert result['completed']==32 and (tmp_path/'00000.attempt2.json').exists()
    row=json.loads((tmp_path/'00000.generation.json').read_text());row['seed']+=1
    (tmp_path/'00000.generation.json').write_text(json.dumps(row))
    with pytest.raises(ValueError,match='identity'):run(tmp_path,2)


def gpu_inventory():
    return {'host':'fixture','inventory_complete':True,'idle_device_indices':[0,1,2,3],
        'local_storage':{'available_bytes':100*1024**3},'host_memory':{'available_bytes':1024*1024**3},
        'devices':[{'index':i,'uuid':f'GPU-{i}','memory_mib':81920} for i in range(4)]}


def initialize(root,leases=None,hours=.322):
    (root/'registry.json').write_text(json.dumps({'owner':'e13v2','device_hours':hours,'leases':leases or []}))


def claim(root,index,batch,**kwargs):
    return anchor_lease.claim(root,gpu_inventory(),index,sources=[],reservation_bindings=[],
                              batch=batch,now=1000,**kwargs)


def test_independent_policies_claim_distinct_devices_and_preserve_prior_hours(tmp_path):
    initialize(tmp_path)
    first=claim(tmp_path,0,'base');claim(tmp_path,1,'half');claim(tmp_path,2,'full1')
    with pytest.raises(RuntimeError,match='three'):claim(tmp_path,3,'full2')
    release(tmp_path,first['id'],cleanup_verified=True,now=1360)
    registry=json.loads((tmp_path/'registry.json').read_text())
    assert registry['device_hours']==pytest.approx(.422)
    assert anchor_lease.accounting(registry)==pytest.approx((.1,4.))
    with pytest.raises(RuntimeError,match='already reserved'):claim(tmp_path,1,'base')


def test_active_reservations_count_against_phase_budget(tmp_path):
    completed={'id':'old','phase':anchor_lease.PHASE,'status':'RELEASED','device_hours':143.}
    initialize(tmp_path,[completed],143.322)
    claim(tmp_path,0,'base',seconds=1800)
    with pytest.raises(RuntimeError,match='budget'):claim(tmp_path,1,'half',seconds=1801)
    claim(tmp_path,1,'half',seconds=1800)
    registry=json.loads((tmp_path/'registry.json').read_text())
    assert anchor_lease.accounting(registry)==(143.,1.)


def test_cleanup_uncertainty_and_foreign_reservation_refuse_claim(tmp_path):
    initialize(tmp_path);first=claim(tmp_path,0,'base')
    release(tmp_path,first['id'],cleanup_verified=False,now=1100)
    with pytest.raises(RuntimeError,match='cleanup'):claim(tmp_path,1,'half')
    release(tmp_path,first['id'],cleanup_verified=True,now=1200)
    foreign=tmp_path/'foreign.json';foreign.write_text(json.dumps([{'host':'fixture','gpu':1,'owner':'other'}]))
    with pytest.raises(RuntimeError,match='foreign'):
        anchor_lease.claim(tmp_path,gpu_inventory(),1,sources=[{'path':str(foreign)}],reservation_bindings=[],batch='half',now=1200)


def test_lease_boundary_defers_cells_without_consuming_retry(tmp_path):
    m,train=manifest();checks=iter([True,False])
    result=anchor_panel.run_segment(m,train,tmp_path,generate_batch=generate,lease_check=lambda:None,
        prerequisites={'lp1':{'status':'PASS'}},segment_id=0,lease_id='fixture',maximum_cells=256,
        may_start_batch=lambda:next(checks))
    assert result['completed']==32 and result['attempted_in_segment']==32 and result['status']=='CHECKPOINT'
    assert not (tmp_path/'00032.attempt1.json').exists()
    resumed=run(tmp_path,1,maximum=32)
    assert resumed['completed']==64 and not (tmp_path/'00032.attempt2.json').exists()


def test_anchor_constructor_preserves_all_s2_settings_except_explicit_tokenizer(tmp_path,monkeypatch):
    from types import SimpleNamespace
    import runtime,anchor_runtime
    captures=[]
    monkeypatch.setitem(sys.modules,'vllm',SimpleNamespace(LLM=lambda **kwargs:captures.append(kwargs)))
    policy=tmp_path/'policy.json';policy.write_text(json.dumps({'precision':'float16','generation':{'vllm_cfg':{'precision':'float16'}}}))
    config={'model':'fixture-base-weights','tokenizer':'frozen-full-tokenizer','numerical_dtype':'float16',
            'policy_config':str(policy),'gpu_memory_utilization':.8,'batch_size':32}
    runtime.build_engine(config,{'max_model_len':15945});anchor_runtime.build_engine(config,{'max_model_len':15945})
    a,b=captures;assert a.pop('tokenizer')=='fixture-base-weights';assert b.pop('tokenizer')=='frozen-full-tokenizer'
    assert a==b and a['dtype']=='float16' and a['seed']==1302100 and a['enable_prefix_caching'] is False


def test_anchor_actual_sampling_requests_match_frozen_s2_runtime(tmp_path,monkeypatch):
    from types import SimpleNamespace
    import runtime,anchor_runtime
    requests=[];tokenizers=[]
    class Engine:
        def __init__(self,**kwargs):pass
        def generate(self,prompts,params,**kwargs):
            requests.append((prompts,params,kwargs))
            return [SimpleNamespace(prompt_token_ids=p['prompt_token_ids'],outputs=[SimpleNamespace(
                token_ids=[2],logprobs=[{2:SimpleNamespace(logprob=-.2)}],finish_reason='stop')]) for p in prompts]
    class Tokenizer:
        @staticmethod
        def from_pretrained(path,**kwargs):
            tokenizers.append(path);return SimpleNamespace(decode=lambda *a,**kw:'synthetic')
    monkeypatch.setitem(sys.modules,'vllm',SimpleNamespace(__version__='0.10.0',LLM=Engine,SamplingParams=lambda **kw:kw))
    monkeypatch.setitem(sys.modules,'transformers',SimpleNamespace(AutoTokenizer=Tokenizer))
    policy=tmp_path/'policy.json';policy.write_text(json.dumps({'precision':'float16','generation':{'vllm_cfg':{'precision':'float16'}}}))
    mf=tmp_path/'manifest.json';mf.write_text(json.dumps({'max_model_len':15945,'terminal_token_ids':[2],
        'cells':[{'prompt_token_ids':[1,3],'seed':17},{'prompt_token_ids':[1,4],'seed':19}]}))
    ids=tmp_path/'train.txt';ids.write_text('synthetic\n')
    config={'model':'fixture-base','tokenizer':'common-frozen','numerical_dtype':'float16','policy_config':str(policy),
        'manifest':str(mf),'train_ids':str(ids),'generation_root':str(tmp_path/'out'),'prerequisites':{},
        'gpu_memory_utilization':.8,'batch_size':32,'maximum_cells':256,'segment_id':0}
    monkeypatch.setenv('E13_EXECUTION_ID','fixture')
    def frozen(manifest,train,root,generate,**kwargs):return kwargs['generate_batch'](manifest['cells'])
    def segmented(manifest,train,root,**kwargs):return kwargs['generate_batch'](manifest['cells'])
    monkeypatch.setattr(runtime,'generate_once',frozen);monkeypatch.setattr(anchor_runtime,'run_segment',segmented)
    old=runtime.generation(config);new=anchor_runtime.generation(config)
    assert requests[0]==requests[1] and old==new
    assert tokenizers==['fixture-base','common-frozen']
    assert [p['seed'] for p in requests[1][1]]==[17,19]


def dispatch_fixture(tmp_path,monkeypatch,*,fail_install=False,unknown_exit=False):
    from types import SimpleNamespace
    import subprocess,anchor_dispatch
    registry=tmp_path/'leases';registry.mkdir();initialize(registry)
    route={'host':'fixture','environment':{},'supervisor_script':'/fixture/anchor_supervisor.py',
           'runtime':{'python':'fixture-python','panel_root':'/fixture/panel','generation_root':'/fixture/generation'}}
    config={'batch':'base','maximum_seconds':7200,'maximum_cells':256,'foreign_registries':[],
            'reservation_bindings':[],'routes':[route]}
    plan={'state_root':str(tmp_path/'state'),'lease_root':str(registry),'watchdog_root':'fixture-watch',
          'watchdog_run':'fixture-run','published_revision':'fixture-revision'}
    path=tmp_path/'plan.json';path.write_text(json.dumps(plan))
    monkeypatch.setattr(anchor_dispatch,'published',lambda _:config)
    monkeypatch.setattr(anchor_dispatch,'remote_inventory',lambda _: {'declared':4312,'completed':0,'pending':4312,'exhausted':0,'started_cells':0})
    monkeypatch.setattr(anchor_dispatch,'observe',lambda _:gpu_inventory())
    monkeypatch.setattr(anchor_dispatch.subprocess,'run',lambda *a,**kw:SimpleNamespace(returncode=0))
    def install(*args):
        if fail_install:raise RuntimeError('synthetic prelaunch failure')
    monkeypatch.setattr(anchor_dispatch,'install_segment',install)
    monkeypatch.setattr(anchor_dispatch,'retire_remote_lease',lambda *a:None)
    launched=[]
    def command(host,argv,**kwargs):
        if argv[0]=='env':
            launched.append(argv)
            if unknown_exit:raise subprocess.TimeoutExpired(argv,7200)
            return SimpleNamespace(returncode=0)
        return SimpleNamespace(stdout=json.dumps({'status':'COMPLETE','completed':4312,'cleanup_verified':True}))
    monkeypatch.setattr(anchor_dispatch,'command',command)
    return anchor_dispatch,path,registry,launched


def test_dispatch_releases_complete_panel_and_never_repeats(tmp_path,monkeypatch):
    module,path,registry,launched=dispatch_fixture(tmp_path,monkeypatch)
    assert module.dispatch(path)['status']=='COMPLETE'
    assert module.dispatch(path)['status']=='COMPLETE' and len(launched)==1
    assert json.loads((registry/'registry.json').read_text())['leases'][0]['status']=='RELEASED'


def test_prelaunch_failure_releases_unused_device(tmp_path,monkeypatch):
    module,path,registry,launched=dispatch_fixture(tmp_path,monkeypatch,fail_install=True)
    with pytest.raises(RuntimeError):module.dispatch(path)
    assert not launched and json.loads((registry/'registry.json').read_text())['leases'][0]['status']=='RELEASED'
    assert module.dispatch(path)['status']=='HALTED_INFRA'


def test_unknown_exit_quarantines_lease_until_owned_cleanup(tmp_path,monkeypatch):
    import subprocess
    module,path,registry,launched=dispatch_fixture(tmp_path,monkeypatch,unknown_exit=True)
    with pytest.raises(subprocess.TimeoutExpired):module.dispatch(path)
    assert json.loads((registry/'registry.json').read_text())['leases'][0]['status']=='CLEANUP_REQUIRED'
    assert module.dispatch(path)['status']=='CLEANUP_REQUIRED' and len(launched)==1


def test_changed_missing_cell_attempt_cannot_authorize_retry(tmp_path):
    def failed(cells):raise RuntimeError('synthetic interruption')
    with pytest.raises(RuntimeError):run(tmp_path,0,failed,32)
    path=tmp_path/'00000.attempt1.json';record=json.loads(path.read_text());record['seed']+=1
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError,match='attempt identity'):run(tmp_path,1)


def test_poller_launches_independent_plans_without_claiming_devices(tmp_path,monkeypatch):
    import anchor_watch
    from types import SimpleNamespace
    for name in ('base','half','full1'):(tmp_path/(name+'.plan.json')).write_text('{}')
    monkeypatch.setattr(anchor_watch,'poll',lambda _: {'checked_utc':'fixture'})
    calls=[]
    def launch(argv,**kwargs):
        calls.append(argv);assert kwargs['start_new_session'];return SimpleNamespace(pid=100+len(calls))
    monkeypatch.setattr(anchor_watch.subprocess,'Popen',launch)
    result=anchor_watch.run(tmp_path)
    assert len(calls)==3 and result['device_claims_by_poller']==0
    assert all('anchor_dispatch.py' in x[1] for x in calls)


def test_new_foreign_reservation_file_blocks_claim(tmp_path):
    registry=tmp_path/'owned';registry.mkdir();initialize(registry)
    foreign=tmp_path/'foreign';foreign.mkdir()
    search={'roots':[str(foreign)],'paths':[]}
    (foreign/'new_lease.json').write_text('{"released":false}')
    with pytest.raises(RuntimeError,match='path inventory changed'):
        claim(registry,0,'base',reservation_inventory=search)
    assert not json.loads((registry/'registry.json').read_text())['leases']
