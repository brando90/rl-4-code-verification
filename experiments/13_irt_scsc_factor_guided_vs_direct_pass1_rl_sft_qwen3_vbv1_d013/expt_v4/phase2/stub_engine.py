"""TLDR: Produce labelled tiny synthetic engine evidence without models, CUDA, or optimizer calls."""
from types import SimpleNamespace
import os
import torch
from common import object_digest, write_new
from filtered_policy import support, filtered_logprobs
from generation_contract import extract_raw
from gates import REPLAY_KEYS, replay_binding


class StubEngine:
    synthetic=True
    def __init__(self, *, no_signal=False, crash=None, improve_at=50):
        if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('stub requires CUDA_VISIBLE_DEVICES empty')
        self.no_signal=no_signal;self.crash=crash;self.improve_at=improve_at
        logits=torch.linspace(-10,10,100)
        values,ids=logits.log_softmax(-1).topk(64)
        self.output=SimpleNamespace(token_ids=[99],logprobs=[{int(i):SimpleNamespace(logprob=float(v)) for i,v in zip(ids,values)}])
        self.logits=logits

    def measure(self, op, path, payload):
        if self.crash==op:
            self.crash=None
            write_new(path/'infrastructure_failure.json',{'generated_responses':0,'optimizer_started':False,'statistics_started':False})
            raise RuntimeError('simulated infrastructure crash before generation')
        if op in ('generate','probe','refit'):
            full=payload.get('full',True);n=payload.get('responses',8)
            rows=[]
            for i in range(n):
                receipt=extract_raw(self.output,vocab_size=100,full=full)
                row={'cell':i,'output_token_ids':[99],'receipt':receipt,'synthetic':True}
                rows.append(row)
            write_new(path/'generations.json',rows)
            if op=='generate':return {'rows':rows,'generated_responses':n,'certified_fraction':1.}
            mask=support(self.logits);lp,mass=filtered_logprobs(self.logits,mask,torch.tensor(99))
            positions=[{'response':i,'position':0,**rows[i]['receipt'][0],
                        'trainer_support':mask.nonzero().flatten().tolist(),'trainer_logp':float(lp),
                        'discarded_mass':float(mass)} for i in range(n)]
            return {'positions':positions,'old_supports':[p['trainer_support'] for p in positions],
                    'receipt_on_off_identical':True,'generated_responses':n,'rows':rows}
        if op=='score':
            rows=[{'task_id':t,'sample_idx':s,'split':'train','strict':0 if self.no_signal else int(s==0),
                   'factored_reward':0. if self.no_signal else (s%8)/7} for t in payload['tasks'] for s in range(32)]
            return {'rows':rows,'declared':1024,'measured':1024}
        if op=='update':
            # Symbolic weights and metrics only: no nn.Module or optimizer exists.
            binding=replay_binding(**{k:object_digest([k,payload]) for k in REPLAY_KEYS})
            return {'preclip_gradient_norm':.5,'before_weights':object_digest('before'),
                    'after_weights':object_digest(['after',payload]),'loss':.125,'replay_binding':binding,
                    'optimizer_steps':0,'synthetic_transition':True}
        if op=='replay':return {'loss':payload['loss'],'replay_binding':payload['replay_binding']}
        if op=='maximum_length':
            return {'device_seconds':1.,'updates':1,'peak_memory_bytes':1000,'probe_sequence_length':20041,
                    'maximum_train_prompt':7753,'probe_forward_backward':True,'generated_tokens':256,
                    'generation_seconds':1.,'lean_wall_seconds':1.,'timeout_count':0,'scoring_slots':256,
                    'storage_growth_bytes':1000,'synthetic':True}
        if op=='audits':
            return {'status':'PASS','mutations':{'padding':0,'deletion':0,'substitution':0},
                    'reward_increasing_mutations':[], 'hidden_coverage_controls':True,
                    'baseline':{'reward':.5,'theorem_count':2.,'coverage':.8},'synthetic':True}
        if op=='pilot_update':
            small=extract_raw(self.output,vocab_size=100,full=False)
            strict=[int(i < (32 if payload['update']>=self.improve_at else 8)) for i in range(256)]
            g=payload['G'];rewards=(payload['placebo'] if payload['arm']=='P' else
                strict if payload['arm']=='A' else [i%8/7 for i in range(256)])
            from placebo import density
            return {'arm':payload['arm'],'seed':payload['seed'],'update':payload['update'],
                    'completed':True,'strict':strict,'generated_tokens':[1]*256,'receipt':small,
                    'certified_fraction':1.,'density':density([rewards[i:i+g] for i in range(0,256,g)]),
                    'audit':{'reward':.5,'theorem_count':2.,'coverage':.8},
                    'optimizer_steps':0,'synthetic_transition':True}
        raise ValueError('unknown stub operation: '+op)
