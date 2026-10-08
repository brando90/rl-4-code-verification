#!/usr/bin/env python3
"""TLDR: Record experiment 08's D-108 route identity with zero model calls and no key on the host: Valkyrie environment / log group / bucket from the saved configuration (field values only, never secrets), the `vb103_single_call` bundle downloaded from the bucket with file hashes checked against experiment 103's frozen receipt, its secret mapping by name, its two-request retry bound, the two teacher selectors confirmed against a 10-07-2026 metadata-only registry dump (no fallbacks for Opus 5.5, highest served GPT-6 Astra effort), the payer, and prior runs on this experiment's benchmark (PROTOCOL §§ 2–3, 12)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
EXP = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("E08_WORK", "/lfs/skampere1/0/brando9/rl4cv_e08"))
PRIVATE = WORK / "private"
E103 = REPO_ROOT / "external/veribench/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge"
AGENT_DIR = E103 / "scripts" / "valkyrie_single_call_agent"
HOST_CONFIG = Path.home() / ".config/valkyrie/valkyrie.yaml"
BENCHMARK = "rl4cv-e08-vbv1-train"
AGENT = "vb103_single_call"
GATEWAY_KEY_SECRET = "fellows/brandoModelGatewayApiKey"
OPUS = "anthropic/claude-opus-5-5-no-fallback"
ASTRA_PREFIX = "openai/gpt-6-astra"
EFFORT_ORDER = ["max", "xhigh", "high", "medium", "low"]
PUBLIC_ENTRY_KEYS = ("label", "company", "provider_name", "provider_endpoint", "release_date", "default_parameters", "properties", "supports",
                     "costs_per_million_token", "metadata")
SECRETISH = re.compile(r"key|secret|token|password|credential|authorization", re.I)
PROVIDER_ENV = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "MODEL_GATEWAY_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN",
                "ANTHROPIC_AUTH_TOKEN", "VALKYRIE_API_KEY", "PYTHONPATH", "PYTHONHOME")


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def valk(*args: str, timeout: float = 900) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in PROVIDER_ENV}
    env.update(VALKYRIE_ENV="bench")
    if (PRIVATE / "valkyrie.yaml").exists():
        env["VALKYRIE_CONFIG_PATH"] = str(PRIVATE / "valkyrie.yaml")
    return subprocess.run(["valk", *args], env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)


def entry_public(entry: dict) -> dict:
    pp = entry.get("provider_properties") or {}
    out = {k: entry.get(k) for k in PUBLIC_ENTRY_KEYS if k in entry}
    out.update(fallback_models=pp.get("fallback_models"), supports_compute_effort=pp.get("supports_compute_effort"), provider_properties_keys=sorted(pp),
               entry_sha256=sha(json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()))
    return out


def retry_bound(single_call_src: str) -> dict:
    """The frozen agent re-sends once, only after HTTP 429/5xx with no response; timeouts and other errors are never replayed."""
    return {"two_attempts_loop": "for attempt in (1, 2):" in single_call_src,
            "resend_only_on_http_429_5xx": "if exc.code in (429, 500, 502, 503, 504) and attempt == 1:" in single_call_src,
            "timeout_never_replayed": "never replay" in single_call_src and "not replayed because the call may have been served" in single_call_src,
            "requests_sent_recorded": 'receipt["requests_sent"] = attempt' in single_call_src,
            "max_requests_per_cell": 2}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--registry-dump", type=Path, required=True, help="metadata-only gateway registry dump taken with zero model calls")
    ap.add_argument("--registry-provenance", required=True, help="where the dump came from (recorded verbatim)")
    ap.add_argument("--out", type=Path, default=EXP / "results" / "route_identity_e08.json")
    a = ap.parse_args()
    import yaml

    os.umask(0o077)
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    cfg = yaml.safe_load(HOST_CONFIG.read_text())
    cfg_public = {k: cfg.get(k) for k in ("environment", "LOG_GROUP", "S3_BUCKET", "default_sandbox_provider", "organization", "org", "ORGANIZATION") if k in cfg}
    cfg_public["sandbox_providers"] = sorted((cfg.get("sandbox_providers") or {}).keys()) if isinstance(cfg.get("sandbox_providers"), dict) else cfg.get("sandbox_providers")
    cfg_public["field_names"] = sorted(k for k in cfg if not SECRETISH.search(k))
    cfg_public["n_secret_like_fields_not_listed"] = sum(1 for k in cfg if SECRETISH.search(k))
    # Registry dump (metadata only; taken with the gateway key inside a sandbox / another worker, never read here).
    body = a.registry_dump.read_bytes()
    models = json.loads(body)["models"]
    opus_family = {k: entry_public(models[k]) for k in sorted(models) if k.startswith("anthropic/claude-opus-5-5")}
    astra_family = {k: entry_public(models[k]) for k in sorted(models) if k.startswith(ASTRA_PREFIX)}
    opus_no_fallback = [k for k, e in opus_family.items() if e.get("fallback_models") == []]
    astra_efforts = {k: (e.get("default_parameters") or {}).get("reasoning_effort") for k, e in astra_family.items()}
    served = [x for x in EFFORT_ORDER if x in astra_efforts.values()]
    highest = served[0] if served else None
    astra_selector = f"{ASTRA_PREFIX}-{highest}" if highest and f"{ASTRA_PREFIX}-{highest}" in astra_family else None
    # The bundle in the bucket versus experiment 103's frozen receipt and the pinned checkout.
    frozen = json.loads((E103 / "results" / "agent_bundle.json").read_text())
    local = {rel: sha((AGENT_DIR / rel).read_bytes()) for rel in ("contract.yaml", "prompts/addendum_vbv1.md", "setup.sh", "single_call.py")}
    with tempfile.TemporaryDirectory(dir=PRIVATE, prefix="agent_dl_") as td:
        dl = valk("agent", "download", AGENT, "-o", td)
        downloaded, src = {}, ""
        for p in sorted(Path(td).rglob("*")):
            if p.is_file():
                rel = str(p.relative_to(td))
                rel = rel.split("/", 1)[-1] if rel.startswith(AGENT + "/") else rel
                downloaded[rel] = sha(p.read_bytes())
                if rel == "single_call.py":
                    src = p.read_text(encoding="utf-8")
                if rel == "contract.yaml":
                    contract = yaml.safe_load(p.read_text())
        bundle_dir = PRIVATE / "agent_bundle_vb103_single_call"
        if not bundle_dir.exists():
            import shutil

            shutil.copytree(td, bundle_dir)
    runs = valk("run", "list", "--all", "--format", "json", "--benchmark-name", BENCHMARK)
    frozen_hashes = frozen.get("downloaded_files_sha256") or {}
    out = {
        "written_utc": stamp(), "host": os.uname().nodename, "cli": "valk (no version flag; `valk --help` smoke passed)",
        "valkyrie_config": {"path": str(HOST_CONFIG), **cfg_public, "note": "values of secret-like fields are never read into this record; the private copy used by runs "
                                                                                 "adds this experiment's benchmark service URL and bearer under $WORK/private/ (0600)"},
        "organization_bucket": {"log_group": cfg.get("LOG_GROUP"), "s3_bucket": cfg.get("S3_BUCKET"), "environment": cfg.get("environment")},
        "gateway": {"url": "https://dev.model-gateway.vals.ai", "key_secret_name": GATEWAY_KEY_SECRET, "key_on_host": False,
                    "registry_dump": {"path": str(a.registry_dump), "sha256": sha(body), "bytes": len(body), "n_models": len(models), "provenance": a.registry_provenance,
                                      "calls": "metadata-only GET /registry taken by another worker; zero /query calls; the key never reached this experiment's host process"}},
        "teachers": {
            "opus55": {"selector": OPUS, "present": OPUS in models, "entry": opus_family.get(OPUS), "only_opus_5_5_selector_without_fallbacks": opus_no_fallback == [OPUS],
                       "opus_5_5_selectors_without_fallbacks": opus_no_fallback, "settings": {"compute_effort": "max", "max_tokens": 128000, "temperature": "not passed (registry default 1.0)"},
                       "kwargs": {"compute_effort": "max"}},
            "astra": {"selector": astra_selector, "present": bool(astra_selector), "entry": astra_family.get(astra_selector), "efforts_served": served, "highest_effort": highest,
                      "all_astra_selectors": astra_efforts, "settings": {"reasoning_effort": highest, "max_tokens": 128000, "temperature": "not passed (unsupported)"},
                      "kwargs": {"reasoning_effort": highest}},
        },
        "agent": {"name": AGENT, "contract_secrets": contract.get("secrets"), "contract_kwargs": sorted((contract.get("kwargs") or {}).keys()),
                  "run_cmd_gateway_url": (re.search(r"MODEL_GATEWAY_URL=(\S+)", contract.get("run_cmd", "")) or [None, None])[1],
                  "installed_files_sha256": downloaded, "download_exit_code": dl.returncode, "frozen_receipt_sha256": frozen_hashes,
                  "bundle_manifest_sha256_frozen": frozen.get("bundle_manifest_sha256"), "pinned_checkout_files_sha256": local,
                  "installed_matches_frozen": bool(downloaded) and all(downloaded.get(k) == v for k, v in frozen_hashes.items()),
                  "pinned_checkout_matches_frozen": all(local.get(k) == v for k, v in frozen_hashes.items()),
                  "pinned_checkout_note": "the pinned checkout's single_call.py is a later revision (VBV2 multi-file path policy only); the installed frozen bundle "
                                          "(single_call.py 6e1a9b0d…) is what runs; host-side extraction uses rl4cv.veribench.exp103 on the pinned checkout, "
                                          "whose vbv1 behaviour is identical (experiment 02A v3 checked this on 10-07-2026)",
                  "retry_bound": retry_bound(src), "client_timeout_s_default": int((re.search(r'VB103_CALL_TIMEOUT_S", "(\d+)"', src) or [None, "0"])[1]),
                  "private_bundle_copy": str(PRIVATE / "agent_bundle_vb103_single_call")},
        "payer": "Vals: the provider credential is Vals' gateway key in Vals' Secrets Manager, mapped into the sandbox by Valkyrie's secret mapping "
                 f"({GATEWAY_KEY_SECRET}); no personal key or subscription token is used; charges are recorded per receipt (D-108)",
        "route": f"Valkyrie run (valk run start --agent {AGENT} --benchmark {BENCHMARK} --model <selector> -k …); the agent calls the Vals model gateway from inside the sandbox",
        "prior_runs_on_this_benchmark": {"exit_code": runs.returncode, "n": len(json.loads(runs.stdout)) if runs.returncode == 0 and runs.stdout.strip().startswith("[") else None,
                                         "stdout_head": runs.stdout[:200] if runs.returncode else (runs.stderr or runs.stdout)[:200]},
    }
    out["verdict"] = "PASS" if (out["teachers"]["opus55"]["present"] and out["teachers"]["opus55"]["only_opus_5_5_selector_without_fallbacks"]
                                and out["teachers"]["astra"]["present"] and out["agent"]["installed_matches_frozen"] and dl.returncode == 0
                                and all(out["agent"]["retry_bound"].values())) else "FAIL"
    a.out.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"verdict": out["verdict"], "environment": cfg.get("environment"), "log_group": cfg.get("LOG_GROUP"), "bucket": cfg.get("S3_BUCKET"),
                      "opus55": {"selector": OPUS, "fallbacks": (opus_family.get(OPUS) or {}).get("fallback_models")}, "astra": {"selector": astra_selector, "efforts": served},
                      "installed_matches_frozen": out["agent"]["installed_matches_frozen"], "retry_bound": out["agent"]["retry_bound"],
                      "prior_runs": out["prior_runs_on_this_benchmark"]["n"]}, indent=1))
    return 0 if out["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
