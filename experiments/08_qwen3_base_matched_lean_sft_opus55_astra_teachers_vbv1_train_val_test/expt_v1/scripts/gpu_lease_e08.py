#!/usr/bin/env python3
"""TLDR: Shared GPU-admission interface on skampere1 between experiment 08's orchestrator (`pipeline_e08.py`) and other same-user owners (experiment 09's
overnight study): one lease registry (`$WORK/pipeline/leases.json`) guarded by one lock (`$WORK/pipeline/lock`, flock), every lease carrying the holder's
process identity (pid, process start ticks, boot id, host), a bounded expiry and a predeclared boundary; stale leases (dead pid, new boot, expired) are
ignored by both sides and never block a device; a device is granted only when it has no compute process from anyone and no live lease. Device inventory
FAILS CLOSED: any nvidia-smi failure, timeout, malformed row or unresolved process owner raises GpuStateUnknown and nothing is granted or launched. A
bounded `hold` (kind preflight-hold, no process identity, <= 4 h) lets an owner reserve devices while provisioning; it never blocks 14B and is
superseded by that owner's first real `request`. Policy
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
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORK = Path(os.environ.get("E08_WORK", "/lfs/skampere1/0/brando9/rl4cv_e08"))
P = WORK / "pipeline"
REGISTRY, LOCK, ADMISSION, STATE = P / "leases.json", P / "lock", P / "admission.json", P / "state.json"
E08_OWNER = "e08-pipeline"
LIMITS = {"e09": {"max_devices": 2, "max_ttl_hours": 16.0, "budget_device_hours": 32.0}}
HOLD_KIND, HOLD_MAX_HOURS, HOLD_BUDGET_HOURS = "preflight-hold", 4.0, 8.0   # a hold is not admitted training: short, bounded, one at a time, no refresh loop
PIPELINE_FRESH_S = 900
ME_USER = os.environ.get("USER") or "brando9"     # same-user processes are ours; tests override this
NVSMI_TIMEOUT_S = 30
UUID_RE = re.compile(r"^(GPU|MIG)-[0-9a-fA-F-]{8,}$")


class GpuStateUnknown(RuntimeError):
    """Device inventory could not be established with certainty; callers must fail closed (no grant, no launch)."""


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def ts(dt: datetime | None = None) -> str:
    return (dt or now_utc()).isoformat(timespec="seconds")


def parse(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


def boot_id() -> str:
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


def hostname() -> str:
    return os.uname().nodename


def proc_start(pid: int) -> str | None:
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
        return stat.rsplit(")", 1)[1].split()[19]        # field 22: starttime in clock ticks since boot
    except (FileNotFoundError, ProcessLookupError, IndexError):
        return None


def identity(pid: int | None) -> dict | None:
    if not pid:
        return None
    return {"pid": int(pid), "pid_start": proc_start(int(pid)), "boot_id": boot_id(), "host": hostname()}


def identity_alive(ident: dict | None) -> bool | None:
    """True/False for a lease with an identity; None when the lease carries none (legacy: trusted until released)."""
    if not ident or not ident.get("pid"):
        return None
    if ident.get("boot_id") != boot_id() or ident.get("host", hostname()) != hostname():
        return False
    start = proc_start(ident["pid"])
    return start is not None and (ident.get("pid_start") is None or start == ident["pid_start"])


def _runner(args: list[str]) -> tuple[int, str]:
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=NVSMI_TIMEOUT_S)
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise GpuStateUnknown(f"{args[0]} failed to run: {exc!r}") from exc
    return r.returncode, r.stdout


def gpu_table(runner=_runner) -> dict[int, set[str]]:
    """index -> users of compute processes on that device (empty set = idle). Fails closed: raises GpuStateUnknown on any
    non-zero exit, timeout, malformed or unrecognized row, or a compute process whose owner cannot be resolved."""
    rc, out = runner(["nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader"])
    if rc != 0:
        raise GpuStateUnknown(f"nvidia-smi device query exit {rc}")
    idx: dict[str, int] = {}
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = [x.strip() for x in line.split(",")]
        if len(parts) != 2 or not parts[0].isdigit() or not UUID_RE.match(parts[1]) or parts[1] in idx:
            raise GpuStateUnknown(f"malformed device row: {line!r}")
        idx[parts[1]] = int(parts[0])
    if not idx:
        raise GpuStateUnknown("nvidia-smi reported no devices")
    rc, out = runner(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid", "--format=csv,noheader"])
    if rc != 0:
        raise GpuStateUnknown(f"nvidia-smi compute-apps query exit {rc}")
    table = {i: set() for i in idx.values()}
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = [x.strip() for x in line.split(",")]
        if len(parts) != 2 or parts[0] not in idx or not parts[1].isdigit():
            raise GpuStateUnknown(f"malformed or unrecognized compute-app row: {line!r}")
        rc, user = runner(["ps", "-o", "user=", "-p", parts[1]])
        user = user.strip()
        if rc != 0 or not user or len(user.split()) != 1:
            raise GpuStateUnknown(f"owner of pid {parts[1]} on device {idx[parts[0]]} unresolved (ps exit {rc}, {user!r})")
        table[idx[parts[0]]].add(user)
    return table


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
        if v.get("owner") != owner or v.get("kind") == HOLD_KIND:     # a hold runs no compute and costs no budget
            continue
        start, end = parse(v["since"]), parse(v.get("released_at")) or parse(v.get("expires_utc")) or now
        if lease_state(v, now) in ("live", "expired"):
            end = parse(v.get("expires_utc")) or now          # reserved through its declared expiry
        used += len(v["gpus"]) * max(0.0, (end - start).total_seconds()) / 3600.0
    return round(used, 3)


def hold_hours_used(d: dict, owner: str, now: datetime) -> float:
    used = 0.0
    for v in d.values():
        if v.get("owner") == owner and v.get("kind") == HOLD_KIND:
            start, end = parse(v["since"]), (parse(v.get("released_at")) if v.get("released") else parse(v.get("expires_utc"))) or now
            used += max(0.0, (end - start).total_seconds()) / 3600.0
    return round(used, 3)


def withdraw_holds(d: dict, now: datetime, reason: str) -> list[str]:
    """Release every live provisioning hold (any foreign owner); called when 14B becomes genuinely admissible. Never touches a real lease."""
    gone = []
    for k, v in d.items():
        if v.get("kind") == HOLD_KIND and lease_state(v, now) == "live":
            v.update(released=True, released_at=ts(now), note=(v.get("note") or "") + f" | withdrawn: {reason}")
            gone.append(k)
    return gone


def admission(owner: str = "e09", table: dict | None = None, ctx: dict | None = None, d: dict | None = None, now: datetime | None = None, me_user: str | None = None) -> dict:
    """Policy for one foreign owner. Pure given (table, ctx, d) so it is unit-testable."""
    now = now or now_utc()
    d = load() if d is None else d
    lim = LIMITS[owner]
    try:
        table = gpu_table() if table is None else table
        ctx = e08_context() if ctx is None else ctx
    except GpuStateUnknown as exc:
        return {"checked_utc": ts(now), "owner": owner, "admission": "closed", "reason": f"GPU state unknown, failing closed: {exc}", "gpu_state_unknown": True, "limits": lim,
                "live_leases": {k: {"owner": v.get("owner"), "stage": v.get("stage"), "gpus": v["gpus"]} for k, v in live_leases(d, now).items()}}
    me_user = me_user or ME_USER
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
        if withdraw_holds(d, now, "14B genuinely admissible"):
            save(d)
            out["holds_withdrawn"] = True
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
    """Under the caller's lock: deny (3, reason) or write the lease (0, lease). Both sides check identity and staleness before launching.
    kind == HOLD_KIND is a bounded provisioning hold: no process identity, <= HOLD_MAX_HOURS, never blocks 14B, superseded by the owner's next real request."""
    now = now or now_utc()
    d = load() if d is None else d
    lim = LIMITS[owner]
    hold = kind == HOLD_KIND
    if n < 1 or n > lim["max_devices"]:
        return 3, {"granted": False, "reason": f"n must be 1..{lim['max_devices']}"}
    max_ttl = HOLD_MAX_HOURS if hold else lim["max_ttl_hours"]
    if ttl_hours <= 0 or ttl_hours > max_ttl:
        return 3, {"granted": False, "reason": f"ttl_hours must be in (0, {max_ttl}] for kind {kind}"}
    ident = None
    if not hold:
        if not pid:
            return 3, {"granted": False, "reason": "a real lease needs --pid of the long-lived driver (a hold needs none)"}
        ident = identity(pid)
        if ident is None or ident["pid_start"] is None:
            return 3, {"granted": False, "reason": f"pid {pid} is not alive; pass the pid of the long-lived driver (tmux pane or trainer) that will hold the lease"}
    # an owner's live holds are superseded by its new hold or real request; their devices are preferred if still idle
    superseded = [k for k, v in live_leases(d, now).items() if v.get("owner") == owner and v.get("kind") == HOLD_KIND]
    preferred = [g for k in superseded for g in d[k]["gpus"]]
    for k in superseded:
        d[k].update(released=True, released_at=ts(now), note=(d[k].get("note") or "") + " | superseded")
    a = admission(owner, table, ctx, d, now)
    if a["admission"] != "open":
        if superseded:
            save(d)
        return 3, {"granted": False, "reason": a["reason"], "admission": a, "superseded_holds": superseded}
    if a["max_grantable_now"] < n:
        if superseded:
            save(d)
        return 3, {"granted": False, "reason": f"only {a['max_grantable_now']} device(s) grantable now, {n} requested", "admission": a, "superseded_holds": superseded}
    if hold and hold_hours_used(d, owner, now) + ttl_hours > HOLD_BUDGET_HOURS:
        if superseded:
            save(d)
        return 3, {"granted": False, "reason": f"hold budget exhausted: {hold_hours_used(d, owner, now)} + {ttl_hours} h > {HOLD_BUDGET_HOURS} h of holds (no indefinite refresh)"}
    if not hold and budget_used_hours(d, owner, now) + n * ttl_hours > lim["budget_device_hours"]:
        if superseded:
            save(d)
        return 3, {"granted": False, "reason": f"request of {n} x {ttl_hours} h would exceed the {lim['budget_device_hours']} device-hour budget (used {budget_used_hours(d, owner, now)})"}
    cands = [g for g in preferred if g in a["candidate_devices"]] + [g for g in a["candidate_devices"] if g not in preferred]
    gpus = sorted(cands[:n])
    lease_id = f"{owner}-{'hold-' if hold else ''}{now.strftime('%Y%m%dT%H%M%SZ')}-{'_'.join(map(str, gpus))}"
    lease = {"owner": owner, "stage": kind, "kind": kind, "gpus": gpus, "cuda_visible_devices": ",".join(map(str, gpus)), "since": ts(now),
             "expires_utc": ts(now + timedelta(hours=ttl_hours)), "ttl_hours": ttl_hours, "boundary": boundary, "note": note, "identity": ident,
             "released": False, "released_at": None, "last_heartbeat_utc": ts(now), "blocks_14b": not hold, "superseded_holds": superseded,
             "granted_under": {k: a[k] for k in ("devices_with_other_users", "fourteen_b", "reason")}}
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
            "devices": _devices_or_error()}


def _devices_or_error():
    try:
        return {str(i): sorted(us) for i, us in gpu_table().items()}
    except GpuStateUnknown as exc:
        return {"error": str(exc), "state": "unknown (fail closed)"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status"); sub.add_parser("admission")
    p = sub.add_parser("request")
    p.add_argument("--owner", default="e09", choices=list(LIMITS)); p.add_argument("--n", type=int, default=2); p.add_argument("--kind", default="trajectory")
    p.add_argument("--ttl-hours", type=float, default=16.0); p.add_argument("--pid", type=int, required=True, help="pid of the long-lived driver that holds the lease")
    p.add_argument("--boundary", required=True, help="predeclared stopping boundary (e.g. 'checkpoint every 50 steps; stops at step N or at expiry')")
    p.add_argument("--note", default="")
    h = sub.add_parser("hold", help="bounded provisioning hold: no pid, <= 4 h, never blocks 14B, superseded by the owner's next request")
    h.add_argument("--owner", default="e09", choices=list(LIMITS)); h.add_argument("--n", type=int, default=2); h.add_argument("--ttl-hours", type=float, default=2.0)
    h.add_argument("--boundary", required=True); h.add_argument("--note", default="")
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
        elif a.cmd == "hold":
            rc, out = grant(a.owner, a.n, HOLD_KIND, a.ttl_hours, None, a.boundary, a.note)
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
