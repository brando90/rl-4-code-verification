"""Bind the matched trainer to original base weights and the frozen V25 proof-version corpus."""
import importlib.util
import json
import sys
from pathlib import Path
import assemble as config

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

def main():
    receipt=json.loads((config.ROOT/'base/data/prepare_receipt.json').read_text())
    assert receipt['initial_model']=='Qwen/Qwen3-1.7B-Base'
    assert receipt['fresh_optimizer'] and not receipt['sft_weights_reused']
    assert receipt['rows']==3568 and receipt['steps']==1784
    for name,expected in receipt['v25_source_sha256'].items():
        assert config.digest(config.HERE/name)==expected,name
    assert config.START.name=='ea980cb0a6c2ae4b936e82123acc929f1cec04c1'
    frozen=load('assemble',config.FROZEN/'assemble.py')
    frozen.ROOT=config.ROOT;frozen.START=config.START;frozen.HERE=config.FROZEN;frozen.REPO=config.REPO
    trainer=load('v25_matched_training_loop',config.HERE/'train.py')
    trainer.main()

if __name__=='__main__':
    main()
