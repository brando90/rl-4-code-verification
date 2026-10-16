"""Keep orphan cleanup outside live trees and frozen scientific evidence."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys

import pytest

HERE = Path(__file__).resolve().parents[1] / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3'
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('e08_lean_cleanup', HERE / 'reap_timed_out_lean.py')
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


@pytest.fixture
def fixture(tmp_path):
    root = tmp_path / 'runtime'; root.mkdir()
    proc = tmp_path / 'proc'; proc.mkdir()
    boot = proc / 'sys/kernel/random/boot_id'; boot.parent.mkdir(parents=True); boot.write_text('boot')
    (proc / 'uptime').write_text('2000 2000')
    lean = tmp_path / 'lean'; lean.write_text('fixture executable')
    source = root / 'ladder/validation/jobs/demo_g8_s0/task/verifier/solution.lean'
    source.parent.mkdir(parents=True); source.write_text('example : True := by trivial\n')
    raw = root / 'ladder/validation/raw/gen_demo_g8.jsonl'; raw.parent.mkdir(parents=True)
    raw.write_text(json.dumps({'task_id': 'task', 'sample_idx': 0, 'lean': source.read_text()}) + '\n')
    manifest = {'systems': [{'label': 'demo'}], 'task_ids': ['task'],
                'cells': [{'system': 'demo', 'task_id': 'task', 'sample_idx': 0}]}
    pid = proc / '123'; pid.mkdir()
    fields = ['S', '1'] + ['0'] * 17 + ['100']
    (pid / 'stat').write_text('123 (lean) ' + ' '.join(fields))
    (pid / 'status').write_text('Uid:\t' + '\t'.join([str(os.getuid())] * 4))
    (pid / 'exe').symlink_to(lean)
    (pid / 'cmdline').write_bytes(b'lean\0' + str(source).encode() + b'\0')
    fence = cleanup.Fence(root, manifest, lean, proc)
    return fence, pid, source, raw


def test_exact_raw_cell_is_candidate(fixture):
    fence, _, source, _ = fixture
    c = fence.inspect(123)
    assert c['source'] == str(source) and c['boot_id'] == 'boot' and c['start_ticks'] == '100'


@pytest.mark.parametrize('change', ['live_parent', 'young', 'zombie', 'foreign_uid', 'different_exe',
                                   'extra_arg', 'wrong_hash', 'duplicate_raw', 'symlink_escape', 'namespace'])
def test_rejects_non_candidates(fixture, change):
    fence, pid, source, raw = fixture
    if change in ('live_parent', 'young', 'zombie'):
        fields = (pid / 'stat').read_text().rsplit(')', 1)[1].split()
        if change == 'live_parent': fields[1] = '99'
        if change == 'young': fields[19] = str(int(1999 * os.sysconf('SC_CLK_TCK')))
        if change == 'zombie': fields[0] = 'Z'
        (pid / 'stat').write_text('123 (lean) ' + ' '.join(fields))
    elif change == 'foreign_uid':
        (pid / 'status').write_text('Uid:\t999999 999999 999999 999999')
    elif change == 'different_exe':
        (pid / 'exe').unlink(); (pid / 'exe').symlink_to(sys.executable)
    elif change == 'extra_arg':
        (pid / 'cmdline').write_bytes((pid / 'cmdline').read_bytes() + b'--extra\0')
    elif change == 'wrong_hash': source.write_text('changed')
    elif change == 'duplicate_raw': raw.write_text(raw.read_text() * 2)
    elif change == 'symlink_escape':
        target = fence.root / 'outside.lean'; target.write_text(source.read_text())
        source.unlink(); source.symlink_to(target)
    else:
        target = fence.root / 'namespace_diagnostic/demo/task/0/solution.lean'
        target.parent.mkdir(parents=True); target.write_text(source.read_text())
        (pid / 'cmdline').write_bytes(b'lean\0' + str(target).encode() + b'\0')
    assert cleanup.inspect_or_none(fence, 123) is None


def test_identity_changed_before_signal_is_skipped(fixture, monkeypatch):
    fence, pid, _, _ = fixture
    candidate = fence.inspect(123)
    (pid / 'stat').write_text((pid / 'stat').read_text().replace(' 100', ' 101'))
    calls = []
    monkeypatch.setattr(cleanup.os, 'pidfd_open', lambda _: 44)
    monkeypatch.setattr(cleanup.os, 'close', calls.append)
    monkeypatch.setattr(cleanup.signal, 'pidfd_send_signal', lambda *args: pytest.fail('stale identity signaled'))
    assert cleanup.retire(fence, candidate, lambda: True, grace=0)['signals'] == []
    assert calls == [44]


def test_escalation_rechecks_parent_and_deadline(fixture, monkeypatch):
    fence, pid, _, _ = fixture
    candidate = fence.inspect(123); signals = []
    monkeypatch.setattr(cleanup.os, 'pidfd_open', lambda _: 44)
    monkeypatch.setattr(cleanup.os, 'close', lambda _: None)
    def send(fd, sig):
        assert fd == 44
        signals.append(sig)
        (pid / 'stat').write_text((pid / 'stat').read_text().replace(') S 1 ', ') S 99 '))
    monkeypatch.setattr(cleanup.signal, 'pidfd_send_signal', send)
    result = cleanup.retire(fence, candidate, lambda: True, grace=0)
    assert signals == [signal.SIGTERM] and not result['still_eligible']
    assert cleanup.retire(fence, candidate, lambda: False, grace=0)['signals'] == []


def test_both_phases_and_original_deadline_bound_cleanup(tmp_path):
    (tmp_path / 'recovery_config.json').write_text(json.dumps({'recovery_deadline_unix': 100}))
    for ph in 'ab': (tmp_path / f'phase_{ph}_state.json').write_text(json.dumps({'status': 'RUNNING'}))
    assert cleanup.window_open(tmp_path, 99)
    assert not cleanup.window_open(tmp_path, 100)
    (tmp_path / 'phase_a_state.json').write_text(json.dumps({'status': 'DONE'}))
    assert cleanup.window_open(tmp_path, 99)
    (tmp_path / 'phase_b_state.json').write_text(json.dumps({'status': 'DONE'}))
    assert not cleanup.window_open(tmp_path, 99)
    (tmp_path / 'phase_b_state.json').write_text('{}')
    with pytest.raises(ValueError): cleanup.window_open(tmp_path, 99)
