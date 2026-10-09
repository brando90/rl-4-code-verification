"""Check three renamed-control ambiguity witnesses with Lean itself before declaring the uniqueness gate blocked."""
import hashlib
import json
from pathlib import Path

from controls_e12_round2 import PHASE, WORK, lean
from rl4cv.forecast import verify_forecast


def main():
    for name in ('e12_phase_a_forecast', 'e12_phase_a_forecast_amendment_A1', 'e12_phase_a_forecast_amendment_A2'):
        assert verify_forecast(PHASE / 'forecasts' / (name + '.json'))
    controls = json.loads((PHASE / 'results/controls_e12_round2.json').read_text())
    assert controls['complete'] and controls['n_selected'] == 50
    rows = {row['task_id']: row for row in controls['rows']}
    witnesses = []
    for task in controls['selected_tasks']:
        row = rows[task]
        if not row['C1']['all_pass'] or row['C2']['compile']['status'] != 'ok':
            continue
        for diagnostic in row['C2']['diagnostics']:
            if diagnostic['status'] == 'ambiguous' and len(diagnostic['candidates']) == 2:
                path = Path(row['C2']['candidate_path'])
                assert hashlib.sha256(path.read_bytes()).hexdigest() == row['C2']['candidate_sha256']
                witnesses.append({'task_id': task, 'gold_symbol': diagnostic['gold_symbol'],
                                  'alternatives': diagnostic['candidates'], 'module': path.stem,
                                  'candidate_sha256': row['C2']['candidate_sha256']})
                break
        if len(witnesses) == 3:
            break
    assert len(witnesses) == 3
    source = '\n'.join(['import ' + w['module'] for w in witnesses] +
                       ['#check _root_.' + name for w in witnesses for name in w['alternatives']]) + '\n'
    probe = WORK / 'AmbiguityWitness.lean'
    probe.write_text(source)
    receipt = lean(probe)
    assert receipt['status'] == 'ok'
    output = Path(receipt['log']).read_text()
    # These first witnesses have simple signatures, so Lean prints each on one line.
    checks = [line for line in output.splitlines() if ' : ' in line]
    assert len(checks) == 6, output
    for i, witness in enumerate(witnesses):
        left, right = checks[2*i:2*i+2]
        assert left.split(' : ', 1)[1] == right.split(' : ', 1)[1]
        witness['lean_checks'] = [left, right]
    report = {'witnesses': witnesses, 'compiler_receipt': receipt,
              'probe_sha256': hashlib.sha256(source.encode()).hexdigest(),
              'controls_sha256': hashlib.sha256((PHASE / 'results/controls_e12_round2.json').read_bytes()).hexdigest(),
              'three_exact_type_ambiguities_confirmed': True,
              'max_recoverable_with_these_three_failures': 47, 'n_tasks': 50,
              'required_recovered_at_95_percent': 48}
    (PHASE / 'results/ambiguity_witnesses.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'witnesses'}))


if __name__ == '__main__':
    main()
