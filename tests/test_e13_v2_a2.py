"""Synthetic tests for Amendment A2 retry bounds, admission, isolation and disclosure."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

V2 = Path(__file__).resolve().parents[1] / 'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2'
spec = importlib.util.spec_from_file_location('e13_a2_test', V2 / 'reproduction/a2_reconcile.py')
a2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a2)


def rows(route, unresolved=0, limits=0):
    n = a2.DENOMINATORS[route]
    return ([{'status': 'unresolved_measurement'} for _ in range(unresolved)] +
            [{'status': 'deterministic_resource_limit'} for _ in range(limits)] +
            [{'status': 'measured', 'oracle_equal': True, 'consistency': 'consistent'}
             for _ in range(n - unresolved - limits)])


@pytest.mark.parametrize('route,maximum', [('opaque', 5), ('ordinary', 33)])
def test_a2_route_tolerance_boundary_and_accounting(route, maximum):
    assert a2.public_receipt(route, rows(route, maximum, 7), [], {})['admitted']
    assert not a2.public_receipt(route, rows(route, maximum + 1), [], {})['admitted']
    assert not a2.public_receipt(route, rows(route)[:-1], [], {})['admitted']


def test_a2_equality_is_separate_from_missingness_and_consistency():
    data = rows('opaque', 2, 7)
    public = a2.public_receipt('opaque', data, data[:2], {})
    assert public['equality_among_measured'] == 'PASS' and public['admitted']
    data[-1] = {'status': 'measured', 'oracle_equal': False, 'consistency': 'consistent'}
    public = a2.public_receipt('opaque', data, [], {})
    assert public['equality_among_measured'] == 'FAIL' and not public['admitted']
    data[-1].update(oracle_equal=True, consistency='untyped_strict_success_component_deficit')
    public = a2.public_receipt('opaque', data, [], {})
    assert public['equality_among_measured'] == 'PASS'
    assert public['component_consistency'] == 'FAIL' and not public['admitted']
    data[-1] = {'status': 'integrity_defect'}
    assert not a2.public_receipt('opaque', data, [], {})['admitted']


def test_a2_opaque_public_receipt_cannot_disclose_cell_evidence():
    data = rows('opaque', 2)
    data[0].update(cell_id='SECRET_CELL', strict='SECRET_VALUE', components='SECRET_FACTOR',
                   source_path='SECRET_SOURCE', exception='SECRET_REASON')
    text = json.dumps(a2.public_receipt('opaque', data, data[:2], {'effective_results': 'hash'}))
    assert 'SECRET' not in text
    public = json.loads(text)
    assert public['retried_untyped_cells'] == 2
    assert public['retry_outcome_classes'] == {'unresolved_measurement': 2}


def test_a2_reserves_exactly_one_retry_and_preserves_attempt_one(tmp_path):
    db = a2.watchdog.database(tmp_path)
    db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?)',
               (a2.RUN, 'R2/cell', 1, 'source-hash', 'unresolved_measurement', 'before', 'after'))
    db.commit()
    before = tuple(db.execute('SELECT * FROM attempts').fetchone())
    with pytest.raises(RuntimeError, match='source binding'):
        a2.reserve_retry(db, 'R2/cell', 'changed-hash')
    a2.reserve_retry(db, 'R2/cell', 'source-hash')
    records = list(db.execute('SELECT * FROM attempts ORDER BY attempt'))
    assert tuple(records[0]) == before and records[1]['attempt'] == 2
    with pytest.raises(RuntimeError, match='one terminal untyped'):
        a2.reserve_retry(db, 'R2/cell', 'source-hash')


@pytest.mark.parametrize('status', sorted(a2.TYPED))
def test_a2_cannot_retry_a_typed_cell(tmp_path, status):
    db = a2.watchdog.database(tmp_path)
    db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?)',
               (a2.RUN, 'R2/cell', 1, 'source-hash', status, 'before', 'after'))
    db.commit()
    with pytest.raises(RuntimeError, match='one terminal untyped'):
        a2.reserve_retry(db, 'R2/cell', 'source-hash')


def test_a2_waits_for_original_run_before_reading_any_cell(tmp_path, monkeypatch):
    monkeypatch.setenv('WR', str(tmp_path))
    with pytest.raises(RuntimeError, match='original R2 is still running'):
        a2.reconcile_route('opaque')
    assert not (tmp_path / 'R2_A2').exists()


def test_a2_worker_command_keeps_code_route_and_resource_limit():
    command = a2.command_for({'address_space_bytes': 68719476736}, 'opaque', 17)
    assert command[0:3] == ['prlimit', '--as=68719476736', '--']
    assert command[4] == str(V2 / 'reproduction/cell_worker.py')
    assert command[5:] == ['--route', 'opaque', '--ordinal', '17', '--attempt', '2']


def test_a2_combines_only_two_fixed_public_routes():
    receipts = [a2.public_receipt(route, rows(route, a2.CEILINGS[route]), [], {})
                for route in a2.DENOMINATORS]
    assert a2.combine(receipts)['status'] == 'PASS'
    receipts[0]['admitted'] = False
    assert a2.combine(receipts)['status'] == 'FAIL'
    with pytest.raises(ValueError, match='both routes'):
        a2.combine(receipts[:1])


def test_a2_process_retry_and_resume_preserve_originals(tmp_path, monkeypatch, capsys):
    """Exercise real child processes and the ledger using authored synthetic receipts."""
    monkeypatch.setenv('WR', str(tmp_path))
    monkeypatch.setattr(a2, 'DENOMINATORS', {'ordinary': 2, 'opaque': 2})
    v2 = tmp_path / 'synthetic_v2'
    (v2 / 'locks').mkdir(parents=True)
    monkeypatch.setattr(a2, 'V2', v2)
    original = tmp_path / 'R2'
    (original / 'opaque').mkdir(parents=True)
    (original / 'public_result.json').write_text('{"status":"INCOMPLETE"}')
    (original / 'launch_receipt.json').write_text('{"coordinators":[]}')
    (original / 'opaque_public_receipt.json').write_text('{"status":"INCOMPLETE"}')
    manifest = [{'cell_id': f'SEALED_SYNTHETIC_{i}', 'source_sha256': 'same-source',
                 'split': 'test', 'task_id': 'synthetic', 'group_id': 'synthetic', 'sample_idx': i}
                for i in range(2)]
    old = [{**r, 'ordinal': i, 'attempt': 1, 'status': 'unresolved_measurement'}
           for i, r in enumerate(manifest)]
    (original / 'opaque_manifest.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in manifest))
    old_path = original / 'opaque/results.jsonl'
    old_path.write_text(''.join(json.dumps(r) + '\n' for r in old))
    old_bytes = old_path.read_bytes()
    (v2 / 'locks/A2_reconciliation.json').write_text(json.dumps({
        'observed_opaque_untyped_cells': 2,
        'original_opaque_public_receipt_sha256': a2.sha(original / 'opaque_public_receipt.json')}))
    monkeypatch.setattr(a2, 'verify_bindings', lambda _: {'max_workers': 2, 'p99_peak_bytes': 1024})
    wd = tmp_path / 'watchdog'
    wd.mkdir()
    db = a2.watchdog.database(wd)
    db.execute('CREATE TABLE r2_slots (run TEXT,pid INTEGER,identity_json TEXT,cell TEXT,PRIMARY KEY(run,pid))')
    for row in manifest:
        db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?)',
                   (a2.RUN, 'R2/' + row['cell_id'], 1, row['source_sha256'], 'unresolved_measurement', 'before', 'after'))
    db.commit()
    originals = [tuple(r) for r in db.execute('SELECT * FROM attempts ORDER BY cell')]
    db.close()
    fake = tmp_path / 'authored_worker.py'
    fake.write_text('''import json,os,sys,time
from pathlib import Path
time.sleep(.2)
root=Path(os.environ['WR'])/'R2';i=int(sys.argv[1])
row=json.loads((root/'opaque_manifest.jsonl').read_text().splitlines()[i])
row.update(ordinal=i,attempt=2,status='measured',oracle_equal=True,consistency='consistent')
p=root/'opaque/cells'/f'{i:05d}'/'attempt_2';p.mkdir(parents=True)
(p/'receipt.json').write_text(json.dumps(row))
''')
    monkeypatch.setattr(a2, 'command_for', lambda execution, route, ordinal: [sys.executable, str(fake), str(ordinal)])
    receipt = a2.reconcile_route('opaque')
    assert receipt['admitted'] and receipt['retry_outcome_classes'] == {'measured': 2}
    assert old_path.read_bytes() == old_bytes
    assert 'SEALED_SYNTHETIC' not in capsys.readouterr().out
    def prohibited(*args):
        raise AssertionError('resume must not start another attempt')
    monkeypatch.setattr(a2, 'command_for', prohibited)
    assert a2.reconcile_route('opaque', resume=True) == receipt
    db = a2.watchdog.database(wd)
    assert [tuple(r) for r in db.execute('SELECT * FROM attempts WHERE attempt=1 ORDER BY cell')] == originals
    assert db.execute('SELECT count(*) FROM attempts WHERE attempt=2').fetchone()[0] == 2
    assert db.execute('SELECT count(*) FROM attempts WHERE attempt>2').fetchone()[0] == 0
    db.close()
