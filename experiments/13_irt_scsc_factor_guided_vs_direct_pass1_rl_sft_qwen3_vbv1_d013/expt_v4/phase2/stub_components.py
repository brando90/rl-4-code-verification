"""TLDR: Replace engine primitives with labelled CPU fixtures while exercising real adapter composition."""
import json
from pathlib import Path
from common import digest,object_digest,write_new


def run(config):
    import os
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('stub engines require no GPU')
    stage=config['stage'];p=config['payload'];root=Path(config['stage_root']);root.mkdir(parents=True,exist_ok=True)
    if stage=='generate':
        paths=[];backend=[{'TopKTopPSampler.forward':'forward_native','backend_log_line':'synthetic native backend fixture','synthetic':True}]
        for i,c in enumerate(p['cells']):
            pos={'position':0,'token':151645,'sampled_raw_logprob':0.,'top_k_certified':True,'nucleus_certified':True,
                 'certified':True,'support_size':1,'generator_logp':0.,'reason':'synthetic'}
            if p['full']:pos.update(generator_support=[151645],top_token_ids=[151645]+list(range(63)),top_raw_logprobs=[0.]+[-100.]*63)
            row={**c,'output_token_ids':[151645],'receipt':[pos] if p['receipt'] else [],
                 'completion':'synthetic engine output','finish_reason':'stop','at_token_cap':False,'synthetic':True,'worker_backend':backend}
            target=root/f'{i:05d}.generation.json';write_new(target,row);paths.append(str(target))
        return {'row_paths':paths,'generated_responses':len(paths),'worker_backend':backend,'certified_fraction':1.}
    if stage=='probabilities':
        return {'positions':[{'response':i,'position':0,**r['receipt'][0],'trainer_support':[151645],
                'trainer_logp':0.,'discarded_mass':0.} for i,r in enumerate(p['rows'])]}
    if stage=='score':
        rows=[]
        for r in p['rows']:
            success=int(r['sample']==0) if r['update']==0 else int(r['group_index']< (4 if r['update']>=50 else 1))
            rows.append({**r,'strict':success,'factored_reward':r['sample']%8/7,
                         'sample_idx':r['sample'],'status':'measured','wall_seconds':.01})
        return {'rows':rows,'declared':len(rows),'measured':len(rows)}
    if stage=='update':
        from gates import REPLAY_KEYS,replay_binding
        rows=[r for g in p['groups'] for r in g]
        n=sum(len(r['receipt']) for r in rows);u=sum(not t['certified'] for r in rows for t in r['receipt'])
        if u*100>n:return {'status':'STOP_V4_A4','importance':{'uncertified_generated_fraction':u/n},'optimizer_steps':0}
        for name in ('before','after'):
            write_new(root/name/'receipt.json',{'synthetic':True,'symbolic':name})
        binding=replay_binding(**{k:object_digest([k,p]) for k in REPLAY_KEYS})
        result={'before_weights':object_digest('before'),'after_weights':object_digest('after'),
            'preclip_gradient_norm':.5,'loss':.125,'replay_binding':binding,'source_update':str(root),
            'checkpoint':str(root/'after'),'optimizer_steps':0,'training_seconds':.1,
            'importance':{'certified_fraction':1.,'uncertified_generated_fraction':0.,'uncertified_actor_fraction':0.,
                          'perturbation_bound':0.,'actor_logweight_certified_only':{'p01':0.,'median':0.,'p99':0.,'clamp_rate':0.}}}
        write_new(root/'result.json',result);return result
    if stage=='export':
        write_new(root/'model/export_receipt.json',{'synthetic':True,'checkpoint':p['checkpoint']})
        return {'model':str(root/'model')}
    if stage=='replay':
        old=json.loads((Path(p['source_update'])/'result.json').read_text())
        return {'loss':old['loss'],'replay_binding':old['replay_binding']}
    if stage=='maximum_length':
        return {'peak_memory_bytes':1000,'probe_sequence_length':20041,'maximum_train_prompt':7753,'probe_forward_backward':True}
    if stage=='audit_score':
        return {'status':'PASS','hidden_coverage_controls':True,'mutations':dict.fromkeys(['padding','deletion','substitution'],32),
                'reward_increasing_mutations':[],'baseline':{'reward':.5,'theorem_count':2.,'coverage':.8}}
    raise ValueError('unknown stub component')
