"""Observe disposable layout updates without changing training arithmetic."""
import os
if os.environ.get('E08_LAYOUT_PROBE'):
    import json, time, pathlib, resource, hashlib
    import torch
    from torch.distributed.tensor import DTensor
    OUT = pathlib.Path(os.environ['E08_LAYOUT_PROBE'])
    OUT.mkdir(parents=True, exist_ok=True)
    count = 0
    names = {}
    def local(t):
        return t.to_local() if isinstance(t, DTensor) else t
    def emit(event, **fields):
        row = dict(event=event, time=time.time(), pid=os.getpid(), rank=torch.distributed.get_rank() if torch.distributed.is_initialized() else None, **fields)
        with (OUT / f'worker_{os.getpid()}.jsonl').open('a') as f:
            f.write(json.dumps(row, allow_nan=False)+'\n')
    emit('python_start', torch=torch.__version__, threads=torch.get_num_threads())
    old_backward = torch.autograd.backward
    def backward(*args, **kwargs):
        global count
        start=time.monotonic()
        ret=old_backward(*args, **kwargs)
        count+=1
        emit('backward', number=count, seconds=time.monotonic()-start)
        return ret
    torch.autograd.backward=backward
    def forward_hook(module, args, kwargs):
        if 'ForCausalLM' not in type(module).__name__:
            return
        for n,p in module.named_parameters():
            names[id(p)]=n
        ids=kwargs.get('input_ids', args[0] if args else None)
        emit('forward', shape=list(ids.shape) if ids is not None else None, autocast_dtype=str(torch.get_autocast_dtype('cuda')), autocast=torch.is_autocast_enabled('cuda'))
    old_call = torch.nn.Module._call_impl
    def call(self, *args, **kwargs):
        if 'ForCausalLM' in type(self).__name__: forward_hook(self, args, kwargs)
        return old_call(self, *args, **kwargs)
    torch.nn.Module._call_impl = call
    orig_step=torch.optim.AdamW.step
    def step(self, *args, **kwargs):
        start=time.monotonic(); probes=[]; states={}; placement=[]
        for group in self.param_groups:
            for p in group['params']:
                if p.grad is None: continue
                lp=local(p).detach(); lg=local(p.grad).detach(); name=names.get(id(p),'unknown')
                states[str((str(lp.device),str(lp.dtype),str(lg.device),str(lg.dtype)))]=states.get(str((str(lp.device),str(lp.dtype),str(lg.device),str(lg.dtype))),0)+1
                if 'q_norm' in name or 'k_norm' in name:
                    placement.append({'name':name,'mesh_names':list(p.device_mesh.mesh_dim_names) if isinstance(p,DTensor) else None,'placements':str(p.placements) if isinstance(p,DTensor) else None,'grad_norm':lg.norm().item(),'grad_sha256':hashlib.sha256(lg.cpu().numpy().tobytes()).hexdigest()})
                if len(probes)<2:
                    q=torch.nn.Parameter(lp.flatten()[:2048].to('cuda').clone());q.grad=lg.flatten()[:2048].to('cuda').clone()
                    kw={k:group[k] for k in ['lr','betas','eps','weight_decay','foreach','fused','amsgrad','maximize','capturable','differentiable'] if k in group}
                    opt=torch.optim.AdamW([q],**kw)
                    if p in self.state:
                        for k,v in self.state[p].items():
                            opt.state[q][k]=local(v).detach().flatten()[:2048].to('cuda').clone() if torch.is_tensor(v) and v.numel()>1 else v.clone() if torch.is_tensor(v) else v
                    orig_step(opt)
                    probes.append((p,q,name))
        emit('before_optimizer', backward_count=count,states=states,qk_norms=placement,lr=self.param_groups[0]['lr'],threads=torch.get_num_threads(),peak_cuda_allocated=torch.cuda.max_memory_allocated(),peak_cuda_reserved=torch.cuda.max_memory_reserved(),max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        ret=orig_step(self,*args,**kwargs)
        comparisons=[]
        for p,q,name in probes:
            actual=local(p).detach().flatten()[:2048].cpu();expected=q.detach().cpu()
            comparisons.append({'name':name,'max_abs_error':(actual-expected).abs().max().item(),'pass':torch.allclose(actual,expected,rtol=1e-5,atol=1e-7)})
        moment_states=sorted(set((str(local(v).device),str(local(v).dtype)) for st in self.state.values() for k,v in st.items() if torch.is_tensor(v) and k in ('exp_avg','exp_avg_sq')))
        emit('after_optimizer',seconds=time.monotonic()-start,moments=moment_states,comparisons=comparisons,peak_cuda_allocated=torch.cuda.max_memory_allocated(),peak_cuda_reserved=torch.cuda.max_memory_reserved(),max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return ret
    torch.optim.AdamW.step=step
