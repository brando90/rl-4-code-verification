"""Bind the unchanged V12 training loop to the final cohort on its original SNAP runtime."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
REPO=RUN/'repo'
EXP=Path('experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test')
HERE=REPO/EXP/'expt_v19'
FROZEN=REPO/EXP/'expt_v12'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--condition',default='final');parser.add_argument('--smoke',action='store_true');args=parser.parse_args();assert args.condition=='final'
    asm=load('assemble',FROZEN/'assemble.py');asm.ROOT=RUN/'corpus_training_v19/conditions';asm.START=RUN/'onep7/runs/mixed/hf';asm.HERE=FROZEN
    receipt=json.loads((asm.ROOT/'final/data/prepare_receipt.json').read_text());assert receipt['preparation_code_sha256']==asm.digest(HERE/'assemble_final_data.py')
    decision=json.loads((RUN/'corpus_training_v19/production_host.json').read_text());assert decision['state']=='FROZEN' and decision['host']=='SNAP'
    assert receipt['v18_completion_sha256']==decision['v18_completion_sha256']
    train=load('v19_pinned_training_loop',FROZEN/'train.py');sys.argv=[str(FROZEN/'train.py'),'--condition','final']+(['--smoke'] if args.smoke else []);train.main()
if __name__=='__main__':main()
