"""TLDR: Verify A2/A3/A4 semantics, real component boundaries and anonymous forecast aggregation on CPU."""
import copy
import json
from pathlib import Path
import sys
import pytest
import torch
from common import digest,write_new
from test_filtered_policy import loss_batch
from importance import guard,effective_behavior,UncertifiedStop,summarize
from nemo_objective import FilteredClippedPGLossFn,LOSS
from sampler_checks import engine_check
from pause_v3 import boundary,VETO_END


def many_tokens():
    logits,data=loss_batch()
    logits=logits[:,:1].expand(1,101,30).clone()
    for key,v in list(data.items()):
        if v.ndim>=2:data[key]=v[:,:1].expand(1,101,*v.shape[2:]).clone()
    data['input_ids'][:]=29;data['token_mask'][:]=1;data['token_mask'][:,0]=0
    from filtered_policy import support,filtered_logprobs
    lp,_=filtered_logprobs(logits[:,:-1],support(logits[:,:-1]),data['input_ids'][:,1:])
    data['prev_logprobs'][:,1:]=lp;data['generation_logprobs'][:,1:]=lp
    data['advantages'][:]=1.;data['v4_certified']=torch.ones((1,101),dtype=torch.bool)
    data['v4_certified'][0,1]=False;data['generation_logprobs'][0,1]=float('nan')
    return logits,data


def test_a4_installed_loss_unit_weight_certified_clipping_and_bound(monkeypatch):
    monkeypatch.setattr(torch.Tensor,'cuda',lambda self,*a,**kw:self)
    import importance
    importance.COLLECTOR=[]
    logits,data=many_tokens();data['generation_logprobs'][:,2:]-=torch.log(torch.tensor(1.5))
    previous=copy.deepcopy(data)
    report=guard(data);assert report['uncertified_generated_fraction']==.01
    effective=effective_behavior(data)
    assert (data['prev_logprobs']-effective).exp()[0,1]==1
    assert torch.equal(effective[:,2:],data['generation_logprobs'][:,2:])
    current=(logits+torch.arange(30)*.03).requires_grad_()
    loss,metrics=FilteredClippedPGLossFn()(current/.6,data,torch.tensor(1.),torch.tensor(100.))
    from filtered_policy import support,filtered_logprobs
    logp,_=filtered_logprobs(current[:,:-1],support(logits[:,:-1]),data['input_ids'][:,1:])
    ratio=(logp-data['prev_logprobs'][:,1:]).exp()
    clipped=torch.maximum(-ratio,-ratio.clamp(.8,1.28))
    weights=(data['prev_logprobs']-effective).exp().clamp(max=2)[:,1:]
    assert loss.item()==pytest.approx(float((weights*clipped).mean()),abs=1e-6)
    assert metrics['v4_perturbation_bound']==pytest.approx(float(clipped[0,0].abs()/100),abs=1e-6)
    loss.backward();assert torch.isfinite(current.grad).all()
    assert torch.isnan(data['generation_logprobs'][0,1])
    for key in ('prev_logprobs','advantages','token_mask','sample_mask','v4_support_ids'):
        assert torch.equal(data[key],previous[key])
    assert 'approx_entropy' not in metrics and 'token_mult_prob_error' not in metrics
    detail=importance.COLLECTOR[-1];assert detail['v4_certified_actor_tokens']==99
    stats=summarize(detail['v4_actor_logweight_values'])['actor_logweight_certified_only']
    assert stats['median']==pytest.approx(__import__('math').log(1.5),abs=1e-6)
    assert stats['tokens']==99 and stats['clamp_rate']==0
    assert LOSS['reference_policy_kl_penalty']==0


@pytest.mark.parametrize('which',['generated','actor'])
def test_a4_whole_update_stop_before_train(which,monkeypatch):
    _,data=many_tokens()
    if which=='generated':data['v4_certified'][0,2]=False
    else:data['token_mask'][0,100]=0 # 1/99 valid tokens
    from nemo_objective import train_filtered
    class Forbidden:
        def train(self,*a,**kw):raise AssertionError('optimizer cannot be reached')
    with pytest.raises(UncertifiedStop):train_filtered(Forbidden(),data,lease_check=lambda:None)


def test_a4_actor_denominator_includes_all_accumulation_rows():
    _,data=many_tokens()
    for k,v in list(data.items()):data[k]=v.repeat(2,*([1]*(v.ndim-1)))
    data['v4_certified'][1]=True;data['sample_mask'][1]=0
    data['token_mask'][0,99:]=0
    with pytest.raises(UncertifiedStop) as e:guard(data)
    assert e.value.report['uncertified_generated_fraction']<.01
    assert e.value.report['uncertified_actor_fraction']>.01


def test_a2_installed_receipt_and_engine_fallback():
    p=Path(__file__).resolve().parents[1]/'phase2/sampler_cpu_receipt.json';r=json.loads(p.read_text())
    assert r['positions']>=10000 and r['mismatched_tokens']==0 and r['flashinfer_absent']
    a=[[1,2]]*8;b=copy.deepcopy(a);b[0]=[1,3]
    assert engine_check(a,a)['status']=='PASS'
    assert engine_check(a,b)['status']=='NEED_R2'
    assert engine_check(a,b,a)['status']=='FAIL'
    c=copy.deepcopy(a);c[1]=[1]
    result=engine_check(a,b,c)
    assert result['status']=='PASS' and result['R0_R1'][0]['first_divergence']==1
    b[2]=[3];b[3]=[3];assert engine_check(a,b,c)['status']=='FAIL'


@pytest.mark.parametrize('processes,leases,pane,expected',[
    ([{'kind':'runner'},{'kind':'stage'}],[],'waiting for an idle GPU','WAIT_STAGE_RUNNING'),
    ([{'kind':'runner'}],['lease'],'waiting for an idle GPU','WAIT_LEASE_HELD'),
    ([{'kind':'runner'}],[],'running','WAIT_BOUNDARY'),
    ([{'kind':'runner'}],[],'waiting for an idle GPU','READY')])
def test_pause_refuses_running_stage(processes,leases,pane,expected):
    assert boundary(pane,processes,leases)==expected


def test_pause_refuses_before_window_without_probe(tmp_path):
    from pause_v3 import pause
    with pytest.raises(ValueError,match='veto'):
        pause('unused',work=tmp_path,veto_not_issued=True,now=VETO_END-1,
              probe=lambda *a:pytest.fail('must not inspect or signal'))
    assert not list(tmp_path.iterdir())


def test_adapter_vectors_and_environment(tmp_path):
    from stage_process import command
    argv,env=command(tmp_path/'runtime.json')
    assert argv[0]==sys.executable and argv[-2:] == ['--config',str(tmp_path/'runtime.json')]
    assert env['VLLM_USE_FLASHINFER_SAMPLER']=='0' and env['HF_HUB_OFFLINE']=='1'
    assert '--stub-engines' not in argv
    argv,env=command(tmp_path/'runtime.json',synthetic=True)
    assert argv[-1]=='--stub-engines' and env['CUDA_VISIBLE_DEVICES']==''


def test_retained_subprocess_timeout_and_normal_equivalence(tmp_path):
    import subprocess
    from scoring_runtime import retain_commands
    with retain_commands(tmp_path/'commands'):
        result=subprocess.run([sys.executable,'-c','print("hello")'],capture_output=True,text=True,timeout=5)
        assert result.stdout=='hello\n' and result.returncode==0
        with pytest.raises(subprocess.TimeoutExpired):
            subprocess.run([sys.executable,'-c','import time; print("partial",flush=True); time.sleep(3)'],capture_output=True,timeout=.2)
    assert (tmp_path/'commands/0001/stdout').read_text()=='partial\n'
    assert json.loads((tmp_path/'commands/0001/exit.json').read_text())['timeout']


def test_forecast_verifies_and_rejects_mutation(tmp_path):
    from forecast_score import verified,FORECAST_SHA256,auc,q8
    source=next(Path(__file__).resolve().parents[3].glob('19_*/expt_v1/forecasts/e19_g3_forecast_v4_g0.json'))
    d=verified(source);assert len(d['per_task']['task_id'])==539
    assert source.with_suffix('.sha256').read_text().startswith(FORECAST_SHA256)
    p=tmp_path/'forecast.json';p.write_bytes(source.read_bytes()+b' ')
    p.with_suffix('.sha256').write_bytes(source.with_suffix('.sha256').read_bytes())
    with pytest.raises(ValueError):verified(p)
    assert auc([0,0,1,1],[False,False,True,True])==1
    assert q8(0)==0 and q8(32)==0 and q8(16)>0


def test_never_publish_task_ids_from_forecast(monkeypatch,tmp_path):
    import forecast_score as f
    tasks=[f'private_{i}' for i in range(32)]
    fake={'per_task':{'task_id':tasks,**{k:list(range(32)) for k in f.FIELDS}},'v4_g0':{'tasks':tasks}}
    monkeypatch.setattr(f,'verified',lambda p:fake)
    rows=[{'task_id':t,'sample_idx':j,'strict':int(j<i)} for i,t in enumerate(tasks) for j in range(32)]
    r=f.score('fixture',rows,tasks,8,tmp_path)
    assert r['complete_tasks']==32 and r['gate_input'] is False and r['chosen_G']==8
    assert 'private_' not in json.dumps(r) and len(r['forecasts'])==3
    assert (tmp_path/'private_forecast_join.json').exists()


def test_inherited_advantages_match_installed_v3_scaling():
    from gates import advantages
    from nemo_rl.algorithms.utils import calculate_baseline_and_std_per_prompt
    rewards=torch.tensor([0.,0.,0.,0.,.3,.4,.5,1.])
    base,std=calculate_baseline_and_std_per_prompt(torch.zeros((8,1),dtype=torch.long),rewards,torch.ones(8),leave_one_out_baseline=True)
    expected=rewards-base;selected=std>0;expected[selected]/=std[selected]+1e-6
    actual=advantages([[{'strict':float(r)} for r in rewards]],'strict')[0]['advantages']
    assert actual==pytest.approx(expected.tolist(),abs=1e-7)


def test_a4_cap_two_and_certified_only_metrics(monkeypatch):
    monkeypatch.setattr(torch.Tensor,'cuda',lambda self,*a,**kw:self)
    import importance
    importance.COLLECTOR=[]
    logits,data=many_tokens();data['generation_logprobs'][:,2:]-=10
    loss,metrics=FilteredClippedPGLossFn()(logits/.6,data,torch.tensor(1.),torch.tensor(100.))
    assert loss.item()==pytest.approx(-1.99,abs=1e-6)
    d=importance.COLLECTOR[-1]
    assert summarize(d['v4_actor_logweight_values'])['actor_logweight_certified_only']['clamp_rate']==1


def test_actual_trainer_batch_keeps_unknown_and_complete_missing_group():
    from trainer_runtime import batch
    from gates import advantages
    row={'task_id':'test','split':'train','prompt_token_ids':[100],'output_token_ids':[151645],
         'finish_reason':'stop','strict':1,'receipt':[{'token':151645,'certified':True,'generator_logp':0.}]}
    groups=[[copy.deepcopy(row) for _ in range(8)] for _ in range(32)]
    groups[0][0]['receipt'][0].update(certified=False,generator_logp=None)
    groups[1][0]['strict']=None
    data=batch(groups,advantages(groups,'strict'))
    assert torch.isnan(data['generation_logprobs'][0,1]) and data['v4_certified'][0,1]==False
    assert data['sample_mask'][8:16].sum()==0
    r=guard(data);assert r['generated_positions']==256 and r['valid_actor_tokens']==248
    assert r['uncertified_generated_fraction']==1/256 and r['uncertified_actor_fraction']==1/248


def test_old_support_measurement_allows_refit_token_outside_old_support():
    from trainer_support import freeze_batch
    old,data=loss_batch();data['input_ids'][0,1]=0
    with pytest.raises(ValueError,match='outside'):freeze_batch(old,data)
    r=freeze_batch(old,data,allow_outside=True)
    assert torch.isneginf(r['prev_logprobs'][0,1])
    assert 0 not in r['v4_support_ids'][0,1][r['v4_support_mask'][0,1]].tolist()


def test_stage_pythonpath_and_forecast_location_are_real():
    from stage_process import command
    _,env=command('/unused')
    assert str(Path(__file__).resolve().parents[4]/'src') in env['PYTHONPATH'].split(':')
    assert env['PATH'].split(':')[0]==str(Path.home()/'.elan/bin')
    from runner import __file__ as runner_path
    assert len(list(Path(runner_path).resolve().parents[3].glob('19_*/expt_v1/forecasts/e19_g3_forecast_v4_g0.json')))==1


def test_retirement_keeps_latest_and_verifiable_metadata(tmp_path):
    from retention import retire_completed
    from stage_ledger import tree_bindings
    work=tmp_path/'run';roots=[]
    for u in (1,2):
        root=work/'PILOT30/A_1301'/f'update_{u:05d}';roots.append(root)
        for name in ('before','after'):
            write_new(root/'update'/name/'receipt.json',{'bindings':[{'sha256':'synthetic'}]})
            p=root/'update'/name/'weights/state.distcp';p.parent.mkdir();p.write_bytes(b'synthetic')
        write_new(root/'export/export_receipt.json',{'synthetic':True})
        (root/'export/weights.bin').write_bytes(b'synthetic')
        write_new(root/'summary.json',{'completed':True,'checkpoint':str(root/'update/after'),'model':str(root/'export')})
    before=tree_bindings(work)
    retire_completed(work,'A',1301,2)
    assert tree_bindings(work)==before
    assert not (roots[0]/'update/after/weights/state.distcp').exists()
    assert not (roots[1]/'update/before/weights/state.distcp').exists()
    assert (roots[1]/'update/after/weights/state.distcp').exists()
    assert (roots[1]/'export/weights.bin').exists()
    assert list(roots[0].rglob('*.retired.json'))


@pytest.mark.parametrize('arguments,expected',[
    (['/venv/bin/python','pilot_run.py','--arm','A','--seed','1301'],True),
    (['/venv/bin/python','/repo/resume_pilot_after_foreign_gpu.py','retry','A','1301','3'],True),
    (['sh','-c','cd /repo && python pilot_run.py --arm A --seed 1301'],False),
    (['python','pilot_run.py','--arm','B','--seed','1301'],False),
])
def test_pause_runner_identity_excludes_pane_shell(arguments,expected):
    from pause_v3 import is_runner
    assert is_runner(arguments,'A','1301') is expected


def test_pause_group_allows_only_its_verified_pane_shell():
    from pause_v3 import isolated_group
    runner={'pid':11,'ppid':10,'pgid':10,'uid':100,'arguments':['python','pilot_run.py']}
    shell={'pid':10,'ppid':1,'pgid':10,'uid':100,'arguments':['sh','-c','runner command']}
    assert isolated_group(runner,10,[shell,runner])
    assert not isolated_group(runner,10,[shell,runner,{'pid':12}])
    assert not isolated_group(runner,99,[shell,runner])
    assert not isolated_group(runner,10,[{**shell,'uid':101},runner])
