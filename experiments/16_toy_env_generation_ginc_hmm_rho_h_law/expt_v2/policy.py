"""CPU transformers, four-token sampling, and GRPO with exact per-token forward KL."""
import math
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from .ginc import V, BOS, VOCAB, K, rewards

SCALES = {'n1': (16,1,2), 'n2': (32,2,2), 'n3': (64,2,4), 'n4': (128,3,4)}

class TinyLM(nn.Module):
    def __init__(self, d, layers, heads):
        super().__init__()
        self.tok = nn.Embedding(VOCAB, d)
        self.pos = nn.Embedding(40, d)
        layer = nn.TransformerEncoderLayer(d, heads, 4*d, dropout=0., batch_first=True, norm_first=True)
        self.body = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(d)
        self.head = nn.Linear(d, V)
    def forward(self, tokens):
        length = tokens.shape[1]
        h = self.tok(tokens) + self.pos(torch.arange(length))
        mask = torch.triu(torch.full((length,length), float('-inf')), diagonal=1)
        return self.head(self.norm(self.body(h, mask=mask, is_causal=True)))
    def n_params(self):
        return sum(p.numel() for p in self.parameters())

def with_bos(x):
    x = torch.as_tensor(x, dtype=torch.long)
    return torch.cat([torch.full((len(x),1), BOS, dtype=torch.long), x], 1)


def pretrain(model, docs, steps, batch=64, lr=3e-3):
    gen = torch.Generator().manual_seed(0)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=.01)
    data = with_bos(docs)
    losses=[]
    for step in range(steps):
        seq = data[torch.randint(len(data), (batch,), generator=gen)]
        loss = F.cross_entropy(model(seq[:,:-1]).flatten(0,1), seq[:,1:].flatten())
        for group in opt.param_groups:
            group['lr'] = lr * .5 * (1 + math.cos(math.pi * step / steps))
        opt.zero_grad(); loss.backward(); opt.step()
        losses.append(float(loss.detach()))
        if (step+1) % 500 == 0:
            print(f'pretrain {step+1}/{steps} loss={np.mean(losses[-50:]):.5f}', flush=True)
    return losses

@torch.no_grad()
def generate(model, x, group=1, gen=None, greedy=False, chunk=256):
    outputs=[]
    for start in range(0,len(x),chunk):
        seq = with_bos(x[start:start+chunk]).repeat_interleave(group,0)
        ys=[]
        for _ in range(K):
            logits=model(seq)[:,-1]
            y=logits.argmax(-1) if greedy else torch.multinomial(logits.softmax(-1),1,generator=gen).squeeze(-1)
            ys.append(y); seq=torch.cat([seq,y[:,None]],1)
        outputs.append(torch.stack(ys,1).reshape(-1,group,K).numpy())
    return np.concatenate(outputs)


def exact_kl(logits, reference_logits):
    """Full-vocabulary KL(pi_theta || pi_0) at every supplied token prefix; reference detached."""
    logp = logits.log_softmax(-1)
    logq = reference_logits.detach().log_softmax(-1)
    return (logp.exp() * (logp-logq)).sum(-1)


def rollout_loss(model, ref, x, actions, reward, kl_coef=1.):
    batch, group, k = actions.shape
    seq = torch.cat([with_bos(x).repeat_interleave(group,0), torch.as_tensor(actions.reshape(-1,k))],1)
    length = x.shape[1]
    logits = model(seq[:,:-1])[:,length:length+k]
    with torch.no_grad():
        reference_logits = ref(seq[:,:-1])[:,length:length+k]
    r = torch.as_tensor(reward, dtype=logits.dtype)
    adv = r - (r.sum(1,keepdim=True)-r)/(group-1)
    logprobs = logits.log_softmax(-1).gather(-1,torch.as_tensor(actions.reshape(-1,k))[:,:,None]).squeeze(-1)
    pg = -(adv.detach().flatten() * logprobs.mean(-1)).mean()
    kl = exact_kl(logits, reference_logits).mean()
    return pg + kl_coef*kl, kl


def grpo(model, ref, pool, steps, eval_at, eval_fn, seed, batch=16, group=8, lr=1e-4, kl_coef=1.):
    gen=torch.Generator().manual_seed(seed)
    rng=np.random.default_rng(seed)
    opt=torch.optim.Adam(model.parameters(),lr=lr)
    out={}
    for step in range(1,steps+1):
        idx=rng.integers(len(pool.x),size=batch)
        x,y=pool.x[idx],pool.y[idx]
        a=generate(model,x,group,gen)
        reward,_=rewards(a,y)
        loss,kl=rollout_loss(model,ref,x,a,reward,kl_coef)
        opt.zero_grad(); loss.backward(); opt.step()
        if step in eval_at:
            out[step] = eval_fn(model)
            out[step]['last_train_kl']=float(kl.detach())
    return out
