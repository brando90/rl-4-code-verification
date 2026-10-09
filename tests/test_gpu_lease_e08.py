"""TLDR: Unit tests for experiment 08's shared GPU-admission interface (gpu_lease_e08): lease states (live / released / expired / stale identity), the admission policy (14B all-8 priority only when other users leave 8 devices free; 2-device / 16 h / 32 device-hour limits for experiment 09; only idle unleased devices), and grant/release bookkeeping on a temporary registry. No GPUs or model calls."""
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/scripts"


ALIVE_PID, DEAD_PID = 4242, 2_000_000_000


def hermetic(m, tmp_path):
    """No /proc, no uname, no $USER: inject boot / host / process-start identities and the test user (production keeps the real Linux checks)."""
    m.P = tmp_path; m.REGISTRY = tmp_path / "leases.json"; m.LOCK = tmp_path / "lock"; m.ADMISSION = tmp_path / "admission.json"; m.STATE = tmp_path / "state.json"
    m.boot_id = lambda: "boot-test"
    m.hostname = lambda: "host-test"
    m.proc_start = lambda pid: {ALIVE_PID: "777"}.get(int(pid))
    m.ME_USER = "brando9"
    return m


def load(tmp_path):
    spec = importlib.util.spec_from_file_location("gpu_lease_e08", SCRIPTS / "gpu_lease_e08.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return hermetic(m, tmp_path)


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
    dead = dict(live, identity={"pid": DEAD_PID, "pid_start": "1", "boot_id": "boot-test", "host": "host-test"})
    assert m.lease_state(dead, NOW) == "stale"
    other_boot = dict(live, identity={"pid": ALIVE_PID, "pid_start": "777", "boot_id": "not-this-boot", "host": "host-test"})
    assert m.lease_state(other_boot, NOW) == "stale"
    other_host = dict(live, identity={"pid": ALIVE_PID, "pid_start": "777", "boot_id": "boot-test", "host": "elsewhere"})
    assert m.lease_state(other_host, NOW) == "stale"
    restarted = dict(live, identity={"pid": ALIVE_PID, "pid_start": "1", "boot_id": "boot-test", "host": "host-test"})   # pid reused by a newer process
    assert m.lease_state(restarted, NOW) == "stale"
    mine = dict(live, identity=m.identity(ALIVE_PID))
    assert mine["identity"] == {"pid": ALIVE_PID, "pid_start": "777", "boot_id": "boot-test", "host": "host-test"} and m.lease_state(mine, NOW) == "live"


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
    me = ALIVE_PID
    rc, out = m.grant("e09", 3, "trajectory", 16.0, me, "b", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d={}, now=NOW)
    assert rc == 3 and "1..2" in out["reason"]
    rc, out = m.grant("e09", 2, "trajectory", 17.0, me, "b", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d={}, now=NOW)
    assert rc == 3 and "ttl" in out["reason"]
    d = {}
    rc, out = m.grant("e09", 2, "trajectory", 16.0, None, "b", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d={}, now=NOW)
    assert rc == 3 and "--pid" in out["reason"]                 # a real lease is PID-bound
    rc, lease = m.grant("e09", 2, "trajectory", 16.0, me, "checkpoint every 50 steps", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d=d, now=NOW)
    assert rc == 0 and lease["gpus"] == [0, 1] and lease["cuda_visible_devices"] == "0,1" and lease["expires_utc"] == m.ts(NOW + timedelta(hours=16))
    d = json.loads((tmp_path / "leases.json").read_text())
    assert m.budget_used_hours(d, "e09", NOW) == 32.0
    rc, out = m.grant("e09", 1, "trajectory", 1.0, me, "b", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d=d, now=NOW)
    assert rc == 3 and "holds 2" in out["reason"]
    # the orchestrator's view: leased devices are not free
    live = m.live_leases(d, NOW)
    assert {g for v in live.values() for g in v["gpus"]} == {0, 1}
    later = NOW + timedelta(hours=1)
    r = m.release(lease["lease_id"], d, now=later)
    assert r["ok"] and not m.live_leases(json.loads((tmp_path / "leases.json").read_text()), later)
    d = json.loads((tmp_path / "leases.json").read_text())
    assert m.budget_used_hours(d, "e09", later) == 2.0          # released: actual 2 devices x 1 h
    rc, out = m.grant("e09", 2, "trajectory", 16.0, me, "b", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d=d, now=later)
    assert rc == 3 and "budget" in out["reason"]
    rc, out = m.grant("e09", 2, "trajectory", 15.0, me, "b", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d=d, now=later)
    assert rc == 0 and out["gpus"] == [0, 1]


def test_grant_denied_when_14b_can_run(tmp_path):
    m = load(tmp_path)
    rc, out = m.grant("e09", 2, "trajectory", 8.0, ALIVE_PID, "b", table=TABLE_ALL_FREE_OF_OTHERS, ctx=CTX_14B_PENDING, d={}, now=NOW)
    assert rc == 3 and "14B" in out["reason"] and not (tmp_path / "leases.json").exists()


# ---------------------------------------------------------------- fail-closed device inventory and provisioning holds
def fake_runner(dev_rc=0, dev_out="0, GPU-aaaaaaaa-1111\n1, GPU-bbbbbbbb-2222\n", app_rc=0, app_out="", ps=None, timeout=False):
    def runner(args):
        if timeout:
            raise RuntimeError("should have been converted")  # replaced below
        if args[1] == "--query-gpu=index,uuid":
            return dev_rc, dev_out
        if args[1] == "--query-compute-apps=gpu_uuid,pid":
            return app_rc, app_out
        if args[0] == "ps":
            return (ps or {}).get(args[-1], (1, ""))
        raise AssertionError(args)
    return runner


def test_gpu_table_happy_path(tmp_path):
    m = load(tmp_path)
    r = fake_runner(app_out="GPU-bbbbbbbb-2222, 4242\n", ps={"4242": (0, "someone\n")})
    assert m.gpu_table(r) == {0: set(), 1: {"someone"}}


def test_gpu_table_fails_closed(tmp_path):
    m = load(tmp_path)
    import pytest
    with pytest.raises(m.GpuStateUnknown):
        m.gpu_table(fake_runner(dev_rc=1))
    with pytest.raises(m.GpuStateUnknown):                      # device query ok, compute-app query failed
        m.gpu_table(fake_runner(app_rc=15))
    with pytest.raises(m.GpuStateUnknown):                      # malformed device row
        m.gpu_table(fake_runner(dev_out="0, GPU-aaaaaaaa-1111\n[Not Supported]\n"))
    with pytest.raises(m.GpuStateUnknown):                      # compute app on an unrecognized uuid
        m.gpu_table(fake_runner(app_out="GPU-cccccccc-3333, 17\n", ps={"17": (0, "x\n")}))
    with pytest.raises(m.GpuStateUnknown):                      # partial/malformed compute row
        m.gpu_table(fake_runner(app_out="GPU-aaaaaaaa-1111\n"))
    with pytest.raises(m.GpuStateUnknown):                      # owner unresolved (process vanished)
        m.gpu_table(fake_runner(app_out="GPU-aaaaaaaa-1111, 99\n", ps={"99": (1, "")}))
    with pytest.raises(m.GpuStateUnknown):                      # no devices at all
        m.gpu_table(fake_runner(dev_out=""))
    def timing_out(args):
        raise m.GpuStateUnknown("nvidia-smi failed to run: TimeoutExpired")
    with pytest.raises(m.GpuStateUnknown):
        m.gpu_table(timing_out)


def test_admission_and_grant_fail_closed_on_unknown_gpu_state(tmp_path, monkeypatch):
    m = load(tmp_path)
    monkeypatch.setattr(m, "gpu_table", lambda runner=None: (_ for _ in ()).throw(m.GpuStateUnknown("compute-apps exit 15")))
    a = m.admission("e09", None, CTX_14B_PENDING, {}, NOW, me_user="brando9")
    assert a["admission"] == "closed" and a.get("gpu_state_unknown") and "failing closed" in a["reason"]
    rc, out = m.grant("e09", 2, "trajectory", 8.0, ALIVE_PID, "b", table=None, ctx=CTX_14B_PENDING, d={}, now=NOW)
    assert rc == 3 and "failing closed" in out["reason"] and not (tmp_path / "leases.json").exists()


def test_hold_is_bounded_superseded_and_withdrawn(tmp_path):
    m = load(tmp_path)
    rc, out = m.grant("e09", 2, m.HOLD_KIND, 5.0, None, "provisioning", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d={}, now=NOW)
    assert rc == 3 and "4.0" in out["reason"]                     # hold ttl capped at 4 h
    rc, hold = m.grant("e09", 2, m.HOLD_KIND, 2.0, None, "provisioning", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d={}, now=NOW)
    assert rc == 0 and hold["gpus"] == [0, 1] and hold["identity"] is None and hold["blocks_14b"] is False
    d = json.loads((tmp_path / "leases.json").read_text())
    assert m.budget_used_hours(d, "e09", NOW) == 0.0            # a hold costs no training budget
    assert m.hold_hours_used(d, "e09", NOW) == 2.0
    # the orchestrator's inference view: held devices are reserved
    assert {g for v in m.live_leases(d, NOW).values() for g in v["gpus"]} == {0, 1}
    # a real request from the same owner supersedes the hold and prefers its devices
    rc, real = m.grant("e09", 2, "trajectory", 16.0, ALIVE_PID, "step boundary", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d=d, now=NOW + timedelta(minutes=30))
    assert rc == 0 and real["gpus"] == [0, 1] and real["identity"]["pid"] == ALIVE_PID and real["superseded_holds"] == [hold["lease_id"]]
    d = json.loads((tmp_path / "leases.json").read_text())
    assert d[hold["lease_id"]]["released"] and m.lease_state(d[real["lease_id"]], NOW + timedelta(minutes=31)) == "live"
    # hold refresh loop is bounded by the hold budget
    d2 = {}
    for i in range(2):
        rc, h = m.grant("e09", 2, m.HOLD_KIND, 4.0, None, "p", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d=d2, now=NOW + timedelta(hours=4 * i))
        assert rc == 0
        d2 = json.loads((tmp_path / "leases.json").read_text())
    rc, out = m.grant("e09", 2, m.HOLD_KIND, 1.0, None, "p", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d=d2, now=NOW + timedelta(hours=8))
    assert rc == 3 and "hold budget" in out["reason"]
    # 14B becomes genuinely admissible: the live hold is withdrawn automatically, admission closes
    d3 = {}
    rc, h = m.grant("e09", 2, m.HOLD_KIND, 2.0, None, "p", table=TABLE_OTHER_USER, ctx=CTX_14B_PENDING, d=d3, now=NOW)
    d3 = json.loads((tmp_path / "leases.json").read_text())
    a = m.admission("e09", TABLE_ALL_FREE_OF_OTHERS, CTX_14B_PENDING, d3, NOW + timedelta(minutes=5), me_user="brando9")
    assert a["admission"] == "closed" and a.get("holds_withdrawn")
    d3 = json.loads((tmp_path / "leases.json").read_text())
    assert d3[h["lease_id"]]["released"] and "withdrawn" in d3[h["lease_id"]]["note"]


def test_orchestrator_14b_gate_ignores_holds_but_inference_respects_them(tmp_path):
    m = load(tmp_path)
    spec = importlib.util.spec_from_file_location("pipeline_e08", SCRIPTS / "pipeline_e08.py")
    pl = importlib.util.module_from_spec(spec); spec.loader.exec_module(pl)
    hermetic(pl.GL, tmp_path)
    d = {"e09-hold-x": {"owner": "e09", "kind": m.HOLD_KIND, "stage": m.HOLD_KIND, "gpus": [0, 1], "since": m.ts(NOW), "expires_utc": m.ts(NOW + timedelta(hours=2)), "released": False, "identity": None},
         "e09-real-y": {"owner": "e09", "kind": "trajectory", "stage": "trajectory", "gpus": [2], "since": m.ts(NOW), "expires_utc": m.ts(NOW + timedelta(hours=2)), "released": False, "identity": m.identity(ALIVE_PID)},
         "e09-dead-z": {"owner": "e09", "kind": "trajectory", "stage": "trajectory", "gpus": [3], "since": m.ts(NOW), "expires_utc": m.ts(NOW + timedelta(hours=2)), "released": False,
                        "identity": {"pid": DEAD_PID, "pid_start": "1", "boot_id": "boot-test", "host": "host-test"}}}
    (tmp_path / "leases.json").write_text(json.dumps(d))
    state = {"stages": {}}
    assert pl.active_leases(state) == {"e09-hold-x": [0, 1], "e09-real-y": [2]}            # stale lease ignored
    assert pl.active_leases(state, blocking_only=True) == {"e09-real-y": [2]}              # 14B gate ignores the hold
    pl.gpu_table = lambda: {i: set() for i in range(8)}
    assert pl.device_view(state)["free"] == [3, 4, 5, 6, 7]                                 # inference never takes held or really leased devices
    pl.gpu_table = lambda: (_ for _ in ()).throw(pl.GL.GpuStateUnknown("boom"))
    dv = pl.device_view(state)
    assert dv["free"] == [] and dv["unknown"]                                              # unknown state: nothing free
