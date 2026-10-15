"""Validate actual installed NeMo CPU batching and replay utilities without allocating a device."""
from pathlib import Path
import importlib.util
import json,os,subprocess
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
spec=importlib.util.spec_from_file_location('e13_training_data',PHASE/'training_data.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def groups():
    out=[]
    for group_index in range(3):
        rows=[]
        for slot in range(8):
            reward=slot/7 if group_index==0 else .1 if group_index==1 else 1. if slot else None
            rows.append({'split':'train','group_index':group_index,'slot':slot,'task_id':'same_fixture_task',
                'prompt_token_ids':[1,2],'output_token_ids':[3,9],'generation_logprobs':[-.3,-.2],
                'finish_reason':'stop','reward':reward})
        out.append({'group_index':group_index,'task_id':'same_fixture_task','rows':rows})
    return out


@pytest.mark.parametrize('defect',['test','missing_slot','prompt','eos','support','cap'])
def test_invalid_training_receipts_fail_before_tensor_or_model_work(defect):
    data=groups();row=data[0]['rows'][0]
    if defect=='test':row['split']='test'
    if defect=='missing_slot':data[0]['rows'].pop()
    if defect=='prompt':row['prompt_token_ids']=[4]
    if defect=='eos':row['output_token_ids']=[9,3]
    if defect=='support':row['generation_logprobs'][0]=None
    if defect=='cap':row['finish_reason']='length'
    with pytest.raises(ValueError):module.validate_groups(data,terminal_token_ids=[9])


def test_installed_nemo_batches_masks_loss_and_worker_replay_on_cpu(tmp_path):
    python=Path(os.environ.get('E13_NEMO_PYTHON','/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'))
    if not python.exists():
        if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION')=='1':pytest.fail('required installed NeMo CPU verification route missing')
        pytest.skip('installed NeMo environment unavailable')
    source=tmp_path/'groups.json';source.write_text(json.dumps(groups()))
    code=r'''
import json,sys,random
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import numpy as np,torch
from training_data import build
from worker_state import save_rng,restore_rng,parameter_digest,optimizer_digest
from nemo_rl.algorithms.loss_functions import ClippedPGLossFn
assert not torch.cuda.is_available(), 'CPU regression must not allocate an experiment device'
data,counts=build(json.loads(Path(sys.argv[2]).read_text()),pad_token_id=0,terminal_token_ids=[9])
assert counts['declared_slots']==24 and counts['measured_rewards']==23
assert counts['usable_groups']==2 and counts['unmeasured_groups']==1
assert counts['generated_tokens']==48 and counts['optimized_tokens']==32
assert data['token_mask'].tolist()==[[0.,0.,1.,1.]]*24
assert (data['advantages'][8:]==0).all() and (data['sample_mask'][16:]==0).all()
assert (data['sample_mask'][:16]==1).all() and (data['advantages'][:8,2:]!=0).any()
torch.manual_seed(42)
logits=torch.randn(24,4,12,requires_grad=True)
lp=torch.log_softmax(logits.detach()[:,:-1].float(),-1).gather(-1,data['input_ids'][:,1:,None]).squeeze(-1)
data['prev_logprobs']=torch.cat([torch.zeros(24,1),lp],1)
data['generation_logprobs']=data['prev_logprobs'].clone()
loss_fn=ClippedPGLossFn(dict(reference_policy_kl_penalty=0.,ratio_clip_min=.2,ratio_clip_max=.28,
 ratio_clip_c=None,use_on_policy_kl_approximation=False,use_importance_sampling_correction=True,
 truncated_importance_sampling_ratio=2.,token_level_loss=True,sequence_level_importance_ratios=False))
# The installed loss hard-codes one Tensor.cuda() placement. Override only that
# placement in this CPU fixture; the production trainer remains unchanged.
original_cuda=torch.Tensor.cuda
torch.Tensor.cuda=lambda self,*args,**kwargs:self
try:loss,metrics=loss_fn(logits,data,torch.tensor(16.),torch.tensor(32.))
finally:torch.Tensor.cuda=original_cuda
assert torch.isfinite(loss)
loss.backward();assert torch.isfinite(logits.grad).all()
assert (logits.grad[8:]==0).all() and (logits.grad[:8]!=0).any()
class Worker:pass
worker=Worker();worker.model=torch.nn.Linear(2,2)
original=parameter_digest(worker)
path=Path(sys.argv[2]).with_name('rng.pt')
save_rng(worker,path)
a=(random.random(),float(np.random.random()),torch.rand(3))
restore_rng(worker,path)
b=(random.random(),float(np.random.random()),torch.rand(3))
assert a[:2]==b[:2] and torch.equal(a[2],b[2])
assert parameter_digest(worker)==original
with torch.no_grad():next(worker.model.parameters()).add_(1e-4)
assert parameter_digest(worker)['sha256']!=original['sha256']
worker.optimizer=torch.optim.AdamW(worker.model.parameters(),lr=1e-6)
worker.scheduler=torch.optim.lr_scheduler.LambdaLR(worker.optimizer,lambda step:1.)
start=optimizer_digest(worker)
worker.model(torch.ones(1,2)).sum().backward();worker.optimizer.step();worker.scheduler.step()
assert optimizer_digest(worker)['sha256']!=start['sha256']
import copy
saved=copy.deepcopy(worker.optimizer.state_dict());sched=copy.deepcopy(worker.scheduler.state_dict())
expected=optimizer_digest(worker)
worker.optimizer.step();worker.scheduler.step()
worker.optimizer.load_state_dict(saved);worker.scheduler.load_state_dict(sched)
assert optimizer_digest(worker)==expected
print(json.dumps({'status':'PASS','device_allocations':0,'counts':counts,'finite_loss':float(loss.detach()),'test_only_device_move':'Tensor.cuda is CPU identity in this fixture'}))
'''
    result=subprocess.run([str(python),'-c',code,str(PHASE),str(source)],capture_output=True,text=True,timeout=120,
        env={**os.environ,'CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'})
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    receipt=json.loads(result.stdout.splitlines()[-1]);assert receipt['status']=='PASS' and receipt['device_allocations']==0
