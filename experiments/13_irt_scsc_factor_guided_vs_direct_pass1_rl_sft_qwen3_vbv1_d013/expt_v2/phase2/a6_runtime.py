"""Execute the one source-bound A6 diagnostic generation attempt on its claimed device."""
import argparse,importlib.metadata,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'phase1'))
from panel import digest
from runtime import check_lease,numerical_dtype
from a6_generation import generate
from a6_contract import validate_manifest


def verify(config):
    table={b['path']:b['sha256']for b in config['bindings']}
    if len(table)!=len(config['bindings']):raise ValueError('duplicate diagnostic binding')
    for path,sha in table.items():
        if digest(path)!=sha:raise ValueError('changed diagnostic runtime binding: '+path)
    required=[Path(__file__).resolve(),HERE/'a6_generation.py',HERE/'a6_contract.py',HERE/'evaluation_contract.py',
        HERE.parent/'phase1/runtime.py',HERE.parent/'phase1/device_binding.py',Path(config['manifest']),Path(config['allowlist']),Path(config['policy_config'])]
    for key in ('model','tokenizer'):
        files=[p for p in Path(config[key]).iterdir()if p.is_file()]
        if not any(p.suffix=='.safetensors'for p in files):raise ValueError('frozen weights absent')
        required+=files
    if any(table.get(str(p))!=digest(p)for p in required):raise ValueError('missing diagnostic dependency')
    for name,version in config['runtime_versions'].items():
        if importlib.metadata.version(name)!=version:raise ValueError('diagnostic package version changed: '+name)
    if numerical_dtype(config)!='float16' or config['max_model_len']!=32768 or config['batch_size']!=32:raise ValueError('diagnostic runtime changed')
    manifest=json.loads(Path(config['manifest']).read_text());validate_manifest(manifest,Path(config['allowlist']).read_text().splitlines())
    lease=json.loads(Path(config['lease_path']).read_text())
    if lease['phase']!='v2-S2-A6-diagnostic' or lease['id']!=config['lease_id']:raise ValueError('not the A6 device claim')
    check_lease(config);return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);a=p.parse_args()
    config=json.loads(a.config.read_text());manifest=verify(config)
    print(json.dumps(generate(config,manifest,list(range(512)),root=config['generation_root'])))
