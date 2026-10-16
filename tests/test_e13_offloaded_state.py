"""Reproduce CPU-offloaded DTensor collective failure and preserve complete checkpoint digest bytes."""
from pathlib import Path
import json,os,subprocess
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'


def test_installed_one_rank_dtensor_digest_without_collective(tmp_path):
    python=Path(os.environ.get('E13_NEMO_PYTHON','/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'))
    if not python.exists():
        if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION')=='1':pytest.fail('required installed NeMo route unavailable')
        pytest.skip('installed NeMo unavailable')
    code=r'''
import sys,json,hashlib
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,sys.argv[1])
import torch,torch.distributed as dist
from torch.distributed.device_mesh import init_device_mesh
from torch.distributed.tensor import DTensor,Shard,Replicate,Partial
from worker_state import complete_tensor,parameter_digest,optimizer_digest
from checkpoint_state_preflight import inspect_worker
assert not torch.cuda.is_available()
torch.set_num_threads(1)
dist.init_process_group('gloo',init_method='file://'+str(Path(sys.argv[2])/'rendezvous'),rank=0,world_size=1)
mesh=init_device_mesh('cpu',(1,))
values=torch.arange(12,dtype=torch.float16).reshape(3,4)
def worker(value):
 return SimpleNamespace(model=SimpleNamespace(state_dict=lambda:{'weight':value}),
  optimizer=SimpleNamespace(state_dict=lambda:{'state':{0:{'exp_avg':value,'exp_avg_sq':[value]}},'param_groups':[{'lr':1e-6}]}),
  scheduler=SimpleNamespace(state_dict=lambda:{'last_epoch':0}))
# Independent legacy byte serialization, not just equality between two new paths.
h=hashlib.sha256();h.update(json.dumps(['weight',str(values.dtype),list(values.shape)],separators=(',',':')).encode())
h.update(values.reshape(-1).view(torch.uint8).numpy().tobytes())
expected=parameter_digest(worker(values));assert expected['sha256']==h.hexdigest()
expected_optimizer=optimizer_digest(worker(values))
assert complete_tensor(values) is values
original=DTensor.full_tensor
calls=[]
def unsupported(self,*args,**kwargs):
 calls.append(True)
 raise RuntimeError('No backend type associated with device type cpu')
try:
 for placement in (Shard(0),Shard(1),Replicate(),Partial()):
  distributed=DTensor.from_local(values.clone(),mesh,[placement],run_check=True)
  assert torch.equal(original(distributed),values)
  DTensor.full_tensor=unsupported
  try:distributed.full_tensor()
  except RuntimeError as exc:assert str(exc)=='No backend type associated with device type cpu'
  else:raise AssertionError('original failure not reproduced')
  count=len(calls)
  assert parameter_digest(worker(distributed))==expected
  assert optimizer_digest(worker(distributed))==expected_optimizer
  receipt=inspect_worker(worker(distributed))
  assert receipt['distributed_state_tensors']==receipt['cpu_offloaded_state_tensors']==1
  assert receipt['parameters']==expected and len(calls)==count
  DTensor.full_tensor=original
 # A multi-rank value must gather rather than hash only its local shard.
 class Multi:
  device_mesh=SimpleNamespace(size=lambda:2)
  def to_local(self):raise AssertionError('multi-rank shard was read')
  def full_tensor(self):return values
 assert complete_tensor(Multi()) is values
 class Bad:
  device_mesh=mesh
  shape=(12,)
  def to_local(self):return values
  def full_tensor(self):raise AssertionError('mismatch must fail closed')
 try:complete_tensor(Bad())
 except ValueError as exc:assert 'shape mismatch' in str(exc)
 else:raise AssertionError('invalid local shape was accepted')
 try:inspect_worker(worker(values))
 except ValueError as exc:assert 'did not exercise' in str(exc)
 else:raise AssertionError('ordinary tensor passed distributed preflight')
 print(json.dumps({'status':'PASS','original_error_reproduced':True,'placements':4,
  'parameter_and_nested_optimizer_digests_equal':True,'gpu_allocations':0}))
finally:
 DTensor.full_tensor=original
 dist.destroy_process_group()
# Reproduce the actual backend-dispatch failure without a GPU or monkeypatch:
# registering Gloo only for CUDA leaves CPU collective dispatch unsupported.
dist.init_process_group('cuda:gloo',init_method='file://'+str(Path(sys.argv[2])/'cuda_only_rendezvous'),rank=0,world_size=1)
try:
 mesh=init_device_mesh('cpu',(1,))
 distributed=DTensor.from_local(values.clone(),mesh,[Shard(0)],run_check=False)
 try:distributed.full_tensor()
 except RuntimeError as exc:assert str(exc)=='No backend type associated with device type cpu'
 else:raise AssertionError('real unsupported CPU collective did not fail')
 assert parameter_digest(worker(distributed))==expected
 assert optimizer_digest(worker(distributed))==expected_optimizer
 assert inspect_worker(worker(distributed))['cpu_offloaded_state_tensors']==1
 print(json.dumps({'status':'PASS','original_error_reproduced':True,'real_backend_dispatch_error':True,
  'parameter_and_nested_optimizer_digests_equal':True,'gpu_allocations':0}))
finally:dist.destroy_process_group()
'''
    result=subprocess.run([str(python),'-c',code,str(PHASE),str(tmp_path)],capture_output=True,text=True,timeout=120,
        env={**os.environ,'CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
             'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1'})
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    receipt=json.loads(result.stdout.splitlines()[-1]);assert receipt['status']=='PASS' and receipt['gpu_allocations']==0
