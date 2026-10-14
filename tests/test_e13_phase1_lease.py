"""Check device exclusion, foreign reservations, resource accounting and fenced cleanup."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1'
sys.path.insert(0, str(ROOT))
import lease


def setup(tmp_path):
    registry = tmp_path/'leases'; registry.mkdir()
    (registry/'registry.json').write_text(json.dumps({'owner':'e13v2', 'leases':[], 'device_hours':0}))
    foreign = tmp_path/'foreign.json'; foreign.write_text('{}')
    inventory = {'inventory_complete': True, 'host': 'fixture', 'idle_device_indices': [0],
                 'local_storage': {'available_bytes': 1000},
                 'devices': [{'index':0,'uuid':'GPU-fixture','memory_mib':81920}]}
    kw = {'sources':[{'path':str(foreign)}], 'reservation_bindings':[], 'seconds':1800,
          'cumulative_limit_hours':1., 'storage_required_bytes':100, 'minimum_memory_mib':40000, 'now':1000}
    return registry, foreign, inventory, kw


def test_claim_and_release_account_exactly_once(tmp_path):
    root, _, inventory, kw = setup(tmp_path)
    record = lease.claim(root, inventory, 0, **kw)
    with pytest.raises(RuntimeError, match='adoption'):
        lease.claim(root, inventory, 0, **kw)
    held = lease.release(root, record['id'], cleanup_verified=False, now=1100)
    assert held['status'] == 'CLEANUP_REQUIRED'
    released = lease.release(root, record['id'], cleanup_verified=True, now=1180)
    assert released['device_hours'] == pytest.approx(.05)
    lease.release(root, record['id'], cleanup_verified=True, now=2000)
    assert json.loads((root/'registry.json').read_text())['device_hours'] == pytest.approx(.05)


@pytest.mark.parametrize('condition', ['busy','unknown','small','disk','host_ram','budget','reservation','expired_foreign'])
def test_unavailable_or_reserved_device_never_claimed(condition, tmp_path):
    root, foreign, inventory, kw = setup(tmp_path)
    if condition == 'busy': inventory['idle_device_indices'] = []
    if condition == 'unknown': inventory['inventory_complete'] = False
    if condition == 'small': inventory['devices'][0]['memory_mib'] = 16000
    if condition == 'disk': inventory['local_storage']['available_bytes'] = 1
    if condition == 'host_ram': kw['minimum_host_available_bytes'] = 100
    if condition == 'budget': kw['cumulative_limit_hours'] = .1
    if condition == 'reservation':
        foreign.write_text(json.dumps({'reserved': {'host':'fixture','gpus':[0],'owner':'other'}}))
    if condition == 'expired_foreign':
        foreign.write_text(json.dumps({'old': {'host':'fixture','gpus':[0],'owner':'other','expires_unix':1}}))
    with pytest.raises(RuntimeError): lease.claim(root, inventory, 0, **kw)
    assert json.loads((root/'registry.json').read_text())['leases'] == []


def test_released_foreign_device_is_available(tmp_path):
    root, foreign, inventory, kw = setup(tmp_path)
    foreign.write_text(json.dumps({'old': {'released':True,'host':'fixture','gpus':[0],'owner':'other'}}))
    assert lease.claim(root, inventory, 0, **kw)['status'] == 'ACTIVE'


def test_changed_master_reservation_evidence_is_rejected(tmp_path):
    root, foreign, inventory, kw = setup(tmp_path)
    kw['reservation_bindings'] = [{'path':str(foreign), 'sha256':'0'*64}]
    with pytest.raises(RuntimeError, match='reservation evidence'):
        lease.claim(root, inventory, 0, **kw)


def test_cleanup_only_signals_matching_execution_marker():
    from lp1 import cleanup
    marker = 'synthetic-'+uuid.uuid4().hex
    owned = subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'],
                             env={**os.environ, 'E13_EXECUTION_ID':marker}, start_new_session=True)
    other = subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'], start_new_session=True)
    try:
        receipt = cleanup(marker)
        owned.wait(timeout=5)
        assert receipt['verified'] and owned.returncode != 0
        assert other.poll() is None
        assert all(row['pid'] == owned.pid for row in receipt['signals'])
    finally:
        for child in (owned, other):
            if child.poll() is None: child.terminate()
            child.wait(timeout=5)
