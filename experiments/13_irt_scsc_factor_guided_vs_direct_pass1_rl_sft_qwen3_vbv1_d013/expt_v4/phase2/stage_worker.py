"""TLDR: Dispatch one leased v4 component; CPU stub engines are explicit and never measured evidence."""
import argparse
import json
import os
from pathlib import Path
from common import write_new,digest


def run(config,stub=False):
    from admission import check_admission
    from device_guard import check
    check_admission(config['admission'],require_launch=not stub)
    check(config)
    if os.environ.get('VLLM_USE_FLASHINFER_SAMPLER')!='0':raise ValueError('native sampler environment required')
    if stub:
        from stub_components import run as simulated
        return simulated(config)
    import importlib.metadata
    for package,version in config['runtime_versions'].items():
        if importlib.metadata.version(package)!=version:raise ValueError('runtime changed: '+package)
    stage=config['stage'];p=config['payload'];root=Path(config['stage_root'])
    if stage=='generate':
        from generation_runtime import generate
        c={**config,'model':p['model']}
        result=generate(c,p['cells'],root=root,full=p['full'],receipt=p['receipt'])
        return {**result,'row_paths':[str(x) for x in sorted(root.glob('*.generation.json'))],
                'worker_backend':json.loads((root/'worker_backend.json').read_text())}
    if stage=='score':
        from scoring_runtime import score
        return score(config,p['rows'],root/'cells')
    if stage=='audit_score':
        from audit_runtime import audits
        return audits(config,p['rows'],root/'audit')
    if stage=='update':
        from trainer_runtime import execute_update
        from importance import UncertifiedStop
        try:return execute_update({**config,'checkpoint':p.get('checkpoint'),'run_seed':p.get('run_seed',config['run_seed'])},p['groups'],p['advantages'],root)
        except UncertifiedStop as exc:return {'status':'STOP_V4_A4','importance':exc.report,'optimizer_steps':0,'resample':False}
    if stage=='probabilities':
        from trainer_runtime import probabilities
        return probabilities({**config,'checkpoint':p.get('checkpoint'),'support_only':p.get('support_only',False)},p['rows'])
    if stage=='replay':
        from trainer_runtime import replay
        return replay(config,p['source_update'],root)
    if stage=='export':
        import legacy
        from training_checkpoint import export
        export(p['checkpoint'],root/'model',model_config=config['initial_model'],tokenizer=config['tokenizer'])
        return {'model':str(root/'model'),'native_checkpoint':p['checkpoint']}
    if stage=='maximum_length':
        from trainer_runtime import policy_session,length_probe,owned_call
        with policy_session(config,init_optimizer=False) as (policy,_):
            result=owned_call(policy,length_probe,config)
        if len(result)!=1:raise ValueError('one rank required')
        r=result[0];r.pop('optimizer_steps');r.pop('wall_seconds');r['maximum_train_prompt']=7753
        return r
    raise ValueError('unknown component')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--stub-engines',action='store_true')
    a=p.parse_args();config=json.loads(a.config.read_text())
    if config['synthetic']!=a.stub_engines:raise ValueError('mode mismatch')
    r=run(config,a.stub_engines);r['synthetic']=a.stub_engines
    path=Path(config['stage_root'])/'result.json'
    # Primitives may already have written their domain result; the component
    # envelope is separate and is always what the parent consumes.
    write_new(path.with_name('component_result.json'),r)
