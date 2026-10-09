#!/usr/bin/env python3
"""TLDR: Serialized, resumable orchestrator for the rest of experiment 08 (runbook §§ 8–11) on skampere1. Every tick, under the file lock it shares
with the host watchdog, it validates ACTUAL artifacts (exported checkpoints with hash manifests plus a training log that matches the frozen token
schedule; scored ladder files with exactly 135 × 8 or 222 × 8 distinct scored rows and 8 complete scorer shards; a committed `selection.json`),
dispatches the next ready stages into named tmux sessions under GPU leases (a device with any compute process, or leased by another stage, is never
used; the 14B SFT gets all 8 devices only when no inference stage holds a lease, and no new inference starts while the only thing blocking 14B is our
own inference), distinguishes active from waiting or stale stages by real child processes and output freshness, relaunches a crashed stage once
(all launchers resume and never regenerate a finished cell), and after all 20 validation rungs plus Base 14B are valid runs the frozen selection,
commits it, and only then runs the conditional test generation, judge route controls and judging (D-102, Vals-funded Valkyrie route, frozen
settings), the D-009 test analysis and publication. It changes no scientific setting and sends no email. Usage: pipeline_e08.py [--once] [--dry]."""
from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gpu_lease_e08 as GL  # noqa: E402  shared GPU-admission interface (registry, lock, identities, policy)

REPO = Path(__file__).resolve().parents[4]
EXP = Path(__file__).resolve().parents[2]          # experiments/08_.../ (results.md lives here)
EXPV = Path(__file__).resolve().parents[1]         # expt_v1/ (scripts, results, CKPT)
S = EXPV / "scripts"
RES = EXPV / "results"
WORK = Path(os.environ.get("E08_WORK", "/lfs/skampere1/0/brando9/rl4cv_e08"))
P = WORK / "pipeline"
STATE_PATH, LOCK, LEASES = P / "state.json", P / "lock", P / "leases.json"
PY = str(REPO / ".venv" / "bin" / "python")
SIZES = ("1.7B", "4B", "8B", "14B")
FRACTIONS = ("0.125", "0.25", "0.5", "0.75", "1.0")
SFT_GPUS = {"8B": 4, "14B": 8}
N_VAL, N_TEST, G = 135, 222, 8
FRESH_S = 3600                 # live session whose log has not changed for an hour -> reported stale (never killed)
MAX_RETRY = 1
MAX_GEN = 2                    # concurrent generation stages (one vLLM process each); one launch per tick (flashinfer JIT race)
ADOPTED = {"sft_1.7B_f0.75": ("rl4cv-e08-ladder-1_7B", WORK / "ladder" / "driver_sft_1p7B_f0p75_validation_resume.log"),
           "sft_4B_f0.75": ("rl4cv-e08-ladder-4B", WORK / "ladder" / "driver_sft_4B_f0p75_validation_resume.log")}
JUDGE_PORTS = {"judge-controls": 9741, "judge-test": 9742}      # inside the claimed block 9740-9759 (teachers service used 9740)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def ts() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def local_stamp() -> str:
    return subprocess.run(["date", "+%m-%d-%Y %H:%M %Z"], capture_output=True, text=True).stdout.strip()


def log(msg: str) -> None:
    P.mkdir(parents=True, exist_ok=True)
    with (P / "pipeline.log").open("a") as fh:
        fh.write(f"[{ts()}] {msg}\n")


def run(cmd, timeout: int = 1800, **kw) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, timeout=timeout, **kw)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        return subprocess.CompletedProcess(cmd, 124, stdout=out, stderr="timeout")


def read_json(p: Path, default=None):
    return json.loads(p.read_text()) if p.exists() else default


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n")
    tmp.replace(p)


# ----------------------------------------------------------------------------------------------- sessions, devices, leases
def session_alive(name: str) -> bool:
    return run(["tmux", "has-session", "-t", name]).returncode == 0


def pane_pid(name: str):
    r = run(["tmux", "list-panes", "-t", name, "-F", "#{pane_pid}"])
    return int(r.stdout.split()[0]) if r.returncode == 0 and r.stdout.strip() else None


def descendants(pid) -> list[tuple[str, str]]:
    if not pid:
        return []
    r = run(["pstree", "-p", str(pid)])
    return re.findall(r"([a-zA-Z0-9_.+-]+)\((\d+)\)", r.stdout)[1:] if r.returncode == 0 else []


gpu_table = GL.gpu_table


def leases() -> dict:
    return GL.load()


def active_leases(state: dict) -> dict[str, list[int]]:
    """Every LIVE lease in the shared registry, ours or another owner's (experiment 09): not released, not expired, holder process alive."""
    out = {}
    for n, l in GL.live_leases().items():
        if l.get("owner", GL.E08_OWNER) == GL.E08_OWNER and state["stages"].get(n, {}).get("status") not in ("launched", "running"):
            continue    # our own lease whose stage is no longer live (released on the next observe)
        out[n] = l["gpus"]
    return out


def take_lease(name: str, gpus: list[int], pid=None, kind: str = "inference") -> None:
    d = leases()
    d[name] = {"owner": GL.E08_OWNER, "stage": name, "kind": kind, "gpus": gpus, "cuda_visible_devices": ",".join(map(str, gpus)), "since": ts(), "expires_utc": None,
               "boundary": "stage end (resumable launcher; lease released when the merged generation exists or the stage finishes)", "identity": GL.identity(pid), "released": False, "released_at": None}
    write_json(LEASES, d)


def release_lease(name: str) -> None:
    d = leases()
    if name in d and not d[name].get("released"):
        d[name].update(released=True, released_at=ts())
        write_json(LEASES, d)
        log(f"lease released: {name} {d[name]['gpus']}")


def device_view(state: dict, me: str | None = None) -> dict:
    """free = idle and unleased; others = devices with other users' processes (never ours to take)."""
    me_user = os.environ.get("USER", "brando9")
    table = gpu_table()
    leased = {g: n for n, gs in active_leases(state).items() for g in gs if n != me}
    return {"free": sorted(i for i, us in table.items() if not us and i not in leased), "others": sorted(i for i, us in table.items() if us - {me_user}),
            "leased": leased, "n_devices": len(table)}


# ----------------------------------------------------------------------------------------------- artifact validation
def sched() -> dict:
    return json.loads((RES / "sft_schedule.json").read_text())


def rungs() -> list[tuple[str, int]]:
    c = sched()["checkpoints"]
    return [(f, c[f]["step"]) for f in FRACTIONS]


def label(size: str, frac: str) -> str:
    return f"sft_{size.replace('.', 'p')}_f{frac.replace('.', 'p')}"


def export_ok(size: str, step: int) -> bool:
    hf = WORK / "ckpt" / size / "hf" / f"step_{step}"
    sums = hf / "SHA256SUMS"
    if not (sums.exists() and (hf / "config.json").exists() and (hf / "tokenizer.json").exists()):
        return False
    listed = sums.read_text()
    weights = [p for p in hf.iterdir() if p.suffix in (".bin", ".safetensors")]
    return bool(weights) and all(p.stat().st_size > 1_000_000 and p.name in listed for p in weights)


def exports_ok(size: str) -> bool:
    return all(export_ok(size, step) for _, step in rungs())


def train_log_ok(size: str) -> bool:
    d = read_json(RES / "train_logs" / f"sft_{size.replace('.', 'p')}_summary.json")
    return bool(d and d.get("n_steps") == sched()["steps"] and (d.get("schedule_comparison") or {}).get("matches_schedule"))


def ensure_train_log(size: str) -> None:
    out = RES / "train_logs" / f"sft_{size.replace('.', 'p')}_summary.json"
    if out.exists() or not exports_ok(size):
        return
    cmd = (f"cd {WORK}/nemo_rl && UV_CACHE_DIR={WORK}/cache/uv env -u PYTHONPATH uv run python {S}/extract_train_logs_e08.py --tb-dir {WORK}/ckpt/{size}/logs "
           f"--size {size} --out-csv {RES}/train_logs/sft_{size.replace('.', 'p')}_steps.csv --out-json {out}")
    r = run(cmd, timeout=1800)
    log(f"extract_train_logs {size}: rc={r.returncode} {r.stdout.strip()[-200:]}")


def ladder_valid(lab: str, split: str) -> dict:
    """Declared cells all scored (distinct rows), 8 complete per-task shards, merged generation present."""
    n_tasks = N_VAL if split == "validation" else N_TEST
    root = WORK / "ladder" / split
    scored, gen = root / "scored" / f"scored_{lab}_g8.jsonl", root / "raw" / f"gen_{lab}_g8.jsonl"
    v = {"rows": 0, "distinct": 0, "unscored": 0, "shards_ok": 0, "gen_rows": 0}
    if gen.exists():
        v["gen_rows"] = sum(1 for l in gen.open(encoding="utf-8") if l.strip())
    if scored.exists():
        keys = set()
        for l in scored.open(encoding="utf-8"):
            if l.strip():
                r = json.loads(l)
                v["rows"] += 1
                v["unscored"] += r.get("status") != "scored"
                keys.add((r["task_id"], int(r["sample_idx"])))
        v["distinct"] = len(keys)
    for k in range(G):
        d = root / "scores" / f"{lab}_g8_s{k}"
        csvs = list(d.glob("*_per_task.csv")) if d.is_dir() else []
        if len(csvs) == 1 and sum(1 for _ in csv.DictReader(csvs[0].open(encoding="utf-8"))) == n_tasks:
            v["shards_ok"] += 1
    v["gen_complete"] = v["gen_rows"] == n_tasks * G
    v["valid"] = v["rows"] == v["distinct"] == n_tasks * G and v["unscored"] == 0 and v["shards_ok"] == G
    return v


def nshards(lab: str, split: str):
    p = WORK / "ladder" / split / "ids" / f"{lab}.nshards"
    return int(p.read_text().strip()) if p.exists() else None


def git(*args, timeout=300) -> subprocess.CompletedProcess:
    return run(["git", "-C", str(REPO), *args], timeout=timeout)


def selection_committed():
    p = RES / "selection.json"
    rel = str(p.relative_to(REPO))
    if not p.exists() or git("ls-files", "--error-unmatch", rel).returncode != 0 or git("diff", "--quiet", "HEAD", "--", rel).returncode != 0:
        return None
    return json.loads(p.read_text())


# ----------------------------------------------------------------------------------------------- publication
def publish(paths: list[Path], message: str) -> bool:
    rel = [str(p.relative_to(REPO)) for p in paths if p.exists()]
    if not rel:
        return False
    if git("add", "--", *rel).returncode:
        log("git add failed"); return False
    if git("diff", "--cached", "--quiet").returncode == 0:
        return True
    if git("diff", "--check", "--cached").returncode:
        log("git diff --check failed; not committing"); return False
    t = run(["make", "-C", str(REPO), "test"], timeout=1800, env={**os.environ, "PATH": f"{REPO}/.venv/bin:{os.environ.get('PATH', '')}"})
    git("commit", "-q", "-m", message + "\n\nCo-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>")
    if t.returncode:
        log(f"make test FAILED (rc={t.returncode}); committed locally, NOT pushed: {t.stdout[-300:]}")
        return False
    if git("pull", "--ff-only").returncode:
        git("pull", "--no-rebase", "--no-edit")
    r = git("push", "origin", "HEAD:main")
    log(f"publish '{message[:70]}': {'pushed' if r.returncode == 0 else 'PUSH FAILED ' + r.stderr[-200:]}")
    return r.returncode == 0


# ----------------------------------------------------------------------------------------------- stage control
def stage(state: dict, name: str) -> dict:
    return state["stages"].setdefault(name, {"retries": 0, "status": "pending"})


def watch_globs(name: str) -> list[str]:
    if name.startswith("sft_"):
        size = name.split("_", 1)[1]
        return [f"{WORK}/ckpt/{size}/logs/**/events.out.tfevents.*", f"{WORK}/ckpt/{size}/driver_logs/*.log"]
    if name.startswith("ladder_val_"):
        return [f"{WORK}/ladder/validation/logs/*{name[len('ladder_val_'):]}*", f"{WORK}/ladder/validation/scores/.partial_{name[len('ladder_val_'):]}_g8_s*/**"]
    if name.startswith("ladder_test_"):
        return [f"{WORK}/ladder/test/logs/*{name[len('ladder_test_'):]}*", f"{WORK}/ladder/test/scores/.partial_{name[len('ladder_test_'):]}_g8_s*/**"]
    return []


def launch(state: dict, name: str, session: str, cmd: str, gpus, log_path: Path, dry: bool) -> bool:
    st = stage(state, name)
    if session_alive(session):
        st.update(status="running", session=session, log=str(log_path)); return True
    if st.get("retries", 0) > MAX_RETRY:
        if st.get("status") != "critical":
            log(f"CRITICAL {name}: crashed more than {MAX_RETRY} time(s); not relaunching")
        st["status"] = "critical"; return False
    if dry:
        log(f"DRY would launch {name} in {session} gpus={gpus}: {cmd[:200]}"); st["would_launch"] = cmd; return False
    log_path.parent.mkdir(parents=True, exist_ok=True)
    exit_file = P / f"{name}.exit"
    exit_file.unlink(missing_ok=True)
    r = run(["tmux", "new-session", "-d", "-s", session, f"{cmd} >> {log_path} 2>&1; echo $? > {exit_file}"])
    if r.returncode:
        st.update(status="launch_failed", error=r.stderr[-200:]); log(f"launch failed {name}: {r.stderr[-200:]}"); return False
    pid = pane_pid(session)
    if gpus:
        take_lease(name, gpus, pid=pid, kind="sft" if name.startswith("sft_") else "inference")
    st.update(status="launched", session=session, launched_at=ts(), log=str(log_path), gpus=gpus or [], pane_pid=pid, cmd=cmd, watch=watch_globs(name))
    log(f"LAUNCH {name} in {session} gpus={gpus}: {cmd[:200]}")
    return True


def freshness_age(st: dict):
    """Seconds since the newest write among the stage log and its watched globs (None when nothing exists yet)."""
    paths = [Path(st["log"])] if st.get("log") else []
    for pat in st.get("watch", []):
        paths.extend(Path("/").glob(pat.lstrip("/")))
    times = [p.stat().st_mtime for p in paths if p.exists()]
    return (time.time() - max(times)) if times else None


def observe(state: dict, name: str, done: bool) -> str:
    """done / running (active | waiting | stale, by real children and log freshness) / crashed / pending / critical."""
    st = stage(state, name)
    if done:
        if st.get("status") != "done":
            log(f"DONE {name}")
        st.update(status="done", done_at=st.get("done_at") or ts()); release_lease(name); return "done"
    session = st.get("session")
    if session and session_alive(session):
        pid = pane_pid(session)
        kids = descendants(pid)
        age = freshness_age(st)
        active = any(k[0] not in ("sleep", "bash", "sh", "tmux") for k in kids)
        st.update(status="running", pane_pid=pid, n_children=len(kids), active=active, log_age_s=int(age) if age is not None else None,
                  health="active" if active and (age is None or age < FRESH_S) else ("waiting" if not active else "stale"), observed=ts())
        if st["health"] == "stale" and not st.get("stale_logged"):
            log(f"STALE {name}: live session, {len(kids)} children, log unchanged for {int(age)} s"); st["stale_logged"] = True
        return "running"
    if st.get("status") in ("launched", "running"):
        ex = P / f"{name}.exit"
        rc = ex.read_text().strip() if ex.exists() else "no-exit-file"
        st.update(status="crashed", exit=rc, retries=st.get("retries", 0) + 1, crashed_at=ts()); release_lease(name)
        log(f"CRASHED {name}: exit {rc} (retry {st['retries']} of {MAX_RETRY})")
    return st.get("status", "pending")


# ----------------------------------------------------------------------------------------------- the tick
def tick(state: dict, dry: bool) -> dict:
    summary, launched_gen = {}, 0
    # 1. SFT chains: 8B adopted from its live session; 14B only after 8B's verified exports, with no active lease and 8 idle devices.
    for size in ("8B", "14B"):
        name, session = f"sft_{size}", f"rl4cv-e08-sft-{size}"
        ensure_train_log(size)
        status = observe(state, name, exports_ok(size) and train_log_ok(size))
        if exports_ok(size) and not train_log_ok(size) and (RES / "train_logs" / f"sft_{size.replace('.', 'p')}_summary.json").exists():
            stage(state, name)["status"] = "critical"; log(f"CRITICAL {name}: exports present but the training log does not match the frozen schedule")
        if status in ("pending", "crashed", "waiting_gpu", "waiting_leases") and (size == "8B" or (exports_ok("8B") and train_log_ok("8B"))):
            dv = device_view(state, name)
            need = SFT_GPUS[size]
            if size == "14B" and active_leases(state):
                stage(state, name)["status"] = "waiting_leases"; stage(state, name)["devices"] = dv; stage(state, name)["waiting_on"] = active_leases(state)
            elif len(dv["free"]) >= need:
                launch(state, name, session, f"bash {S}/launch_sft_e08.sh {size} {','.join(map(str, dv['free'][:need]))}", dv["free"][:need], WORK / "ckpt" / f"driver_{size}.log", dry)
            else:
                stage(state, name)["status"] = "waiting_gpu"; stage(state, name)["devices"] = dv
        summary[name] = stage(state, name)["status"]
    for size in ("1.7B", "4B"):
        summary[f"sft_{size}"] = "done" if exports_ok(size) and train_log_ok(size) else "INCOMPLETE"
    st14 = stage(state, "sft_14B")["status"]
    fourteen_pending = exports_ok("8B") and train_log_ok("8B") and st14 not in ("done", "critical", "launched", "running")
    fourteen_running = st14 in ("launched", "running")
    # 2. Validation rungs: generation needs one leased device; scoring is CPU-only.
    n_gen = sum(1 for n, st in state["stages"].items() if n.startswith("ladder_") and st.get("status") in ("launched", "running") and not st.get("gen_released"))
    for size in SIZES:
        for frac, step in rungs():
            lab, name = label(size, frac), f"ladder_val_{label(size, frac)}"
            v = ladder_valid(lab, "validation")
            st = stage(state, name)
            key = f"sft_{size}_f{frac}"
            if key in ADOPTED and not st.get("session") and session_alive(ADOPTED[key][0]):
                st.update(session=ADOPTED[key][0], log=str(ADOPTED[key][1]), status="running", adopted=True, gen_released=True, watch=watch_globs(name))
            status = observe(state, name, v["valid"])
            if status == "running" and v["gen_complete"] and not st.get("gen_released"):
                release_lease(name); st["gen_released"] = True; n_gen -= 1
            if status in ("pending", "crashed", "waiting_gpu") and export_ok(size, step) and st.get("retries", 0) <= MAX_RETRY:
                shards = nshards(lab, "validation") or 1
                gpus = None
                if not v["gen_complete"]:
                    dv = device_view(state, name)
                    hold_for_14b = fourteen_pending and dv["n_devices"] - len(dv["others"]) >= 8
                    if fourteen_running or hold_for_14b or n_gen + launched_gen >= MAX_GEN or launched_gen >= 1 or len(dv["free"]) < shards:
                        st["status"] = "waiting_gpu"; st["devices"] = {"free": dv["free"], "others": dv["others"], "hold_for_14b": hold_for_14b}; summary[name] = "waiting_gpu"; continue
                    gpus = dv["free"][:shards]
                else:
                    st["gen_released"] = True
                session = f"rl4cv-e08-ladder-{size.replace('.', '_')}-f{frac.replace('.', 'p')}"
                hf = WORK / "ckpt" / size / "hf" / f"step_{step}"
                cmd = f"SCORE_PAR=4 bash {S}/run_ladder_e08.sh validation {lab} {hf} local {','.join(map(str, gpus)) if gpus else '0'} 1"
                if launch(state, name, session, cmd, gpus, WORK / "ladder" / f"driver_{lab}_validation_pipeline.log", dry) and gpus:
                    launched_gen += 1
                    run([PY, str(S / "make_ladder_manifest_e08.py")])
            summary[name] = stage(state, name)["status"]
    # 3. Ladder analysis after each newly valid rung; selection once all 20 rungs and Base 14B are valid and all four training logs match the schedule.
    newly = [n for n, st in state["stages"].items() if n.startswith("ladder_val_") and st.get("status") == "done" and not st.get("published")]
    n_valid = sum(1 for sz in SIZES for f in FRACTIONS if ladder_valid(label(sz, f), "validation")["valid"])
    all_valid = n_valid == 20 and ladder_valid("base14b", "validation")["valid"]
    logs_ok = all(train_log_ok(sz) for sz in SIZES)
    sel = selection_committed()
    if not dry and (newly or (all_valid and not sel)):
        run([PY, str(S / "make_ladder_manifest_e08.py")])
        select = all_valid and not sel and logs_ok
        r = run([PY, str(S / "analyze_ladder.py"), "--split", "validation"] + ([] if select else ["--no-selection"]), timeout=3600)
        log(f"analyze_ladder validation (selection={select}) rc={r.returncode}: {r.stdout.strip()[-300:]} {r.stderr.strip()[-300:]}")
        if r.returncode == 0:
            update_results_ladder()
            paths = [RES / "validation_ladder.json", RES / "ladder", RES / "ladder_manifest.json", RES / "train_logs", EXP / "results.md"]
            if select and (RES / "selection.json").exists():
                paths.append(RES / "selection.json")
                publish(paths, "Experiment 08 § 9: validation ladder complete at all four sizes; frozen selection committed before any test generation")
                sel = selection_committed()
            else:
                publish(paths, f"Experiment 08 § 9: validation ladder progress ({', '.join(n.replace('ladder_val_', '') for n in newly) or 'refresh'})")
            for n in newly:
                state["stages"][n]["published"] = True
        if all_valid and not logs_ok:
            log("CRITICAL selection blocked: a training log does not match the frozen schedule (PROTOCOL § 8)")
    try:
        adm = GL.write_admission()
        summary["e09_admission"] = f"{adm['admission']} ({adm.get('candidate_devices', [])})"
    except Exception as exc:  # noqa: BLE001
        log(f"admission write failed: {exc!r}")
    summary["selection"] = sel.get("verdict") if sel else ("ready" if all_valid else f"pending ({n_valid}/20 rungs valid)")
    # 4. Test phase only after a committed selection.
    if sel and sel.get("verdict") in ("RL-READY", "PARTIAL"):
        test_phase(state, sel, dry, summary, fourteen_running)
    elif sel:
        summary["test"] = f"not run (verdict {sel.get('verdict')})"
        if not dry:
            finalize(state, sel)
    return summary


# ----------------------------------------------------------------------------------------------- results.md (live ladder table)
def update_results_ladder() -> None:
    vl = read_json(RES / "validation_ladder.json")
    if not vl:
        return
    lines = ["| System | Status | Extraction | Capped | Mixed tasks (share; Wilson 95%) | Gates | pass@8 | mean pass | mean tokens |", "|---|---|---:|---:|---|---|---:|---:|---:|"]
    for lab, r in sorted(vl["systems"].items()):
        g, d = r["gates"], r["diagnostics"]
        lines.append(f"| `{lab}` | {r['status']} | {g['a_extraction']['n']} / {g['a_extraction']['of']} | {g['b_capped']['n']} / {g['b_capped']['of']} | "
                     f"{g['c_mixed']['n']} / {g['c_mixed']['of']} ({g['c_mixed']['share']}; {g['c_mixed']['wilson95']}) | {'PASS' if g['pass'] else 'fail'} | "
                     f"{d['pass_at_8_share']} | {d['mean_pass_rate']} | {d['mean_generated_tokens']} |")
    sel = read_json(RES / "selection.json")
    tail = ""
    if sel:
        tail = (f"\n**Selection (PROTOCOL § 9, frozen rule):** verdict **{sel['verdict']}**, f* = {sel.get('f_star')}; earliest passing fraction per size "
                f"{json.dumps(sel.get('earliest_passing_fraction_per_size'))}; tokens needed {json.dumps(sel.get('tokens_needed'))}; incomplete systems "
                f"{sel.get('incomplete_systems')}. `expt_v1/results/selection.json` is committed before any test generation (D-004).\n")
    block = ("## Validation ladder (live; PROTOCOL § 9: 135 tasks × 8 samples per system; gates (a) extraction ≥ 972/1080, (b) capped ≤ 108/1080, (c) mixed `kernel_binary` tasks ≥ 7/135; p-val=n/a)\n\n"
             f"Written {vl['written_utc']} by the pipeline from `expt_v1/results/validation_ladder.json` (per-task and per-cell CSVs under `expt_v1/results/ladder/`).\n\n"
             + "\n".join(lines) + "\n" + tail + "\n")
    t = (EXP / "results.md").read_text()
    if "## Validation ladder (live;" in t:
        t = re.sub(r"## Validation ladder \(live;.*?(?=\n## )", block.rstrip("\n") + "\n", t, count=1, flags=re.S)
    else:
        t = t.replace("## Open questions for Brando", block + "## Open questions for Brando", 1)
    t = re.sub(r"^\*\*Last updated:\*\* .*$", f"**Last updated:** {local_stamp()} (pipeline: validation ladder table)", t, count=1, flags=re.M)
    (EXP / "results.md").write_text(t)


# ----------------------------------------------------------------------------------------------- test phase
def model_args(system: dict) -> tuple[str, str]:
    if system.get("hf_path"):
        return system["hf_path"], "local"
    lm = read_json(RES / "ladder_manifest.json", {"systems": []})
    base = next(s for s in lm["systems"] if s["label"] == system["label"])
    return base["model"], base["revision"]


def test_phase(state: dict, sel: dict, dry: bool, summary: dict, fourteen_running: bool) -> None:
    tm = RES / "test_manifest.json"
    if not tm.exists():
        if dry:
            summary["test"] = "would write test manifest"; return
        write_json(tm, {"written_utc": ts(), "split": "test", "n_tasks": N_TEST, "samples_per_task": G, "selection_sha256": sha((RES / "selection.json").read_bytes()),
                        "task_ids_sha256": sel["test_manifest"]["task_ids_sha256"], "systems": [dict(s, in_test=True) for s in sel["test_manifest"]["systems"]],
                        "n_declared_cells": sel["test_manifest"]["n_declared_cells"], "note": "frozen from the committed selection.json before any test generation"})
        publish([tm], "Experiment 08 § 10: test manifest frozen from the committed selection (before any test generation)")
    systems = read_json(tm)["systems"]
    gen_systems = [s for s in systems if s.get("source") != "e05"]
    n_gen = sum(1 for n, st in state["stages"].items() if n.startswith("ladder_") and st.get("status") in ("launched", "running") and not st.get("gen_released"))
    launched = 0
    for s in gen_systems:
        lab, name = s["label"], f"ladder_test_{s['label']}"
        v = ladder_valid(lab, "test")
        st = stage(state, name)
        status = observe(state, name, v["valid"])
        if status == "running" and v["gen_complete"] and not st.get("gen_released"):
            release_lease(name); st["gen_released"] = True; n_gen -= 1
        if status in ("pending", "crashed", "waiting_gpu") and st.get("retries", 0) <= MAX_RETRY:
            shards = nshards(lab, "test") or 1
            gpus = None
            if not v["gen_complete"]:
                dv = device_view(state, name)
                if fourteen_running or n_gen + launched >= MAX_GEN or launched >= 1 or len(dv["free"]) < shards:
                    st["status"] = "waiting_gpu"; summary[name] = "waiting_gpu"; continue
                gpus = dv["free"][:shards]
            else:
                st["gen_released"] = True
            model, rev = model_args(s)
            cmd = f"SCORE_PAR=4 bash {S}/run_ladder_e08.sh test {lab} {model} {rev} {','.join(map(str, gpus)) if gpus else '0'} 1"
            if launch(state, name, f"rl4cv-e08-test-{lab}", cmd, gpus, WORK / "ladder" / f"driver_{lab}_test_pipeline.log", dry) and gpus:
                launched += 1
        summary[name] = stage(state, name)["status"]
    n_done = sum(1 for s in gen_systems if ladder_valid(s["label"], "test")["valid"])
    if n_done < len(gen_systems):
        summary["test_generation"] = f"{n_done}/{len(gen_systems)} systems scored"; return
    summary["test_generation"] = "done"
    if dry:
        return
    if state.get("test_cells_manifest_sha") != sha(tm.read_bytes()):
        r = run([PY, str(S / "analyze_ladder.py"), "--manifest", str(tm), "--split", "test", "--out", str(RES / "test_ladder_kernel.json"), "--no-selection"], timeout=3600)
        log(f"analyze_ladder test rc={r.returncode}: {r.stdout.strip()[-300:]} {r.stderr.strip()[-300:]}")
        if r.returncode:
            summary["test"] = "kernel analysis failed"; return
        state["test_cells_manifest_sha"] = sha(tm.read_bytes())
        publish([RES / "test_ladder_kernel.json", RES / "ladder"], "Experiment 08 § 10: test-split kernel factors for every system on the frozen test manifest")
    judge_phase(state, sel, summary)


def deployed(name: str, benchmark: str, pack: Path) -> bool:
    port = JUDGE_PORTS[name]
    args = ["--name", name, "--benchmark", benchmark, "--port", str(port), "--pack", str(pack)]
    if run([PY, str(S / "deploy_service_e08.py"), "status", *args], timeout=300).returncode == 0:
        return True
    n = len([p for p in pack.iterdir() if p.is_dir()])
    r = run([PY, str(S / "deploy_service_e08.py"), "deploy", *args, "--expected-tasks", str(n)], timeout=900)
    log(f"deploy {name} ({benchmark}, port {port}, {n} tasks): rc={r.returncode} {r.stdout.strip()[-200:]} {r.stderr.strip()[-200:]}")
    return r.returncode == 0


def judge_phase(state: dict, sel: dict, summary: dict) -> None:
    """D-102 judging via the validated Valkyrie agent (vb103_judge; H2_sol_high + H2_opus55_max, 3 repeats, median then mean/5): controls first."""
    J, drv = RES / "judge", str(S / "judge_rl4cv_e08.py")
    js = state.setdefault("judge", {})
    if js.get("controls") != "PASS":
        ctl = read_json(J / "judge_pack_controls.json")
        if not ctl:
            r = run([PY, drv, "build-controls"], timeout=1800); log(f"build-controls rc={r.returncode}: {r.stdout.strip()[-200:]}")
            ctl = read_json(J / "judge_pack_controls.json")
            if not ctl:
                summary["judge"] = "build-controls failed"; return
        if not deployed("judge-controls", "veribench-rl4cv-e08-controls", Path(ctl["pack_abs"])):
            summary["judge"] = "controls service unavailable"; return
        runs = (read_json(J / "state.json", {}) or {}).get("runs", {})
        if not any(k.startswith("controls/") for k in runs):
            r = run([PY, drv, "admit", "--suite", "rl4cv-e08-controls", "--concurrency", "8"], timeout=1800); log(f"admit controls rc={r.returncode}: {r.stdout.strip()[-300:]}")
            summary["judge"] = "controls admitted"; return
        if run([PY, drv, "poll"], timeout=1800).returncode != 0:
            summary["judge"] = "controls running"; return
        run([PY, drv, "harvest", "--suite", "rl4cv-e08-controls"], timeout=3600)
        r = run([PY, drv, "controls-check"], timeout=600)
        js["controls"] = "PASS" if r.returncode == 0 else "FAIL"
        log(f"controls-check: {js['controls']} {r.stdout.strip()[-300:]}")
        publish([J / "controls_check.json", J / "harvests", J / "state.json", J / "judge_pack_controls.json"], f"Experiment 08 § 10: judge route controls {js['controls']}")
        if js["controls"] != "PASS":
            summary["judge"] = "CONTROLS FAIL: judge route not validated on this transport; test judging NOT admitted (blocker for Brando)"; log(summary["judge"]); return
    tp = read_json(J / "judge_pack_test.json")
    if not tp:
        r = run([PY, drv, "build-test", "--systems", str(RES / "test_manifest.json")], timeout=3600); log(f"build-test rc={r.returncode}: {r.stdout.strip()[-300:]} {r.stderr.strip()[-300:]}")
        tp = read_json(J / "judge_pack_test.json")
        if not tp or tp.get("verdict") != "PASS":
            summary["judge"] = "build-test failed"; return
        publish([J / "judge_pack_test.json"], "Experiment 08 § 10: judge test pack built (every IC_tests = 1 cell + the 60-cell audit per system; 3 repeats × 2 members)")
    if not deployed("judge-test", "veribench-rl4cv-e08-test", Path(tp["pack_abs"])):
        summary["judge"] = "test service unavailable"; return
    runs = (read_json(J / "state.json", {}) or {}).get("runs", {})
    systems = list(tp["per_system"])
    pending = [s for s in systems if not any(k.startswith(f"{s}/") for k in runs)]
    for s in pending:
        r = run([PY, drv, "admit", "--suite", f"rl4cv-e08:{s}", "--concurrency", "12"], timeout=1800); log(f"admit {s} rc={r.returncode}: {r.stdout.strip()[-200:]}")
    if pending:
        summary["judge"] = f"admitted {len(pending)} systems"; return
    if run([PY, drv, "poll"], timeout=1800).returncode != 0:
        summary["judge"] = "judging running"; return
    for s in systems:
        if not (J / f"fsc_{s}.json").exists():
            run([PY, drv, "harvest", "--suite", f"rl4cv-e08:{s}"], timeout=3600)
            r = run([PY, drv, "fsc", "--system", s], timeout=600); log(f"fsc {s} rc={r.returncode}: {r.stdout.strip()[-200:]}")
    if not all((J / f"fsc_{s}.json").exists() for s in systems):
        summary["judge"] = "fsc incomplete"; return
    publish([J], "Experiment 08 § 10: judge harvests and compile-gated FSC per system")
    summary["judge"] = "done"
    r = run([PY, str(S / "analyze_test.py")], timeout=3600); log(f"analyze_test rc={r.returncode}: {r.stdout.strip()[-300:]} {r.stderr.strip()[-300:]}")
    if r.returncode == 0:
        finalize(state, sel)


def finalize(state: dict, sel: dict) -> None:
    if (P / "DONE").exists():
        return
    update_results_final(sel)
    (WORK / "STATUS_e08").write_text("DONE\n")
    ok = publish([EXP / "results.md", RES / "test_eval.json"], f"Experiment 08: final results published (verdict {sel.get('verdict')})")
    write_json(P / "DONE", {"written_utc": ts(), "verdict": sel.get("verdict"), "published": ok, "note": "pipeline terminal receipt; operator finalizes README row, CKPT, teardown and cron"})
    log(f"FINAL DONE (published={ok})")


def update_results_final(sel: dict) -> None:
    te = read_json(RES / "test_eval.json")
    t = (EXP / "results.md").read_text()
    if te:
        lines = ["| System | Scope | Known / declared cells | IC_tests | IC_proofs | fsc_compiled | SCSC [task-bootstrap 95%] | kernel_binary mean |", "|---|---|---:|---:|---:|---:|---|---:|"]
        for lab, r in sorted(te["systems"].items()):
            for sc in ("all", "core", "industryset"):
                p = r["scopes"][sc]; pt = p["point_common_cohort"]; b = p.get("bootstrap95_task") or {}
                if pt.get("SCSC") is None:
                    lines.append(f"| `{lab}` | {sc} | {p['n_known_cells']} / {p['n_declared_cells']} | n/a | n/a | n/a | n/a | n/a |"); continue
                ci = b.get("SCSC")
                lines.append(f"| `{lab}` | {sc} | {p['n_known_cells']} / {p['n_declared_cells']} | {pt['IC_tests']:.4f} | {pt['IC_proofs']:.4f} | {pt['fsc_compiled']:.4f} | "
                             f"{pt['SCSC']:.4f}" + (f" [{ci[0]:.4f}, {ci[1]:.4f}]" if ci else "") + f" | {p.get('kernel_binary_mean_pass_rate')} |")
        plines = ["| Size | Selected − Base | kernel_binary mean pass-rate diff [95%] | SCSC diff [95%] | shared known cells |", "|---|---|---|---|---:|"]
        for size, scopes in (te.get("paired_differences") or {}).items():
            a = scopes.get("all") or {}
            if a:
                plines.append(f"| {size} | `{a.get('selected')}` − `{a.get('base')}` | {a.get('kernel_binary_mean_pass_rate_diff')} | {a.get('SCSC_diff')} | {a.get('n_shared_known_cells')} |")
        block = ("## Test evaluation (once; PROTOCOL § 10 and D-009: geometric mean of factor means on the common known cohort; 10,000 task-bootstrap resamples, seed 0; p-val=n/a)\n\n"
                 f"Verdict {sel['verdict']}, f* = {sel.get('f_star')}. Written {te['written_utc']} from `expt_v1/results/test_eval.json`; unknown cells stay in the declared denominator and are listed there.\n\n"
                 + "\n".join(lines) + "\n\nPaired differences on all 222 tasks (shared known cohort, shared resampled task indices):\n\n" + "\n".join(plines) + "\n\n")
        if "## Test evaluation (once;" in t:
            t = re.sub(r"## Test evaluation \(once;.*?(?=\n## )", block.rstrip("\n") + "\n", t, count=1, flags=re.S)
        else:
            t = t.replace("## Open questions for Brando", block + "## Open questions for Brando", 1)
    status = (f"**Status:** DONE ({local_stamp()}; verdict {sel['verdict']}; test split evaluated once after the committed selection)" if te
              else f"**Status:** DONE ({local_stamp()}; verdict {sel['verdict']}; no test evaluation because no size passed the validation gates)")
    t = re.sub(r"^\*\*Status:\*\* .*$", status, t, count=1, flags=re.M)
    t = re.sub(r"^\*\*Last updated:\*\* .*$", f"**Last updated:** {local_stamp()} (pipeline: final results)", t, count=1, flags=re.M)
    t = re.sub(r"^\*\*TLDR-end:\*\* .*$", f"**TLDR-end:** [rl4cv: expt 08 matched Lean SFT warm start] Verdict {sel['verdict']} (f* = {sel.get('f_star')}; tokens needed "
              f"{json.dumps(sel.get('tokens_needed'))}); the validation ladder and test tables above carry every count with its denominator.", t, count=1, flags=re.M)
    (EXP / "results.md").write_text(t)


# ----------------------------------------------------------------------------------------------- main loop
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry", action="store_true", help="observe and report; launch nothing, publish nothing")
    ap.add_argument("--interval", type=int, default=120)
    a = ap.parse_args()
    P.mkdir(parents=True, exist_ok=True)
    while True:
        with LOCK.open("w") as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            state = read_json(STATE_PATH, {"created": ts(), "stages": {}})
            if "sft_8B" not in state["stages"] and session_alive("rl4cv-e08-sft-8B"):
                state["stages"]["sft_8B"] = {"retries": 0, "session": "rl4cv-e08-sft-8B", "status": "running", "log": str(WORK / "ckpt" / "driver_8B.log"), "adopted": True,
                                             "watch": watch_globs("sft_8B")}
                take_lease("sft_8B", [0, 1, 2, 3], pid=pane_pid("rl4cv-e08-sft-8B"), kind="sft")
            try:
                summary = tick(state, a.dry)
            except Exception as exc:  # noqa: BLE001 keep the loop alive and record the failure
                summary = {"tick_error": repr(exc)[:400]}; log(f"tick error: {exc!r}")
            state.update(last_tick=ts(), summary=summary, boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(), pid=os.getpid(), dry=a.dry)
            write_json(STATE_PATH, state)
            print(json.dumps({k: v for k, v in summary.items() if v != "done"}, sort_keys=True))
            fcntl.flock(lk, fcntl.LOCK_UN)
        if a.once or (P / "DONE").exists():
            return 0
        time.sleep(a.interval)


if __name__ == "__main__":
    raise SystemExit(main())
