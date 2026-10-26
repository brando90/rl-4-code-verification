"""Publish retained terminal results after verified tests, without changing active runtime source files."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

from technical import ROOT, V3
from cohort import digest
from pilot_dispatch import alive
from progress import refresh
from training_checkpoint import write_new


def publication_tree(repo, relative, paths, *, base='origin/main', temporary_root=None):
    """Overlay owned result files on the latest remote tree without touching the normal index or checkout."""
    base_sha = subprocess.check_output(['git', 'rev-parse', base], cwd=repo, text=True).strip()
    if subprocess.check_output(['git', 'diff', '--name-only', 'HEAD', base_sha, '--', *paths], cwd=repo, text=True):
        raise RuntimeError('remote changed owned result paths; reconcile before publication')
    with tempfile.TemporaryDirectory(dir=temporary_root) as temporary:
        env = {**os.environ, 'GIT_INDEX_FILE': str(Path(temporary) / 'index')}
        def output(*args):
            return subprocess.check_output(['git', *args], cwd=repo, env=env, text=True)
        output('read-tree', base_sha)
        output('add', '--', *paths)
        filenames = output('diff', '--cached', '--name-only', base_sha).splitlines()
        if not filenames or any(not name.startswith(relative + '/') for name in filenames):
            raise RuntimeError('terminal publication path inventory is not exclusively v3')
        diff = output('diff', '--cached', '--no-ext-diff', base_sha)
        if re.search(r'(?:sk-(?:proj-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16})', diff):
            raise RuntimeError('potential credential pattern in staged content; publication stopped')
        output('diff', '--cached', '--check', base_sha)
        tree = output('write-tree').strip()
    return tree, base_sha, filenames


def publish(pid, start_ticks):
    while alive(pid, start_ticks): time.sleep(30)
    refresh()
    terminal = ROOT / 'phase2/pilot_dispatch'
    if not (terminal / 'result.json').exists() and not (terminal / 'error.json').exists():
        raise RuntimeError('dispatcher died without a terminal receipt; publication requires diagnosis')
    repo = V3.parents[2]
    relative = str(V3.relative_to(repo))
    source_paths = [relative + '/phase2', relative + '/tests', relative + '/env.sh']
    if subprocess.check_output(['git', 'status', '--porcelain', '--', *source_paths], cwd=repo, text=True):
        raise RuntimeError('runtime source changed since publication; refuse unattended source commit')
    alias = Path('/lfs/skampere1/0/ultimate-utils'); target = '/lfs/skampere1/0/brando9/ultimate-utils'
    made_alias = False
    if not alias.exists() and not alias.is_symlink():
        alias.symlink_to(target); made_alias = True
    env = {**os.environ, 'CUDA_VISIBLE_DEVICES': '', 'E13_REQUIRE_LEAN_INTEGRATION': '1',
           'PYTHONDONTWRITEBYTECODE': '1',
           'PATH': '/lfs/skampere1/0/brando9/rl4cv_e13v2/venv/bin:' + os.environ['PATH'],
           'PYTEST_ADDOPTS': f'-p no:cacheprovider --basetemp={ROOT}/tmp/pytest_terminal_{os.getpid()}'}
    env.pop('CODEX_HOME', None)
    log = ROOT / 'terminal_tests.log'
    try:
        with log.open('x') as out:
            tested = subprocess.run(['make', 'test'], cwd=repo, env=env, stdout=out, stderr=subprocess.STDOUT, timeout=3600)
    finally:
        if made_alias and alias.is_symlink() and os.readlink(alias) == target: alias.unlink()
    receipt = {'command': 'make test', 'exit_code': tested.returncode, 'log': str(log), 'sha256': digest(log),
               'tail': log.read_text().splitlines()[-8:], 'api_spend_usd': 0, 'finished_unix': time.time()}
    write_new(V3 / 'results/terminal_publication_tests.json', receipt)
    if tested.returncode: raise RuntimeError('terminal tests failed; retained results not pushed')
    paths = [relative + '/results', relative + '/results.md', relative + '/CKPT_factored_pilot.md']
    if (V3 / 'RESULTS_T2_v3.md').exists(): paths.append(relative + '/RESULTS_T2_v3.md')
    subprocess.run(['git', 'fetch', 'origin', 'main'], cwd=repo, check=True)
    tree, base, filenames = publication_tree(repo, relative, paths, temporary_root=ROOT / 'tmp')
    commit = subprocess.check_output(['git', 'commit-tree', tree, '-p', base, '-m',
        'Record Experiment 13 v3 terminal local pilot evidence'], cwd=repo, text=True).strip()
    subprocess.run(['git', 'push', 'origin', commit + ':main'], cwd=repo, check=True)
    write_new(ROOT / 'terminal_publication.json', {'status': 'PUSHED', 'commit': commit, 'files': filenames,
              'api_spend_usd': 0, 'scientific_completion': json.loads((V3 / 'results/live_progress.json').read_text())['status']})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dispatcher-pid', type=int, required=True)
    parser.add_argument('--start-ticks', required=True)
    args = parser.parse_args()
    try: publish(args.dispatcher_pid, args.start_ticks)
    except Exception as exc:
        write_new(ROOT / 'terminal_publication_error.json', {'status': 'NOT_PUBLISHED', 'error_type': type(exc).__name__,
                  'error': str(exc), 'finished_unix': time.time()})
        raise
