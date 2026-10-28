"""Unit tests for experiment 25's completion-mode generator pieces (prompt, extraction, scoring, measurement) with a fake generator; no GPU needed."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_P = Path(__file__).resolve().parents[1] / 'experiments/25_checkpoint_reuse_for_rho_h_law/expt_v2'
sys.path.insert(0, str(_P))
import completion as c  # noqa: E402


def test_prompt_format_and_stop():
    p = c.format_prompt([('1+1?', '2'), ('2+2?', '4')], '3+3?')
    assert p == 'Question: 1+1?\nAnswer: 2\n\nQuestion: 2+2?\nAnswer: 4\n\nQuestion: 3+3?\nAnswer:'
    assert c.STOP == '\n\nQuestion:'


def test_extract_and_numeric_match():
    assert c.extract_first_line(' 12\n\nQuestion: x') == '12'
    assert c.numeric_match('$1,200 dollars', '1200') == 1.0
    assert c.numeric_match('about 7', '8') == 0.0
    assert c.numeric_match('no number', '8') == 0.0


def test_boxed_integer():
    assert c.boxed_integer('so \\boxed{1,200}.') == '1200'
    assert c.boxed_integer('\\boxed{\\frac{1}{2}}') is None
    assert c.boxed_integer('\\boxed{\\text{x}} then \\boxed{-4}') == '-4'
    assert c.boxed_integer('no box') is None


def _env(n=6):
    return {'env_id': 'gsm8k/train500', 'items': [{'item_id': f'e#{i}', 'gold': str(i), 'prompt': 'p'} for i in range(n)]}


def _rows(env, correct_pattern):
    rows = []
    for it, pat in zip(env['items'], correct_pattern):
        samples = [{'text': it['gold'] if ok else '999', 'generated_tokens': 5, 'finish_reason': 'stop'} for ok in pat]
        rows.append({'item_id': it['item_id'], 'samples': samples})
    return rows


def test_score_and_measure_with_fake_generator():
    pytest.importorskip('rl4cv.experience')
    env = _env(4)
    pats = [[1, 0] * 4, [1] * 8, [0] * 8, [1, 1, 1, 0, 0, 0, 0, 0]]
    recs = c.score_raw(env, _rows(env, pats))
    assert len(recs) == 32 and sum(r['reward'] for r in recs) == 4 + 8 + 0 + 3
    m = c.measure(recs)
    assert m['n_groups'] == 4 and m['n_mixed'] == 2 and m['measurable'] is True
    assert m['rho'] > 0 and 0 <= m['H'] <= 1


def test_truncation_is_not_admitted_and_empty_is_zero():
    env = _env(1)
    rows = [{'item_id': 'e#0', 'samples': [{'text': '', 'generated_tokens': 0, 'finish_reason': 'stop'},
                                          {'text': '0', 'generated_tokens': 512, 'finish_reason': 'length'}]}]
    recs = c.score_raw(env, rows)
    assert recs[0]['reward'] == 0.0 and recs[0]['generated_tokens'] == 1 and not recs[0]['extracted_nonempty']
    assert recs[1]['admitted'] is False and recs[1]['reward'] == 1.0


def test_rg_reward_matches_gold_answer():
    try:
        import e18a_common as C18
        C18.ensure_pycosat()
        import reasoning_gym  # noqa: F401
    except ImportError as e:
        pytest.skip(f'reasoning-gym not available: {e}')
    env = c.build_env('rg/basic_arithmetic/L0', 12, Path('.'))
    assert len(env['items']) == 12 and len(env['exemplars']) == c.N_SHOT
    assert not ({q for q, _ in env['exemplars']} & {it['question'] for it in env['items']})
    it = env['items'][0]
    assert c.reward('rg/basic_arithmetic/L0', it['gold'], it) == 1.0
    assert c.reward('rg/basic_arithmetic/L0', 'banana', it) == 0.0
