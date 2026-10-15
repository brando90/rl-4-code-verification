"""Capture and restore actual owned NeMo worker RNG state and hash tensor values for technical replay gates."""
from __future__ import annotations


def parameter_digest(worker):
    """Called on every owned worker through installed Ray's __ray_call__, never on a foreign actor."""
    import hashlib,json,torch
    digest=hashlib.sha256();parameters=0;elements=0
    for name,value in sorted(worker.model.state_dict().items()):
        if hasattr(value,'full_tensor'):value=value.full_tensor()
        tensor=value.detach().cpu().contiguous()
        digest.update(json.dumps([name,str(tensor.dtype),list(tensor.shape)],separators=(',',':')).encode())
        digest.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
        parameters+=1;elements+=tensor.numel()
    return {'sha256':digest.hexdigest(),'state_tensors':parameters,'elements':elements}


def save_rng(worker,path):
    """Save Python, NumPy, Torch host and all visible leased-device generators before the update."""
    import os,random
    from pathlib import Path
    import numpy as np
    import torch
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    state={'python':random.getstate(),'numpy':np.random.get_state(),'torch':torch.get_rng_state(),
           'cuda':torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []}
    with path.open('xb') as out:torch.save(state,out);out.flush();os.fsync(out.fileno())
    import hashlib
    return {'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cuda_generators':len(state['cuda'])}


def restore_rng(worker,path):
    """Load only this run's hash-bound trusted checkpoint; restore every recorded generator."""
    import random,numpy as np,torch
    state=torch.load(path,map_location='cpu',weights_only=False)
    random.setstate(state['python']);np.random.set_state(state['numpy']);torch.set_rng_state(state['torch'])
    if state['cuda']:
        if len(state['cuda'])!=torch.cuda.device_count():raise ValueError('replay device topology changed')
        torch.cuda.set_rng_state_all(state['cuda'])
    return {'restored':True,'cuda_generators':len(state['cuda'])}


def optimizer_digest(worker):
    """Verify optimizer and scheduler restoration separately from weight or loss agreement."""
    import hashlib,json,torch
    digest=hashlib.sha256()
    def update(value):
        if hasattr(value,'full_tensor'):value=value.full_tensor()
        if torch.is_tensor(value):
            tensor=value.detach().cpu().contiguous()
            digest.update(json.dumps(['tensor',str(tensor.dtype),list(tensor.shape)]).encode())
            digest.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
        elif isinstance(value,dict):
            digest.update(b'dict')
            for key in sorted(value,key=lambda k:(type(k).__name__,str(k))):update(key);update(value[key])
        elif isinstance(value,(list,tuple)):
            digest.update(type(value).__name__.encode());digest.update(str(len(value)).encode())
            for item in value:update(item)
        elif value is None or isinstance(value,(str,bool,int,float)):
            digest.update(json.dumps([type(value).__name__,value],allow_nan=False).encode())
        else:raise ValueError('unsupported checkpoint state type: '+type(value).__name__)
    update({'optimizer':worker.optimizer.state_dict(),'scheduler':worker.scheduler.state_dict()})
    return {'sha256':digest.hexdigest(),'optimizer_type':type(worker.optimizer).__name__,
            'scheduler_type':type(worker.scheduler).__name__}
