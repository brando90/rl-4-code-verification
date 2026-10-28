"""TLDR: score raw samples from gen_vllm.py with Reasoning Gym or exact numeric match and write rho, H, q_mixed and the measurability flag per environment (CPU)."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import completion as c


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--items-dir', required=True)
    ap.add_argument('--raw-dir', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--tag', default='')
    a = ap.parse_args()
    res = {}
    for f in sorted(Path(a.raw_dir).glob('*.jsonl')):
        env = json.loads((Path(a.items_dir) / (f.stem + '.json')).read_text())
        rows = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
        recs = c.score_raw(env, rows)
        res[env['env_id']] = c.measure(recs)
    Path(a.out).write_text(json.dumps({'tag': a.tag, 'envs': res}, indent=1))
    for k, v in res.items():
        print(f"{k:32s} n={v['n_groups']} mixed={v['n_mixed']} q={v['q_mixed_empirical']:.3f} rho={v['rho']:.1f} H={v['H']:.3f} acc={v['mean_reward']:.3f} tok={v['mean_generated_tokens']:.0f} adm={v['admission_rate']:.2f} ok={v['measurable']}")


if __name__ == '__main__':
    main()
