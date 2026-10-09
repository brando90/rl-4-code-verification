"""Recompile a frozen, outcome-independent sample of 100 nonempty primary candidates with two workers."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from rl4cv.forecast import verify_forecast

PHASE = Path(__file__).resolve().parents[1]
WORK = Path('/lfs/skampere1/0/brando9/rl4cv_e12')
LAKE = Path('/lfs/skampere1/0/brando9/rl4cv_e08/grading/lean_src')
LAKE_BIN = '/lfs/skampere1/0/brando9/.elan/bin/lake'


def run_lean(path, timeout=600, extra=()):
    start = time.monotonic()
    cmd = ['nice', '-n', '10', LAKE_BIN, 'env', 'lean', '-j', '1', *extra, str(path)]
    proc = subprocess.Popen(cmd, cwd=LAKE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, start_new_session=True)
    try:
        output, _ = proc.communicate(timeout=timeout)
        status = 'ok' if proc.returncode == 0 else 'error'
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        output, _ = proc.communicate()
        status = 'timeout'
    return {'command': cmd, 'returncode': proc.returncode, 'status': status,
            'seconds': time.monotonic() - start, 'output': output}


def main():
    for name in ('e12_phase_a_forecast', 'e12_phase_a_forecast_amendment_A1'):
        assert verify_forecast(PHASE / 'forecasts' / (name + '.json'))
    manifest = json.loads((PHASE / 'results/input_manifest_A1.json').read_text())
    eligible = [r for r in manifest['cells'] if r.get('bytes', 0) > 0 and
                r.get('recorded_compiles') is not None and r['join_status'] in ('bound', 'located_without_recorded_hash')]
    salt = 'rl4cv-e12-compile:'
    selected = sorted(eligible, key=lambda r: hashlib.sha256((salt+r['system']+':'+r['task_id']).encode()).hexdigest())[:100]
    assert len(selected) == 100
    selection = {'rule': 'first 100 by SHA256(rl4cv-e12-compile: + system + : + task_id) among nonempty joined files with recorded compile status; empty outputs are not Lean submissions under the frozen scorer',
                 'n_eligible': len(eligible), 'cells': selected}
    dest = PHASE / 'results/compile_selection_A1.json'
    if dest.exists():
        assert json.loads(dest.read_text()) == selection
    else:
        dest.write_text(json.dumps(selection, indent=1)+'\n')
    out = WORK / 'compile_reproduction_A1'; out.mkdir(exist_ok=True)

    def check(row):
        key = hashlib.sha256((row['system']+':'+row['task_id']).encode()).hexdigest()
        receipt = out / (key+'.json')
        if receipt.exists():
            old = json.loads(receipt.read_text()); assert old['sha256'] == row['sha256']; return old
        path = Path(row['path']); assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256']
        result = run_lean(path)
        (out / (key+'.log')).write_text(result.pop('output'))
        result.update(system=row['system'], task_id=row['task_id'], sha256=row['sha256'],
                      recorded_compiles=row['recorded_compiles'], observed_compiles=result['status']=='ok',
                      matches=(result['status']=='ok')==row['recorded_compiles'], log_path=str(out/(key+'.log')))
        receipt.write_text(json.dumps(result, indent=1)+'\n')
        return result
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(check, r) for r in selected]
        for f in concurrent.futures.as_completed(futures):
            rows.append(f.result())
            print(json.dumps({'completed': len(rows), 'matches': sum(r['matches'] for r in rows), 'last': rows[-1]['task_id'], 'seconds': rows[-1]['seconds']}), flush=True)
    rows.sort(key=lambda r: (r['system'], r['task_id']))
    report = {'n': len(rows), 'n_matches': sum(r['matches'] for r in rows),
              'gate': .99, 'passes': sum(r['matches'] for r in rows) >= 99, 'rows': rows,
              'lake_dir': str(LAKE), 'lean_toolchain': (LAKE/'lean-toolchain').read_text().strip(),
              'lake_manifest_sha256': hashlib.sha256((LAKE/'lake-manifest.json').read_bytes()).hexdigest()}
    (PHASE/'results/compile_reproduction_A1.json').write_text(json.dumps(report, indent=1)+'\n')
    print(json.dumps({k: report[k] for k in ('n', 'n_matches', 'passes')}), flush=True)
    raise SystemExit(0 if report['passes'] else 2)


if __name__ == '__main__':
    main()
