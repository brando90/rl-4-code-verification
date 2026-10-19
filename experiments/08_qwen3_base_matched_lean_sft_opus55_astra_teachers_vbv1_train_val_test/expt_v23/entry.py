"""Bind the unchanged frozen training loop to original base weights and the strict V23 corpus."""
import importlib.util,json,sys
from pathlib import Path
import assemble as config

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def main():
 receipt=json.loads((config.ROOT/'base/data/prepare_receipt.json').read_text());assert receipt['initial_model']=='Qwen/Qwen3-1.7B-Base' and receipt['fresh_optimizer'] and not receipt['sft_weights_reused']
 for name,sha in receipt['v23_source_sha256'].items():assert config.digest(config.HERE/name)==sha,name
 assert config.START.name=='ea980cb0a6c2ae4b936e82123acc929f1cec04c1'
 old=load('assemble',config.FROZEN/'assemble.py');old.ROOT=config.ROOT;old.START=config.START;old.HERE=config.FROZEN;old.REPO=config.REPO
 trainer=load('v23_original_training_loop',config.FROZEN/'train.py');trainer.main()
if __name__=='__main__':main()
