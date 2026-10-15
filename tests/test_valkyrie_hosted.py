"""Check the hosted-Valkyrie migration (10-14-2026) offline: preflight evidence, secret-backed service registration and the ported launchers, with a fake CLI and zero tracker or model calls."""
from __future__ import annotations

from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types

import pytest

from rl4cv import valkyrie_hosted as hosted

REPO = Path(__file__).parents[1]
E08V2 = REPO / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/scripts"
E09 = REPO / "experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/expt_v1"
BEARER = "synthetic-bearer-value-0123456789"


class FakeCli:
    """Answers like `vals-ai/Valkyrie@prod` 865135f and records every call (argv, stdin)."""

    def __init__(self, credential="a login", providers="* daytona → daytona\n", secrets=("brandoModelGatewayApiKey",),
                 agents=("vb103_judge",), fail=()):
        self.credential, self.providers, self.secrets, self.agents, self.fail = credential, providers, secrets, agents, fail
        self.calls: list[tuple[list[str], str | None]] = []

    def __call__(self, argv, *, env=None, input=None, **kwargs):
        args = argv[1:]
        self.calls.append((args, input))
        if " ".join(args[:2]) in self.fail or args[0] in self.fail:
            return subprocess.CompletedProcess(argv, 1, "", "synthetic failure")
        out = {
            "whoami": f"brando@example.org in BrandoMiranda on https://tracker.example (using {self.credential})\n",
            "provider": self.providers,
            "secret": json.dumps({"secrets": [{"name": n, "reference": n} for n in self.secrets]}) if args[:2] == ["secret", "list"] else "✓ Secret saved.\n",
            "agent": json.dumps({"agents": [{"name": n, "last_modified": None} for n in self.agents]}),
            "benchmark": f"Runs of {args[3] if len(args) > 3 else ''} now use the URL.\n",
        }[args[0]]
        return subprocess.CompletedProcess(argv, 0, out, "")


def test_preflight_pass_records_identity_without_secret_values():
    cli = FakeCli()
    out = hosted.preflight(require_login=True, require_secrets=[hosted.GATEWAY_SECRET], require_agents=["vb103_judge"],
                           env={}, runner=cli)
    assert out["verdict"] == "PASS", out["problems"]
    assert out["identity"] == {"account": "brando@example.org", "organization": "BrandoMiranda",
                               "tracker_url": "https://tracker.example", "credential": "login"}
    assert out["default_provider"] == "daytona" and out["providers"] == {"daytona": "daytona"}
    assert out["required_secrets_present"] == [hosted.GATEWAY_SECRET]
    assert [c[0][0] for c in cli.calls] == ["whoami", "provider", "secret", "agent"]


@pytest.mark.parametrize("cli,needle", [
    (FakeCli(credential="an access key"), "needs `valkyrie login`"),
    (FakeCli(providers="No provider has a secret yet.\n"), "no default sandbox provider"),
    (FakeCli(providers="* daytona (default; no secret set — run `valkyrie provider set daytona SECRET`)\n"), "no default sandbox provider"),
    (FakeCli(secrets=()), "brandoModelGatewayApiKey is missing"),
    (FakeCli(agents=()), "vb103_judge is not installed"),
    (FakeCli(fail=("whoami",)), "valkyrie whoami failed"),
])
def test_preflight_fails_closed(cli, needle):
    out = hosted.preflight(require_login=True, require_secrets=[hosted.GATEWAY_SECRET], require_agents=["vb103_judge"],
                           env={}, runner=cli)
    assert out["verdict"] == "FAIL" and any(needle in p for p in out["problems"]), out["problems"]


def test_register_service_pipes_bearer_on_stdin_only():
    cli = FakeCli()
    reg = hosted.register_service("rl4cv-e08-vbv1-train", "https://a-b.trycloudflare.com", BEARER, env={}, runner=cli)
    (secret_args, secret_in), (svc_args, svc_in) = cli.calls
    assert secret_args == ["secret", "set", "rl4cv-e08-vbv1-train-bearer"] and secret_in == "Bearer " + BEARER
    assert svc_args == ["benchmark", "service", "set", "rl4cv-e08-vbv1-train", "https://a-b.trycloudflare.com",
                        "--auth-secret", "rl4cv-e08-vbv1-train-bearer", "--auth-header", "Authorization"] and svc_in is None
    assert all(BEARER not in a for args, _ in cli.calls for a in args)
    assert BEARER not in json.dumps(reg)


def test_register_service_rejects_bad_names_urls_and_failures():
    with pytest.raises(hosted.HostedValkyrieError):
        hosted.register_service("fellows/x", "https://a.trycloudflare.com", BEARER, env={}, runner=FakeCli())
    with pytest.raises(hosted.HostedValkyrieError):
        hosted.register_service("x", "http://127.0.0.1:9740", BEARER, env={}, runner=FakeCli())
    with pytest.raises(hosted.HostedValkyrieError) as exc:
        hosted.register_service("x", "https://a.trycloudflare.com", BEARER, env={}, runner=FakeCli(fail=("benchmark service",)))
    assert BEARER not in str(exc.value)


def test_local_registry_roundtrip_is_private(tmp_path):
    bearer = tmp_path / "service_bearer"
    bearer.write_text(BEARER + "\n")
    registry = tmp_path / "private" / "services.json"
    reg = {"registered_utc": "t", "auth_secret": "b-bearer", "auth_header": "Authorization"}
    hosted.record_local(registry, "b", "https://a.trycloudflare.com", bearer, reg)
    assert registry.stat().st_mode & 0o777 == 0o600
    assert BEARER not in registry.read_text()
    assert hosted.lookup_local(registry, "b") == ("https://a.trycloudflare.com", "Bearer " + BEARER)
    with pytest.raises(hosted.HostedValkyrieError):
        hosted.lookup_local(registry, "missing")


def test_cli_env_drops_dead_yaml_selectors_and_provider_keys():
    env = hosted.cli_env(["OPENAI_API_KEY"], base={"VALKYRIE_CONFIG_PATH": "x", "VALKYRIE_ENV": "bench",
                                                   "OPENAI_API_KEY": "k", "VALKYRIE_URL": "u", "PATH": "/usr/bin"})
    assert set(env) == {"VALKYRIE_URL", "PATH"} and env["PATH"].startswith(str(Path(sys.executable).parent))


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_e08v2_deploy_no_longer_reads_valkyrie_yaml():
    source = (E08V2 / "deploy_service_e08v2.py").read_text()
    for dead in ("import yaml", "custom_benchmark_services", "benchmark_auth", "HOST_CONFIG"):
        assert dead not in source


def test_e08v2_register_updates_live_deployment(tmp_path, monkeypatch):
    deploy = load(E08V2 / "deploy_service_e08v2.py", "deploy_service_e08v2_under_test")
    monkeypatch.setattr(deploy, "PRIVATE", tmp_path)
    monkeypatch.setattr(deploy, "SERVICES", tmp_path / "services.json")
    monkeypatch.setattr(deploy, "PUBLIC_RECEIPT", tmp_path / "public" / "deployment_e08.json")
    (tmp_path / "service_bearer").write_text(BEARER)
    (tmp_path / "deployment.json").write_text(json.dumps({"service_pid": 1, "tunnel_pid": 2, "tunnel_url": "https://a.trycloudflare.com"}))
    monkeypatch.setattr(deploy, "alive", lambda pid: True)
    monkeypatch.setattr(deploy, "probe", lambda url, bearer, timeout=20: 200)
    cli = FakeCli()
    real_run = hosted.run
    monkeypatch.setattr(hosted, "run", lambda args, **kw: real_run(args, **{**kw, "runner": cli}))
    assert deploy.cmd_register(None) == 0
    receipt = json.loads((tmp_path / "deployment.json").read_text())
    assert receipt["valkyrie_registration"]["auth_secret"] == "rl4cv-e08-vbv1-train-bearer"
    public = json.loads((tmp_path / "public" / "deployment_e08.json").read_text())
    assert "account" not in public["valkyrie_identity"]["identity"] and BEARER not in json.dumps(public)
    assert hosted.lookup_local(tmp_path / "services.json", "rl4cv-e08-vbv1-train")[0] == "https://a.trycloudflare.com"


def test_e08v2_judge_env_drops_yaml_selectors(monkeypatch):
    if not (REPO / "external/veribench/experiments/100_karpathy_recipe_tc_judge_search_human_train_val_test/scripts").is_dir():
        pytest.skip("pinned judge dependencies unavailable")
    judge = load(E08V2 / "judge_rl4cv_e08v2.py", "judge_rl4cv_e08v2_under_test")
    monkeypatch.setenv("VALKYRIE_CONFIG_PATH", "x")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-must-be-removed")
    actual = judge.env()
    assert "VALKYRIE_CONFIG_PATH" not in actual and "VALKYRIE_ENV" not in actual and "OPENAI_API_KEY" not in actual


def test_e08v2_judge_source_reads_hosted_route():
    source = (E08V2 / "judge_rl4cv_e08v2.py").read_text()
    assert "valkyrie.yaml" not in source and "custom_benchmark_services" not in source
    assert "route_identity_hosted_v2.json" in source and "hosted.lookup_local(SERVICES" in source


def test_argon_qa_cli_env_has_no_yaml_selectors(monkeypatch):
    argon = load(REPO / "scripts/argon_qa/argon_qa.py", "argon_qa_under_test")
    seen = {}
    monkeypatch.setattr(argon.subprocess, "run", lambda argv, **kw: seen.update(kw) or subprocess.CompletedProcess(argv, 0, "", ""))
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-must-be-removed")
    argon.valkyrie("whoami")
    assert not {"VALKYRIE_CONFIG_PATH", "VALKYRIE_ENV", "GEMINI_API_KEY"} & set(seen["env"])
    assert "custom_benchmark_services" not in (REPO / "scripts/argon_qa/argon_qa.py").read_text()


def test_e09_judge_service_registers_on_tracker(tmp_path, monkeypatch):
    children = types.ModuleType("owned_processes")
    children.ROOT = tmp_path
    children.alive = lambda record: True
    children.stop = lambda record: None
    children.spawn = lambda *a, **k: None
    records = {"processes": []}

    @contextmanager
    def registry(root=None):
        yield records
    children.registry = registry
    monkeypatch.setitem(sys.modules, "owned_processes", children)

    service = types.SimpleNamespace(NAME=None)

    def cmd_deploy(_):
        private = tmp_path / "private"
        (private / f"service_bearer_{service.NAME}").write_text(BEARER)
        (private / f"deployment_{service.NAME}.json").write_text(json.dumps({"tunnel_url": "https://e.trycloudflare.com"}))
        records["processes"] += [{"pid": 1, "start_ticks": "1", "kind": "e09_judge_service"},
                                 {"pid": 2, "start_ticks": "2", "kind": "e09_judge_tunnel"}]
        return 0
    service.cmd_deploy = cmd_deploy
    monkeypatch.setitem(sys.modules, "deploy_judge_e09", types.SimpleNamespace(service=service))
    cli = FakeCli()
    real_run = hosted.run
    monkeypatch.setattr(hosted, "run", lambda args, **kw: real_run(args, **{**kw, "runner": cli}))
    module = load(E09 / "judge_service_e09.py", "judge_service_e09_under_test")
    judge = module.JudgeService()
    judge.deploy({"pack_abs": str(tmp_path), "benchmark": "rl4cv-e09-batch", "batch_id": "0123456789abcdef99", "n_tasks": 6})
    assert (tmp_path / "private/valkyrie.yaml").read_text() == "{}\n"        # scratch for the frozen helper only
    registered = [a for a, _ in cli.calls if a[:3] == ["benchmark", "service", "set"]]
    assert registered == [["benchmark", "service", "set", "rl4cv-e09-batch", "https://e.trycloudflare.com",
                           "--auth-secret", "rl4cv-e09-batch-bearer", "--auth-header", "Authorization"]]
    receipt = json.loads(judge.receipt.read_text())
    assert receipt["valkyrie_registration"]["auth_secret"] == "rl4cv-e09-batch-bearer"
