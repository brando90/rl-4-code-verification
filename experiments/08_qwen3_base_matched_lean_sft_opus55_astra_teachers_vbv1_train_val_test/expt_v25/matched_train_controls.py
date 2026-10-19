"""Check matching against real V20 data and reject shuffled examples, prompts, batches and reference hashes without a GPU."""
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import types

os.environ['CUDA_VISIBLE_DEVICES']=''
RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
HERE=Path(__file__).resolve().parent
ref=RUN/'corpus_training_v20/base'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')
config=types.ModuleType('assemble')
for k,v in dict(ROOT=RUN/'corpus_training_v25',START=Path('/unused_control_no_model_load'),HERE=HERE,SEED=20261019,digest=digest,write=write).items():setattr(config,k,v)
sys.modules['assemble']=config
spec=importlib.util.spec_from_file_location('matched_trainer_control',HERE/'train.py');trainer=importlib.util.module_from_spec(spec);spec.loader.exec_module(trainer)
import torch
tokens=torch.load(ref/'data/tokens.pt',weights_only=True);batches=json.loads((ref/'data/schedule.json').read_text())
matched={k:digest(path) for k,path in {'training_sha256':ref/'data/training.jsonl','tokens_sha256':ref/'data/tokens.pt','schedule_sha256':ref/'data/schedule.json','steps_sha256':ref/'run/steps.csv'}.items()}
receipt=dict(rows=3568,steps=1784,matched_reference=matched)
rates,meta=trainer.load_matched_reference(tokens,batches,receipt)
assert rates==[float(row['learning_rate']) for row in csv.DictReader((ref/'run/steps.csv').open())]
checks={'real_reference3568_rows1784_updates':True,'exact1784_recorded_learning_rates':True}
def reject(name,ts,bs,rc):
    try:trainer.load_matched_reference(ts,bs,rc)
    except AssertionError:checks[name]=True
    else:raise AssertionError('Accepted mismatched control:'+name)
changed=list(tokens);changed[0]=dict(tokens[0],uid='WRONG_CONTROL_ID');reject('reject_wrong_example_identity',changed,batches,receipt)
changed=list(tokens);first=dict(tokens[0]);first['ids']=list(first['ids']);first['ids'][0]+=1;changed[0]=first;reject('reject_changed_prompt_token',changed,batches,receipt)
changed=list(batches);changed[0]=dict(changed[0],indices=list(reversed(changed[0]['indices'])));reject('reject_changed_batch_order',tokens,changed,receipt)
changed=dict(receipt,matched_reference=dict(matched,steps_sha256='0'*64));reject('reject_changed_reference_trajectory',tokens,batches,changed)
output=dict(status='PASS',checks=checks,matched_reference=matched,trainer_sha256=digest(HERE/'train.py'),rows=3568,steps=1784,model_calls=0,gpu_used=False,reference_files_changed=False)
write(RUN/'corpus_training_v25/matched_train_controls.json',output);print(json.dumps(output,indent=2))
