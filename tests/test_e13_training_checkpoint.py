"""Exercise installed native save/restore/export on a tiny authored CPU model, without a GPU or dataset."""
from pathlib import Path
import importlib.util
import json,os,subprocess
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
spec=importlib.util.spec_from_file_location('e13_training_checkpoint',PHASE/'training_checkpoint.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_checkpoint_manifest_refuses_changed_bytes_and_escaping_paths(tmp_path):
    (tmp_path/'weights').write_bytes(b'fixture')
    bindings=module.file_bindings(tmp_path)
    assert module.verify_files(tmp_path,bindings)
    (tmp_path/'weights').write_bytes(b'changed')
    with pytest.raises(ValueError,match='changed'):module.verify_files(tmp_path,bindings)
    bindings[0]['relative_path']='../weights'
    with pytest.raises(ValueError,match='escapes'):module.verify_files(tmp_path,bindings)
    with pytest.raises(ValueError,match='duplicate'):module.verify_files(tmp_path,bindings*2)


def test_checkpoint_inventory_rejects_symlink(tmp_path):
    (tmp_path/'source').write_text('fixture')
    (tmp_path/'link').symlink_to(tmp_path/'source')
    with pytest.raises(ValueError,match='symlink'):module.file_bindings(tmp_path)


def test_installed_native_checkpoint_replay_and_export_cpu(tmp_path):
    python=Path(os.environ.get('E13_NEMO_PYTHON','/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'))
    if not python.exists():
        if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION')=='1':pytest.fail('required installed NeMo route unavailable')
        pytest.skip('installed NeMo unavailable')
    code=r'''
import json,sys,random
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,sys.argv[1])
import numpy as np,torch,ray
from transformers import Qwen3Config,Qwen3ForCausalLM,PreTrainedTokenizerFast
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from nemo_rl.utils.native_checkpoint import save_checkpoint
from training_checkpoint import save,restore,export,verify_files
from trainer_core import update
from worker_state import parameter_digest,optimizer_digest,initialize_rng
assert not torch.cuda.is_available()
torch.set_num_threads(1);torch.manual_seed(17)
root=Path(sys.argv[2]);source=root/'source';source.mkdir()
config=Qwen3Config(vocab_size=16,hidden_size=16,intermediate_size=32,num_hidden_layers=1,
 num_attention_heads=2,num_key_value_heads=2,head_dim=8,max_position_embeddings=32,
 attention_dropout=.1,tie_word_embeddings=False)
model=Qwen3ForCausalLM(config);config.save_pretrained(source)
tokenizer=PreTrainedTokenizerFast(tokenizer_object=Tokenizer(WordLevel({f't{i}':i for i in range(16)},unk_token='t0')),
 unk_token='t0',eos_token='t1',pad_token='t2')
tokenizer.save_pretrained(source)
worker=SimpleNamespace(model=model,optimizer=torch.optim.AdamW(model.parameters(),lr=1e-3))
worker.scheduler=torch.optim.lr_scheduler.LambdaLR(worker.optimizer,lambda step:1.)
# Execute our callbacks synchronously on this authored CPU worker. The installed
# checkpoint implementation is real; Ray transport and distributed GPU behavior are not tested here.
class Call:
 def remote(self,fn,*args):return fn(worker,*args)
class Policy:
 def prepare_for_lp_inference(self):worker.model.eval()
 def prepare_for_training(self):worker.model.train()
 def get_logprobs(self,data):
  with torch.no_grad():
   logits=worker.model(data['input_ids']).logits
   values=logits[:,:-1].float().log_softmax(-1).gather(-1,data['input_ids'][:,1:,None]).squeeze(-1)
   return {'logprobs':torch.cat([torch.zeros(values.shape[0],1),values],1)}
 def train(self,data,loss_fn,gbs,mbs):
  assert gbs==len(data['input_ids'])==8 and mbs==1
  worker.model.train();worker.optimizer.zero_grad()
  logits=worker.model(data['input_ids']).logits
  original_cuda=torch.Tensor.cuda;torch.Tensor.cuda=lambda self,*args,**kwargs:self
  try:loss,metrics=loss_fn(logits,data,data['sample_mask'].sum(),
    (data['token_mask'][:,1:]*data['sample_mask'][:,None]).sum())
  finally:torch.Tensor.cuda=original_cuda
  loss.backward();norm=torch.nn.utils.clip_grad_norm_(worker.model.parameters(),1.)
  worker.optimizer.step();worker.scheduler.step()
  return {'loss':loss.detach().reshape(1),'grad_norm':norm.reshape(1)}
 worker_group=SimpleNamespace(workers=[SimpleNamespace(__ray_call__=Call())])
 def save_checkpoint(self,weights,optimizer,tokenizer_path):
  save_checkpoint(worker.model,weights,worker.optimizer,worker.scheduler,optimizer,tokenizer,tokenizer_path)
policy=Policy();original_get=ray.get;ray.get=lambda value:value
initialize_rng(worker,13011)
seeded=(random.random(),float(np.random.random()),torch.rand(3))
initialize_rng(worker,13011)
repeated=(random.random(),float(np.random.random()),torch.rand(3))
assert seeded[:2]==repeated[:2] and torch.equal(seeded[2],repeated[2])
initialize_rng(worker,13012)
assert seeded[0]!=random.random()
try:initialize_rng(worker,True)
except ValueError:pass
else:raise AssertionError('boolean is not a paired run seed')
try:
 initial_parameters=parameter_digest(worker);initial_optimizer=optimizer_digest(worker)
 saved=save(policy,root/'native',provenance={'fixture':'authored CPU model','update':0})
 assert parameter_digest(worker)==initial_parameters
 assert optimizer_digest(worker)==initial_optimizer, 'native saver must not advance initially empty Adam state'
 before=parameter_digest(worker);optim=optimizer_digest(worker)
 ids=torch.tensor([[3,4,5,1]])
 def fixture_step():
  worker.model.train();worker.optimizer.zero_grad()
  loss=worker.model(input_ids=ids,labels=ids).loss
  loss.backward();worker.optimizer.step();worker.scheduler.step()
  return float(loss.detach()),parameter_digest(worker),optimizer_digest(worker)
 first=fixture_step();assert first[1]!=before and first[2]!=optim
 assert all(int(state['step'])==1 for state in worker.optimizer.state.values())
 restore(policy,root/'native')
 assert parameter_digest(worker)==before and optimizer_digest(worker)==optim
 second=fixture_step();assert first==second,(first,second)
 updated=save(policy,root/'updated',provenance={'fixture':'authored CPU model','update':1})
 exported=export(root/'updated',root/'export',model_config=source,tokenizer=source)
 assert exported['parameters']==parameter_digest(worker)
 loaded=Qwen3ForCausalLM.from_pretrained(root/'export',local_files_only=True)
 assert parameter_digest(SimpleNamespace(model=loaded))==parameter_digest(worker)
 loaded.eval();worker.model.eval()
 with torch.no_grad():assert torch.equal(loaded(ids).logits,worker.model(ids).logits)
 verify_files(root/'export',exported['bindings'])
 try:export(root/'updated',root/'export',model_config=source,tokenizer=source)
 except FileExistsError:pass
 else:raise AssertionError('existing export was overwritten')
 rows=[{'split':'train','task_id':'authored_fixture','group_index':0,'slot':i,
  'prompt_token_ids':[3,4],'output_token_ids':[5,1],'generation_logprobs':[-2.,-2.],
  'finish_reason':'stop','reward':float(i%2)} for i in range(8)]
 groups=[{'group_index':0,'task_id':'authored_fixture','rows':rows}]
 loss_config=dict(reference_policy_kl_penalty=0.,ratio_clip_min=.2,ratio_clip_max=.28,
  ratio_clip_c=None,use_on_policy_kl_approximation=False,use_importance_sampling_correction=True,
  truncated_importance_sampling_ratio=2.,token_level_loss=True,sequence_level_importance_ratios=False)
 receipt=update(policy,groups,pad_token_id=2,terminal_token_ids=[1],loss_config=loss_config,
  root=root/'core_update',provenance={'fixture':'authored CPU update'},lease_check=lambda:None,replay=True)
 assert receipt['status']=='MEASURED' and receipt['optimizer_updates']==1 and receipt['parameter_change']
 assert receipt['replay']['maximum_loss_difference']==0.
 assert receipt['replay']['parameter_digest_equal'] and receipt['replay']['optimizer_digest_equal']
 assert receipt['counts']['declared_slots']==8 and receipt['counts']['generated_tokens']==16
 state=parameter_digest(worker);optim=optimizer_digest(worker)
 for row in rows:row['reward']=None
 missing=update(policy,groups,pad_token_id=2,terminal_token_ids=[1],loss_config=loss_config,
  root=root/'unmeasured',provenance={'fixture':'authored CPU missing scores'},lease_check=lambda:None)
 assert missing['status']=='UNMEASURED' and missing['optimizer_updates']==0
 assert state==parameter_digest(worker) and optim==optimizer_digest(worker)
 print(json.dumps({'status':'PASS','gpu_allocations':0,'replay_loss_difference':abs(first[0]-second[0]),
  'exact_updated_weights_and_optimizer':True,'native_to_export_tensor_identity':True,'export_reload_logits_equal':True}))
finally:ray.get=original_get
'''
    result=subprocess.run([str(python),'-c',code,str(PHASE),str(tmp_path)],capture_output=True,text=True,timeout=120,
        env={**os.environ,'CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
             'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1'})
    assert result.returncode==0,result.stdout+'\n'+result.stderr
    receipt=json.loads(result.stdout.splitlines()[-1]);assert receipt['status']=='PASS' and receipt['gpu_allocations']==0
