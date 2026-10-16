"""Validate every completed cell and durable receipt against the frozen primary panel."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from adapter_v2 import cell_outcome, per_test_plan
from evaluate_v2 import runtime_hashes
from support_v2 import PHASE, V1, WORK, digest, verify_inputs, atomic_json


def audit(work):
    frozen = verify_inputs()
    completion = json.loads((PHASE/'results/evaluation_complete_v2.json').read_text())
    source = work/'cells_v2.jsonl'
    assert completion['complete'] and completion['n_unique_groups'] == 4626
    assert completion['outcomes_sha256'] == digest(source)
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    inputs = json.loads((V1/'results/input_manifest_A1.json').read_text())['cells']
    original = {(r['system'],r['task_id']):r for r in inputs}
    assert len(rows) == len(original) == 9856
    assert {(r['system'],r['task_id']) for r in rows} == original.keys()
    suites = {r['task_id']:r for r in json.loads((V1/'results/hidden_tests_manifest.json').read_text())['tasks']}
    pins = runtime_hashes()
    runtime_manifest = json.loads((work/'evaluation_run_manifest_v2.json').read_text())
    assert runtime_manifest['inputs'] == frozen and runtime_manifest['runtime_hashes'] == pins
    counts = Counter(); tests = Counter(); runner = Counter(); seconds = []
    def lean_receipts(value):
        if isinstance(value,dict):
            if 'seconds' in value and 'status' in value and 'log' in value:
                runner[value['status']] += 1
                seconds.append(value['seconds'])
            for key,item in value.items():
                if key != 'infrastructure_retries':
                    lean_receipts(item)
        elif isinstance(value,list):
            for item in value:
                lean_receipts(item)
    for row in rows:
        key = (row['system'],row['task_id']); before = original[key]
        assert all(row[k] == v for k,v in before.items()), key
        counts[row['status']] += 1
        suite = suites[row['task_id']]
        assert row['n_tests'] == suite['n_tests']
        assert row['n_evaluable'] + row['n_type_unknown'] + row['n_unmapped'] == row['n_tests']
        assert row['n_pass'] <= row['n_evaluable'] <= row['n_mapped'] <= row['n_tests']
        assert row['applicable'] == (row['n_evaluable'] > 0)
        assert row['fully_applicable'] == (row['n_tests'] > 0 and row['n_evaluable'] == row['n_tests'])
        if row['receipt'] is None:
            assert not (row['compiles'] is True and suite['n_tests'] and row['join_status'] not in ('file_missing','join_ambiguous'))
            if row['status'] == 'noncompiling':
                assert row['hidden_all_pass'] == 0 and row['hidden_pass_rate'] == 0
            else:
                assert row['hidden_all_pass'] is None
            continue
        counts['receipts'] += 1
        receipt = json.loads(Path(row['receipt']).read_text())
        assert receipt['runtime_hashes'] == pins
        assert receipt['input_sha256'] == row['sha256'] == digest(row['path'])
        assert receipt['task_id'] == row['task_id']
        group = hashlib.sha256((row['task_id']+':'+row['sha256']).encode()).hexdigest()
        assert Path(row['receipt']).name == group+'.json'
        output = {int(k):v for k,v in receipt.get('evaluation',{}).get('outputs',{}).items()}
        expected = cell_outcome(suite['n_tests'],output,per_test_plan(suite['tests'],receipt['mapping']))
        assert all(row[k] == receipt[k] == v for k,v in expected.items()), key
        tests.update(r['status'] for r in row['per_test'])
        compiled = receipt['compile']
        if compiled.get('reused'):
            counts['modules_reused'] += 1
            module = work/'evaluation_v2/modules'/('E12Eval'+group[:24])
            assert digest(module.with_suffix('.lean')) == row['sha256']
            assert digest(module.with_suffix('.olean')) == compiled['olean_sha256']
        if receipt.get('infrastructure_retries'):
            counts['groups_with_infrastructure_retry'] += 1
            assert len(receipt['infrastructure_retries']) == 1
        if receipt.get('retry_interrupted'):
            counts['interrupted_retries'] += 1
        lean_receipts(receipt)
    assert counts['receipts'] == 4626
    return {'complete':True,'n_declared':len(rows),'n_systems':len({r['system'] for r in rows}),
            'n_tasks':len({r['task_id'] for r in rows}),'outcomes_sha256':digest(source),
            'counts':dict(counts),'eligible_per_test_status_counts':dict(tests),
            'lean_receipt_status_counts':dict(runner),
            'lean_receipt_seconds_total':sum(seconds),'lean_receipt_seconds_max':max(seconds,default=None),
            'runtime_hashes':pins,'frozen_inputs':frozen,
            'checks':['all original cell fields unchanged','complete unique declared panel','source hashes match',
                      'per-test outcomes independently reconstructed','all partitions consistent',
                      'copied module hashes match','bounded retry receipts','frozen runtime and input hashes']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--work',type=Path,default=WORK)
    args = parser.parse_args()
    result = audit(args.work)
    atomic_json(PHASE/'results/completion_audit_v2.json',result)
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
