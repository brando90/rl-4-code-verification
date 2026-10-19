"""Verify the two immutable tiny releases and publish their exact 500-row union.

This performs no generation, Lean compilation, or changes to either final release.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import time

RUN = Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
PINS = {
    'v21': ('tiny_training.jsonl', 'f757a318cbcf5b8ddae32d26ad582df0bbbfc224f02179ac75bd22c5d2850f57',
            'd9bbc3d0c702590881a4d27aba6862881263bd21994d8fc56e6a135a126bf323', 470),
    'v22': ('repaired_tiny_training.jsonl', 'b4d9b103158515af58005856658432bf23190c68588e01d7d552a83974bf52a8',
            'd9a38a1b869260fcc5711d1674df9acb69954716944b15d9d132c1981b5282a0', 30),
}

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def main() -> None:
    originals = [json.loads(x) for x in (RUN/'curriculum/training.jsonl').read_text().splitlines()]
    combined = {}
    manifests = {}
    releases = {}
    excluded = set()
    for phase, (name, data_sha, completion_sha, count) in PINS.items():
        root = RUN/('lean_corpus_'+phase)
        final = root/'final'
        assert sha((root/'completion.json').read_bytes()) == completion_sha
        completion = json.loads((root/'completion.json').read_text())
        assert completion['accepted'] == count
        raw = (final/name).read_bytes()
        assert sha(raw) == data_sha == completion['training_sha256']
        rows = [json.loads(line) for line in raw.splitlines()]
        proof_raw = (final/'proof_receipts_manifest.json').read_bytes()
        assert sha(proof_raw) == completion['proof_receipts_manifest_sha256']
        proofs = {p['example_index']:p for p in json.loads(proof_raw)}
        assert len(rows) == len(proofs) == count
        outcome_raw = (final/'row_results.csv').read_bytes()
        assert sha(outcome_raw) == completion['row_results_sha256']
        outcomes = list(csv.DictReader(outcome_raw.decode().splitlines()))
        if phase == 'v21':
            excluded = {r['task_id'] for r in outcomes if r['admitted'] == 'False'}
        else:
            assert excluded == {r['task_id'] for r in outcomes}
        for row in rows:
            index = row['example_index']
            assert index not in combined and row['task_id'] == originals[index]['task_id']
            assert row['messages'][:2] == originals[index]['messages'][:2]
            assert row['current_kernel_verified'] is True
            proof = proofs[index]
            assert proof['task_id'] == row['task_id']
            assert proof['source_sha256'] == row['lean_sha256']
            receipt_raw = (final/proof['portable_receipt']).read_bytes()
            assert sha(receipt_raw) == proof['receipt_sha256']
            binding_raw = (final/proof['portable_comment_binding']).read_bytes()
            binding = json.loads(binding_raw)
            assert binding['kernel_receipt_sha256'] == proof['receipt_sha256']
            assert binding['annotated_source_sha256'] == proof['source_sha256']
            assert binding['kernel_checked_source_sha256'] == proof['kernel_checked_source_sha256']
            assert binding['original_bytes_preserved'] is True
            assert binding['noncomment_tokens_unchanged'] is True
            files_raw = (final/proof['files_manifest']).read_bytes()
            assert sha(files_raw) == proof['files_manifest_sha256']
            combined[index] = row
            manifests[index] = dict(example_index=index, task_id=row['task_id'], phase=phase,
                source_sha256=row['lean_sha256'], receipt_sha256=proof['receipt_sha256'],
                receipt_path=str(final/proof['portable_receipt']),
                comment_binding_path=str(final/proof['portable_comment_binding']),
                comment_binding_sha256=sha(binding_raw),
                files_manifest_path=str(final/proof['files_manifest']),
                files_manifest_sha256=proof['files_manifest_sha256'])
        releases[phase] = dict(rows=count, training_path=str(final/name), training_sha256=data_sha,
            completion_path=str(root/'completion.json'), completion_sha256=completion_sha,
            proof_manifest_path=str(final/'proof_receipts_manifest.json'),
            proof_manifest_sha256=sha(proof_raw))
    assert len(combined) == 500 and set(combined) == set(range(500))
    assert len({r['task_id'] for r in combined.values()}) == 500
    target = RUN/'lean_corpus_v22/handoff'
    target.mkdir(exist_ok=True)
    raw = ''.join(json.dumps(combined[i], sort_keys=True)+'\n' for i in range(500)).encode()
    out = target/'tiny_500_training.jsonl'
    if out.exists():
        assert out.read_bytes() == raw
    else:
        out.write_bytes(raw)
    manifest = [manifests[i] for i in range(500)]
    mr = (json.dumps(manifest, indent=2)+'\n').encode()
    mp = target/'tiny_500_proof_manifest.json'
    if mp.exists():
        assert mp.read_bytes() == mr
    else:
        mp.write_bytes(mr)
    receipt = dict(state='PASS', rows=500, unique_original_ids=500, original_indices='0..499',
        exact_failure_delta=True, original_system_user_unchanged=True,
        proof_and_comment_bindings_verified=500, releases=releases,
        union_training_path=str(out), union_training_sha256=sha(raw),
        union_proof_manifest_path=str(mp), union_proof_manifest_sha256=sha(mr),
        model_calls=0, compiler_calls=0, observed_unix=time.time())
    rp = target/'union_verification.json'
    if not rp.exists():
        rp.write_text(json.dumps(receipt, indent=2)+'\n')
    print(rp.read_text())

if __name__ == '__main__':
    main()
