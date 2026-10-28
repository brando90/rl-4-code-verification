"""TLDR: sample G completions per 8-shot prompt with vLLM for experiment 25's public-checkpoint arms; reads items JSON built by completion.py, writes raw samples JSONL (runs on a GPU host, needs only vllm)."""
import argparse
import json
import time
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--model', required=True)
    ap.add_argument('--items', nargs='+', required=True, help='env item files (JSON with env_id, items, meta)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--n-items', type=int, default=None)
    ap.add_argument('--group', type=int, default=8)
    ap.add_argument('--max-tokens', type=int, default=512)
    ap.add_argument('--gpu-mem', type=float, default=0.85)
    ap.add_argument('--revision', default=None)
    a = ap.parse_args()
    from vllm import LLM, SamplingParams
    t0 = time.time()
    llm = LLM(model=a.model, revision=a.revision, dtype='bfloat16', max_model_len=4096, gpu_memory_utilization=a.gpu_mem,
              enable_prefix_caching=True, seed=0)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for f in a.items:
        env = json.loads(Path(f).read_text())
        items = env['items'][:a.n_items]
        sp = SamplingParams(n=a.group, temperature=1.0, top_p=1.0, max_tokens=a.max_tokens, stop=['\n\nQuestion:'],
                            seed=env['meta']['sampling_seed'])
        res = llm.generate([it['prompt'] for it in items], sp)
        rows = [{'item_id': it['item_id'], 'samples': [{'text': o.text, 'generated_tokens': len(o.token_ids), 'finish_reason': o.finish_reason}
                                                       for o in r.outputs]} for it, r in zip(items, res)]
        path = out / (env['env_id'].replace('/', '__') + '.jsonl')
        path.write_text('\n'.join(json.dumps(r) for r in rows) + '\n')
        print(json.dumps({'env': env['env_id'], 'n_items': len(rows), 'seconds': round(time.time() - t0, 1)}), flush=True)


if __name__ == '__main__':
    main()
