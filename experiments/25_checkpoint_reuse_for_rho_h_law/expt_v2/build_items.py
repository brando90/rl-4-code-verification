"""TLDR: build the frozen item files (8-shot prompts, gold answers) for experiment 25's ten completion-mode environments (CPU; needs reasoning-gym 0.1.25 and the GSM8K and MATH train parquet files)."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import completion as c


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    ap.add_argument('--data-dir', required=True)
    ap.add_argument('--n-test', type=int, default=500)
    ap.add_argument('--envs', nargs='*', default=c.ENV_IDS)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    not_built = []
    for e in a.envs:
        env = c.build_env(e, a.n_test, Path(a.data_dir))
        if len(env['items']) < c.MIN_ITEMS:
            print(e, 'NOT BUILT: only', len(env['items']), 'distinct test questions', flush=True)
            not_built.append({'env_id': e, 'n_distinct_test_questions': len(env['items'])})
            continue
        (out / (e.replace('/', '__') + '.json')).write_text(json.dumps(env))
        print(e, len(env['items']), flush=True)
    (out / 'not_built.json').write_text(json.dumps(not_built))


if __name__ == '__main__':
    main()
