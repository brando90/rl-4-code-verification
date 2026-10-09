"""TLDR: Unit tests for experiment 08's shared GPU-admission interface (gpu_lease_e08): lease states (live / released / expired / stale identity), the admission policy (14B all-8 priority only when other users leave 8 devices free; 2-device / 16 h / 32 device-hour limits for experiment 09; only idle unleased devices), and grant/release bookkeeping on a temporary registry. No GPUs or model calls."""
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/scripts"


def load(tmp_path):
    spec = importlib.util.spec_from_file_location("gpu_lease_e08", SCRIPTS / "gpu_lease_e08.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.P = tmp_path; m.REGISTRY = tmp_path / "leases.json"; m.LOCK = tmp_path / "lock"; m.ADMISSION = tmp_path / "admission.json"; m.STATE = tmp_path / "state.json"
    return m


NOW = datetime(2026, 10, 9, 3, 0, tzinfo=timezone.utc)
TABLE_OTHER_USER = {0: set(), 1: set(), 2: set(), 3: set(), 4: {"someone"}, 5: {"someone"}, 6: {"brando9"}, 7: {"brando9"}}
TABLE_ALL_FREE_OF_OTHERS = {0: set(), 1: set(), 2: set(), 3: set(), 4: set(), 5: set(), 6: {"brando9"}, 7: {"brando9"}}
CTX_14B_PENDING = {"eight_done": True, "fourteen_done": False}


def test_lease_states(tmp_path):
    m = load(tmp_path)
    live = {"owner": "e09", "gpus": [1], "since": m.ts(NOW), "expires_utc": m.ts(NOW + timedelta(hours=1)), "released": False, "identity": None}
    assert m.lease_state(live, NOW) == "live"
    assert m.lease_state(dict(live, released=True), NOW) == "released"
    assert m.lease_state(dict(live, expires_utc=m.ts(NOW - timedelta(seconds=1))), NOW) == "expired"
    dead = dict(live, identity={"pid": 2_000_000_000, "pid_start": "1", "boot_id": m.boot_id(), "host": m.os.uname().nodename})
    assert m.lease_state(dead, NOW) == "stale"
    other_boot = dict(live, identity={"pid": m.os.getpid(), "pid_start": m.proc_start(m.os.getpid()), "boot_id": "not-this-boot", "host": m.os.uname().nodename})
    assert m.lease_state(other_boot, NOW) == "stale"
    mine = dict(live, identity=m.identity(m.os.getpid()))
    assert m.lease_state(mine, NOW) == "live"


def test_admission_open_while_other_users_block_14b(tmp_path):
    m = load(tmp_path)
    d = {"ladder_val_x": {"owner": "e08-pipeline", "stage": "ladder_val_x", "gpus": [6], "since": m.ts(NOW), "released": False, "identity": None},
         "ladder_val_y": {"owner": "e08-pipeline", "stage": "ladder_val_y", "gpus": [7], "since": m.ts(NOW), "released": False, "identity": None}}
    a = m.admission("e09", TABLE_OTHER_USER, CTX_14B_PENDING, d, NOW, me_user="brando9")
    assert a["admission"] == "open" and a["candidate_devices"] == [0, 1] and a["fourteen_b"]["pending"] and not a["fourteen_b"]["can_run_now_or_soon"]
    assert a["devices_with_other_users"] == [4, 5]


def test_admission_closed_when_14b_can_run(tmp_path):
    m = load(tmp_path)
    a = m.admission("e09", TABLE_ALL_FREE_OF_OTHERS, CTX_14B_PENDING, {}, NOW, me_user="brando9")
    assert a["admission"] == "closed" and "14B" in a["reason"]
    # 14B not pending (already done): open again
    a2 = m.admission("e09", TABLE_ALL_FREE_OF_OTHERS, {"eight_done": True, "fourteen_done": True}, {}, NOW, me_user="brando9")
    assert a2["admission"] == "open" and a2["candidate_devices"] == [0, 1]
    # 14B running holds everything: nothing idle
    d = {"sft_14B": {"owner": "e08-pipeline", "stage": "sft_14B", "gpus": list(range(8)), "since": m.ts(NOW), "released": False, "identity": None}}
    a3 = m.admission("e09", {i: set() for i in range(8)}, CTX_14B_PENDING, d, NOW, me_user="brando9")
    assert a3["admission"] == "closed" and a3["fourteen_b"]["running"]


def test_grant_limits_and_release(tmp_path):
    m = load(tmp_path)
    rc, out = m.grant("e09", 3, "trajectory", 16.0, None, "b", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d={}, now=NOW)
    assert rc == 3 and "1..2" in out["reason"]
    rc, out = m.grant("e09", 2, "trajectory", 17.0, None, "b", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d={}, now=NOW)
    assert rc == 3 and "ttl" in out["reason"]
    d = {}
    rc, lease = m.grant("e09", 2, "trajectory", 16.0, None, "checkpoint every 50 steps", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d=d, now=NOW)
    assert rc == 0 and lease["gpus"] == [0, 1] and lease["cuda_visible_devices"] == "0,1" and lease["expires_utc"] == m.ts(NOW + timedelta(hours=16))
    d = json.loads((tmp_path / "leases.json").read_text())
    assert m.budget_used_hours(d, "e09", NOW) == 32.0
    rc, out = m.grant("e09", 1, "trajectory", 1.0, None, "b", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d=d, now=NOW)
    assert rc == 3 and "holds 2" in out["reason"]
    # the orchestrator's view: leased devices are not free
    live = m.live_leases(d, NOW)
    assert {g for v in live.values() for g in v["gpus"]} == {0, 1}
    later = NOW + timedelta(hours=1)
    r = m.release(lease["lease_id"], d, now=later)
    assert r["ok"] and not m.live_leases(json.loads((tmp_path / "leases.json").read_text()), later)
    d = json.loads((tmp_path / "leases.json").read_text())
    assert m.budget_used_hours(d, "e09", later) == 2.0          # released: actual 2 devices x 1 h
    rc, out = m.grant("e09", 2, "trajectory", 16.0, None, "b", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d=d, now=later)
    assert rc == 3 and "budget" in out["reason"]
    rc, out = m.grant("e09", 2, "trajectory", 15.0, None, "b", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d=d, now=later)
    assert rc == 0 and out["gpus"] == [0, 1]


def test_grant_denied_when_14b_can_run(tmp_path):
    m = load(tmp_path)
    rc, out = m.grant("e09", 2, "trajectory", 8.0, None, "b", table=TABLE_ALL_FREE_OF_OTHERS, ctx=CTX_14B_PENDING, d={}, now=NOW)
    assert rc == 3 and "14B" in out["reason"] and not (tmp_path / "leases.json").exists()
