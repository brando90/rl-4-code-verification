"""TLDR: Exact-six-rating, duplicate, budget and crash/readmission negative controls."""
import importlib.util
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[1] / 'experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/expt_v1/fsc_queue.py'
spec = importlib.util.spec_from_file_location('e09_queue_controls', path)
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


def result():
    return {'ratings': [{'config': c, 'repeat': r, 'status': 'measured',
                        'score_raw': r, 'prompt_hash_matches': True, 'run_id': 'fixture', 'cost_usd': .1}
                       for c in queue.CONFIGS for r in (1, 2, 3)]}


def payload(candidate='a'):
    return dict(candidate=candidate, reference='reference', source='source', judge_fingerprint='frozen')


def test_exact_six_and_median_aggregation():
    assert queue.six_rating_result(result())['fsc'] == .4


@pytest.mark.parametrize('kind', ['missing', 'duplicate', 'parse_error', 'hash', 'aggregation'])
def test_native_missing_or_invalid_blocks(kind):
    row = result()
    if kind == 'missing':
        row['ratings'].pop()
    elif kind == 'duplicate':
        row['ratings'][0] = row['ratings'][1]
    elif kind == 'parse_error':
        row['ratings'][0]['status'] = 'parse_error'
    elif kind == 'hash':
        row['ratings'][0]['prompt_hash_matches'] = False
    else:
        row['fsc'] = .5
    with pytest.raises(RuntimeError):
        queue.six_rating_result(row)


def test_exact_cache_and_fixed_call_budget(tmp_path):
    calls = []
    def transport(rows):
        calls.append(rows)
        return {row['key']: result() for row in rows}
    q = queue.BatchFSCQueue(tmp_path, transport, 12, lambda: None)
    assert len(q.request_many([payload(), payload()]).result()) == 2
    q.request_many([payload(), payload('b')]).result()
    assert sum(len(c) for c in calls) == 2
    with pytest.raises(RuntimeError, match='budget exhausted'):
        q.request_many([payload('c')]).result()
    q.close()


def test_partial_batch_is_not_cached_or_readmitted(tmp_path):
    calls = []
    def transport(rows):
        calls.append(rows)
        response = {row['key']: result() for row in rows}
        response[rows[-1]['key']]['ratings'].pop()
        return response
    q = queue.BatchFSCQueue(tmp_path, transport, 24, lambda: None)
    with pytest.raises(RuntimeError):
        q.request_many([payload(), payload('b')]).result()
    assert not list(tmp_path.glob('[0-9a-f]' * 64 + '.json'))
    with pytest.raises(RuntimeError, match='adopt recorded runs'):
        q.request_many([payload(), payload('b')]).result()
    with pytest.raises(RuntimeError, match='adopt recorded runs'):
        q.request_many([payload(), payload('c')]).result()
    assert len(calls) == 1
    q.close()
