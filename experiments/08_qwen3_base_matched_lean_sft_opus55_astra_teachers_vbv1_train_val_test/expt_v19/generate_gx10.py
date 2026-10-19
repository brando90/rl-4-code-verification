"""Run frozen validation prompts through a GPU Transformers sampler with explicit per-cell random streams."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
import time


class GX10Engine:
    """Reuse frozen prompt/extraction/row assembly while replacing only the inference engine."""

    def __init__(self,args):
        import torch
        import transformers
        from transformers import AutoModelForCausalLM,AutoTokenizer
        from rl4cv.veribench.generate import resolve_stop_token_ids
        assert os.environ.get('CUDA_VISIBLE_DEVICES')=='0' and torch.cuda.device_count()==1
        self.torch=torch;self.args=args
        dtype_name=os.environ.get('GX19_INFERENCE_DTYPE')
        assert dtype_name in ('float16','bfloat16'),'Declare and freeze inference dtype before generation'
        dtype=getattr(torch,dtype_name)
        self.tokenizer=AutoTokenizer.from_pretrained(args.model,revision=args.revision,local_files_only=True)
        self.tokenizer.padding_side='left'
        if self.tokenizer.pad_token_id is None:self.tokenizer.pad_token=self.tokenizer.eos_token
        self.model=AutoModelForCausalLM.from_pretrained(args.model,revision=args.revision,local_files_only=True,torch_dtype=dtype,attn_implementation='sdpa').to('cuda').eval()
        self.model.config.use_cache=True
        eos=self.model.generation_config.eos_token_id
        self.stop_ids=set(eos if isinstance(eos,list) else [eos])|set(resolve_stop_token_ids(self.tokenizer,args.stop_token))
        self.stop_ids.discard(None)
        self.runtime=dict(backend='transformers_gpu_per_cell_rng_v19',torch=torch.__version__,transformers=transformers.__version__,dtype=dtype_name,attention='sdpa',cuda_visible_devices='0',gpu=torch.cuda.get_device_name(),model=args.model,seed_policy='one CUDA torch.Generator per declared cell; exact frozen seed',batch=args.batch,max_tokens=args.max_tokens,temperature=args.temperature,top_p=args.top_p,top_k=args.top_k,stop_token_ids=sorted(self.stop_ids),started_unix=time.time(),source_sha256=__import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest(),numerical_equivalence_to_vllm_claimed=False)
        path=Path(args.out).with_suffix('.runtime.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(self.runtime,indent=2)+'\n')

    def sample(self,logits,generator):
        torch=self.torch;a=self.args
        logits=logits.float()
        if a.temperature==0:return int(logits.argmax().item())
        logits=logits/a.temperature
        if a.top_k>0:
            logits,candidates=torch.topk(logits,min(a.top_k,logits.shape[-1]),sorted=True)
        else:candidates=torch.arange(logits.shape[-1],device=logits.device)
        if a.top_p<1:
            ordered,indices=torch.sort(logits,descending=True)
            cumulative=torch.softmax(ordered,dim=-1).cumsum(dim=-1)
            remove=cumulative>a.top_p
            remove[1:]=remove[:-1].clone();remove[0]=False
            logits=logits.masked_fill(torch.zeros_like(remove).scatter(0,indices,remove),float('-inf'))
        probabilities=torch.softmax(logits,dim=-1)
        assert bool(torch.isfinite(probabilities).all()) and float(probabilities.sum())>0,'Invalid sampling probabilities'
        selected=torch.multinomial(probabilities,1,generator=generator)
        return int(candidates[selected].item())

    def generate(self,texts,seeds):
        from rl4cv.veribench.generate import Completion
        torch=self.torch;a=self.args
        assert len(texts)==len(seeds) and texts
        encoded=self.tokenizer(texts,return_tensors='pt',padding=True,add_special_tokens=False).to('cuda')
        counts=encoded['attention_mask'].sum(-1).tolist()
        position_ids=encoded['attention_mask'].long().cumsum(-1)-1
        position_ids.masked_fill_(encoded['attention_mask']==0,0)
        generators=[torch.Generator(device='cuda').manual_seed(int(seed)) for seed in seeds]
        generated=[[] for _ in texts];reasons=['length' for _ in texts];active=list(range(len(texts)))
        attention=encoded['attention_mask']
        with torch.inference_mode():
            outputs=self.model(input_ids=encoded['input_ids'],attention_mask=attention,position_ids=position_ids,use_cache=True,logits_to_keep=1)
            del encoded
            for step in range(a.max_tokens):
                logits=outputs.logits[:,-1,:];past=outputs.past_key_values
                selected=[];keep=[];still_active=[]
                for local,original in enumerate(active):
                    token=self.sample(logits[local],generators[original]);generated[original].append(token)
                    if token in self.stop_ids:reasons[original]='stop'
                    else:keep.append(local);selected.append(token);still_active.append(original)
                del outputs,logits
                if not keep or step+1==a.max_tokens:break
                indices=torch.tensor(keep,device='cuda',dtype=torch.long)
                if len(keep)!=len(active):past.batch_select_indices(indices)
                attention=attention.index_select(0,indices)
                attention=torch.cat([attention,torch.ones((len(keep),1),device='cuda',dtype=attention.dtype)],dim=1)
                positions=attention.sum(-1,keepdim=True)-1
                outputs=self.model(input_ids=torch.tensor(selected,device='cuda',dtype=torch.long).unsqueeze(-1),attention_mask=attention,position_ids=positions,past_key_values=past,use_cache=True,logits_to_keep=1)
                active=still_active
        return [Completion(self.tokenizer.decode(tokens,skip_special_tokens=True),int(counts[i]),len(tokens),reasons[i]) for i,tokens in enumerate(generated)]


def main():
    repo=Path(os.environ['GX19_REPO']).resolve();sys.path.insert(0,str(repo/'src'))
    import rl4cv.veribench.generate as frozen
    frozen._HfEngine=GX10Engine
    argv=sys.argv[1:]
    if '--backend' not in argv:argv+=['--backend','hf']
    assert argv[argv.index('--backend')+1]=='hf','This wrapper is the explicit Transformers fallback'
    return frozen.main(argv)


if __name__=='__main__':raise SystemExit(main())
