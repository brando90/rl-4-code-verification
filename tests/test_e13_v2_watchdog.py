"""Exercise fenced recovery, orphan adoption, process ownership and persistent retry budgets."""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/watchdog_e13v2.py'
SPEC = importlib.util.spec_from_file_location('e13v2_watchdog', SCRIPT)
WD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WD)


def test_fake_mailer_deduplicates_completion(tmp_path):
    mail = tmp_path / 'mail.jsonl'
    script = tmp_path / 'mailer.py'
    script.write_text('import sys\nfrom pathlib import Path\nwith Path(sys.argv[1]).open("a") as f: f.write(sys.stdin.read()+"\\n")\n')
    (tmp_path / 'terminal.json').write_text(json.dumps({'run': 'test', 'status': 'complete', 'message': 'fixture complete'}))
    config = {'mailer': [sys.executable, str(script), str(mail)]}
    WD.check(tmp_path, 'test', config)
    WD.check(tmp_path, 'test', config)
    messages = [json.loads(s) for s in mail.read_text().splitlines()]
    assert len(messages) == 1
    assert messages[0]['to'] == ['brando.science@gmail.com'] and messages[0]['cc'] == []


def test_concurrent_recovery_starts_one_process(tmp_path):
    (tmp_path / 'config.json').write_text(json.dumps({'recover': ['sleep', '60']}))
    command = [sys.executable, str(SCRIPT), '--root', str(tmp_path), '--run', 'test', 'check']
    children = [subprocess.Popen(command, stdout=subprocess.PIPE, text=True) for _ in range(4)]
    receipts = [json.loads(child.communicate(timeout=10)[0]) for child in children]
    assert all(child.returncode == 0 for child in children)
    db = WD.database(tmp_path)
    rows = list(db.execute('SELECT * FROM processes'))
    try:
        assert len(rows) == 1
        assert sum(r['status'] == 'recovery_started_unverified' for r in receipts) == 1
        assert sum(r['status'] == 'owner_alive' for r in receipts) == 3
    finally:
        for row in rows:
            WD.kill_registered(db, 'test', row['pid'])
        db.close()


def test_orphaned_child_is_adopted_without_relaunch(tmp_path):
    launcher = subprocess.run([sys.executable, '-c',
        'import subprocess; p=subprocess.Popen(["sleep","60"],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); print(p.pid)'],
        capture_output=True, text=True, check=True)
    pid = int(launcher.stdout)
    db = WD.database(tmp_path)
    WD.register(db, 'test', 'cell_worker', pid)
    try:
        receipt = WD.check(tmp_path, 'test', {'recover': ['false']})
        assert receipt['status'] == 'adopted_children'
        assert receipt['children_adopted'] == 1
        assert len(list(db.execute('SELECT * FROM processes'))) == 1
    finally:
        WD.kill_registered(db, 'test', pid)
        db.close()


def test_attempt_budget_survives_database_reopen_and_identity_change(tmp_path):
    db = WD.database(tmp_path)
    assert WD.begin(db, 'test', 'cell', 'a' * 64) == 1
    with pytest.raises(RuntimeError, match='retry'):
        WD.begin(db, 'test', 'cell', 'a' * 64)
    WD.finish(db, 'test', 'cell', 1, 'transient_infrastructure')
    db.close()
    db = WD.database(tmp_path)
    with pytest.raises(RuntimeError, match='integrity'):
        WD.begin(db, 'test', 'cell', 'b' * 64)
    assert WD.begin(db, 'test', 'cell', 'a' * 64) == 2
    WD.finish(db, 'test', 'cell', 2, 'transient_infrastructure')
    db.close()
    db = WD.database(tmp_path)
    with pytest.raises(RuntimeError, match='retry'):
        WD.begin(db, 'test', 'cell', 'a' * 64)
    db.close()


def test_deterministic_failure_never_retries(tmp_path):
    db = WD.database(tmp_path)
    WD.begin(db, 'test', 'cell', 'a' * 64)
    WD.finish(db, 'test', 'cell', 1, 'deterministic_resource_limit')
    with pytest.raises(RuntimeError, match='retry'):
        WD.begin(db, 'test', 'cell', 'a' * 64)
    db.close()


@pytest.mark.skipif(not shutil.which('tmux'), reason='owned tmux kill self-test requires tmux')
def test_owned_unique_tmux_kill_case(tmp_path):
    session = 'e13v2-selftest-' + uuid.uuid4().hex
    subprocess.run(['tmux', 'new-session', '-d', '-s', session, 'sleep 60'], check=True)
    db = WD.database(tmp_path)
    try:
        pid = int(subprocess.check_output(['tmux', 'list-panes', '-t', session, '-F', '#{pane_pid}'], text=True))
        item = WD.register(db, 'test', 'owner', pid)
        assert WD.live(item)
        assert not WD.live({**item, 'start_ticks': item['start_ticks'] + 1})
        assert not WD.live({**item, 'boot_id': 'not-this-boot'})
        with pytest.raises(RuntimeError, match='unowned'):
            WD.kill_registered(db, 'other-run', pid)
        subprocess.run(['tmux', 'kill-session', '-t', session], check=True)
        for _ in range(100):
            if not WD.live(item):
                break
            time.sleep(.01)
        assert not WD.live(item)
        assert WD.check(tmp_path, 'test', {})['status'] == 'owner_absent'
    finally:
        subprocess.run(['tmux', 'kill-session', '-t', session], capture_output=True)
        db.close()
