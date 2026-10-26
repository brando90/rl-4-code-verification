"""vLLM rollouts for the log-prob mismatch diagnostic (rl4cv e21). One config per process."""
import argparse, json, glob, os, random
ap = argparse.ArgumentParser()
ap.add_argument("--model"); ap.add_argument("--packs"); ap.add_argument("--dtype", default="bfloat16")
ap.add_argument("--mode", default="processed_logprobs"); ap.add_argument("--out"); ap.add_argument("--ntasks", type=int, default=64)
ap.add_argument("--nsamp", type=int, default=4); ap.add_argument("--max-tokens", type=int, default=3072)
ap.add_argument("--gpu-util", type=float, default=0.6)
a = ap.parse_args()
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained(a.model)
dirs = sorted(glob.glob(a.packs + "/*/instruction.md")); random.Random(0).shuffle(dirs); dirs = dirs[:a.ntasks]
prompts = []
for d in dirs:
    txt = open(d).read()
    ids = tok.apply_chat_template([{"role": "user", "content": txt}], add_generation_prompt=True, tokenize=True)
    ids = ids["input_ids"] if hasattr(ids, "keys") else ids
    if len(ids) < 6000: prompts.append((os.path.basename(os.path.dirname(d)), list(ids)))
llm = LLM(a.model, dtype=a.dtype, gpu_memory_utilization=a.gpu_util, max_model_len=10240, logprobs_mode=a.mode, seed=0, enable_prefix_caching=False)
reqs, params = [], []
for ti, (name, ids) in enumerate(prompts):
    for k in range(a.nsamp):
        reqs.append({"prompt_token_ids": ids})
        params.append(SamplingParams(n=1, temperature=0.6, top_p=0.95, top_k=20, max_tokens=a.max_tokens, seed=1000 * ti + k, logprobs=0))
outs = llm.generate(reqs, params, use_tqdm=False)
with open(a.out, "w") as f:
    for i, o in enumerate(outs):
        c = o.outputs[0]
        lps = [lp[t].logprob for t, lp in zip(c.token_ids, c.logprobs)]
        f.write(json.dumps({"task": prompts[i // a.nsamp][0], "prompt_ids": list(o.prompt_token_ids), "completion_ids": list(c.token_ids), "vllm_lp": lps, "finish": c.finish_reason}) + "\n")
print("wrote", a.out, len(outs), "rollouts")
