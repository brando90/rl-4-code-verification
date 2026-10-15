"""Verify fixed audit denominators, original-score provenance and missing input retention."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

PHASE = Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0, str(PHASE))
spec = importlib.util.spec_from_file_location('e13_audit_inputs', PHASE/'audit_inputs.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def fixture(tmp_path):
    cells = []; evidence = []
    source = b'theorem value : 1 = 1 := rfl\n'
    for i in range(32):
        task = f'train_{i}'
        root = tmp_path/f'original_{i}'
        (root/'evidence/components').mkdir(parents=True)
        (root/'solution.lean').write_bytes(source)
        (root/'worker_result.json').write_text(json.dumps({'status': 'measured', 'task_id': task,
            'sample_idx': 0, 'batch': 'full1', 'policy': 'sft_4B_f1p0', 'source_sha256': m.digest(root/'solution.lean')}))
        (root/'evidence/components/frontend.json').write_text(json.dumps({
            'schema': 'e13-declaration-probe-v2', 'terminal': True,
            'commands': [{'index': 0, 'start': 0, 'stop': len(source),
                          'syntax': {'declaration_kind': 'Lean.Parser.Command.theorem', 'short_name': 'value'}}],
            'theorems': [{'command_index': 0}]}))
        cells.append({'audit_id': f'audit_{i}', 'task_id': task, 'group_id': f'group_{i}',
                      'split': 'train', 'baseline_batch': 'full1', 'baseline_sample': 0})
        evidence.append({'task_id': task, **{k: {'path': str(root/p), 'sha256': m.digest(root/p)}
            for k, p in [('source', 'solution.lean'), ('score', 'worker_result.json'),
                         ('frontend', 'evidence/components/frontend.json')]}})
    return {'condition': 'v2-S2', 'audit_tasks': 32, 'cells': cells}, evidence, [c['task_id'] for c in cells]


def test_all_128_variants_and_original_bytes_are_retained(tmp_path):
    cohort, evidence, train = fixture(tmp_path)
    result = m.prepare(cohort, evidence, train_ids=train, output=tmp_path/'prepared')
    assert result['declared_variants'] == len(result['cells']) == 128
    assert result['missing_inputs'] == result['new_measurements'] == 0
    assert result['status'] == 'PREPARED_NOT_ADMITTED'
    original = result['cells'][0]
    assert original['original_measurement_reused']
    assert Path(original['source']['path']).read_bytes() == Path(evidence[0]['source']['path']).read_bytes()
    assert len({r['cell_id'] for r in result['cells']}) == 128
    with pytest.raises(FileExistsError): m.prepare(cohort, evidence, train_ids=train, output=tmp_path/'prepared')


def test_missing_source_and_incomplete_frontend_keep_declared_slots(tmp_path):
    cohort, evidence, train = fixture(tmp_path)
    evidence[0] = {'task_id': train[0]}
    front = Path(evidence[1]['frontend']['path'])
    value = json.loads(front.read_text()); value['terminal'] = False
    front.write_text(json.dumps(value)); evidence[1]['frontend']['sha256'] = m.digest(front)
    result = m.prepare(cohort, evidence, train_ids=train, output=tmp_path/'prepared')
    assert len(result['cells']) == 128 and result['missing_inputs'] == 7
    assert all(r['source'] is None for r in result['cells'][:4])
    assert result['cells'][4]['original_measurement_reused']


def test_changed_bytes_and_detached_frontend_are_refused(tmp_path):
    cohort, evidence, train = fixture(tmp_path)
    changed = copy.deepcopy(evidence); changed[0]['source']['sha256'] = '0'*64
    with pytest.raises(ValueError, match='input changed'):
        m.prepare(cohort, changed, train_ids=train, output=tmp_path/'changed')
    detached = tmp_path/'frontend.json'; detached.write_bytes(Path(evidence[0]['frontend']['path']).read_bytes())
    evidence[0]['frontend']['path'] = str(detached)
    with pytest.raises(ValueError, match='detached'):
        m.prepare(cohort, evidence, train_ids=train, output=tmp_path/'detached')


def test_cross_split_duplicate_and_wrong_sample_are_refused(tmp_path):
    cohort, evidence, train = fixture(tmp_path)
    changed = copy.deepcopy(cohort); changed['cells'][0]['split'] = 'test'
    with pytest.raises(ValueError, match='held-out'): m.prepare(changed, evidence, train_ids=train, output=tmp_path/'split')
    changed = copy.deepcopy(cohort); changed['cells'][0]['group_id'] = changed['cells'][1]['group_id']
    with pytest.raises(ValueError, match='32-group'): m.prepare(changed, evidence, train_ids=train, output=tmp_path/'duplicate')
    score = Path(evidence[0]['score']['path']); value = json.loads(score.read_text()); value['sample_idx'] = 1
    score.write_text(json.dumps(value)); evidence[0]['score']['sha256'] = m.digest(score)
    with pytest.raises(ValueError, match='identity'): m.prepare(cohort, evidence, train_ids=train, output=tmp_path/'sample')
