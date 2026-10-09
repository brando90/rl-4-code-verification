"""TLDR: Sanitize exact input/runtime/source identities without configuration secrets."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ROOT = REPO.parent
MODEL = Path('/lfs/skampere1/0/brando9/rl4cv_e08/ckpt/1.7B/hf/step_658')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024**2), b''):
            h.update(block)
    return h.hexdigest()


def main():
    hashes = {}
    for line in (MODEL / 'SHA256SUMS').read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        assert '/' not in name and name not in ('.', '..')
        actual = sha(MODEL / name)
        assert actual == expected, f'Initialization file mismatch: {name}'
        hashes[name] = actual
    source = {}
    for root in (ROOT / 'nemo_rl', REPO / 'external/veribench', REPO / 'external/veribench_scorer'):
        source[str(root)] = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    packages = {p.metadata['Name']: p.version for p in importlib.metadata.distributions() if p.metadata['Name']}
    split_root = REPO / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split'
    result = {'written_utc': datetime.now(timezone.utc).isoformat(),
              'python_executable': sys.executable, 'python_version': platform.python_version(),
              'sources': source, 'installed_packages': dict(sorted(packages.items())),
              'initialization_files_sha256': hashes,
              'initialization_identity_sha256': hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
              'inherited_split_artifacts_sha256': {p.name: sha(p) for p in sorted(split_root.glob('*')) if p.is_file()},
              'screening_status': 'Inherited D-013 split/screen receipts preserved; no new external training data or held-out source opened',
              'owned_adapters_sha256': {p.name: sha(p) for p in (HERE / 'adapters').glob('*') if p.is_file()},
              'nemo_uncommitted_diff_sha256': hashlib.sha256(subprocess.check_output(['git', '-C', str(ROOT / 'nemo_rl'), 'diff', '--unified=0'])).hexdigest(),
              'sampler_installed_sha256': sha(ROOT / 'nemo_rl/.venv/lib/python3.12/site-packages/vllm/v1/sample/sampler.py'),
              'scientific_admission': False}
    (HERE / 'results/resolved_identity.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'initialization_files_verified': len(hashes), 'packages': len(packages),
                      'initialization_identity_sha256': result['initialization_identity_sha256']}))


if __name__ == '__main__':
    main()
