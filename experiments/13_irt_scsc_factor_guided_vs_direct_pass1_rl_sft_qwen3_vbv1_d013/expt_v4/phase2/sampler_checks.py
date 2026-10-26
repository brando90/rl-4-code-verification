"""TLDR: Test installed CPU sampling and reduce the frozen V4-A2 three-run engine criterion."""
import argparse
import importlib.util
import os
from pathlib import Path
from common import digest,write_new


def installed_unit(positions=10000):
    if positions<10000:raise ValueError('at least 10000 positions required')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('CPU only')
    os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    import torch
    from types import SimpleNamespace
    from vllm.v1.sample.sampler import Sampler
    torch.set_num_threads(2)
    sampler=Sampler()
    if sampler.topk_topp_sampler.forward.__name__!='forward_native':raise ValueError('unadmitted sampler')
    x=torch.randn(positions,128,generator=torch.Generator().manual_seed(1304004))
    x[::4]=0 # >64 equal kth ties
    x[1::4,:24]=5 # complete kth ties
    x[2::4]=-100
    x[2::4,:3]=.6*torch.tensor([.03,.03,.94]).log() # nucleus boundary ties
    outputs=[];states=[]
    for count in (None,64):
        generators={i:torch.Generator().manual_seed(1304000+i) for i in range(positions)}
        meta=SimpleNamespace(max_num_logprobs=count,all_random=True,all_greedy=False,
            temperature=torch.full((positions,),.6),top_k=torch.full((positions,),20),
            top_p=torch.full((positions,),.95),generators=generators,no_penalties=True,
            allowed_token_ids_mask=None,bad_words_token_ids={},
            logitsprocs=SimpleNamespace(non_argmax_invariant=[],argmax_invariant=[]))
        outputs.append(sampler.forward(x.clone(),meta).sampled_token_ids)
        states.append([g.get_state() for g in generators.values()])
    mismatches=int((outputs[0]!=outputs[1]).sum())
    return {'status':'PASS' if mismatches==0 else 'FAIL','positions':positions,'mismatched_tokens':mismatches,
        'per_request_rng_identical':all(torch.equal(a,b) for a,b in zip(*states)),
        'ties':['kth complete','kth beyond 64','nucleus split'],
        'sampler_forward':sampler.topk_topp_sampler.forward.__name__,
        'flashinfer_absent':importlib.util.find_spec('flashinfer') is None,
        'installed_sampler_sha256':digest(__import__('inspect').getfile(Sampler)),
        'device':'cpu','model_generations':0,'optimizer_steps':0}


def divergences(a,b):
    if len(a)!=8 or len(b)!=8:raise ValueError('eight responses submitted together required')
    result=[]
    for i,(left,right) in enumerate(zip(a,b)):
        if left!=right:
            first=next((j for j,(x,y) in enumerate(zip(left,right)) if x!=y),min(len(left),len(right)))
            result.append({'response':i,'first_divergence':first})
    return result


def engine_check(r0,r1,r2=None):
    d01=divergences(r0,r1)
    if not d01:return {'status':'PASS','R0_R1':[],'R0_R2':None,'R2_required':False}
    if r2 is None:return {'status':'NEED_R2','R0_R1':d01,'R0_R2':None,'R2_required':True}
    d02=divergences(r0,r2)
    return {'status':'PASS' if d02 and len(d01)<=len(d02)+1 else 'FAIL',
            'R0_R1':d01,'R0_R2':d02,'R2_required':True}


def worker_backend(worker):
    """Read the engine's actual Sampler inside its worker; called via collective_rpc."""
    sampler=worker.model_runner.sampler.topk_topp_sampler
    selected=sampler.forward.__name__
    import vllm.v1.sample.ops.topk_topp_sampler as module
    line=('FlashInfer is not available. Falling back to the PyTorch-native implementation of top-p & top-k sampling.'
          if not module.is_flashinfer_available else 'FlashInfer is available, but it is not enabled. Falling back to the PyTorch-native implementation of top-p & top-k sampling.')
    if selected!='forward_native' or os.environ.get('VLLM_USE_FLASHINFER_SAMPLER')!='0':
        raise ValueError('V4-T1 unimplementable: non-native sampler')
    print(line,flush=True)
    return {'pid':os.getpid(),'TopKTopPSampler.forward':selected,'backend_log_line':line,
            'source_sha256':digest(module.__file__),'VLLM_USE_FLASHINFER_SAMPLER':'0'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=installed_unit();write_new(a.output,r);print(r)
