"""TLDR: completion-mode (8-shot Question/Answer) item builder, scorer and rho/H measurement for experiment 25's public-checkpoint arms (R5); generation itself is in gen_vllm.py so this module runs on a CPU box with reasoning-gym."""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'experiments/18_reasoning_gym_generated_env_prerl_scoring_qwen3/expt_v1'))
sys.path.insert(0, str(REPO / 'src'))

STOP = '\n\nQuestion:'
N_SHOT, G, MAX_TOKENS, TEMPERATURE = 8, 8, 512, 1.0
SEED0 = 20261028
RG_FAMILIES = ['basic_arithmetic', 'leg_counting', 'simple_equations', 'coin_flip']
ENV_IDS = [f'rg/{f}/L{l}' for f in RG_FAMILIES for l in (0, 1)] + ['gsm8k/train500', 'math/prealgebra_L1L2_int']
MIN_ITEMS = 20
_NUM = re.compile(r'-?\d+(?:\.\d+)?')


def format_prompt(exemplars: list[tuple[str, str]], question: str) -> str:
    shots = ''.join(f'Question: {q}\nAnswer: {a}\n\n' for q, a in exemplars)
    return f'{shots}Question: {question}\nAnswer:'


def extract_first_line(text: str) -> str:
    return text.split('\n')[0].strip()


def numeric_match(extracted: str, gold: str) -> float:
    nums = _NUM.findall(extracted.replace(',', '').replace('$', '').replace(' ', ''))
    if not nums:
        return 0.0
    try:
        return 1.0 if abs(float(nums[-1]) - float(gold)) < 1e-6 else 0.0
    except ValueError:
        return 0.0


def boxed_integer(solution: str):
    """Content of the last \\boxed{...} if it is an integer (after removing commas), else None."""
    i = solution.rfind('\\boxed{')
    if i < 0:
        return None
    j, depth = i + 7, 1
    while j < len(solution) and depth:
        depth += {'{': 1, '}': -1}.get(solution[j], 0)
        j += 1
    inner = solution[i + 7:j - 1].replace(',', '').replace('\\!', '').strip()
    return inner if re.fullmatch(r'-?\d+', inner) else None


def build_env(env_id: str, n_test: int, data_dir: Path) -> dict:
    """Items for one environment: {'env_id','exemplars','items':[{'item_id','prompt','gold','question'}],'meta'}."""
    index = ENV_IDS.index(env_id)
    meta = {'env_id': env_id, 'index': index, 'sampling_seed': SEED0 + index}
    if env_id.startswith('rg/'):
        import e18a_common as C
        _, fam, lvl = env_id.split('/')
        spec = next(s for s in C.all_sets() if s.set_id == env_id)
        pool = C.rg_dataset(spec, 4 * n_test)
        ex_spec = type(spec)(**{**spec.__dict__, 'seed': spec.seed + 7_000_000})
        expool = C.rg_dataset(ex_spec, 4 * n_test)
        exemplars, seen = [], set()
        for i in range(len(expool)):
            q = expool[i]['question']
            if q not in seen and len(exemplars) < N_SHOT:
                seen.add(q)
                exemplars.append((q, str(expool[i]['answer'])))
        # small-space environments repeat questions: keep each distinct question once and never test on an exemplar
        questions, entries = [], {}
        for i in range(len(pool)):
            q = pool[i]['question']
            if q in seen or len(questions) >= n_test:
                continue
            seen.add(q)
            entries[len(questions)] = dict(pool[i])
            questions.append((q, str(pool[i]['answer'])))
        meta.update({'seed': spec.seed, 'rg_version': '0.1.25', 'n_distinct_in_pool': len(seen) - N_SHOT})
    elif env_id == 'gsm8k/train500':
        import pandas as pd
        df = pd.read_parquet(data_dir / 'gsm8k_train.parquet')
        ids = random.Random(20261020).sample(range(len(df)), n_test)
        rest = [i for i in range(len(df)) if i not in set(ids)]
        ex_ids = random.Random(20261021).sample(rest, N_SHOT)
        gold = lambda a: a.split('####')[-1].strip().replace(',', '')
        questions = [(df.question[i], gold(df.answer[i])) for i in ids]
        exemplars = [(df.question[i], gold(df.answer[i])) for i in ex_ids]
        meta.update({'test_indices': ids, 'exemplar_indices': ex_ids})
        entries = None
    elif env_id == 'math/prealgebra_L1L2_int':
        import pandas as pd
        df = pd.read_parquet(data_dir / 'math_prealgebra_train.parquet')
        elig = [i for i in range(len(df)) if df.level[i] in ('Level 1', 'Level 2') and boxed_integer(df.solution[i]) is not None]
        ex_ids = random.Random(20261021).sample(elig, N_SHOT)
        ids = [i for i in elig if i not in set(ex_ids)][:n_test]
        questions = [(df.problem[i], boxed_integer(df.solution[i])) for i in ids]
        exemplars = [(df.problem[i], boxed_integer(df.solution[i])) for i in ex_ids]
        meta.update({'n_eligible': len(elig), 'test_indices': ids, 'exemplar_indices': ex_ids})
        entries = None
    else:
        raise ValueError(env_id)
    assert len(exemplars) == N_SHOT and len(questions) >= 0 and not ({q for q, _ in exemplars} & {q for q, _ in questions})
    items = [{'item_id': f'{env_id}#{i}', 'question': q, 'gold': a, 'prompt': format_prompt(exemplars, q)} for i, (q, a) in enumerate(questions)]
    if entries is not None:
        for it, i in zip(items, range(len(items))):
            it['rg_entry'] = json.dumps(entries[i], default=str)
    meta['n_items'] = len(items)
    return {'env_id': env_id, 'exemplars': exemplars, 'items': items, 'meta': meta}


def reward(env_id: str, text: str, item: dict) -> float:
    ext = extract_first_line(text)
    if not ext:
        return 0.0
    if env_id.startswith('rg/'):
        import e18a_common as C
        ds = _rg_for(env_id, item)
        return float(ds.score_answer(ext, json.loads(item['rg_entry'])))
    return numeric_match(ext, item['gold'])


_RG_CACHE: dict = {}


def _rg_for(env_id, item):
    if env_id not in _RG_CACHE:
        import e18a_common as C
        spec = next(s for s in C.all_sets() if s.set_id == env_id)
        _RG_CACHE[env_id] = C.rg_dataset(spec, 8)
    return _RG_CACHE[env_id]


def score_raw(env: dict, raw_rows: list[dict]) -> list[dict]:
    """raw_rows: {'item_id','samples':[{'text','generated_tokens','finish_reason'}]} -> flat records for groups_from_records."""
    by_id = {it['item_id']: it for it in env['items']}
    recs = []
    for row in raw_rows:
        it = by_id[row['item_id']]
        for k, s in enumerate(row['samples']):
            recs.append({'task_id': row['item_id'], 'sample_idx': k, 'reward': reward(env['env_id'], s['text'], it),
                         'generated_tokens': max(1, int(s['generated_tokens'])), 'admitted': s['finish_reason'] != 'length',
                         'extracted_nonempty': bool(extract_first_line(s['text']))})
    return recs


def measure(recs: list[dict]) -> dict:
    from rl4cv.experience import groups_from_records, measure_environment
    m = measure_environment(groups_from_records(recs, reward_key='reward'))
    d = m.to_dict()
    d['n_mixed'] = round(m.q_mixed_empirical * m.n_groups)
    d['measurable'] = bool(m.q_mixed_empirical >= 0.2)
    d['extraction_nonempty_rate'] = sum(r['extracted_nonempty'] for r in recs) / len(recs)
    return d
