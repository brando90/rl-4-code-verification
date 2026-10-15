"""Execute one complete-group installed NeMo update, retaining the exact replay inputs and state."""
from __future__ import annotations

from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent
PHASE1=HERE.parent/'phase1'
if str(PHASE1) not in sys.path:sys.path.insert(0,str(PHASE1))
from runtime import check_lease
from training_data import build
from training_checkpoint import write_new,digest,save,restore,owned_call
from worker_state import parameter_digest,optimizer_digest,initialize_rng


def plain(value):
    """Serialize tensor/scalar metrics without silently converting nonfinite results."""
    if hasattr(value,'detach'):value=value.detach().cpu().tolist()
    if hasattr(value,'item') and not isinstance(value,(list,dict)):value=value.item()
    if isinstance(value,dict):return {str(k):plain(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [plain(v) for v in value]
    if isinstance(value,float) and not math.isfinite(value):raise ValueError('nonfinite trainer metric')
    if value is None or isinstance(value,(str,bool,int,float)):return value
    raise ValueError('unsupported trainer metric: '+type(value).__name__)


@contextmanager
def policy_session(config,*,checkpoint=None,init_optimizer=True):
    """Construct a new owned Ray cluster on the freshly checked numeric leased device."""
    import ray
    from transformers import AutoTokenizer
    from nemo_rl.distributed.virtual_cluster import RayVirtualCluster
    from nemo_rl.distributed.ray_actor_environment_registry import ACTOR_ENVIRONMENT_REGISTRY
    from nemo_rl.models.policy.lm_policy import Policy
    check_lease(config)
    policy_config=json.loads(Path(config['policy_config']).read_text())
    if (policy_config['precision']!='float16' or policy_config['generation']['vllm_cfg']['precision']!='float16'
            or policy_config['model_name']!=config['initial_model']):
        raise ValueError('S2 trainer model or numerical configuration changed')
    tokenizer=AutoTokenizer.from_pretrained(config['tokenizer'],local_files_only=True)
    ACTOR_ENVIRONMENT_REGISTRY['nemo_rl.models.policy.dtensor_policy_worker.DTensorPolicyWorker']=sys.executable
    original_pythonpath=os.environ.get('PYTHONPATH')
    os.environ['PYTHONPATH']=os.pathsep.join([str(HERE),str(PHASE1),original_pythonpath or '']).rstrip(os.pathsep)
    cluster=None;policy=None
    try:
        ray.init(address='local',num_gpus=1,num_cpus=4,include_dashboard=False,
                 _temp_dir=config['ray_temp'],log_to_driver=True)
        cluster=RayVirtualCluster([1],num_gpus_per_node=1,name='e13v2-S2-training')
        policy=Policy(cluster,policy_config,tokenizer,name_prefix='e13v2-S2-training',
                      init_optimizer=init_optimizer,init_reference_model=False)
        if checkpoint is not None:
            if not init_optimizer:raise ValueError('resuming training requires optimizer state')
            restore(policy,checkpoint)
        else:
            owned_call(policy,initialize_rng,config['run_seed'])
        yield policy,tokenizer
    finally:
        if policy is not None:policy.shutdown()
        if cluster is not None:cluster.shutdown()
        ray.shutdown()
        if original_pythonpath is None:os.environ.pop('PYTHONPATH',None)
        else:os.environ['PYTHONPATH']=original_pythonpath


def recompute(policy,data,*,lease_check):
    """Use the admitted batch-one log-probability path, retaining assistant and terminal positions."""
    import torch
    from nemo_rl.distributed.batched_data_dict import BatchedDataDict
    policy.prepare_for_lp_inference()
    output=torch.zeros_like(data['generation_logprobs'])
    for index,length in enumerate(data['input_lengths'].tolist()):
        lease_check()
        row=BatchedDataDict({'input_ids':data['input_ids'][index:index+1,:length].clone(),
            'input_lengths':torch.tensor([length],dtype=torch.long),
            'token_mask':data['token_mask'][index:index+1,:length].clone(),
            'sample_mask':torch.ones(1,dtype=torch.float32)})
        values=policy.get_logprobs(row)['logprobs'][0,:length].detach().cpu()
        mask=data['token_mask'][index,:length].bool()
        if len(values)!=length or not torch.isfinite(values[mask]).all():
            raise ValueError('unsupported or misaligned trainer log probabilities')
        output[index,:length]=values
    data['prev_logprobs']=output
    return data


def update(policy,groups,*,pad_token_id,terminal_token_ids,loss_config,root,provenance,lease_check,replay=False):
    """Run once; T3 may explicitly replay the saved batch from the identical pre-update state."""
    import torch
    from nemo_rl.algorithms.loss_functions import ClippedPGLossFn
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    write_new(root/'attempt.json',{'condition':'v2-S2','provenance':provenance,'explicit_T3_replay':replay,
                                  'started_unix':time.time()})
    write_new(root/'groups.json',groups)
    try:
        data,counts=build(groups,pad_token_id=pad_token_id,terminal_token_ids=terminal_token_ids)
        write_new(root/'counts.json',counts)
        if counts['usable_groups']==0:
            result={'condition':'v2-S2','status':'UNMEASURED','counts':counts,'optimizer_updates':0,
                    'reason':'no complete measured reward group; no optimizer call'}
            write_new(root/'result.json',result);return result
        lease_check();data=recompute(policy,data,lease_check=lease_check)
        # The exact loss input is durable before any optimizer operation. Retain
        # behavior and recomputed probabilities, including masked groups.
        batch_path=root/'batch.pt'
        with batch_path.open('xb') as out:
            torch.save(dict(data),out);out.flush()
            import os;os.fsync(out.fileno())
        policy.prepare_for_training()
        before=save(policy,root/'before',provenance={**provenance,'batch_sha256':digest(batch_path)})
        loss_fn=ClippedPGLossFn(loss_config)
        lease_check();started=time.monotonic()
        metrics=plain(policy.train(data,loss_fn,gbs=counts['declared_slots'],mbs=1))
        if metrics.get('grad_norm') is None:raise ValueError('training gradient norm missing')
        elapsed=time.monotonic()-started
        after_parameters=owned_call(policy,parameter_digest);after_optimizer=owned_call(policy,optimizer_digest)
        after=save(policy,root/'after',provenance={**provenance,'batch_sha256':digest(batch_path),'transition':'after'})
        if after['parameters']!=after_parameters or after['optimizers']!=after_optimizer:
            raise ValueError('saving updated checkpoint changed training state')
        replay_result=None
        if replay:
            # First-update state remains saved separately; this diagnostic second
            # execution never becomes the continuation checkpoint.
            lease_check();policy.prepare_for_training();restore(policy,root/'before')
            replay_data=torch.load(batch_path,map_location='cpu',weights_only=True)
            from nemo_rl.distributed.batched_data_dict import BatchedDataDict
            replay_metrics=plain(policy.train(BatchedDataDict(replay_data),loss_fn,
                                             gbs=counts['declared_slots'],mbs=1))
            first_loss=torch.as_tensor(metrics['loss'],dtype=torch.float64)
            second_loss=torch.as_tensor(replay_metrics['loss'],dtype=torch.float64)
            if first_loss.shape!=second_loss.shape:raise ValueError('replay loss dimensions changed')
            difference=float((first_loss-second_loss).abs().max())
            replay_result={'metrics':replay_metrics,'maximum_loss_difference':difference,
                'within_0p001':difference<=.001,
                'parameter_digest_equal':owned_call(policy,parameter_digest)==after_parameters,
                'optimizer_digest_equal':owned_call(policy,optimizer_digest)==after_optimizer}
            # Restore the durable first update for any subsequent refit inspection.
            restore(policy,root/'after')
        result={'condition':'v2-S2','status':'MEASURED','counts':counts,'optimizer_updates':1,
            'diagnostic_replay_updates':int(replay),'metrics':metrics,'training_seconds':elapsed,
            'parameter_change':before['parameters']!=after_parameters,'replay':replay_result,
            'before_receipt_sha256':digest(root/'before/receipt.json'),
            'after_receipt_sha256':digest(root/'after/receipt.json'),'batch_sha256':digest(batch_path)}
        write_new(root/'result.json',result);return result
    except Exception as exc:
        write_new(root/'error.json',{'condition':'v2-S2','status':'INCOMPLETE','error_type':type(exc).__name__,
            'error':str(exc),'provenance':provenance,'rerun_admitted':False})
        raise
