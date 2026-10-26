"""Check GPU sampling support, independent RNG streams, EOS/stop handling and active-row removal without held-out prompts."""
from types import SimpleNamespace
import json
import os
from pathlib import Path
import torch
from generate_gx10 import GX10Engine
from common import ROOT,digest,write

class Encoding(dict):
    def to(self,device):return Encoding({k:v.to(device) for k,v in self.items()})
class Tokenizer:
    def __call__(self,texts,**kwargs):
        ids=torch.tensor([[int(s)] for s in texts]);return Encoding(input_ids=ids,attention_mask=torch.ones_like(ids))
    def decode(self,tokens,skip_special_tokens):return ','.join(map(str,[t for t in tokens if t!=7]))
class Cache:
    def batch_select_indices(self,indices):self.indices=indices
class Model:
    def __call__(self,input_ids,**kwargs):
        logits=torch.full((input_ids.shape[0],1,8),-100.,device='cuda')
        for i,token in enumerate(input_ids[:,-1].tolist()):logits[i,0,7 if token in (2,4) else 4]=100.
        return SimpleNamespace(logits=logits,past_key_values=kwargs.get('past_key_values',Cache()))

def main():
    assert os.environ['CUDA_VISIBLE_DEVICES']=='0' and torch.cuda.device_count()==1
    engine=object.__new__(GX10Engine);engine.torch=torch;engine.args=SimpleNamespace(temperature=.6,top_k=2,top_p=.95,max_tokens=5)
    logits=torch.tensor([100.,99.,-100.,-100.],device='cuda')
    def draws(seed):return [engine.sample(logits,gen) for gen in [torch.Generator(device='cuda').manual_seed(seed)] for _ in range(64)]
    first=draws(934);assert first==draws(934) and set(first)<=set([0,1])
    gen_a=torch.Generator(device='cuda').manual_seed(91);gen_b=torch.Generator(device='cuda').manual_seed(92)
    interleaved=[]
    for _ in range(32):interleaved.append(engine.sample(logits,gen_a));engine.sample(logits,gen_b)
    reference=torch.Generator(device='cuda').manual_seed(91);assert interleaved==[engine.sample(logits,reference) for _ in range(32)]
    engine.args.top_p=.01;assert set(draws(934))=={0}
    engine.args.temperature=0.;engine.tokenizer=Tokenizer();engine.model=Model();engine.stop_ids={7}
    outputs=engine.generate(['2','3'],[1,2]);assert [(o.generated_tokens,o.finish_reason,o.text) for o in outputs]==[(1,'stop',''),(2,'stop','4')]
    engine.args.max_tokens=1;outputs=engine.generate(['3'],[2]);assert outputs[0].generated_tokens==1 and outputs[0].finish_reason=='length'
    result=dict(status='PASS',checks=['top_k_support','top_p_support','RNG_replay','independent_per_cell_streams','stop_token','active_row_removal','length_cap'],cuda=torch.cuda.get_device_name(),source_sha256=digest(Path(__file__)),sampler_sha256=digest(Path(__file__).with_name('generate_gx10.py')),held_out_prompts_used=False)
    write(ROOT/'controls/inference_controls.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
