"""Execute a source-bound retained-checkpoint evaluation segment with the frozen historical sampler."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'phase1'))
from runtime import check_lease,numerical_dtype
from technical_runtime import bound
from evaluation_generation import validate_manifest,generate
from training_checkpoint import write_new

STAGES=('evaluation_preflight','evaluation_generate')


def verify(config,stage):
    if stage not in STAGES or config.get('stage')!=stage or config.get('condition')!='v2-S2':
        raise ValueError('unregistered retained-checkpoint evaluation stage')
    paths=[str(Path(b['path']).resolve()) for b in config['bindings']]
    if not paths or len(paths)!=len(set(paths)):raise ValueError('duplicate or empty evaluation runtime bindings')
    for b in config['bindings']:bound(config,b['path'])
    for name in ('evaluation_runtime.py','evaluation_generation.py','evaluation_contract.py','technical_runtime.py','training_checkpoint.py'):
        bound(config,HERE/name)
    for name in ('runtime.py','device_binding.py'):bound(config,HERE.parent/'phase1'/name)
    for key in ('manifest','allowlist','policy_config'):bound(config,config[key])
    for package,version in config['runtime_versions'].items():
        if importlib.metadata.version(package)!=version:raise ValueError('installed evaluation version changed: '+package)
    if numerical_dtype(config)!='float16' or config['batch_size']!=32 or config['max_model_len']!=32768:
        raise ValueError('frozen evaluation engine contract changed')
    manifest=json.loads(Path(config['manifest']).read_text())
    if manifest['purpose'] not in ('validation','test'):raise ValueError('retained-checkpoint evaluation split required')
    if any(manifest.get(k)!=config[k] for k in ('purpose','arm','run_seed','boundary')):
        raise ValueError('evaluation runtime belongs to another selected checkpoint')
    cells=validate_manifest(manifest,Path(config['allowlist']).read_text().splitlines())
    if stage=='evaluation_generate':
        indexes=config['indexes']
        if (not indexes or len(indexes)>256 or indexes!=sorted(set(indexes))
                or any(type(i) is not int or not 0<=i<len(cells) for i in indexes)):
            raise ValueError('invalid retained-checkpoint evaluation segment')
    for key in ('model','tokenizer'):
        directory=Path(config[key]);files=[p for p in directory.rglob('*') if p.is_file()]
        if not files or (key=='model' and not any(p.suffix in ('.bin','.safetensors') for p in files)):
            raise ValueError('empty frozen evaluation weights or tokenizer')
        for p in files:bound(config,p)
    check_lease(config);return manifest


def run(config,stage):
    manifest=verify(config,stage)
    if stage=='evaluation_preflight':
        import runtime,evaluation_generation
        original=runtime.build_engine
        try:
            runtime.build_engine=lambda c,m:evaluation_generation.build_engine(c)
            runtime.preflight(config)
        finally:runtime.build_engine=original
        return
    result=generate(config,manifest,config['indexes'],root=config['stage_root'])
    receipt={**result,'stage':'EVALUATION_GENERATION','arm':config['arm'],'run_seed':config['run_seed'],
        'boundary':config['boundary'],'snapshot_sha256':config['snapshot_sha256'],
        'model_binding_sha256':config['model_binding_sha256'],'learning_rollout_tokens':0}
    write_new(Path(config['stage_root'])/'evaluation_result.json',receipt);return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',required=True,type=Path)
    p.add_argument('--stage',required=True,choices=STAGES);a=p.parse_args()
    print(json.dumps(run(json.loads(a.config.read_text()),a.stage),sort_keys=True))
