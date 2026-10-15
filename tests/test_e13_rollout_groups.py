"""Verify exact rollout/scorer joins, missing-reward retention and pre-generation placebo independence."""
import copy
import importlib.util
from pathlib import Path
import sys

import pytest

PHASE = Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0, str(PHASE))
spec = importlib.util.spec_from_file_location('e13_rollout_groups', PHASE/'rollout_groups.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
from arm_rewards import plan_group


def fixture(arm='A', groups=1):
    plans = [plan_group(arm, seed=1301, update=1, group_index=i, tasks=['authored'],
                       placebo_distribution=[0., .2, 1.] if arm == 'P' else None) for i in range(groups)]
    cells = [{**c, 'prompt_token_ids': [12, 13], 'arm': arm, 'run_seed': 1301, 'update': 1,
              'group_index': p['group_index']} for p in plans for c in p['cells']]
    generated = [{**c, 'output_token_ids': [14, 151645], 'generation_logprobs': [-.4, -.1],
                  'finish_reason': 'stop', 'at_token_cap': False, 'completion': 'authored'} for c in cells]
    scored = [{**c, 'status': 'measured', 'strict': c['sample'] % 2} for c in cells]
    return cells, generated, scored, plans


def test_shuffled_receipts_join_by_identity_and_keep_missing_reward_without_dropping_tokens():
    cells, generated, scored, plans = fixture(groups=2)
    scored[3]['status'] = 'unresolved_measurement'; scored[3]['strict'] = None
    result = m.assemble(cells, generated[::-1], scored[::-1], train_ids=['authored'], plans=plans)
    assert len(result) == 2 and all(len(g['rows']) == 8 for g in result)
    assert result[0]['rows'][3]['reward'] is None
    assert result[1]['rows'][3]['reward'] == 1.
    assert sum(len(r['output_token_ids']) for g in result for r in g['rows']) == 32


def test_placebo_does_not_depend_on_diagnostic_measurement():
    cells, generated, scored, plans = fixture('P')
    for row in scored: row.update(status='unresolved_measurement', strict=None)
    result = m.assemble(cells, generated, scored, train_ids=['authored'], plans=plans)
    assert [r['reward'] for r in result[0]['rows']] == plans[0]['placebo_draws']
    altered = copy.deepcopy(plans); altered[0]['cells'][0]['seed'] += 1
    with pytest.raises(ValueError, match='pre-generation'):
        m.assemble(cells, generated, scored, train_ids=['authored'], plans=altered)


def test_missing_generation_and_cross_run_or_duplicate_scores_cannot_be_silently_filled():
    cells, generated, scored, plans = fixture()
    with pytest.raises(ValueError, match='every declared'):
        m.assemble(cells, generated[:-1], scored, train_ids=['authored'], plans=plans)
    with pytest.raises(ValueError, match='duplicate'):
        m.assemble(cells, generated, scored+[scored[0]], train_ids=['authored'], plans=plans)
    bad = copy.deepcopy(scored); bad[0]['update'] = 2
    with pytest.raises(ValueError, match='identity'):
        m.assemble(cells, generated, bad, train_ids=['authored'], plans=plans)
    with pytest.raises(ValueError, match='held-out'):
        m.assemble(cells, generated, scored, train_ids=['different'], plans=plans)


def test_technical_update_uses_all_256_slots_and_only_strict_reward():
    cells, generated, scored, plans = fixture(groups=32)
    for rows in (cells, generated, scored):
        for row in rows: row['arm'] = 'technical'
    scored[1].update(status='deterministic_resource_limit', strict=None)
    result = m.assemble(cells, generated, scored, train_ids=['authored'], technical=True)
    assert len(result) == 32 and result[0]['rows'][1]['reward'] is None
    assert result[-1]['rows'][-1]['reward'] == 1.
    with pytest.raises(ValueError, match='32 declared'):
        m.assemble(cells[:8], generated[:8], scored[:8], train_ids=['authored'], technical=True)
    with pytest.raises(ValueError, match='interchanged'):
        m.assemble(cells, generated, scored, train_ids=['authored'], plans=plans)
