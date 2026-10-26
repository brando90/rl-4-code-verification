"""TLDR: Preserve the exact historical pre-engine refusal and narrowly transition its two T1 intents."""
import json
from pathlib import Path
from common import digest

OLD_ADMISSION = '4d4b9918e97194bcb6616de4af62a40e894a63976d72743982524f25ae9b81fb'
ORIGINAL = {
    'started.json': '05e4523be9ef898fcb7ecaa8942b32e23dc0872f4cad7bf417d5ee79269b391d',
    'R0/execution.json': '9e607b79300cb83731030cf8bfae7901c5a83c39b1f6aee637de729fe79689c1',
    'R0/launch.json': '9790505110df0a7d7d220fd1fd9cc36be633ee9f7d203a15663a26426dae9b58',
    'R0/run.log': '416da801f34124159bd2f1fd91590d619e4f658a094aa7e86fc2300929ec4a8d',
    'R0/runtime.json': 'e1303dcb295eb89929ed328a04082bef933d1fea5153790fab444807abb2c4db',
}


def verify_legacy_refusal(attempt, evidence):
    """Only the audited dispatch-7 traceback is grandfathered; no absence inference."""
    from effect_receipts import no_effect_files
    attempt = Path(attempt)
    try:
        if evidence['bindings'] != ORIGINAL or not no_effect_files(attempt, pre_engine=True):
            return False
        allowed = set(ORIGINAL) | {'zero_effect_evidence.json', 'lease_refused.json'}
        if {str(p.relative_to(attempt)) for p in attempt.rglob('*') if p.is_file()} != allowed:
            return False
        if any(digest(attempt/name) != sha for name, sha in ORIGINAL.items()):
            return False
        proof = evidence['legacy_traceback_proof']
        old = Path(proof['original_admission'])
        if digest(old) != OLD_ADMISSION:
            return False
        admitted = {r['path']: r['sha256'] for r in json.loads(old.read_text())['bindings']}
        sources = proof['source_bindings']
        if set(sources) != {'stage_worker.py', 'stage_process.py', 'stage_ledger.py',
                            'device_guard.py', 'generation_runtime.py', 'local_engine.py'}:
            return False
        for name, row in sources.items():
            if digest(row['snapshot']) != row['sha256'] or admitted['phase2/'+name] != row['sha256']:
                return False
        lease_end = Path(proof['lease_end'])
        return (digest(lease_end) == proof['lease_end_sha256']
                and json.loads(lease_end.read_text())['status'] == 'RELEASED'
                and json.loads((attempt/'started.json').read_text())['admission_sha256'] == OLD_ADMISSION)
    except (OSError, ValueError, KeyError, TypeError):
        return False


def accepts(admission_path, work, intent_path, expected):
    """Accept only admission substitution; retain payload, predecessors and mode."""
    from effect_receipts import verified_failure
    try:
        record = json.loads(Path(admission_path).read_text())
        transition = record['readmission']
        work = Path(work).resolve(); path = Path(intent_path).resolve()
        if Path(transition['work']).resolve() != work:
            return False
        relative = str(path.relative_to(work))
        if relative not in ('T1/intent.json', 'T1/probe/intent.json'):
            return False
        if digest(path) != transition['intents'][relative]:
            return False
        attempt = work/'T1/probe/attempt_01'
        if (digest(attempt/'zero_effect_evidence.json') != transition['evidence_sha256']
                or not verified_failure(attempt, refused=True)):
            return False
        original = json.loads(path.read_text())
        if original['admission_sha256'] != OLD_ADMISSION or transition['prior_admission_sha256'] != OLD_ADMISSION:
            return False
        return {**original, 'admission_sha256': digest(admission_path)} == expected
    except (OSError, ValueError, KeyError, TypeError):
        return False
