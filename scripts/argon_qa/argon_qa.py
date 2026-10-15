#!/usr/bin/env python3
"""TLDR: Run a read-only QA review of committed repository snapshots by Gemini 4 Argon through Valkyrie's existing `vb106_rater_v2` transport agent on the Vals model gateway: build packets, self-check them offline, deploy a collect-only benchmark service, admit, harvest and tear down."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from rl4cv.valkyrie_transport import Transport

HOME = Path(os.environ.get("RL4CV_ARGON_QA_HOME", "~/.cache/rl4cv-argon-qa")).expanduser()
VERIBENCH = Path(os.environ.get("VERIBENCH_ROOT", "~/veribench")).expanduser()
SERVICE_DIR = (VERIBENCH / "experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge"
               / "scripts/vb_service_single_call")
AGENT_DIR = (VERIBENCH / "experiments/106_simulated_expert_raters_icl_from_human_labels_leave_one_agent_out_fsc_judge"
             / "scripts/valkyrie_rater_agent_v2")
VALKYRIE_VENV = Path("~/.local/share/uv/tools/valkyrie").expanduser()
CLOUDFLARED = shutil.which("cloudflared") or "/opt/homebrew/bin/cloudflared"
HOST_CONFIG = Path("~/.config/valkyrie/valkyrie.yaml").expanduser()

AGENT, MODEL, BENCHMARK, PORT = "vb106_rater_v2", "google/gemini-4-argon", "rl4cv-argon-qa", 9741
RUN_KWARGS = {"max_tokens": "65536", "reasoning_effort": "high", "temperature": "1.0", "benchmark": BENCHMARK}
OUTPUT_PATH = "/home/user/lean_project/Veribench/QaReview.lean"
STAMP = "<!-- VeriBench agent-spec v7: rl4cv read-only QA review transport task, not a solver task -->"
SYS_BEGIN, SYS_END = "=== VB106_RATER_SYSTEM_BEGIN ===", "=== VB106_RATER_SYSTEM_END ==="
USER_BEGIN, USER_END = "=== VB106_RATER_USER_BEGIN ===", "=== VB106_RATER_USER_END ==="
MARKERS = (SYS_BEGIN, SYS_END, USER_BEGIN, USER_END, "vb106-rater-cell")
TEST_SH = ('#!/usr/bin/env bash\n'
           '# TLDR: Path declaration for an rl4cv QA transport task; the service reads only the SOLUTION_FILE line.\n'
           f'SOLUTION_FILE="{OUTPUT_PATH}"\n'
           'exit 0\n')
DEFAULT_SCOPE = "experiments/01_small_open_models_veribench_v1_single_call_baseline"
DEFAULT_PACKETS = ("qa__e01_a=1ea02ee", "qa__e01_b=1904868")
DEFAULT_CONTEXT = ("CLAUDE.md", "experiments/README.md", "docs/DECISIONS.md")
# Raw per-cell data: listed in the manifest with its size, contents left out of the packet.
DEFAULT_OMIT = (r"/judge/harvests/", r"/judge/judge_pack_[^/]*\.json$", r"task_ids[^/]*\.txt$",
                r"/orchestration/jobs_gpu[^/]*\.txt$", r"/orchestration/shared_queue\.txt$")
PROVIDER_ENV = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY",
                "MODEL_GATEWAY_API_KEY", "VALKYRIE_API_KEY", "TRACKER_SERVICE_URL",
                "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_AUTH_TOKEN", "AUTH_DISABLED", "PYTHONPATH", "PYTHONHOME")
SECRET_RES = (re.compile(r"(api[_-]?key|token|password|secret|auth|bearer)\s*[:=]\s*[\"']?[A-Za-z0-9_\-/+]{16,}", re.I),
              re.compile(r"sk-ant-[A-Za-z0-9_\-]{10,}"), re.compile(r"\bsk-[A-Za-z0-9]{20,}"),
              re.compile(r"AKIA[0-9A-Z]{16}"), re.compile(r"ghp_[A-Za-z0-9]{20,}"), re.compile(r"hf_[A-Za-z]{30,}"))

SYSTEM_PROMPT = """You are an independent quality-assurance (QA) reviewer for a private research repository. You receive a snapshot of one experiment's files (design documents, protocol, code, checkpoints and result summaries) together with the project's rules (CLAUDE.md), the experiment index and the decision log, all at one commit. You cannot run code, open other files or ask questions: review only what is in the packet, and say so when something cannot be checked from it.

Review for CORRECTNESS and SCIENTIFIC INTEGRITY. Flag critical and major issues first:
- claims that contradict each other, the result files, the manifest or the code;
- incomplete or stale reporting: declared models, cells, tables or runs that are missing, status lines that disagree with other files, numbers that do not match their source files;
- logic errors in code (scoring, aggregation, denominators, gating, parsing, retries and resumption, process management);
- violations of the project rules in CLAUDE.md (held-out data, evaluation and scoring rules, compile-gated FSC, unmeasured cells kept in denominators, prospective chronology, model-call routes, file headers);
- verdicts or decisions stated without the evidence that would support them.

For each finding give: an ID (F1, F2, ...), severity (CRITICAL, MAJOR or MINOR), the file path(s), a short verbatim quote or line reference as evidence, why it is wrong, and the minimal fix. Mark a finding UNCERTAIN when the packet cannot settle it. Do not report style preferences, and never invent file contents or quote text that is not in the packet. This is a read-only review: describe fixes, do not rewrite files.

End with exactly:
VERDICT: PASS | FAIL
CRITICAL_ISSUES: [count]
MAJOR_ISSUES: [count]
MINOR_ISSUES: [count]
SUMMARY: [1-2 sentences]
If everything is correct, use PASS with all counts 0."""


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def private_dir(*parts: str) -> Path:
    os.umask(0o077)
    path = HOME.joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(HOME, 0o700)
    return path


def read_json(path: Path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def git(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(REPO), *args], check=True, capture_output=True).stdout


def clean_env(**extra: str) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in PROVIDER_ENV}
    env.update(extra)
    return env


def transport() -> Transport:
    return Transport(HOME / "valkyrie.yaml")


def valkyrie(*args: str, timeout: float = 600) -> subprocess.CompletedProcess:
    return transport().run(list(args), timeout=timeout)


# ------------------------------------------------------------------------------------------------- build
def tracked(commit: str, paths: list[str]) -> list[tuple[str, int]]:
    rows = git("ls-tree", "-r", "-l", commit, "--", *paths).decode().splitlines()
    return [(line.split("\t", 1)[1], int(line.split()[3])) for line in rows]


def file_block(commit: str, path: str) -> str:
    data = git("show", f"{commit}:{path}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = "[binary file, contents omitted]"
    return (f"=== FILE: {path} ({len(data)} bytes, sha256 {sha(data)[:16]}) ===\n{text}"
            f"{'' if text.endswith(chr(10)) else chr(10)}=== END FILE: {path} ===\n")


def user_prompt(commit: str, scope: str, context: list[str], omit: list[re.Pattern]) -> str:
    full = git("rev-parse", commit).decode().strip()
    files = tracked(commit, [scope])
    kept = [p for p, _ in files if not any(rx.search(p) for rx in omit)]
    manifest = "\n".join(f"- {p} ({n} bytes){'' if p in kept else ' [omitted: raw per-cell data]'}"
                         for p, n in files)
    present = [p for p, _ in tracked(commit, context)]
    return (f"Repository: rl-4-code-verification (private). Snapshot commit: {full}.\n"
            f"Review scope: {scope}/ (every file below), checked against the project rules (CLAUDE.md), the "
            f"experiment index (experiments/README.md) and the decision log (docs/DECISIONS.md) at the same commit.\n\n"
            f"## File manifest: every tracked file in scope ({len(files)} files)\n{manifest}\n\n"
            f"## Project context files\n\n" + "\n".join(file_block(commit, p) for p in present)
            + f"\n## Files in scope ({len(kept)} included)\n\n" + "\n".join(file_block(commit, p) for p in kept))


def secret_hits(text: str) -> list[str]:
    hits = [rx.pattern[:40] for rx in SECRET_RES if rx.search(text)]
    known = [HOME / "service_bearer"]
    values = [p.read_text().strip() for p in known if p.exists()]
    if HOST_CONFIG.exists():
        import yaml
        cfg = yaml.safe_load(HOST_CONFIG.read_text()) or {}
        values += [str(v) for k, v in cfg.items() if isinstance(v, str) and re.search("key|secret|token", k, re.I)]
    hits += ["a configured credential value" for v in values if len(v) >= 12 and v in text]
    return hits


def cmd_build(args) -> int:
    pack = private_dir("pack")
    shutil.rmtree(pack)
    pack.mkdir(mode=0o700)
    omit = [re.compile(p) for p in args.omit]
    manifest = {"built_utc": stamp(), "scope": args.scope, "context": args.context, "omit": args.omit,
                "system_sha256": sha(SYSTEM_PROMPT.encode()), "cells": []}
    for spec in args.packet:
        task_id, commit = spec.split("=", 1)
        user = user_prompt(commit, args.scope, args.context, omit)
        for text, what in ((SYSTEM_PROMPT, "system"), (user, "user")):
            bad = [m for m in MARKERS if m in text]
            if bad:
                raise SystemExit(f"{task_id}: the {what} prompt contains transport markers {bad}")
        hits = secret_hits(user)
        if hits:
            raise SystemExit(f"{task_id}: secret scan matched {sorted(set(hits))}; refusing to build")
        header = {"cell": task_id, "commit": git("rev-parse", commit).decode().strip(), "scope": args.scope,
                  "output_path": OUTPUT_PATH, "system_sha256": sha(SYSTEM_PROMPT.encode()),
                  "user_sha256": sha(user.encode()), "prompt_sha256": sha((SYSTEM_PROMPT + "\n\n" + user).encode())}
        body = (STAMP + "\n<!-- vb106-rater-cell: " + json.dumps(header, sort_keys=True, ensure_ascii=True) + " -->\n"
                + SYS_BEGIN + "\n" + SYSTEM_PROMPT + "\n" + SYS_END + "\n"
                + USER_BEGIN + "\n" + user + "\n" + USER_END + "\n")
        (pack / task_id / "tests").mkdir(parents=True)
        (pack / task_id / "instruction.md").write_text(body, encoding="utf-8")
        (pack / task_id / "tests/test.sh").write_text(TEST_SH)
        manifest["cells"].append({**header, "task_id": task_id, "instruction_bytes": len(body.encode()),
                                  "user_bytes": len(user.encode()), "approx_tokens": len(body.encode()) // 4,
                                  "instruction_sha256": sha(body.encode())})
        print(f"{task_id}: commit {header['commit'][:10]}, {len(body.encode()):,} bytes, secret scan clean")
    write_json(HOME / "pack_manifest.json", manifest)
    return 0


def cmd_selfcheck(args) -> int:
    """Round-trip every task file through the agent's own parser and the service's own pack loader."""
    sys.path[:0] = [str(AGENT_DIR), str(SERVICE_DIR)]
    import rater_call                                         # the installed agent's committed source
    import veribench_valkyrie_service as service
    manifest = read_json(HOME / "pack_manifest.json")
    tasks = service.load_task_pack(HOME / "pack")
    ok = True
    for cell in manifest["cells"]:
        text = (HOME / "pack" / cell["task_id"] / "instruction.md").read_text(encoding="utf-8")
        header, system, user = rater_call.parse_task_file(text)
        checks = {"system": sha(system.encode()) == header["system_sha256"] == cell["system_sha256"],
                  "user": sha(user.encode()) == header["user_sha256"] == cell["user_sha256"],
                  "prompt": sha((system + "\n\n" + user).encode()) == header["prompt_sha256"],
                  "system_is_frozen_prompt": system == SYSTEM_PROMPT,
                  "output_path": bool(rater_call.OUTPUT_RE.fullmatch(header["output_path"])),
                  "service_loads": tasks[cell["task_id"]].solution_path == OUTPUT_PATH,
                  "secret_scan": not secret_hits(text)}
        ok &= all(checks.values())
        print(cell["task_id"], "PASS" if all(checks.values()) else "FAIL", checks)
    return 0 if ok else 1


# ------------------------------------------------------------------------------------------------ deploy
def probe(url: str, bearer: str | None) -> int:
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {bearer}"} if bearer else {})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:  # noqa: BLE001 - not reachable yet
        return 0


def alive(pid) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except (TypeError, ValueError, OSError):
        return False


def wait_for(check, what: str, tries: int = 90, delay: float = 2.0):
    for _ in range(tries):
        result = check()
        if result:
            return result
        time.sleep(delay)
    raise SystemExit(f"{what} timed out")


def cmd_deploy(args) -> int:
    receipt_path = HOME / "deployment.json"
    old = read_json(receipt_path, {})
    if alive(old.get("service_pid")) or alive(old.get("tunnel_pid")):
        raise SystemExit("a live deployment is recorded; run teardown first (a new tunnel URL orphans a running run)")
    selected = transport()
    if selected.mode == "hosted":
        selected.preflight(registration=True)
    logs = private_dir("logs")
    bearer_path = HOME / "service_bearer"
    if not bearer_path.exists():
        bearer_path.write_text(secrets.token_urlsafe(36))
    os.chmod(bearer_path, 0o600)
    bearer = bearer_path.read_text().strip()
    env = clean_env(VB_SERVICE_KEY_FILE=str(bearer_path), VB_TASK_PACK=str(HOME / "pack"), VB_CONTROL_PACK="1",
                    VB_NO_COMPILER="1", VB_COLLECT_ONLY="1", VB_GRADE_NETNS="off", VB_IC_PP="offline",
                    VB_LAKE_DIR=str(VERIBENCH / "veribench_dataset/lean_src"),
                    VB_KERNEL_AXIOMS=str(VERIBENCH / "scripts/scsc/kernel_axioms.py"),
                    VB_GRADE_SCRATCH=str(private_dir("grade_scratch")), VB_AGENT_TIMEOUT_S="5400",
                    VB_SETUP_TIMEOUT_S="900", VB_RESOURCES_VCPU="2", VB_RESOURCES_MEMORY="4",
                    VB_RESOURCES_DISK="20")
    local = f"http://127.0.0.1:{PORT}"
    service = subprocess.Popen([str(VALKYRIE_VENV / "bin/uvicorn"), "main:app", "--host", "127.0.0.1",
                                "--port", str(PORT)], cwd=str(SERVICE_DIR), env=env, stdin=subprocess.DEVNULL,
                               stdout=open(logs / "service.log", "ab"), stderr=subprocess.STDOUT,
                               start_new_session=True)
    wait_for(lambda: probe(local + "/health", bearer) == 200 or service.poll() is not None, "local health")
    if service.poll() is not None:
        raise SystemExit("service exited during startup; see logs/service.log")
    if probe(local + "/health", None) != 401:
        service.terminate()
        raise SystemExit("local service answered an unauthenticated probe; refusing to expose it")
    tunnel_log = logs / "tunnel.log"
    tunnel_log.write_bytes(b"")
    tunnel = subprocess.Popen([CLOUDFLARED, "tunnel", "--no-autoupdate", "--url", local],
                              stdin=subprocess.DEVNULL, stdout=open(tunnel_log, "ab"), stderr=subprocess.STDOUT,
                              start_new_session=True)
    url = wait_for(lambda: (re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", tunnel_log.read_text())
                            or [None])[-1], "tunnel hostname")
    wait_for(lambda: probe(url + "/health", bearer) == 200, "tunnel health", tries=60)
    unauth = probe(url + "/health", None)
    if unauth != 401:
        for proc in (service, tunnel):
            proc.terminate()
        raise SystemExit(f"tunnel answered an unauthenticated probe with {unauth}; refusing")
    try:
        registration = selected.register(BENCHMARK, url, bearer_path, HOST_CONFIG)
    except Exception:
        for proc in (tunnel, service):
            proc.terminate()
        raise
    write_json(receipt_path, {
        "deployed_utc": stamp(), **registration, "bearer_file": str(bearer_path), "benchmark": BENCHMARK, "port": PORT, "tunnel_url": url,
        "service_pid": service.pid, "tunnel_pid": tunnel.pid, "local_health": 200, "local_unauthenticated": 401,
        "tunnel_health": 200, "tunnel_unauthenticated": unauth,
        "service_code": str(SERVICE_DIR), "veribench_head": subprocess.run(
            ["git", "-C", str(VERIBENCH), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "service_files_sha256": {p.name: sha(p.read_bytes()) for p in sorted(SERVICE_DIR.glob("*.py"))}})
    print(f"deployed {BENCHMARK} on port {PORT} behind {url}: health 200, unauthenticated 401 (local and tunnel)")
    return 0


# ------------------------------------------------------------------------------------------- run control
def cmd_admit(args) -> int:
    state = read_json(HOME / "run.json", {})
    if state.get("run_id") and not args.force:
        raise SystemExit(f"run {state['run_id']} is already admitted; refusing a second admission")
    selected = transport()
    selected.require_receipt(read_json(HOME / "deployment.json", {}))
    selected.preflight()
    command = ["run", "start", "--agent", AGENT, "--benchmark", BENCHMARK, "--dataset", "default", "--model", MODEL,
               "--concurrency", "2", "--label", args.label]
    for key, value in RUN_KWARGS.items():
        command += ["-k", key, value]
    done = valkyrie(*command)
    (private_dir("logs") / "admit.log").write_text(done.stdout + done.stderr)
    found = re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", done.stdout + done.stderr)
    if done.returncode or not found:
        raise SystemExit(f"admission failed (rc={done.returncode}); see logs/admit.log")
    write_json(HOME / "run.json", {"run_id": found[0], **selected.identity(), "admitted_utc": stamp(), "agent": AGENT, "model": MODEL,
                                   "benchmark": BENCHMARK, "kwargs": RUN_KWARGS, "command": ["valkyrie", *command]})
    print("admitted run", found[0])
    return 0


def cmd_status(args) -> int:
    state = read_json(HOME / "run.json")
    transport().require_receipt(state)
    run_id = state["run_id"]
    done = valkyrie("run", "tasks", run_id)
    print(done.stdout[-4000:] or done.stderr[-2000:])
    return done.returncode


RECEIPT_KEYS = ("task_id", "selector", "status", "started", "ended", "wall_seconds", "requests_sent", "usage",
                "cost_usd", "finish_reason", "fallback", "provider_name", "provider_endpoint", "config",
                "wire_provider_config", "temperature_dropped_unsupported", "wire", "system_sha256", "user_sha256",
                "prompt_sha256", "expected", "output_text_sha256", "output_text_bytes", "written_file",
                "error_kind", "http_status", "reason")


def cmd_harvest(args) -> int:
    state = read_json(HOME / "run.json")
    transport().require_receipt(state)
    run_id = state["run_id"]
    raw = private_dir("raw", run_id)
    results, artifacts = raw / "results.json", raw / "artifacts"
    shutil.rmtree(artifacts, ignore_errors=True)
    for command in (["run", "results", run_id, "--path", str(results)], ["run", "output", run_id, "-o", str(artifacts)]):
        done = valkyrie(*command, timeout=1800)
        with (private_dir("logs") / "harvest.log").open("a") as log:
            log.write(f"{stamp()} {' '.join(command[:2])} rc={done.returncode}\n{done.stdout[-2000:]}{done.stderr[-2000:]}\n")
    out = Path(args.out)
    (out / "responses").mkdir(parents=True, exist_ok=True)
    (out / "receipts").mkdir(parents=True, exist_ok=True)
    seen = []
    for path in sorted(artifacts.rglob("receipt.json")):
        receipt = json.loads(path.read_text())
        task_id = receipt.get("task_id") or path.parent.name
        response = path.parent / "response.txt"
        if not response.exists():
            tarball = next(path.parent.glob("*.tar.gz"), None)
            if tarball:
                import tarfile
                with tarfile.open(tarball) as tf:
                    member = next((m for m in tf.getmembers() if m.name.endswith("/response.txt")), None)
                    if member:
                        response.write_bytes(tf.extractfile(member).read())
        if response.exists():
            text = response.read_text()
            if secret_hits(text):
                raise SystemExit(f"{task_id}: the response matched the secret scan; not copying it")
            (out / "responses" / f"{task_id}.md").write_text(text)
        write_json(out / "receipts" / f"{task_id}.json",
                   {"run_id": run_id, **{k: receipt[k] for k in RECEIPT_KEYS if k in receipt}})
        seen.append((task_id, receipt.get("status"), receipt.get("cost_usd")))
    print(json.dumps({"run_id": run_id, "cells": seen, "results_json": results.exists()}, indent=1))
    return 0 if seen else 1


def cmd_teardown(args) -> int:
    receipt = read_json(HOME / "deployment.json", {})
    for key in ("tunnel_pid", "service_pid"):
        if alive(receipt.get(key)):
            os.killpg(int(receipt[key]), signal.SIGTERM)
    time.sleep(3)
    still = [k for k in ("tunnel_pid", "service_pid") if alive(receipt.get(k))]
    listening = subprocess.run(["lsof", "-nP", f"-iTCP:{PORT}", "-sTCP:LISTEN"], capture_output=True, text=True).stdout
    receipt.update(torn_down_utc=stamp(), still_alive=still, port_free=not listening.strip())
    write_json(HOME / "deployment.json", receipt)
    print(f"teardown: still alive {still or 'none'}; port {PORT} {'free' if not listening.strip() else 'IN USE'}")
    return 0 if not still and not listening.strip() else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    build = sub.add_parser("build")
    build.add_argument("--scope", default=DEFAULT_SCOPE)
    build.add_argument("--packet", action="append", help="task_id=commit (repeatable)")
    build.add_argument("--context", nargs="*", default=list(DEFAULT_CONTEXT))
    build.add_argument("--omit", nargs="*", default=list(DEFAULT_OMIT))
    admit = sub.add_parser("admit")
    admit.add_argument("--label", default="rl4cv-e01-argon-qa")
    admit.add_argument("--force", action="store_true", help="admit although a run is recorded (a new cell set)")
    harvest = sub.add_parser("harvest")
    harvest.add_argument("--out", required=True, help="directory receiving responses/ and receipts/")
    for name in ("selfcheck", "deploy", "status", "teardown"):
        sub.add_parser(name)
    args = ap.parse_args()
    if args.cmd == "build":
        args.packet = args.packet or list(DEFAULT_PACKETS)
    private_dir()
    return globals()[f"cmd_{args.cmd}"](args)


if __name__ == "__main__":
    sys.exit(main())
