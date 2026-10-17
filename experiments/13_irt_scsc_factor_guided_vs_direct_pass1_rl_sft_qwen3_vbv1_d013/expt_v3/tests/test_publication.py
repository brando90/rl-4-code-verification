"""Preserve frozen checkout bytes and another writer's index when publishing over remote advances."""
from pathlib import Path
import subprocess
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'phase2'))
from publish_terminal import publication_tree


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


def repository(root, overlap=False):
    git(root, 'init', '-q')
    git(root, 'config', 'user.email', 'fixture@example.invalid')
    git(root, 'config', 'user.name', 'Fixture')
    (root / 'v3').mkdir(); (root / 'v2').mkdir()
    (root / 'v3/result.md').write_text('old\n')
    (root / 'v2/frozen.py').write_text('frozen\n')
    (root / 'other.txt').write_text('old other\n')
    git(root, 'add', '.'); git(root, 'commit', '-qm', 'base')
    base = git(root, 'rev-parse', 'HEAD')
    (root / ('v3/result.md' if overlap else 'other.txt')).write_text('remote advance\n')
    git(root, 'add', '.'); git(root, 'commit', '-qm', 'remote advance')
    remote = git(root, 'rev-parse', 'HEAD')
    # Keep another writer's staged change, with the active checkout at its old revision.
    git(root, 'reset', '--soft', base)
    (root / 'v3/result.md').write_text('measured result\n')
    return remote


def test_unrelated_remote_work_survives_without_checkout_or_index_changes(tmp_path):
    remote = repository(tmp_path)
    original_index = (tmp_path / '.git/index').read_bytes()
    original_files = {p: p.read_bytes() for p in [tmp_path / 'v2/frozen.py', tmp_path / 'other.txt', tmp_path / 'v3/result.md']}
    tree, parent, files = publication_tree(tmp_path, 'v3', ['v3/result.md'], base=remote)
    assert parent == remote and files == ['v3/result.md']
    assert git(tmp_path, 'show', tree + ':other.txt') == 'remote advance'
    assert git(tmp_path, 'show', tree + ':v3/result.md') == 'measured result'
    assert git(tmp_path, 'show', tree + ':v2/frozen.py') == 'frozen'
    assert (tmp_path / '.git/index').read_bytes() == original_index
    assert all(p.read_bytes() == value for p, value in original_files.items())


def test_remote_edit_of_owned_result_requires_reconciliation(tmp_path):
    remote = repository(tmp_path, overlap=True)
    with pytest.raises(RuntimeError, match='owned result paths'):
        publication_tree(tmp_path, 'v3', ['v3/result.md'], base=remote)
