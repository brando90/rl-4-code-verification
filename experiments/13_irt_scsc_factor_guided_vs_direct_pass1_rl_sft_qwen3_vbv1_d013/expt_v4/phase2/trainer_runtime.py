"""TLDR: Run the installed NeMo policy with fixed filtered supports, A4 guards and exact checkpoint replay."""
from contextlib import contextmanager,ExitStack
import json
import os
from pathlib import Path
import sys
import time
import legacy
from legacy import HERE,V2
from device_guard import check
from effect_receipts import mark
from common import digest,object_digest,write_new
from training_checkpoint import save,restore,owned_call
from worker_state import parameter_digest,optimizer_digest,initialize_rng
from ray_paths import short_directory,check_socket

@contextmanager
def policy_session(config,*,checkpoint=None,init_optimizer=True):
    """Construct a new owned Ray cluster on the freshly checked numeric leased device."""
    import ray
    from transformers import AutoTokenizer
    from nemo_rl.distributed.virtual_cluster import RayVirtualCluster
    from nemo_rl.distributed.ray_actor_environment_registry import ACTOR_ENVIRONMENT_REGISTRY
    from nemo_rl.models.policy.lm_policy import Policy
    if checkpoint is None and (type(config.get('run_seed')) is not int or not 0<=config['run_seed']<2**63):
        raise ValueError('a fixed initial run seed is required before model construction')
    check(config)
    policy_config=json.loads(Path(config['policy_config']).read_text())
    from pilot_configuration import validate
    validate(policy_config,config['context'])
    if (policy_config['precision']!='float16' or policy_config['generation']['vllm_cfg']['precision']!='float16'
            or policy_config['model_name']!=config['initial_model']):
        raise ValueError('S2 trainer model or numerical configuration changed')
    check(config, pre_engine=True)
    mark(config, 'engine_started')
    if init_optimizer:mark(config, 'optimizer_started')
    tokenizer=AutoTokenizer.from_pretrained(config['tokenizer'],local_files_only=True)
    ACTOR_ENVIRONMENT_REGISTRY['nemo_rl.models.policy.dtensor_policy_worker.DTensorPolicyWorker']=sys.executable
    original_pythonpath=os.environ.get('PYTHONPATH')
    os.environ['PYTHONPATH']=os.pathsep.join([str(HERE),str(V2/'phase2'),str(V2/'phase1'),original_pythonpath or '']).rstrip(os.pathsep)
    cluster=None;policy=None;paths=ExitStack()
    try:
        ray_temp=paths.enter_context(short_directory(config['ray_temp']))
        check_socket(ray_temp)
        ray.init(address='local',num_gpus=1,num_cpus=4,include_dashboard=False,
                 _temp_dir=str(ray_temp),log_to_driver=True)
        cluster=RayVirtualCluster([1],num_gpus_per_node=1,name='e13v4-training')
        policy=Policy(cluster,policy_config,tokenizer,name_prefix='e13v4-training',
                      init_optimizer=init_optimizer,init_reference_model=False)
        if checkpoint is not None:
            if not init_optimizer:raise ValueError('resuming training requires optimizer state')
            restore(policy,checkpoint)
        else:
            owned_call(policy,initialize_rng,config['run_seed'])
        yield policy,tokenizer
    finally:
        try:
            if policy is not None:policy.shutdown()
            if cluster is not None:cluster.shutdown()
        finally:
            try:ray.shutdown()
            finally:
                paths.close()
                if original_pythonpath is None:os.environ.pop('PYTHONPATH',None)
                else:os.environ['PYTHONPATH']=original_pythonpath



def batch(groups,adv,pad=151643):
    import torch
    from nemo_rl.distributed.batched_data_dict import BatchedDataDict
    rows=[r for g in groups for r in g]
    if len(rows)!=256 or len(groups) not in (16,32):raise ValueError('256 complete declared slots required')
    for g,a in zip(groups,adv):
        if len(g)!=256//len(groups) or len(a['advantages'])!=len(g):raise ValueError('group mismatch')
        if any(r['task_id']!=g[0]['task_id'] or r['prompt_token_ids']!=g[0]['prompt_token_ids'] for r in g):raise ValueError('mixed prompt group')
    maximum=max(len(r['prompt_token_ids'])+len(r['output_token_ids']) for r in rows)
    if maximum>20041:raise ValueError('v4 context exceeded')
    n=len(rows);ids=torch.full((n,maximum),pad,dtype=torch.long)
    mask=torch.zeros((n,maximum));gen=torch.zeros_like(mask);advantages=torch.zeros_like(mask)
    cert=torch.ones_like(mask,dtype=torch.bool);sample=[];lengths=[]
    flat=[(v,m) for a in adv for v,m in zip(a['advantages'],a['sample_mask'])]
    for i,(r,(a,m)) in enumerate(zip(rows,flat)):
        prompt=r['prompt_token_ids'];out=r['output_token_ids'];tokens=prompt+out
        if r['split']!='train' or not prompt or not out or len(out)>12288:raise ValueError('invalid v4 row')
        if (any(t in (151643,151645) for t in out[:-1]) or
            r['finish_reason']=='length' and len(out)!=12288 or
            r['finish_reason']=='stop' and out[-1] not in (151643,151645) or
            r['finish_reason'] not in ('length','stop')):raise ValueError('terminal contract changed')
        receipts=r['receipt']
        if len(receipts)!=len(out) or [p['token'] for p in receipts]!=out:raise ValueError('receipt alignment changed')
        ids[i,:len(tokens)]=torch.tensor(tokens);mask[i,len(prompt):len(tokens)]=1
        gen[i,len(prompt):len(tokens)]=torch.tensor([p['generator_logp'] if p['certified'] else float('nan') for p in receipts])
        cert[i,len(prompt):len(tokens)]=torch.tensor([p['certified'] for p in receipts])
        advantages[i,len(prompt):len(tokens)]=a;sample.append(m);lengths.append(len(tokens))
    return BatchedDataDict({'input_ids':ids,'input_lengths':torch.tensor(lengths),'token_mask':mask,
        'sample_mask':torch.tensor(sample,dtype=torch.float32),'advantages':advantages,
        'generation_logprobs':gen,'v4_certified':cert,'reference_policy_logprobs':torch.zeros_like(mask)})


def freeze(policy,data,*,allow_outside=False):
    import torch
    from nemo_rl.distributed.batched_data_dict import BatchedDataDict
    from trainer_support import collect_old_support
    from worker_hooks import install_on_policy
    install_on_policy(policy);policy.prepare_for_lp_inference()
    collected=[]
    for i,length in enumerate(data['input_lengths'].tolist()):
        row=BatchedDataDict({'input_ids':data['input_ids'][i:i+1,:length].clone(),
            'input_lengths':torch.tensor([length]),'token_mask':data['token_mask'][i:i+1,:length].clone(),
            'sample_mask':data['sample_mask'][i:i+1].clone()})
        values=owned_call(policy,collect_old_support,row,allow_outside)
        if len(values)!=1:raise ValueError('only one rank admitted')
        collected.append(values[0])
    width=max(r['v4_support_ids'].shape[-1] for r in collected);n,length=data['input_ids'].shape
    data['v4_support_ids']=torch.zeros((n,length,width),dtype=torch.long)
    data['v4_support_mask']=torch.zeros((n,length,width),dtype=torch.bool);data['v4_support_mask'][:,:,0]=True
    for k in ('prev_logprobs','v4_discarded_mass'):data[k]=torch.zeros((n,length))
    for i,r in enumerate(collected):
        l=data['input_lengths'][i];w=r['v4_support_ids'].shape[-1]
        data['v4_support_ids'][i,:l,:w]=r['v4_support_ids'][0]
        data['v4_support_mask'][i,:l,:w]=r['v4_support_mask'][0]
        for k in ('prev_logprobs','v4_discarded_mass'):data[k][i,:l]=r[k][0]
    return data


def reset_collector(worker):
    import importance
    importance.COLLECTOR=[]
    return True


def collect_metrics(worker):
    import importance
    values=importance.COLLECTOR
    return {'logweights':[x for row in values for x in row['v4_actor_logweight_values']],
            'perturbation_bound':sum(r['v4_perturbation_bound'] for r in values),
            'certified_actor_tokens':sum(r['v4_certified_actor_tokens'] for r in values),
            'entropy_numerator_certified_only':sum(r['v4_entropy_numerator_certified_only'] for r in values),
            'probability_error_sum_certified_only':sum(r['v4_probability_error_sum_certified_only'] for r in values)}


def scalar(value):
    import torch
    t=torch.as_tensor(value)
    if t.numel()!=1 or not t.isfinite().all():raise ValueError('finite one-rank scalar required')
    return t.item()


def execute_update(config,groups,adv,root):
    import torch
    from importance import guard,summarize
    from nemo_objective import FilteredClippedPGLossFn
    from gates import replay_binding
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    import shutil
    # Two native 4B float16/Adam states plus export during the transition.
    if shutil.disk_usage(root).free<100*1024**3:raise RuntimeError('insufficient storage for complete checkpoint transition; no optimizer started')
    data=batch(groups,adv)
    guard_report=guard(data) # complete update, BEFORE model/optimizer construction
    write_new(root/'importance_guard.json',guard_report)
    with policy_session(config,checkpoint=config.get('checkpoint')) as (policy,_):
        data=freeze(policy,data);guard(data)
        with (root/'batch.pt').open('xb') as f:torch.save(dict(data),f);f.flush();os.fsync(f.fileno())
        write_new(root/'groups.json',groups);write_new(root/'advantages.json',adv)
        policy.prepare_for_training();before=save(policy,root/'before',provenance={'condition':'e13v4','admission':digest(config['admission'])})
        binding=replay_binding(batch=digest(root/'batch.pt'),rewards=object_digest(groups),advantages=object_digest(adv),
            old_support=object_digest(data['v4_support_ids'].tolist()),pre_weights=object_digest(before['parameters']),
            random_state=object_digest(before['random_states']),optimizer_state=object_digest(before['optimizers']),
            scheduler_state=digest(root/'before/receipt.json'),admission=digest(config['admission']))
        owned_call(policy,reset_collector);check(config);started=time.monotonic()
        write_new(root/'optimizer_intent.json',{'steps':1,'replay_binding':binding})
        metrics=policy.train(data,FilteredClippedPGLossFn(),gbs=256,mbs=1)
        elapsed=time.monotonic()-started
        details=owned_call(policy,collect_metrics)
        if len(details)!=1:raise ValueError('unexpected rank count')
        detail=details[0];logweights=detail.pop('logweights')
        after=save(policy,root/'after',provenance={'condition':'e13v4','transition':'after'})
        result={'before_weights':object_digest(before['parameters']),'after_weights':object_digest(after['parameters']),
            'preclip_gradient_norm':scalar(metrics['grad_norm']),'loss':scalar(metrics['loss']),
            'replay_binding':binding,'source_update':str(root),'checkpoint':str(root/'after'),
            'before_receipt_sha256':digest(root/'before/receipt.json'),'batch_sha256':digest(root/'batch.pt'),
            'optimizer_steps':1,'training_seconds':elapsed,
            'importance':{**guard_report,**detail,**summarize(logweights)}}
        write_new(root/'result.json',result);return result


def replay(config,source,root):
    import torch
    from nemo_rl.distributed.batched_data_dict import BatchedDataDict
    from nemo_objective import FilteredClippedPGLossFn
    from importance import guard
    source=Path(source);prior=json.loads((source/'result.json').read_text())
    if digest(source/'batch.pt')!=prior['batch_sha256'] or digest(source/'before/receipt.json')!=prior['before_receipt_sha256']:
        raise ValueError('replay source changed')
    data=BatchedDataDict(torch.load(source/'batch.pt',map_location='cpu',weights_only=True));guard(data)
    with policy_session(config,checkpoint=str(source/'before')) as (policy,_):
        from worker_hooks import install_on_policy
        install_on_policy(policy);policy.prepare_for_training()
        # Restore RNG last, after preparation, to match the saved pre-step state.
        restore(policy,source/'before');check(config)
        metrics=policy.train(data,FilteredClippedPGLossFn(),gbs=256,mbs=1)
        return {'loss':scalar(metrics['loss']),'replay_binding':prior['replay_binding'],'diagnostic_replay_steps':1}


def probabilities(config,rows):
    import torch
    from nemo_rl.distributed.batched_data_dict import BatchedDataDict
    positions=[]
    with policy_session(config,checkpoint=config.get('checkpoint'),init_optimizer=bool(config.get('checkpoint'))) as (policy,_):
        for i,row in enumerate(rows):
            tokens=row['prompt_token_ids']+row['output_token_ids'];n=len(row['prompt_token_ids'])
            data=BatchedDataDict({'input_ids':torch.tensor([tokens]),'input_lengths':torch.tensor([len(tokens)]),
                'token_mask':torch.tensor([[0.]*n+[1.]*(len(tokens)-n)]),'sample_mask':torch.ones(1)})
            frozen=freeze(policy,data,allow_outside=config.get('support_only',False))
            for j,r in enumerate(row['receipt']):
                k=n+j
                positions.append({**r,'response':i,'position':j,'trainer_support':frozen['v4_support_ids'][0,k][frozen['v4_support_mask'][0,k]].tolist(),
                    'trainer_logp':None if config.get('support_only') else float(frozen['prev_logprobs'][0,k]),'discarded_mass':float(frozen['v4_discarded_mass'][0,k])})
    return {'positions':positions}


def length_probe(worker,config):
    from maximum_length_probe import probe
    from admission import check_admission
    return probe(worker,maximum_train_prompt=7753,response_cap=12288,
                 admission_check=lambda:check_admission(config['admission']),lease_check=lambda:check(config))
