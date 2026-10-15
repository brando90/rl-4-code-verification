"""TLDR: Hosted Valkyrie helpers for the D-108 migration (10-14-2026): a `whoami` + `provider list` preflight that records non-secret evidence, server-side benchmark service registration through an organization secret, and a private local service registry that replaces the dead `valkyrie.yaml` fields.

Valkyrie moved from each user's own AWS account to Vals' hosted cloud. The current command-line interface
(`vals-ai/Valkyrie@prod`) reads only the login in `~/.config/valkyrie/sessions`, `VALKYRIE_API_KEY` and
`VALKYRIE_URL`; `VALKYRIE_CONFIG_PATH`, `VALKYRIE_ENV`, `custom_benchmark_services` and `benchmark_auth` do
nothing. A custom benchmark service is registered on the Tracker instead:

    valkyrie secret set <benchmark>-bearer            # value "Bearer <token>", piped on stdin
    valkyrie benchmark service set <benchmark> <url> --auth-secret <benchmark>-bearer --auth-header Authorization

The agent bundles (vb103_judge, vb103_single_call, vb106_rater_v2) named the gateway secret
`fellows/brandoModelGatewayApiKey`, which a hosted tenant cannot create; veribench's migration renames it in each
contract.yaml to `brandoModelGatewayApiKey` and changes nothing else (`matches_frozen` checks exactly that).

Registration needs a login (`valkyrie login`), not an access key, and must be repeated after every tunnel
restart because the URL changes. Secret values never reach the command line, logs or receipts.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

SECRET_NAME_RE = re.compile(r"^[A-Za-z0-9_+=.@-]{1,128}$")
# Slash-free tenant secret holding the Vals model-gateway credential (same name and override as veribench's helper).
GATEWAY_SECRET = os.environ.get("VB_GATEWAY_SECRET", "brandoModelGatewayApiKey")
OLD_GATEWAY_SECRET = "fellows/brandoModelGatewayApiKey"   # per-user-AWS name; a hosted tenant cannot create it
DEAD_ENV = ("VALKYRIE_CONFIG_PATH", "VALKYRIE_ENV")
WHOAMI_RE = re.compile(r"^(?P<who>.+?) in (?P<org>.+?) on (?P<url>\S+) \(using (?P<credential>[^)]+)\)\s*$")
PROVIDER_RE = re.compile(r"^(?P<default>[* ]) (?P<name>\S+) (?:→|->) (?P<secret>\S+)\s*$")

Runner = Callable[..., subprocess.CompletedProcess]


class HostedValkyrieError(RuntimeError):
    """A hosted-Valkyrie step failed; the message never contains a secret value."""


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def executable() -> str:
    """The `valkyrie` command: the experiment interpreter's own install first (cron may supply only system paths)."""
    local = Path(sys.executable).parent / "valkyrie"
    return str(local) if local.exists() else (shutil.which("valkyrie") or "valkyrie")


def cli_env(strip: Iterable[str] = (), base: dict[str, str] | None = None) -> dict[str, str]:
    """A copy of the environment without the given provider variables and without the dead YAML selectors."""
    drop = set(strip) | set(DEAD_ENV)
    out = {k: v for k, v in (os.environ if base is None else base).items() if k not in drop}
    out["PATH"] = str(Path(sys.executable).parent) + os.pathsep + out.get("PATH", os.defpath)
    return out


def run(args: list[str], *, env: dict[str, str] | None = None, input: str | None = None, timeout: float = 600,
        runner: Runner = subprocess.run) -> subprocess.CompletedProcess:
    return runner([executable(), *args], env=cli_env() if env is None else env, input=input,
                  stdin=None if input is not None else subprocess.DEVNULL, capture_output=True, text=True,
                  timeout=timeout)


def matches_frozen(data: bytes, frozen_sha256: str | None, *, allow_secret_rename: bool = False) -> str | None:
    """'identical' when `data` hashes to the frozen digest; with `allow_secret_rename`, 'secret_renamed_only' when the
    only change is the old slash gateway secret renamed to GATEWAY_SECRET; otherwise None."""
    if not frozen_sha256:
        return None
    if hashlib.sha256(data).hexdigest() == frozen_sha256:
        return "identical"
    if allow_secret_rename:
        text = data.decode("utf-8", errors="strict")
        restored = re.sub(r"(?<![/\w])" + re.escape(GATEWAY_SECRET) + r"(?!\w)", OLD_GATEWAY_SECRET, text)
        if restored != text and hashlib.sha256(restored.encode("utf-8")).hexdigest() == frozen_sha256:
            return "secret_renamed_only"
    return None


def parse_whoami(text: str) -> dict:
    for line in text.splitlines():
        m = WHOAMI_RE.match(line.strip())
        if m:
            credential = {"a login": "login", "an access key": "access_key"}.get(m["credential"], "none")
            return {"account": m["who"], "organization": m["org"], "tracker_url": m["url"], "credential": credential}
    return {}


def parse_providers(text: str) -> dict:
    providers, default = {}, None
    for line in text.splitlines():
        m = PROVIDER_RE.match(line.rstrip())
        if m:
            providers[m["name"]] = m["secret"]
            if m["default"] == "*":
                default = m["name"]
    return {"providers": providers, "default_provider": default}


def secret_names(text: str) -> list[str]:
    """Names from `valkyrie secret list --format json` (the list never carries values)."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    rows = data.get("secrets", data) if isinstance(data, dict) else data
    return sorted({str(r.get("name")) for r in rows if isinstance(r, dict) and r.get("name")}) if isinstance(rows, list) else []


def preflight(*, require_login: bool = False, require_secrets: Iterable[str] = (), require_agents: Iterable[str] = (),
              env: dict[str, str] | None = None, runner: Runner = subprocess.run) -> dict:
    """Check the host's Valkyrie identity and sandbox provider; return non-secret evidence with a PASS/FAIL verdict.

    This replaces the client-side AWS checks (boto3 STS, S3_BUCKET, /aws-runtime, the old account id): the hosted
    Tracker owns the cloud account now, so the evidence is the organization, the credential kind and the provider.
    """
    host = os.uname().nodename
    problems: list[str] = []
    who = run(["whoami"], env=env, runner=runner, timeout=120)
    identity = parse_whoami(who.stdout) if who.returncode == 0 else {}
    if not identity:
        problems.append("valkyrie whoami failed: run `valkyrie login` (`--no-browser` on a headless host)")
    elif identity["credential"] == "none":
        problems.append("valkyrie whoami reports no credential")
    elif require_login and identity["credential"] != "login":
        problems.append("benchmark service registration needs `valkyrie login`; an access key cannot change it")
    prov = run(["provider", "list"], env=env, runner=runner, timeout=120)
    providers = parse_providers(prov.stdout) if prov.returncode == 0 else {"providers": {}, "default_provider": None}
    if not providers["default_provider"] or providers["default_provider"] not in providers["providers"]:
        problems.append("no default sandbox provider with a secret: `valkyrie provider set daytona daytona` and "
                        "`valkyrie provider default daytona`")
    wanted = sorted(set(require_secrets))
    names: list[str] = []
    if wanted:
        listed = run(["secret", "list", "--format", "json"], env=env, runner=runner, timeout=120)
        names = secret_names(listed.stdout) if listed.returncode == 0 else []
        problems += [f"organization secret {n} is missing: `valkyrie secret set {n}`" for n in wanted if n not in names]
    agents_wanted = sorted(set(require_agents))
    agents: list[str] = []
    if agents_wanted:
        listed = run(["agent", "list", "--format", "json"], env=env, runner=runner, timeout=120)
        agents = agent_names(listed.stdout) if listed.returncode == 0 else []
        problems += [f"agent {n} is not installed in this organization: `valkyrie agent push <dir>`"
                     for n in agents_wanted if n not in agents]
    return {"checked_utc": stamp(), "host": host, "verdict": "FAIL" if problems else "PASS", "problems": problems,
            "identity": identity, **providers, "required_secrets": wanted,
            "required_secrets_present": [n for n in wanted if n in names], "required_agents": agents_wanted,
            "required_agents_present": [n for n in agents_wanted if n in agents],
            "evidence_commands": ["valkyrie whoami", "valkyrie provider list"]
            + (["valkyrie secret list --format json (names only)"] if wanted else [])
            + (["valkyrie agent list --format json"] if agents_wanted else [])}


def agent_names(text: str) -> list[str]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    rows = data.get("agents", data) if isinstance(data, dict) else data
    out = set()
    for r in rows if isinstance(rows, list) else []:
        if isinstance(r, dict):
            out.update(str(r[k]) for k in ("name", "alias", "agent_name") if r.get(k))
        elif isinstance(r, str):
            out.add(r)
    return sorted(out)


def bearer_secret_name(benchmark: str) -> str:
    name = f"{benchmark}-bearer"
    if not SECRET_NAME_RE.match(name):
        raise HostedValkyrieError(f"benchmark {benchmark!r} gives an invalid tenant secret name {name!r}")
    return name


def register_service(benchmark: str, url: str, bearer: str, *, header: str = "Authorization",
                     env: dict[str, str] | None = None, runner: Runner = subprocess.run) -> dict:
    """Store `Bearer <token>` as an organization secret and point the Tracker's benchmark service at `url`."""
    if not url.startswith("https://"):
        raise HostedValkyrieError(f"the Tracker needs a public https URL for {benchmark}")
    name = bearer_secret_name(benchmark)
    stored = run(["secret", "set", name], env=env, input="Bearer " + bearer.strip(), runner=runner, timeout=120)
    if stored.returncode:
        raise HostedValkyrieError(f"valkyrie secret set {name} failed (rc={stored.returncode})")
    saved = run(["benchmark", "service", "set", benchmark, url, "--auth-secret", name, "--auth-header", header],
                env=env, runner=runner, timeout=120)
    if saved.returncode:
        raise HostedValkyrieError(f"valkyrie benchmark service set {benchmark} failed (rc={saved.returncode}): "
                                  f"{redact(saved.stderr or saved.stdout, bearer)[-400:]}")
    return {"registered_utc": stamp(), "benchmark": benchmark, "auth_secret": name, "auth_header": header,
            "command": ["valkyrie", "benchmark", "service", "set", benchmark, "<tunnel url>", "--auth-secret", name,
                        "--auth-header", header]}


def redact(text: str, *values: str) -> str:
    for value in values:
        if value and len(value) >= 8:
            text = text.replace(value, "<redacted>")
    return text


def record_local(registry: Path, benchmark: str, url: str, bearer_file: Path, registration: dict) -> None:
    """Keep the URL and bearer location on this host (mode 0600) for direct service checks such as `/verify-task-ids`."""
    data = json.loads(registry.read_text()) if registry.exists() else {}
    data[benchmark] = {"url": url, "bearer_file": str(bearer_file), **{k: registration[k] for k in
                                                                       ("registered_utc", "auth_secret", "auth_header")}}
    registry.parent.mkdir(parents=True, exist_ok=True)
    tmp = registry.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.chmod(tmp, 0o600)
    tmp.replace(registry)


def lookup_local(registry: Path, benchmark: str) -> tuple[str, str]:
    """(service URL, Authorization header value) recorded by `record_local`."""
    data = json.loads(registry.read_text()) if registry.exists() else {}
    if benchmark not in data:
        raise HostedValkyrieError(f"{benchmark} is not registered on this host ({registry}); deploy or register it first")
    entry = data[benchmark]
    return entry["url"], "Bearer " + Path(entry["bearer_file"]).read_text().strip()
