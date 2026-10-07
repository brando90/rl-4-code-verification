#!/usr/bin/env python3
"""TLDR: Record experiment 02A v3's D-108 route identity with zero model calls: host, Valkyrie environment and organization, the Vals AWS identity behind the saved configuration, the agent's gateway-key secret mapping by name, the installed `vb103_single_call` bundle's hashes against experiment 103's frozen receipt, the payer, and a metadata-only gateway registry dump pinning the three teacher selectors."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import ssl
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
EXP = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("E02A_WORK", "/lfs/skampere1/0/brando9/rl4cv_e02a_v3"))
PRIVATE = WORK / "private"
E103 = REPO_ROOT / "external/veribench/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge"
AGENT_DIR = E103 / "scripts" / "valkyrie_single_call_agent"
HOST_CONFIG = Path.home() / ".config/valkyrie/valkyrie.yaml"
GATEWAY_URL = "https://dev.model-gateway.vals.ai"
GATEWAY_KEY_SECRET = "fellows/brandoModelGatewayApiKey"     # the agent contract's secret mapping, by name only
AGENT = "vb103_single_call"
TEACHER_HINTS = {"anthropic": ["fable"], "openai": ["astra"], "google": ["argon"]}
PUBLIC_ENTRY_KEYS = ("label", "company", "provider_name", "provider_endpoint", "release_date", "default_parameters", "properties", "supports",
                     "costs_per_million_token", "metadata")


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):  # noqa: D102
        raise ValueError("gateway redirects prohibited")


def valk(*args: str, timeout: float = 600) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")}
    env.update(VALKYRIE_ENV="bench")
    return subprocess.run(["valk", *args], env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)


def entry_public(entry: dict) -> dict:
    pp = entry.get("provider_properties") or {}
    out = {k: entry.get(k) for k in PUBLIC_ENTRY_KEYS if k in entry}
    out.update(fallback_models=pp.get("fallback_models"), supports_compute_effort=pp.get("supports_compute_effort"),
               provider_properties_keys=sorted(pp), entry_sha256=sha(json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=EXP / "results" / "route_identity_e02a_v3.json")
    a = ap.parse_args()
    import boto3
    import yaml

    os.umask(0o077)
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    cfg = yaml.safe_load(HOST_CONFIG.read_text())
    session = boto3.Session(aws_access_key_id=cfg["AWS_ACCESS_KEY_ID"], aws_secret_access_key=cfg["AWS_SECRET_ACCESS_KEY"],
                            aws_session_token=cfg.get("AWS_SESSION_TOKEN"), region_name=cfg.get("AWS_DEFAULT_REGION", "us-east-1"))
    ident = session.client("sts").get_caller_identity()
    key = session.client("secretsmanager").get_secret_value(SecretId=GATEWAY_KEY_SECRET)["SecretString"]
    try:
        obj = json.loads(key)
        if isinstance(obj, dict):
            key = next(obj[k] for k in ("MODEL_GATEWAY_API_KEY", "api_key", "key") if k in obj)
    except json.JSONDecodeError:
        pass
    # Metadata-only GET of the gateway registry (no /query; zero inference), as experiment 103's fetch_model_registry.py did.
    req = urllib.request.Request(GATEWAY_URL + "/registry", headers={"Authorization": "Bearer " + key, "Accept": "application/json"}, method="GET")
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    with opener.open(req, timeout=60) as r:
        body = r.read(32 * 1024 * 1024)
    del key
    registry = json.loads(body)
    models = registry["models"]
    reg_dir = PRIVATE / "registry"
    reg_dir.mkdir(mode=0o700, exist_ok=True)
    reg_path = reg_dir / f"registry_{stamp().replace(':', '')}.json"
    reg_path.write_bytes(body)
    os.chmod(reg_path, 0o600)
    candidates = {}
    for provider, hints in TEACHER_HINTS.items():
        sel = sorted(k for k in models if k.split("/", 1)[0] == provider and any(h in k.lower() for h in hints))
        candidates[provider] = {k: entry_public(models[k]) for k in sel}
    # The installed agent bundle versus experiment 103's frozen receipt.
    frozen = json.loads((E103 / "results" / "agent_bundle.json").read_text())
    local = {rel: sha((AGENT_DIR / rel).read_bytes()) for rel in ("contract.yaml", "prompts/addendum_vbv1.md", "setup.sh", "single_call.py")}
    with tempfile.TemporaryDirectory(dir=PRIVATE, prefix="agent_dl_") as td:
        dl = valk("agent", "download", AGENT, "-o", td)
        downloaded = {str(p.relative_to(td)).split("/", 1)[-1] if str(p.relative_to(td)).startswith(AGENT + "/") else str(p.relative_to(td)): sha(p.read_bytes())
                      for p in sorted(Path(td).rglob("*")) if p.is_file()}
    contract = yaml.safe_load((AGENT_DIR / "contract.yaml").read_text())
    runs = valk("run", "list", "--all", "--format", "json", "--benchmark-name", "rl4cv-e02a-v3-mbpp")
    out = {
        "written_utc": stamp(), "host": os.uname().nodename, "cli": valk("--version").stdout.strip() or "valk (version flag unsupported)",
        "valkyrie_config": {"path": str(HOST_CONFIG), "environment": cfg.get("environment"), "log_group": cfg.get("LOG_GROUP"), "s3_bucket": cfg.get("S3_BUCKET"),
                            "default_sandbox_provider": cfg.get("default_sandbox_provider"), "sandbox_providers": sorted((cfg.get("sandbox_providers") or {}).keys()),
                            "note": "contents never copied; the private copy used by runs adds this experiment's benchmark service and bearer"},
        "aws_identity": {"arn": ident["Arn"], "account": ident["Account"],
                         "owner": "Vals (account 613431292675, as recorded by VeriBench experiments 90 and 103)"},
        "gateway": {"url": GATEWAY_URL, "key_secret_name": GATEWAY_KEY_SECRET, "key_secret_resolves": True,
                    "registry_fetched_utc": out_stamp if (out_stamp := stamp()) else None, "registry_models": len(models),
                    "registry_sha256": sha(body), "registry_private_copy": str(reg_path), "calls": "GET /registry only (metadata); zero /query calls"},
        "agent": {"name": AGENT, "contract_secrets": contract.get("secrets"), "contract_kwargs": sorted((contract.get("kwargs") or {}).keys()),
                  "run_cmd_gateway_url": re.search(r"MODEL_GATEWAY_URL=(\S+)", contract.get("run_cmd", "")).group(1),
                  "local_files_sha256": local, "installed_files_sha256": downloaded, "download_exit_code": dl.returncode,
                  "frozen_receipt_sha256": frozen.get("downloaded_files_sha256"), "bundle_manifest_sha256_frozen": frozen.get("bundle_manifest_sha256"),
                  "installed_matches_frozen": all(downloaded.get(k) == v for k, v in (frozen.get("downloaded_files_sha256") or {}).items()) and bool(downloaded),
                  "local_matches_frozen": all(local.get(k) == v for k, v in (frozen.get("downloaded_files_sha256") or {}).items())},
        "payer": "Vals: the provider credential is Vals' gateway key in Vals' Secrets Manager, mapped into the sandbox by Valkyrie's secret mapping; no personal key or subscription token is used",
        "route": "Valkyrie run (valk run start --agent vb103_single_call --benchmark rl4cv-e02a-v3-mbpp --model <selector>); the agent calls the Vals model gateway from inside the sandbox",
        "prior_runs_on_this_benchmark": {"exit_code": runs.returncode, "n": len(json.loads(runs.stdout)) if runs.returncode == 0 and runs.stdout.strip().startswith("[") else None},
        "teacher_selector_candidates": candidates,
    }
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"aws_account": ident["Account"], "environment": cfg.get("environment"), "registry_models": len(models),
                      "installed_matches_frozen": out["agent"]["installed_matches_frozen"], "download_exit_code": dl.returncode,
                      "candidates": {p: list(c) for p, c in candidates.items()}}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
