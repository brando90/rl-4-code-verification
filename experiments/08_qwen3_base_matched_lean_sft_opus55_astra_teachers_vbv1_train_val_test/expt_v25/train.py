"""Train the matched proof-version condition with exact V20 batches and learning rates from original base weights."""
from __future__ import annotations
import argparse
import csv
import json
import math
import os
from pathlib import Path
import socket
import time
from assemble import ROOT,START,HERE,SEED,digest,write

def load_matched_reference(tokens, batches, receipt):
    """Verify fixed identities/prompts/batches and recover the exact measured V20 learning-rate clock."""
    reference = ROOT.parent / 'corpus_training_v20' / 'base'
    declared = receipt['matched_reference']
    files = {'training_sha256': reference/'data/training.jsonl',
             'tokens_sha256': reference/'data/tokens.pt',
             'schedule_sha256': reference/'data/schedule.json',
             'steps_sha256': reference/'run/steps.csv'}
    for key, path in files.items():
        assert digest(path) == declared[key], ('Reference hash mismatch', key)
    import torch
    prior_tokens = torch.load(files['tokens_sha256'], weights_only=True)
    prior_rows = [json.loads(line) for line in files['training_sha256'].read_text().splitlines()]
    prior_batches = json.loads(files['schedule_sha256'].read_text())
    assert len(tokens) == len(prior_tokens) == len(prior_rows) == receipt['rows'] == 3568
    assert len(batches) == len(prior_batches) == receipt['steps'] == 1784
    assert [t['uid'] for t in tokens] == [t['uid'] for t in prior_tokens] == [r['uid'] for r in prior_rows]
    for current, old in zip(tokens, prior_tokens):
        assert current['pool'] == old['pool']
        assert current['prompt'] == old['prompt']
        assert current['ids'][:current['prompt']] == old['ids'][:old['prompt']], current['uid']
    assert [b['indices'] for b in batches] == [b['indices'] for b in prior_batches]
    steps = list(csv.DictReader(files['steps_sha256'].open()))
    assert [int(row['step']) for row in steps] == list(range(1,1785))
    rates = [float(row['learning_rate']) for row in steps]
    assert all(math.isfinite(rate) and 0 <= rate <= 2e-5 for rate in rates)
    return rates, dict(reference_run='v20_base', exact_example_order=True,
                       exact_prompt_tokens=True, exact_batch_indices=True,
                       exact_learning_rates=True, rows=3568, steps=1784,
                       reference_hashes=declared)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--condition',default='current');parser.add_argument('--smoke',action='store_true');args=parser.parse_args()
    import torch
    import transformers
    from transformers import AutoModelForCausalLM,AutoTokenizer
    assert os.environ.get('CUDA_VISIBLE_DEVICES') and torch.cuda.device_count()==1
    data=ROOT/args.condition/'data';receipt=json.loads((data/'prepare_receipt.json').read_text());assert receipt['status']=='PASS'
    assert receipt['tokens_sha256']==digest(data/'tokens.pt') and receipt['schedule_sha256']==digest(data/'schedule.json')
    for n,h in receipt['source_sha256'].items():assert digest(HERE/n)==h,n
    initial=json.loads((data/'initial_manifest.json').read_text())
    for name,h in initial.items():assert digest(START/name)==h,name
    tokens=torch.load(data/'tokens.pt',weights_only=True);batches=json.loads((data/'schedule.json').read_text())
    reference_lrs, matched = load_matched_reference(tokens, batches, receipt)
    out=ROOT/args.condition/('smoke' if args.smoke else 'run');out.mkdir(parents=True,exist_ok=True)
    assert not (out/'steps.csv').exists(),'Preserve existing trajectory; explicit recovery required'
    torch.set_num_threads(4);torch.manual_seed(SEED);torch.cuda.manual_seed_all(SEED);torch.backends.cuda.matmul.allow_tf32=False
    model=AutoModelForCausalLM.from_pretrained(START,local_files_only=True,torch_dtype=torch.float32,attn_implementation='sdpa').cuda()
    model.config.use_cache=False;model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});model.train()
    def lr(consumed):
        p=min(consumed/receipt['loss_tokens'],1.0)
        return 2e-5*(0.05+0.95*p/0.03) if p<0.03 else 1e-5*(1+math.cos(math.pi*(p-0.03)/0.97))
    optimizer=torch.optim.AdamW(model.parameters(),lr=lr(0),betas=(0.9,0.98),eps=1e-5,weight_decay=0.1,foreach=False,fused=False)
    identity=dict(condition=args.condition,host=socket.gethostname(),pid=os.getpid(),gpu=torch.cuda.get_device_name(),cuda_visible_devices=os.environ['CUDA_VISIBLE_DEVICES'],torch=torch.__version__,transformers=transformers.__version__,seed=SEED,initial=str(START),initial_manifest_sha256=receipt['initial_manifest_sha256'],training_sha256=receipt['training_sha256'],source_sha256=receipt['source_sha256'],planned_rows=receipt['rows'],planned_loss_tokens=receipt['loss_tokens'],planned_steps=receipt['steps'],smoke=args.smoke,parameter_dtype='float32',autocast_dtype='bfloat16',attention='sdpa',optimizer='fresh AdamW CUDA float32',test_split_opened=False)
    identity.update(matched_reference=matched,matched_trainer_sha256=digest(Path(__file__)),learning_rate_clock='exact measured V20 rate per optimizer update')
    write(out/'matched_reference.json',matched)
    write(out/'identity.json',identity)
    if args.smoke:
        longest=max(range(len(tokens)),key=lambda i:len(tokens[i]['ids']));short=min(range(len(tokens)),key=lambda i:len(tokens[i]['ids']))
        batches=[dict(indices=[longest,short])]
    started=time.monotonic();consumed=0
    fields=['step','loss_tokens','train_loss','grad_norm','learning_rate','elapsed_seconds','peak_gpu_gib','rows_consumed','pool_counts']
    counts={};rows_consumed=0
    with (out/'steps.csv').open('x',buffering=1) as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for step,batch in enumerate(batches,1):
            actual=[tokens[i] for i in batch['indices']];denominator=sum(r['loss_tokens'] for r in actual)
            for group in optimizer.param_groups:group['lr']=reference_lrs[step-1]
            optimizer.zero_grad(set_to_none=True);total=0.0
            for row in actual:
                ids=torch.tensor([row['ids']],dtype=torch.long,device='cuda');labels=ids.clone();labels[:,:row['prompt']]=-100
                assert int((labels!=-100).sum())==row['loss_tokens']
                with torch.autocast('cuda',dtype=torch.bfloat16):loss=model(input_ids=ids,labels=labels).loss
                assert bool(torch.isfinite(loss)),'nonfinite loss'
                weight=row['loss_tokens']/denominator;(loss*weight).backward();total+=float(loss.detach())*weight
                counts[row['pool']]=counts.get(row['pool'],0)+1;rows_consumed+=1;del loss,ids,labels
            grad=torch.nn.utils.clip_grad_norm_(model.parameters(),1.0,error_if_nonfinite=True);assert float(grad)>0
            optimizer.step();consumed+=denominator
            if not args.smoke:assert consumed==batch['cumulative_loss_tokens']
            metrics=dict(step=step,loss_tokens=consumed,train_loss=total,grad_norm=float(grad),learning_rate=optimizer.param_groups[0]['lr'],elapsed_seconds=time.monotonic()-started,peak_gpu_gib=torch.cuda.max_memory_allocated()/2**30,rows_consumed=rows_consumed,pool_counts=json.dumps(counts,sort_keys=True))
            writer.writerow(metrics);write(out/'progress.json',dict(metrics,status='RUNNING',observed_unix=time.time()));print(json.dumps(metrics),flush=True)
            if step==1:write(out/'first_update.json',dict(identity,**metrics,completed_unix=time.time(),status='PASS'))
            if not args.smoke and (step%500==0 or step==len(batches)):
                tmp=out/'training_state.tmp.pt';torch.save(dict(step=step,consumed=consumed,model=model.state_dict(),optimizer=optimizer.state_dict(),identity=identity,cpu_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all()),tmp);tmp.replace(out/'training_state.pt')
    if not args.smoke:
        assert consumed==receipt['loss_tokens'] and rows_consumed==receipt['rows']
        model.save_pretrained(out/'hf',safe_serialization=True);AutoTokenizer.from_pretrained(START,local_files_only=True).save_pretrained(out/'hf');model.generation_config.save_pretrained(out/'hf')
        manifest={p.name:digest(p) for p in sorted((out/'hf').iterdir()) if p.is_file()};write(out/'weights_manifest.json',manifest)
        (out/'hf/SHA256SUMS').write_text(''.join(f'{h}  {n}\n' for n,h in manifest.items()))
    write(out/'result.json',dict(identity,**metrics,status='COMPLETE',ended_unix=time.time()))

if __name__=='__main__':main()
