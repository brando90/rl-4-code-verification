"""Fence native publication ownership and require evidence before mail/completion."""
import importlib.util
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import Mock
import pytest

HERE = Path(__file__).resolve().parents[1] / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3'
sys.path.insert(0, str(HERE))
import native_continuation as native
import notify_run as mail
import recovery_watch as watch


def arm(tmp_path, monkeypatch):
    here = tmp_path / 'source'; here.mkdir()
    monkeypatch.setattr(native, 'HERE', here)
    monkeypatch.setattr(native, 'REQUIRED_HASHES', {'native_continuation.py', 'PROTOCOL.md', 'results/frozen.json'})
    hashes = {}
    for name in native.REQUIRED_HASHES:
        p = here / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('frozen\n')
        hashes[name] = native.sha(p)
    config = {'experiment': str(here), 'recovery_deadline_unix': time.time() + 300, 'max_recoveries': 6,
              'candidates': [{'name': 'existing', 'max_attempts': 2}]}
    owner = {'pid': 999999999, 'boot_id': 'old-boot', 'start_ticks': '1'}
    ack = {'owner': owner, 'attempt': 'recovery-02'}
    release = {**ack, 'released': True, 'mode': 'NATIVE_CONTINUATION'}
    record = {**ack, 'schema': 1, 'armed': True, 'armed_unix': time.time(), 'max_recoveries': 6,
              'deadline_unix': config['recovery_deadline_unix'], 'candidate_caps': {'existing': 2},
              'input_sha256': hashes}
    for name, value in [('owner_ack', ack), ('owner_handoff', release), ('native_continuation_arm', record),
                        ('native_continuation_tests', {'status': 'PASS', 'input_sha256': hashes,
                                                      'failed': 0, 'full_suite_passed': 1300})]:
        watch.write(tmp_path / (name + '.json'), value)
    return config, ack, release


def test_explicit_dead_owner_handoff_is_required(tmp_path, monkeypatch):
    config, ack, release = arm(tmp_path, monkeypatch)
    assert native.authorization(tmp_path, config) == 'AUTHORIZED'
    live = watch.identity(os.getpid())
    for name in ('owner_ack', 'owner_handoff', 'native_continuation_arm'):
        p = tmp_path / (name + '.json'); r = watch.read(p); r['owner'] = live; watch.write(p, r)
    assert native.authorization(tmp_path, config) == 'OWNER_ACTIVE'
    r = watch.read(tmp_path / 'owner_handoff.json'); r['attempt'] = 'older'
    watch.write(tmp_path / 'owner_handoff.json', r)
    assert native.authorization(tmp_path, config) == 'INVALID_HANDOFF'


@pytest.mark.parametrize('change,expected', [('deadline', 'DEADLINE_REACHED'), ('caps', 'INVALID_HANDOFF'),
    ('source', 'SOURCE_CHANGED'), ('tests', 'UNTESTED_SOURCE'), ('mail', 'BLOCKED')])
def test_closed_routes_do_not_execute_commands(tmp_path, monkeypatch, change, expected):
    config, _, _ = arm(tmp_path, monkeypatch)
    if change == 'deadline':
        config['recovery_deadline_unix'] = time.time() - 1
        p = tmp_path / 'native_continuation_arm.json'; r = watch.read(p)
        r['deadline_unix'] = config['recovery_deadline_unix']; watch.write(p, r)
    elif change == 'caps': config['candidates'][0]['max_attempts'] += 1
    elif change == 'source': (native.HERE / 'PROTOCOL.md').write_text('changed')
    elif change == 'tests': (tmp_path / 'native_continuation_tests.json').unlink()
    else: watch.write(tmp_path / 'native_continuation_state.json', {'status': 'MAIL_SENDING'})
    command = Mock(); monkeypatch.setattr(native, 'run', command)
    assert native.tick(tmp_path, config) == expected
    command.assert_not_called()


def test_watch_defers_only_healthy_finite_native_route(tmp_path, monkeypatch):
    config, ack, release = arm(tmp_path, monkeypatch)
    now = time.time()
    assert watch.native_continuation_observation(tmp_path, config, ack, release, [], now)['status'] == 'DEFER'
    assert watch.native_continuation_observation(tmp_path, config, ack, release, ['train:CHILD_DEAD'], now)['status'] == 'NEEDS_RECOVERY'
    watch.write(tmp_path / 'native_continuation_state.json', {'status': 'WAITING_NATIVE_WORK', 'checked_unix': now - 901})
    assert watch.native_continuation_observation(tmp_path, config, ack, release, [], now)['status'] == 'NEEDS_RECOVERY'
    watch.write(tmp_path / 'native_continuation_state.json', {'status': 'BLOCKED', 'checked_unix': now})
    assert watch.native_continuation_observation(tmp_path, config, ack, release, [], now)['status'] == 'NEEDS_RECOVERY'


def test_mail_crash_is_not_retried(tmp_path):
    receipt = tmp_path / 'email_done_v3.json'; accepted = []
    def sender(**kwargs):
        assert watch.read(receipt.with_suffix('.sending.json'))['status'] == 'SENDING'
        accepted.append(kwargs['subject'])
        raise RuntimeError('simulated disconnect after server acceptance')
    with pytest.raises(RuntimeError): mail.deliver(receipt, 'DONE', 'body', sender)
    with pytest.raises(AssertionError, match='Ambiguous'): mail.deliver(receipt, 'DONE', 'body', sender)
    assert accepted == ['DONE'] and not receipt.exists()


def test_mail_existing_receipt_must_match_and_prevents_resend(tmp_path):
    receipt = tmp_path / 'email_done_v3.json'; sender = Mock()
    assert mail.deliver(receipt, 'DONE', 'body', sender) == 'SENT'
    assert mail.deliver(receipt, 'DONE', 'body', sender) == 'PREVIOUSLY_SENT'
    assert sender.call_count == 1
    with pytest.raises(AssertionError, match='does not match'):
        mail.deliver(receipt, 'DONE', 'different body', sender)
    assert watch.read(receipt)['all_recipients_accepted']


def test_success_marker_without_published_notification_is_rejected(tmp_path):
    h = tmp_path / 'source'; (h / 'results').mkdir(parents=True)
    watch.write(h / 'results/validation_summary_v3.json', {'known_cells': 17280, 'declared_cells': 17280,
                                                        'systems': {str(i): {} for i in range(16)}})
    watch.write(tmp_path / 'completion_receipt.json', {'status': 'COMPLETE', 'published_commit': 'abc',
        'notification_sent': True, 'training_verified': True, 'namespace_complete': True, 'forecast_assessed': True})
    assert not watch.completed(tmp_path, h)


def test_real_git_publication_and_foreign_index_guard(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'; remote = tmp_path / 'remote.git'; root = tmp_path / 'runtime'
    repo.mkdir(); root.mkdir()
    def git(*args): return subprocess.run(['git', *args], cwd=repo, check=True, capture_output=True, text=True)
    git('init', '-b', 'main'); git('config', 'user.name', 'Native fixture'); git('config', 'user.email', 'fixture@example.invalid')
    subprocess.run(['git', 'init', '--bare', '--initial-branch=main', str(remote)], check=True, capture_output=True)
    git('remote', 'add', 'origin', str(remote))
    p = repo / 'results.json'; p.write_text('{"known": 1}\n')
    git('add', 'results.json'); git('commit', '-m', 'fixture baseline'); git('push', '-u', 'origin', 'main')
    monkeypatch.setattr(native, 'REPO', repo)
    p.write_text('{"known": 2}\n')
    commit = native.publish([p], root, time.time() + 60, 'publish verified fixture')
    assert commit == git('ls-remote', 'origin', 'refs/heads/main').stdout.split()[0]
    assert watch.read(root / 'native_publication_snapshot.json')['sha256']['results.json'] == native.sha(p)
    other = repo / 'foreign.txt'; other.write_text('preserve'); git('add', 'foreign.txt')
    p.write_text('{"known": 3}\n')
    with pytest.raises(AssertionError, match='Existing staged work'):
        native.publish([p], root, time.time() + 60, 'must not publish')
    assert git('diff', '--cached', '--name-only').stdout.strip() == 'foreign.txt'
    assert git('rev-parse', 'HEAD').stdout.strip() == commit


def test_native_tick_publishes_only_after_validation_and_only_on_events(tmp_path, monkeypatch):
    config, _, _ = arm(tmp_path, monkeypatch)
    import analyze_validation
    here = native.HERE
    watch.write(here / 'results/ladder_manifest_v3.json', {'systems': []})
    watch.write(here / 'results/validation_summary_v3.json', {'systems': {}, 'known_cells': 8640})
    # Fixture science is intentionally synthetic; only ordering/ownership runs here.
    monkeypatch.setattr(native, 'authorization', lambda *_: 'AUTHORIZED')
    monkeypatch.setattr(native, 'progress', lambda *_: ({'a': {'status': 'DONE'}, 'b': {'status': 'RUNNING'}}, {}, ['done']))
    order = []
    monkeypatch.setattr(analyze_validation, 'main', lambda: order.append('analyze'))
    monkeypatch.setattr(native, 'validate_partial', lambda *args: order.append('validate'))
    monkeypatch.setattr(native, 'update_ledger', lambda *args: order.append('ledger'))
    monkeypatch.setattr(native, 'publication_paths', lambda *args: [])
    def publish(*args): order.append('publish'); return 'verified-commit'
    monkeypatch.setattr(native, 'publish', publish)
    assert native.tick(tmp_path, config) == 'PUBLISHED_NATIVE_PROGRESS'
    assert order == ['analyze', 'validate', 'ledger', 'publish']
    assert native.tick(tmp_path, config) == 'WAITING_NATIVE_WORK'
    assert order == ['analyze', 'validate', 'ledger', 'publish']


def test_failed_validation_never_publishes_or_sends(tmp_path, monkeypatch):
    config, _, _ = arm(tmp_path, monkeypatch)
    import analyze_validation
    watch.write(native.HERE / 'results/ladder_manifest_v3.json', {'systems': []})
    watch.write(native.HERE / 'results/validation_summary_v3.json', {'systems': {}, 'known_cells': 8640})
    monkeypatch.setattr(native, 'authorization', lambda *_: 'AUTHORIZED')
    monkeypatch.setattr(native, 'progress', lambda *_: ({'a': {'status': 'DONE'}, 'b': {'status': 'DONE'}}, {}, ['done']))
    monkeypatch.setattr(analyze_validation, 'main', lambda: None)
    def reject(*args): raise AssertionError('native evidence mismatch')
    monkeypatch.setattr(native, 'validate_partial', reject)
    publish = Mock(); command = Mock()
    monkeypatch.setattr(native, 'publish', publish); monkeypatch.setattr(native, 'run', command)
    with pytest.raises(AssertionError, match='mismatch'): native.tick(tmp_path, config)
    publish.assert_not_called(); command.assert_not_called()
    assert watch.read(tmp_path / 'native_continuation_state.json')['status'] == 'BLOCKED'
    assert not (tmp_path / 'completion_receipt.json').exists()


def test_complete_follows_science_push_mail_and_notification_push(tmp_path, monkeypatch):
    config, _, _ = arm(tmp_path, monkeypatch)
    import analyze_validation
    import finalize_results
    here = native.HERE; events = []
    watch.write(here / 'results/ladder_manifest_v3.json', {'systems': []})
    watch.write(here / 'results/validation_summary_v3.json', {'systems': {}, 'known_cells': 17280})
    watch.write(here / 'results/completion_validation_v3.json', {'known_cells': 17280, 'declared_cells': 17280, 'systems': 16})
    (tmp_path / 'completion_email_body.txt').write_text('checked body')
    monkeypatch.setattr(native, 'authorization', lambda *_: 'AUTHORIZED')
    monkeypatch.setattr(native, 'progress', lambda *_: ({'a': {'status': 'DONE'}, 'b': {'status': 'DONE'}}, {}, ['done']))
    monkeypatch.setattr(analyze_validation, 'main', lambda: events.append('analyze'))
    monkeypatch.setattr(finalize_results, 'main', lambda **kwargs: events.append('finalize'))
    monkeypatch.setattr(native, 'validate_partial', lambda *args: events.append('validate'))
    monkeypatch.setattr(native, 'update_ledger', lambda *args: events.append('ledger'))
    monkeypatch.setattr(native, 'publication_paths', lambda *args: [])
    def publish(*args):
        assert not (tmp_path / 'completion_receipt.json').exists()
        if 'science_push' not in events: events.append('science_push'); return 'science'
        assert watch.read(here / 'results/email_done_v3.json')['status'] == 'SENT'
        events.append('notification_push'); return 'notification'
    monkeypatch.setattr(native, 'publish', publish)
    def command(argv, *args, **kwargs):
        if argv[:2] == ['make', 'test']: events.append('tests')
        elif 'DONE' in argv:
            assert events[-1] == 'science_push'
            assert watch.read(tmp_path / 'native_continuation_state.json')['status'] == 'MAIL_SENDING'
            events.append('mail')
            watch.write(here / 'results/email_done_v3.json', {'status': 'SENT', 'all_recipients_accepted': True,
                'subject': '[RUN DONE] rl4cv-e08-v3-sft-continuation: COMPLETE',
                'to': mail.TO, 'cc': mail.CC, 'body': 'checked body'})
        elif argv == ['crontab', '-l']:
            assert watch.read(tmp_path / 'completion_receipt.json')['notification_commit'] == 'notification'
            return '0 * * * * foreign\n* * * * * own # rl4cv-e08-v3-native-continuation'
        elif argv[0] == 'crontab':
            assert Path(argv[1]).read_text() == '0 * * * * foreign\n'; events.append('retire')
        else: raise AssertionError(argv)
    monkeypatch.setattr(native, 'run', command)
    assert native.tick(tmp_path, config) == 'COMPLETE'
    assert events == ['analyze', 'validate', 'finalize', 'tests', 'ledger', 'science_push', 'mail', 'notification_push', 'retire']
    receipt = watch.read(tmp_path / 'completion_receipt.json')
    assert receipt['science_commit'] == 'science' and receipt['published_commit'] == receipt['notification_commit'] == 'notification'


def test_partial_collector_output_is_unknown_until_native_done(tmp_path):
    from analyze_validation import completed_scored_rows
    path = tmp_path / 'partial.jsonl'; path.write_text('{"task_id":')
    assert completed_scored_rows(path, 'RUNNING') == []
    with pytest.raises(json.JSONDecodeError): completed_scored_rows(path, 'DONE')


def test_persisted_mail_receipt_resumes_without_another_delivery(tmp_path, monkeypatch):
    config, ack, release = arm(tmp_path, monkeypatch)
    (tmp_path / 'completion_email_body.txt').write_text('checked body')
    sender = Mock()
    mail.deliver(native.HERE / 'results/email_done_v3.json',
                 '[RUN DONE] rl4cv-e08-v3-sft-continuation: COMPLETE', 'checked body', sender)
    for status in ('MAIL_SENDING', 'NOTIFIED'):
        watch.write(tmp_path / 'native_continuation_state.json', {'status': status, 'checked_unix': time.time()})
        assert native.authorization(tmp_path, config) == 'AUTHORIZED'
        assert watch.native_continuation_observation(tmp_path, config, ack, release, [], time.time())['status'] == 'DEFER'
    assert sender.call_count == 1


def test_publication_lock_restores_descriptors_on_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(native, 'LOCK_FDS', ())
    with pytest.raises(RuntimeError):
        with native.publication_lock(tmp_path):
            assert len(native.LOCK_FDS) == 1
            raise RuntimeError('fail inside lock')
    assert native.LOCK_FDS == ()
    with native.publication_lock(tmp_path): assert len(native.LOCK_FDS) == 1
    assert native.LOCK_FDS == ()


def test_surviving_command_keeps_owner_lock_after_parent_dies(tmp_path):
    """A live Git/test/mail child must fence a second cron after its owner is killed."""
    lock_path = tmp_path / 'recovery.lock'; child_path = tmp_path / 'child.json'
    child_code = ('import json,os,time; from pathlib import Path; from recovery_watch import identity; '
                  f'Path({str(child_path)!r}).write_text(json.dumps(identity(os.getpid()))); time.sleep(30)')
    wrapper = tmp_path / 'parent.py'
    wrapper.write_text('import fcntl,sys,time\nfrom pathlib import Path\n'
        f'sys.path.insert(0,{str(HERE)!r})\nimport native_continuation as n\n'
        f'n.REPO=Path({str(HERE)!r})\nlock=open({str(lock_path)!r},"a")\n'
        'fcntl.flock(lock,fcntl.LOCK_EX)\nn.LOCK_FDS=(lock.fileno(),)\n'
        f'n.run([sys.executable,"-c",{child_code!r}],Path({str(tmp_path)!r}),time.time()+60)\n')
    parent = subprocess.Popen([sys.executable, str(wrapper)])
    child = None
    try:
        until = time.monotonic() + 10
        while not child_path.exists() and time.monotonic() < until: time.sleep(.05)
        assert child_path.exists()
        child = watch.read(child_path); assert watch.alive(child)
        parent.kill(); parent.wait(timeout=5)
        with lock_path.open('a') as lock:
            with pytest.raises(BlockingIOError): fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        if parent.poll() is None: parent.kill(); parent.wait(timeout=5)
        if child and watch.alive(child):
            import signal
            fd = os.pidfd_open(child['pid'])
            try:
                if watch.alive(child): signal.pidfd_send_signal(fd, signal.SIGTERM)
            finally: os.close(fd)
        until = time.monotonic() + 5
        while child and watch.alive(child) and time.monotonic() < until: time.sleep(.05)
    with lock_path.open('a') as lock: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)


def test_publication_retry_is_finite_and_cannot_send_mail(tmp_path, monkeypatch):
    config, _, _ = arm(tmp_path, monkeypatch)
    import analyze_validation
    watch.write(native.HERE / 'results/ladder_manifest_v3.json', {'systems': []})
    watch.write(native.HERE / 'results/validation_summary_v3.json', {'systems': {}, 'known_cells': 8640})
    monkeypatch.setattr(native, 'authorization', lambda *_: 'AUTHORIZED')
    monkeypatch.setattr(native, 'progress', lambda *_: ({'a': {'status': 'DONE'}, 'b': {'status': 'RUNNING'}}, {}, ['done']))
    monkeypatch.setattr(analyze_validation, 'main', lambda: None)
    monkeypatch.setattr(native, 'validate_partial', lambda *args: None)
    monkeypatch.setattr(native, 'update_ledger', lambda *args: None)
    monkeypatch.setattr(native, 'publication_paths', lambda *args: [])
    monkeypatch.setattr(native, 'publish', Mock(side_effect=native.PublicationFailure('transient Git failure')))
    command = Mock(); monkeypatch.setattr(native, 'run', command)
    for i, expected in enumerate(('RETRY_PUBLICATION', 'RETRY_PUBLICATION', 'BLOCKED'), 1):
        with pytest.raises(native.PublicationFailure): native.tick(tmp_path, config)
        state = watch.read(tmp_path / 'native_continuation_state.json')
        assert state['status'] == expected and state['publication_failures'] == i
    command.assert_not_called()


def test_complete_receipt_short_circuits_all_actions(tmp_path, monkeypatch):
    monkeypatch.setattr(native, 'completed', lambda *_: True)
    command = Mock(); monkeypatch.setattr(native, 'run', command)
    auth = Mock(); monkeypatch.setattr(native, 'authorization', auth)
    retire = Mock(); monkeypatch.setattr(native, 'retire_owned_crons', retire)
    assert native.tick(tmp_path, {}) == 'COMPLETE'
    command.assert_not_called(); auth.assert_not_called()
    retire.assert_called_once_with(tmp_path)
    assert watch.read(tmp_path / 'native_continuation_state.json')['status'] == 'COMPLETE'


def test_locked_dependency_paths_exist():
    assert all((HERE / p).is_file() for p in native.REQUIRED_HASHES)


def test_upstream_merge_cannot_push_unvalidated_report_bytes(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'; remote = tmp_path / 'remote.git'; peer = tmp_path / 'peer'
    root = tmp_path / 'runtime'; repo.mkdir(); root.mkdir()
    def git(cwd, *args):
        return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True)
    git(repo, 'init', '-b', 'main')
    git(repo, 'config', 'user.name', 'fixture'); git(repo, 'config', 'user.email', 'fixture@example.invalid')
    git(repo, 'init', '--bare', '--initial-branch=main', str(remote))
    git(repo, 'remote', 'add', 'origin', str(remote))
    p = repo / 'results.md'; baseline = 'first\n' + 'middle\n' * 20 + 'last\n'; p.write_text(baseline)
    git(repo, 'add', 'results.md'); git(repo, 'commit', '-m', 'baseline'); git(repo, 'push', '-u', 'origin', 'main')
    git(repo, 'clone', str(remote), str(peer))
    git(peer, 'config', 'user.name', 'fixture'); git(peer, 'config', 'user.email', 'fixture@example.invalid')
    (peer / 'results.md').write_text(baseline.replace('last', 'upstream'))
    git(peer, 'commit', '-am', 'upstream edit'); git(peer, 'push', 'origin', 'main')
    remote_commit = git(peer, 'rev-parse', 'HEAD').stdout.strip()
    p.write_text(baseline.replace('first', 'validated local'))
    monkeypatch.setattr(native, 'REPO', repo)
    watch.write(root / 'native_continuation_arm.json', {'input_sha256': {}})
    real_run = native.run
    monkeypatch.setattr(native, 'run', lambda command, *args, **kwargs:
                        None if command == ['make', 'test'] else real_run(command, *args, **kwargs))
    with pytest.raises(native.PublicationFailure, match='Merge changed validated artifact'):
        native.publish([p], root, time.time() + 60, 'checked local report')
    assert git(repo, 'ls-remote', 'origin', 'refs/heads/main').stdout.split()[0] == remote_commit
    assert 'validated local' in p.read_text() and 'upstream' in p.read_text()
    assert len(git(repo, 'rev-list', '--parents', '-n', '1', 'HEAD').stdout.split()) == 3


@pytest.mark.parametrize('exit_code,age,matching,expected', [
    (0, 10, True, 'EXITED_AWAITING_SCHEDULER'), (0, 181, True, 'CHILD_DEAD'),
    (1, 10, True, 'CHILD_DEAD'), (0, 10, False, 'CHILD_DEAD')])
def test_successful_exit_handoff_is_exact_and_bounded(tmp_path, exit_code, age, matching, expected):
    now = time.time(); owner = watch.identity(os.getpid())
    dead = {'pid': 999999999, 'boot_id': 'old-boot', 'start_ticks': '1'}
    receipt = tmp_path / 'exit.json'
    watch.write(receipt, {'identity': dead if matching else owner, 'exit_code': exit_code, 'ended_unix': now - age})
    watch.write(tmp_path / 'phase_a_state.json', {'status': 'RUNNING', 'identity': owner, 'jobs': {
        'score_fixture': {'status': 'RUNNING', 'identity': dead, 'exit_receipt': str(receipt)}}})
    assert watch.phase_observation(tmp_path, 'a', now)['jobs']['score_fixture']['status'] == expected


def test_native_successful_exit_waits_without_publication_or_failure(tmp_path, monkeypatch):
    config, _, _ = arm(tmp_path, monkeypatch)
    def pending(*args): raise native.NativeHandoffPending('successful native exit')
    monkeypatch.setattr(native, 'progress', pending)
    command = Mock(); monkeypatch.setattr(native, 'run', command)
    assert native.tick(tmp_path, config) == 'WAITING_NATIVE_HANDOFF'
    command.assert_not_called()
    assert watch.read(tmp_path / 'native_continuation_state.json').get('publication_failures', 0) == 0


def test_verified_alternate_capacity_event_wakes_existing_inventory(tmp_path, monkeypatch):
    config, ack, release = arm(tmp_path, monkeypatch)
    record = watch.read(tmp_path / 'native_continuation_arm.json')
    record['capacity_baseline'] = {'sequence': 4, 'fingerprint': 'unavailable'}
    watch.write(tmp_path / 'native_continuation_arm.json', record)
    route = {'eligible': True, 'alternates': {'slurm': {'nodes': ['ampere1'], 'account': 'infolab'}}}
    event = {'route': route, 'sequence': 5, 'attempt': ack['attempt'],
             'deadline_unix': config['recovery_deadline_unix'], 'observed_unix': time.time(),
             'fingerprint': native.hashlib.sha256(json.dumps(route, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}
    watch.write(tmp_path / 'external_capacity_event.json', event)
    assert watch.native_continuation_observation(tmp_path, config, ack, release, [], time.time())['reason'] == 'eligible_alternate_capacity_changed'
    event['attempt'] = 'older'; watch.write(tmp_path / 'external_capacity_event.json', event)
    assert watch.native_continuation_observation(tmp_path, config, ack, release, [], time.time())['status'] == 'DEFER'


@pytest.mark.parametrize('stage', ['analyze', 'finalize'])
def test_whole_tick_deadline_stops_stalled_work_before_publication(tmp_path, monkeypatch, stage):
    config, _, _ = arm(tmp_path, monkeypatch)
    import analyze_validation
    import finalize_results
    watch.write(native.HERE / 'results/ladder_manifest_v3.json', {'systems': []})
    watch.write(native.HERE / 'results/validation_summary_v3.json', {'systems': {}, 'known_cells': 17280})
    monkeypatch.setattr(native, 'authorization', lambda *_: 'AUTHORIZED')
    monkeypatch.setattr(native, 'progress', lambda *_: ({'a': {'status': 'DONE'}, 'b': {'status': 'DONE'}}, {}, ['done']))
    entered = tmp_path / 'entered'; forbidden = tmp_path / 'published'
    def stall(**kwargs):
        entered.touch(); time.sleep(30)
    monkeypatch.setattr(analyze_validation, 'main', stall if stage == 'analyze' else lambda: None)
    monkeypatch.setattr(finalize_results, 'main', stall if stage == 'finalize' else lambda **kwargs: None)
    monkeypatch.setattr(native, 'validate_partial', lambda *args: None)
    monkeypatch.setattr(native, 'publish', lambda *args: forbidden.touch())
    monkeypatch.setattr(native, 'run', lambda *args, **kwargs: forbidden.touch())
    started = time.monotonic()
    with pytest.raises(TimeoutError, match='deadline'):
        native.supervise(lambda: native.tick(tmp_path, config), time.time() + 1)
    assert time.monotonic() - started < 5 and entered.exists() and not forbidden.exists()
    with native.publication_lock(tmp_path): pass


def test_whole_tick_deadline_bounds_publication_lock_wait(tmp_path):
    entered = tmp_path / 'entered'
    def action():
        with native.publication_lock(tmp_path): entered.touch()
    with (tmp_path / 'results_publication.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with pytest.raises(TimeoutError): native.supervise(action, time.time() + .5)
    assert not entered.exists()


def test_supervisor_cleans_orphan_commands_but_preserves_external_child(tmp_path, monkeypatch):
    child_path = tmp_path / 'orphan.json'; lock_path = tmp_path / 'recovery.lock'
    external = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
    child = None
    try:
        with lock_path.open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            monkeypatch.setattr(native, 'LOCK_FDS', (lock.fileno(),))
            def action():
                code = ('import json,os,time; from pathlib import Path; from recovery_watch import identity; '
                        f'Path({str(child_path)!r}).write_text(json.dumps(identity(os.getpid()))); time.sleep(30)')
                subprocess.Popen([sys.executable, '-c', code], cwd=HERE, pass_fds=native.LOCK_FDS)
                until = time.monotonic() + 5
                while not child_path.exists() and time.monotonic() < until: time.sleep(.02)
                assert child_path.exists()
                # Simulate a checksum caller exiting while its command still runs.
            native.supervise(action, time.time() + 10)
        child = watch.read(child_path)
        until = time.monotonic() + 5
        while watch.alive(child) and time.monotonic() < until: time.sleep(.02)
        assert not watch.alive(child) and external.poll() is None
        with lock_path.open('a') as lock: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        external.terminate(); external.wait(timeout=5)


def test_expired_cli_allows_only_verified_completion_cleanup(tmp_path, monkeypatch):
    watch.write(tmp_path / 'recovery_config.json', {'recovery_deadline_unix': time.time() - 10})
    monkeypatch.setattr(sys, 'argv', ['native_continuation.py', '--root', str(tmp_path)])
    monkeypatch.setattr(native, 'completed', lambda *_: True)
    monkeypatch.setattr(native, 'authorization', lambda *_: pytest.fail('Expired completion must not authorize work'))
    monkeypatch.setattr(native, 'retire_owned_crons', lambda root: (root / 'retired').touch())
    native.main()
    assert (tmp_path / 'retired').exists()
    assert watch.read(tmp_path / 'native_continuation_state.json')['status'] == 'COMPLETE'
