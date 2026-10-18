"""Record every terminal scheduler outcome and retain hashed checkpoints outside purged scratch."""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import time


ROOT = Path(__file__).resolve().parent
ARCHIVE = Path('/home/groups/sanmi/brando9/rl4cv_sherlock/expt_v4')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def classify(records, results):
    """Success requires all scheduler exits and both complete, full-denominator trajectories."""
    good_jobs = len(records) == 3 and all(
        r['State'] == 'COMPLETED' and r['ExitCode'] == '0:0' for r in records)
    good_results = len(results) == 2 and all(
        r.get('status') == 'COMPLETE' and r.get('step') == 658
        and r.get('examples') == 1315 and r.get('loss_tokens') == 5752936
        for r in results)
    return 'COMPLETE' if good_jobs and good_results else 'INCOMPLETE'


def main():
    jobs = list(csv.DictReader((ROOT / 'jobs.tsv').open(), delimiter='\t'))
    ids = [r['job_id'] for r in jobs if r['phase'] != 'finalize']
    raw = subprocess.check_output(['sacct', '-n', '-P', '-X', '-j', ','.join(ids),
        '--format=JobIDRaw,State,ExitCode,Elapsed,NodeList'], text=True)
    records = [dict(zip(['JobID', 'State', 'ExitCode', 'Elapsed', 'NodeList'],
                       line.split('|')[:5])) for line in raw.splitlines() if line.strip()]
    results = [json.loads(p.read_text()) for p in sorted((ROOT / 'runs').glob('*/result.json'))]
    receipt = {'status': classify(records, results), 'checked_unix': time.time(),
               'scheduler': records, 'runs': results, 'archive': str(ARCHIVE),
               'archive_verified': False, 'provider_spend_usd': 0}
    (ROOT / 'terminal_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    hashes = {}
    # Preserve partial checkpoints on failure too; exclude only transient checkpoint writes.
    for source in sorted((ROOT / 'runs').rglob('*')):
        if not source.is_file() or '.tmp.' in source.name:
            continue
        relative = source.relative_to(ROOT)
        destination = ARCHIVE / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        expected = sha(source)
        if destination.exists():
            if sha(destination) != expected:
                raise RuntimeError(f'archive collision: {relative}')
        else:
            temporary = destination.with_name(destination.name + '.copying')
            shutil.copy2(source, temporary)
            if sha(temporary) != expected:
                raise RuntimeError(f'archive verification failed: {relative}')
            temporary.replace(destination)
        hashes[str(relative)] = expected
    receipt['archive_verified'] = True
    receipt['archived_files'] = len(hashes)
    (ROOT / 'archive_manifest.json').write_text(json.dumps(hashes, indent=2) + '\n')
    (ROOT / 'terminal_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    metadata = [p for p in ROOT.rglob('*') if p.is_file() and
        p.relative_to(ROOT).parts[0] not in {'data', 'cache', '__pycache__'} and
        p.suffix in {'.json', '.csv', '.tsv', '.md', '.py', '.sh', '.out'}]
    with tarfile.open(ROOT / 'results_bundle.tar.gz', 'w:gz') as bundle:
        for source in metadata:
            bundle.add(source, arcname=str(source.relative_to(ROOT)))
    shutil.copy2(ROOT / 'results_bundle.tar.gz', ARCHIVE / 'results_bundle.tar.gz')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
