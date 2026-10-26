"""TLDR: Scale v4 worker logits once in float32 before NeMo invokes the filtered loss."""
from types import MethodType
from filtered_policy import TEMPERATURE


def scale_logits(worker,logits):
    """Replace NeMo's in-place low-precision division with vLLM-order float32 division."""
    if worker.cfg['generation']['temperature']!=TEMPERATURE:
        raise ValueError('v4 worker temperature changed')
    return logits.float()/TEMPERATURE


def install(worker):
    if worker.cfg['generation']['temperature']!=TEMPERATURE:
        raise ValueError('v4 worker temperature changed')
    worker._apply_temperature_scaling=MethodType(scale_logits,worker)
    return {'v4_temperature_hook':True,'temperature':TEMPERATURE,'division_dtype':'float32'}


def install_on_policy(policy):
    """Install only on this Policy's owned Ray workers, never a shared/existing cluster."""
    import ray
    workers=policy.worker_group.workers
    if not workers:raise ValueError('v4 policy has no owned workers')
    receipts=ray.get([worker.__ray_call__.remote(install) for worker in workers])
    if not all(r.get('v4_temperature_hook') is True for r in receipts):
        raise ValueError('v4 worker hook not installed')
    return receipts
