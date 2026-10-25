"""Teacher-forced HF re-scoring of vLLM rollouts; mismatch stats (rl4cv e21)."""
import argparse, json, math
import numpy as np, torch
ap = argparse.ArgumentParser()
ap.add_argument("--model"); ap.add_argument("--gen"); ap.add_argument("--dtype"); ap.add_argument("--out"); ap.add_argument("--lm-head-fp32", action="store_true"); ap.add_argument("--T", type=float, default=0.6); ap.add_argument("--eager", action="store_true")
a = ap.parse_args()
from transformers import AutoModelForCausalLM
import transformers.integrations.sdpa_attention as _sa
if a.dtype == "float32": _sa.use_gqa_in_sdpa = lambda *x, **k: False; torch.backends.cuda.enable_math_sdp(False)
T, K, P = a.T, 20, 0.95
dt = {"bfloat16": torch.bfloat16, "float32": torch.float32}[a.dtype]
m = AutoModelForCausalLM.from_pretrained(a.model, dtype=dt, **({"attn_implementation": "eager"} if a.eager else {})).cuda().eval()
W32 = m.lm_head.weight.float() if (a.lm_head_fp32 and dt != torch.float32) else None
def trunc_lp(logits, tgt):
    z = logits.float() / T
    full = torch.log_softmax(z, -1).gather(1, tgt[:, None])[:, 0]
    v, ix = z.topk(K, -1); pr = torch.softmax(v, -1)
    keep = (pr.cumsum(-1) - pr) < P
    pk = pr * keep; pk = pk / pk.sum(-1, keepdim=True)
    hit = (ix == tgt[:, None]) & keep
    sup = hit.any(-1)
    lp = torch.log((pk * hit).sum(-1).clamp_min(1e-30))
    ent = -(torch.softmax(z, -1) * torch.log_softmax(z, -1)).sum(-1)
    return lp, full, sup, ent
rows = []
for line in open(a.gen):
    r = json.loads(line); pi, ci = r["prompt_ids"], r["completion_ids"]
    ids = torch.tensor([pi + ci]).cuda()
    with torch.no_grad():
        h = m.model(ids).last_hidden_state[0, len(pi) - 1:-1]
        outs = []
        for s in range(0, h.shape[0], 1024):
            hc = h[s:s + 1024]
            lg = (hc.float() @ W32.T) if W32 is not None else m.lm_head(hc)
            outs.append(trunc_lp(lg, torch.tensor(ci[s:s + 1024]).cuda()))
    lp = torch.cat([o[0] for o in outs]).cpu().numpy(); fl = torch.cat([o[1] for o in outs]).cpu().numpy()
    sup = torch.cat([o[2] for o in outs]).cpu().numpy(); ent = torch.cat([o[3] for o in outs]).cpu().numpy()
    vl = np.array(r["vllm_lp"])
    rows.append((lp, fl, sup, ent, vl, np.arange(len(vl))))
cat = lambda i: np.concatenate([x[i] for x in rows])
lp, fl, sup, ent, vl, pos = [cat(i) for i in range(6)]
def stats(mask, ref):
    d = np.abs(ref[mask & sup] - vl[mask & sup]); n = int(mask.sum())
    if n == 0: return None
    uns = int((mask & ~sup).sum())
    return {"tokens": n, "unsupported": uns, "gt0.05_in_support": int((d > 0.05).sum()), "share_mismatch(gt0.05+unsupported)": (int((d > 0.05).sum()) + uns) / n,
            "median_abs": float(np.median(d)), "p99_abs": float(np.percentile(d, 99)), "mean_abs": float(d.mean()), "max_abs": float(d.max())}
res = {"model": a.model, "gen": a.gen, "scorer_dtype": a.dtype, "lm_head_fp32": a.lm_head_fp32, "rollouts": len(rows)}
allm = np.ones(len(lp), bool)
res["overall_truncated_support"] = stats(allm, lp)
res["overall_full_softmax"] = stats(allm, fl)
res["by_position"] = {f"{lo}-{hi}": stats((pos >= lo) & (pos < hi), lp) for lo, hi in [(0, 256), (256, 1024), (1024, 10**9)]}
res["by_entropy"] = {f"{lo}-{hi}": stats((ent >= lo) & (ent < hi), lp) for lo, hi in [(0, 0.1), (0.1, 1.0), (1.0, 99)]}
json.dump(res, open(a.out, "w"), indent=1)
np.savez_compressed(a.out.replace(".json", ".npz"), lp=lp.astype(np.float32), fl=fl.astype(np.float32), sup=sup, ent=ent.astype(np.float32), vl=vl.astype(np.float32), pos=pos)
print(json.dumps(res["overall_truncated_support"]))
