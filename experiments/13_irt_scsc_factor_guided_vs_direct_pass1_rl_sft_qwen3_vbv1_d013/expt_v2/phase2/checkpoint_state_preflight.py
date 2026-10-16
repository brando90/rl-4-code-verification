"""Check actual CPU-offloaded model hashing on the leased one-rank trainer before technical admission."""
from pathlib import Path


def inspect_worker(worker):
    """Inspect only the owned real worker, without a prompt or optimizer update."""
    from worker_state import complete_tensor,parameter_digest,optimizer_digest
    distributed=0;cpu_offloaded=0
    for value in worker.model.state_dict().values():
        if not hasattr(value,'full_tensor'):continue
        distributed+=1
        if value.device_mesh.size()!=1:
            raise ValueError('checkpoint preflight requires frozen one-rank topology')
        local=complete_tensor(value)
        if local.device.type=='cpu':cpu_offloaded+=1
    if distributed==0 or cpu_offloaded==0:
        raise ValueError('checkpoint preflight did not exercise CPU-offloaded DTensors')
    return {'distributed_state_tensors':distributed,'cpu_offloaded_state_tensors':cpu_offloaded,
            'parameters':parameter_digest(worker),'optimizer':optimizer_digest(worker)}


def run(config):
    """Close the owned trainer before the separate non-probe generator health check."""
    from trainer_core import policy_session
    from training_checkpoint import owned_call,write_new
    from runtime import check_lease
    check_lease(config)
    with policy_session(config) as (policy,_):
        policy.prepare_for_training()
        workers=owned_call(policy,inspect_worker)
    result={'condition':'v2-S2','status':'PASS','scope':'non-probe checkpoint infrastructure',
            'workers':workers,'optimizer_updates':0,'generated_responses':0,
            'admission_statistics_computed':False}
    write_new(Path(config['attempt_root'])/'dtensor_state_preflight.json',result)
    return result
