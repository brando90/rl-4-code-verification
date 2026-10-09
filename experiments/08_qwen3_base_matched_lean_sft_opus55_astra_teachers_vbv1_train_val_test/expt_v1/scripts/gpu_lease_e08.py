#!/usr/bin/env python3
"""TLDR: Shared GPU-admission interface on skampere1 between experiment 08's orchestrator (`pipeline_e08.py`) and other same-user owners (experiment 09's
overnight study): one lease registry (`$WORK/pipeline/leases.json`) guarded by one lock (`$WORK/pipeline/lock`, flock), every lease carrying the holder's
process identity (pid, process start ticks, boot id, host), a bounded expiry and a predeclared boundary; stale leases (dead pid, new boot, expired) are
ignored by both sides and never block a device; a device is granted only when it has no compute process from anyone and no live lease. Policy
(`admission`): experiment 09 may hold at most 2 devices for at most 16 h and 32 device-hours in total, and only while experiment 08's 14B SFT cannot
genuinely run (8B not finished, 14B done or already running, or other users' jobs leave fewer than 8 devices); once all 8 devices are free of other
users and 14B is pending, new experiment 09 admission closes and admitted work finishes at its own boundary; nothing is ever preempted or killed.
Usage: gpu_lease_e08.py status | admission | request --owner e09 --n 2 --kind trajectory --ttl-hours 16 --pid <driver pid> --boundary "<text>" |
release --lease-id <id> | heartbeat --lease-id <id>. Exit 0 = granted/ok, 3 = denied (JSON reason on stdout). Zero model calls."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORK = Path(os.environ.get("E08_WORK", "/lfs/skampere1/0/brando9/rl4cv_e08"))
P = WORK / "pipeline"
REGISTRY, LOCK, ADMISSION, STATE = P / "leases.json", P / "lock", P / "admission.json", P / "state.json"
E08_OWNER = "e08-pipeline"
LIMITS = {"e09": {"max_devices": 2, "max_ttl_hours": 16.0, "budget_device_hours": 32.0}}
PIPELINE_FRESH_S = 900


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def ts(dt: datetime | None = None) -> str:
    return (dt or now_utc()).isoformat(timespec="seconds")


def parse(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


def boot_id() -> str:
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


def proc_start(pid: int) -> str | None:
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
        return stat.rsplit(")", 1)[1].split()[19]        # field 22: starttime in clock ticks since boot
    except (FileNotFoundError, ProcessLookupError, IndexError):
        return None


def identity(pid: int | None) -> dict | None:
    if not pid:
        return None
    return {"pid": int(pid), "pid_start": proc_start(int(pid)), "boot_id": boot_id(), "host": os.uname().nodename}


def identity_alive(ident: dict | None) -> bool | None:
    """True/False for a lease with an identity; None when the lease carries none (legacy: trusted until released)."""
    if not ident or not ident.get("pid"):
        return None
    if ident.get("boot_id") != boot_id() or ident.get("host", os.uname().nodename) != os.uname().nodename:
        return False
    start = proc_start(ident["pid"])
    return start is not None and (ident.get("pid_start") is None or start == ident["pid_start"])


def gpu_table(nvidia_smi=None) -> dict[int, set[str]]:
    """index -> users of compute processes on that device (empty set = idle)."""
    def run(args):
        return subprocess.run(args, capture_output=True, text=True).stdout
    idx = {}
    for line in run(["nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader"]).splitlines():
        if "," in line:
            i, u = [x.strip() for x in line.split(",")]
            idx[u] = int(i)
    out = {i: set() for i in idx.values()}
    for line in run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader"]).splitlines():
        if "," not in line:
            continue
        u, pid = [x.strip() for x in line.split(",")]
        if u in idx:
            out[idx[u]].add(run(["ps", "-o", "user=", "-p", pid]).strip() or "?")
    return out


def load() -> dict:
    return json.loads(REGISTRY.read_text()) if REGISTRY.exists() else {}


def save(d: dict) -> None:
    P.mkdir(parents=True, exist_ok=True)
    tmp = REGISTRY.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")
    tmp.replace(REGISTRY)


def lease_state(lease: dict, now: datetime | None = None) -> str:
    """released | expired | stale | live."""
    now = now or now_utc()
    if lease.get("released"):
        return "released"
    exp = parse(lease.get("expires_utc"))
    if exp and now > exp:
        return "expired"
    if identity_alive(lease.get("identity")) is False:
        return "stale"
    return "live"


def live_leases(d: dict | None = None, now: datetime | None = None) -> dict[str, dict]:
    d = load() if d is None else d
    return {k: v for k, v in d.items() if lease_state(v, now) == "live"}


def e08_context() -> dict:
    """Artifact facts the policy needs (imported lazily from the orchestrator; file checks only)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import pipeline_e08 as pl  # noqa: E402
    return {"eight_done": pl.exports_ok("8B") and pl.train_log_ok("8B"), "fourteen_done": pl.exports_ok("14B")}


def pipeline_fresh() -> dict:
    st = json.loads(STATE.read_text()) if STATE.exists() else {}
    last = parse(st.get("last_tick"))
    age = (now_utc() - last).total_seconds() if last else None
    return {"last_tick_utc": st.get("last_tick"), "age_s": int(age) if age is not None else None, "fresh": age is not None and age < PIPELINE_FRESH_S,
            "pid": st.get("pid"), "boot_id": st.get("boot_id"), "sft_14B": (st.get("stages") or {}).get("sft_14B", {}).get("status")}


def budget_used_hours(d: dict, owner: str, now: datetime) -> float:
    used = 0.0
    for v in d.values():
        if v.get("owner") != owner:
            continue
        start, end = parse(v["since"]), parse(v.get("released_at")) or parse(v.get("expires_utc")) or now
        if lease_state(v, now) in ("live", "expired"):
            end = parse(v.get("expires_utc")) or now          # reserved through its declared expiry
        used += len(v["gpus"]) * max(0.0, (end - start).total_seconds()) / 3600.0
    return round(used, 3)


def admission(owner: str = "e09", table: dict | None = None, ctx: dict | None = None, d: dict | None = None, now: datetime | None = None, me_user: str | None = None) -> dict:
    """Policy for one foreign owner. Pure given (table, ctx, d) so it is unit-testable."""
    now = now or now_utc()
    table = gpu_table() if table is None else table
    ctx = e08_context() if ctx is None else ctx
    d = load() if d is None else d
    me_user = me_user or os.environ.get("USER", "brando9")
    lim = LIMITS[owner]
    live = live_leases(d, now)
    others = sorted(i for i, us in table.items() if us - {me_user})
    leased = {g for v in live.values() for g in v["gpus"]}
    idle_unleased = sorted(i for i, us in table.items() if not us and i not in leased)
    fourteen_live = any(v.get("stage") == "sft_14B" for v in live.values())
    fourteen_pending = ctx["eight_done"] and not ctx["fourteen_done"] and not fourteen_live
    fourteen_can_run = fourteen_pending and len(table) - len(others) >= 8
    held = sorted(g for v in live.values() if v.get("owner") == owner for g in v["gpus"])
    used_h = budget_used_hours(d, owner, now)
    out = {"checked_utc": ts(now), "owner": owner, "devices_with_other_users": others, "idle_unleased_devices": idle_unleased, "live_leases": {k: {"owner": v.get("owner"), "stage": v.get("stage"), "gpus": v["gpus"], "expires_utc": v.get("expires_utc")} for k, v in live.items()},
           "fourteen_b": {"pending": fourteen_pending, "running": fourteen_live, "can_run_now_or_soon": fourteen_can_run, "eight_done": ctx["eight_done"], "fourteen_done": ctx["fourteen_done"]},
           "owner_devices_held": held, "owner_budget_device_hours_used": used_h, "limits": lim}
    if fourteen_can_run:
        out.update(admission="closed", reason="experiment 08's 14B SFT (all 8 devices, TP 8) can genuinely run: 8B is finished and no other user's job blocks the 8-device reservation; admitted work finishes at its boundary, no new admission")
    elif len(held) >= lim["max_devices"]:
        out.update(admission="closed", reason=f"owner already holds {len(held)} device(s) (limit {lim['max_devices']})")
    elif used_h >= lim["budget_device_hours"]:
        out.update(admission="closed", reason=f"owner budget exhausted: {used_h} of {lim['budget_device_hours']} device-hours reserved")
    else:
        n_ok = min(lim["max_devices"] - len(held), len(idle_unleased))
        out.update(admission="open" if n_ok >= 1 else "closed", max_grantable_now=n_ok, candidate_devices=idle_unleased[:n_ok],
                   reason=("14B cannot start while other users hold devices " + str(others) if fourteen_pending else "14B is not pending") + f"; {n_ok} idle unleased device(s) grantable")
    return out


def write_admission(owner: str = "e09") -> dict:
    a = admission(owner)
    a["pipeline"] = pipeline_fresh()
    tmp = ADMISSION.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(a, indent=1, sort_keys=True) + "\n")
    tmp.replace(ADMISSION)
    return a


def grant(owner: str, n: int, kind: str, ttl_hours: float, pid: int | None, boundary: str, note: str = "", table: dict | None = None, ctx: dict | None = None, d: dict | None = None, now: datetime | None = None) -> tuple[int, dict]:
    """Under the caller's lock: deny (3, reason) or write the lease (0, lease). Both sides check identity and staleness before launching."""
    now = now or now_utc()
    d = load() if d is None else d
    lim = LIMITS[owner]
    if n < 1 or n > lim["max_devices"]:
        return 3, {"granted": False, "reason": f"n must be 1..{lim['max_devices']}"}
    if ttl_hours <= 0 or ttl_hours > lim["max_ttl_hours"]:
        return 3, {"granted": False, "reason": f"ttl_hours must be in (0, {lim['max_ttl_hours']}]"}
    ident = identity(pid)
    if pid and (ident is None or ident["pid_start"] is None):
        return 3, {"granted": False, "reason": f"pid {pid} is not alive; pass the pid of the long-lived driver (tmux pane or trainer) that will hold the lease"}
    a = admission(owner, table, ctx, d, now)
    if a["admission"] != "open":
        return 3, {"granted": False, "reason": a["reason"], "admission": a}
    if a["max_grantable_now"] < n:
        return 3, {"granted": False, "reason": f"only {a['max_grantable_now']} device(s) grantable now, {n} requested", "admission": a}
    if budget_used_hours(d, owner, now) + n * ttl_hours > lim["budget_device_hours"]:
        return 3, {"granted": False, "reason": f"request of {n} x {ttl_hours} h would exceed the {lim['budget_device_hours']} device-hour budget (used {budget_used_hours(d, owner, now)})"}
    gpus = a["candidate_devices"][:n]
    lease_id = f"{owner}-{now.strftime('%Y%m%dT%H%M%SZ')}-{'_'.join(map(str, gpus))}"
    lease = {"owner": owner, "stage": kind, "kind": kind, "gpus": gpus, "cuda_visible_devices": ",".join(map(str, gpus)), "since": ts(now),
             "expires_utc": ts(now + timedelta(hours=ttl_hours)), "ttl_hours": ttl_hours, "boundary": boundary, "note": note, "identity": ident,
             "released": False, "released_at": None, "last_heartbeat_utc": ts(now), "granted_under": {k: a[k] for k in ("devices_with_other_users", "fourteen_b", "reason")}}
    d[lease_id] = lease
    save(d)
    return 0, {"granted": True, "lease_id": lease_id, **lease}


def release(lease_id: str, d: dict | None = None, now: datetime | None = None) -> dict:
    d = load() if d is None else d
    if lease_id not in d:
        return {"ok": False, "reason": "unknown lease"}
    if not d[lease_id].get("released"):
        d[lease_id].update(released=True, released_at=ts(now))
        save(d)
    return {"ok": True, "lease_id": lease_id, "released_at": d[lease_id]["released_at"]}


def heartbeat(lease_id: str) -> dict:
    d = load()
    if lease_id not in d or lease_state(d[lease_id]) != "live":
        return {"ok": False, "state": lease_state(d[lease_id]) if lease_id in d else "unknown"}
    d[lease_id]["last_heartbeat_utc"] = ts()
    save(d)
    return {"ok": True, "lease_id": lease_id, "expires_utc": d[lease_id]["expires_utc"]}


def status() -> dict:
    d = load()
    now = now_utc()
    return {"checked_utc": ts(now), "registry": str(REGISTRY), "lock": str(LOCK), "admission_file": str(ADMISSION), "pipeline": pipeline_fresh(),
            "leases": {k: {"owner": v.get("owner"), "stage": v.get("stage"), "gpus": v["gpus"], "state": lease_state(v, now), "since": v.get("since"), "expires_utc": v.get("expires_utc"),
                           "identity": v.get("identity")} for k, v in d.items()},
            "devices": {str(i): sorted(us) for i, us in gpu_table().items()}}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status"); sub.add_parser("admission")
    p = sub.add_parser("request")
    p.add_argument("--owner", default="e09", choices=list(LIMITS)); p.add_argument("--n", type=int, default=2); p.add_argument("--kind", default="trajectory")
    p.add_argument("--ttl-hours", type=float, default=16.0); p.add_argument("--pid", type=int, required=True, help="pid of the long-lived driver that holds the lease")
    p.add_argument("--boundary", required=True, help="predeclared stopping boundary (e.g. 'checkpoint every 50 steps; stops at step N or at expiry')")
    p.add_argument("--note", default="")
    for name in ("release", "heartbeat"):
        q = sub.add_parser(name); q.add_argument("--lease-id", required=True)
    a = ap.parse_args()
    P.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        if a.cmd == "status":
            out, rc = status(), 0
        elif a.cmd == "admission":
            out = write_admission(); rc = 0 if out["admission"] == "open" else 3
        elif a.cmd == "request":
            rc, out = grant(a.owner, a.n, a.kind, a.ttl_hours, a.pid, a.boundary, a.note)
            write_admission(a.owner)
        elif a.cmd == "release":
            out = release(a.lease_id); rc = 0 if out["ok"] else 3
            write_admission()
        else:
            out = heartbeat(a.lease_id); rc = 0 if out["ok"] else 3
        fcntl.flock(lk, fcntl.LOCK_UN)
    print(json.dumps(out, indent=1, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
