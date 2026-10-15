"""Exercise hosted registration and explicit legacy transport with an executable fake CLI and synthetic receipts."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
import yaml

from rl4cv.valkyrie_transport import Transport

REPO = Path(__file__).resolve().parents[1]
E08 = REPO / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/scripts"


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    for key in ("RL4CV_VALKYRIE_TRANSPORT", "VALKYRIE_BIN", "VALKYRIE_URL", "VALKYRIE_API_KEY"):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def fake_cli(tmp_path, monkeypatch):
    script = tmp_path / "valkyrie"
    log = tmp_path / "calls.jsonl"
    script.write_text(f'''#!{sys.executable}
import json, os, sys
args = sys.argv[1:]
value = sys.stdin.read() if args[:2] == ["secret", "set"] else None
with open(os.environ["FAKE_CALLS"], "a") as f:
    f.write(json.dumps({{"args": args, "stdin": value, "env": {{k: v for k, v in os.environ.items() if k.startswith("VALKYRIE_")}}}}) + "\\n")
if args == ["whoami"]:
    print("test in " + os.environ.get("FAKE_ORG", "fixture") + " on " + os.environ.get("VALKYRIE_URL", "https://fixture.invalid") + " (using " + os.environ.get("FAKE_CREDENTIAL", "a login") + ")")
if args[:3] == ["benchmark", "service", "set"] and os.environ.get("FAKE_FAIL"):
    print("unexpected external reflection", file=sys.stderr)
    sys.exit(7)
''')
    script.chmod(0o700)
    monkeypatch.setenv("VALKYRIE_BIN", str(script))
    monkeypatch.setenv("FAKE_CALLS", str(log))
    return log


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hosted_registration_uses_stdin_and_supported_flags(tmp_path, fake_cli, monkeypatch):
    config = tmp_path / "private.yaml"
    config.write_text("historical configuration stays byte-identical\n")
    bearer = tmp_path / "bearer"
    bearer.write_text("synthetic-bearer")
    monkeypatch.setenv("VALKYRIE_ENV", "old")
    monkeypatch.setenv("VALKYRIE_CONFIG_PATH", "ignored.yaml")
    monkeypatch.setenv("VALKYRIE_URL", "https://fixture.invalid")
    selected = Transport(config)
    receipt = selected.register("fixture", "https://tunnel.invalid", bearer, tmp_path / "absent.yaml")
    calls = [json.loads(row) for row in fake_cli.read_text().splitlines()]
    assert [row["args"] for row in calls] == [
        ["whoami"], ["provider", "list"], ["secret", "set", "fixture-service-auth"],
        ["benchmark", "service", "set", "fixture", "https://tunnel.invalid",
         "--auth-secret", "fixture-service-auth", "--auth-header", "Authorization"],
    ]
    assert calls[2]["stdin"] == "Bearer synthetic-bearer"
    assert all("synthetic-bearer" not in str(row["args"]) for row in calls)
    assert all("VALKYRIE_CONFIG_PATH" not in row["env"] and "VALKYRIE_ENV" not in row["env"] for row in calls)
    assert "synthetic-bearer" not in json.dumps(receipt)
    assert receipt["transport"] == "hosted"
    assert config.read_text() == "historical configuration stays byte-identical\n"


def test_access_key_registration_fails_before_secret_mutation(tmp_path, fake_cli, monkeypatch):
    monkeypatch.setenv("FAKE_CREDENTIAL", "an access key")
    bearer = tmp_path / "bearer"
    bearer.write_text("synthetic")
    with pytest.raises(RuntimeError, match="registration needs"):
        Transport(tmp_path / "absent").register("fixture", "https://fixture.invalid", bearer, tmp_path / "absent")
    assert len(fake_cli.read_text().splitlines()) == 1


def test_registration_failure_is_not_success_or_retried(tmp_path, fake_cli, monkeypatch):
    monkeypatch.setenv("FAKE_FAIL", "1")
    bearer = tmp_path / "bearer"
    bearer.write_text("synthetic")
    with pytest.raises(RuntimeError, match="exit 7") as error:
        Transport(tmp_path / "absent").register("fixture", "https://fixture.invalid", bearer, tmp_path / "absent")
    assert "reflection" not in str(error.value)
    assert len(fake_cli.read_text().splitlines()) == 4


def test_legacy_requires_opt_in_and_retains_prior_services(tmp_path, monkeypatch):
    monkeypatch.setenv("RL4CV_VALKYRIE_TRANSPORT", "legacy")
    with pytest.raises(ValueError, match="VALKYRIE_BIN"):
        Transport(tmp_path / "private.yaml")
    monkeypatch.setenv("VALKYRIE_BIN", "/retained/legacy-valk")
    monkeypatch.setenv("VALKYRIE_API_KEY", "synthetic-hosted")
    monkeypatch.setenv("VALKYRIE_URL", "https://hosted.invalid")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-provider")
    config, host, bearer = (tmp_path / n for n in ("private.yaml", "host.yaml", "bearer"))
    host.write_text(yaml.safe_dump({"custom_benchmark_services": {"old": "https://old.invalid"}}))
    bearer.write_text("synthetic")
    selected = Transport(config)
    selected.register("new", "https://new.invalid", bearer, host)
    selected.register("another", "https://another.invalid", bearer, host)
    assert set(yaml.safe_load(config.read_text())["custom_benchmark_services"]) == {"old", "new", "another"}
    assert config.stat().st_mode & 0o777 == 0o600
    env = selected.env()
    assert env["VALKYRIE_CONFIG_PATH"] == str(config) and env["VALKYRIE_ENV"] == "bench"
    assert not {"VALKYRIE_API_KEY", "VALKYRIE_URL", "OPENAI_API_KEY"} & env.keys()
    assert selected.endpoint("new", tmp_path) == ("https://new.invalid", "Bearer synthetic")


def test_hosted_auth_environment_and_historical_receipt_fence(tmp_path, monkeypatch, fake_cli):
    monkeypatch.setenv("VALKYRIE_API_KEY", "synthetic-hosted")
    monkeypatch.setenv("MODEL_GATEWAY_API_KEY", "synthetic-provider")
    monkeypatch.setenv("VALKYRIE_ENV", "old")
    selected = Transport(tmp_path / "absent")
    assert selected.env()["VALKYRIE_API_KEY"] == "synthetic-hosted"
    assert not {"MODEL_GATEWAY_API_KEY", "VALKYRIE_ENV"} & selected.env().keys()
    with pytest.raises(RuntimeError, match="legacy transport"):
        selected.require_receipt({"run_id": "historical"})
    receipt = selected.identity()
    selected.require_receipt(receipt)
    monkeypatch.setenv("VALKYRIE_URL", "https://other.invalid")
    with pytest.raises(RuntimeError, match="Tracker or organization"):
        Transport(tmp_path / "absent").require_receipt(receipt)
    monkeypatch.delenv("VALKYRIE_URL")
    monkeypatch.setenv("FAKE_ORG", "another-organization")
    with pytest.raises(RuntimeError, match="Tracker or organization"):
        Transport(tmp_path / "absent").require_receipt(receipt)


def test_hosted_endpoint_uses_only_current_matching_receipt(tmp_path, fake_cli):
    selected = Transport(tmp_path / "missing.yaml")
    bearer = tmp_path / "bearer"
    bearer.write_text("synthetic")
    receipt = {**selected.identity(), "benchmark": "fixture", "tunnel_url": "https://fixture.invalid", "bearer_file": str(bearer)}
    path = tmp_path / "deployment_judge.json"
    path.write_text(json.dumps(receipt))
    assert selected.endpoint("fixture", tmp_path) == ("https://fixture.invalid", "Bearer synthetic")
    receipt["torn_down_utc"] = "retired"
    path.write_text(json.dumps(receipt))
    with pytest.raises(RuntimeError, match="exactly one"):
        selected.endpoint("fixture", tmp_path)


@pytest.mark.parametrize("script", [E08 / "deploy_service_e08v2.py", REPO / "scripts/argon_qa/argon_qa.py"])
def test_live_deployment_refused_before_hosted_registration(script, tmp_path, monkeypatch):
    module = load(script, "deploy_fixture")
    monkeypatch.setattr(module, "PRIVATE" if script.parent == E08 else "HOME", tmp_path)
    receipt = tmp_path / "deployment.json"
    receipt.write_text(json.dumps({"service_pid": 123}))
    before = receipt.read_bytes()
    monkeypatch.setattr(module, "alive", lambda pid: bool(pid))
    monkeypatch.setattr(Transport, "preflight", lambda *a, **k: pytest.fail("touched runtime before live-child fence"))
    with pytest.raises(SystemExit, match="live deployment"):
        module.cmd_deploy(None)
    assert receipt.read_bytes() == before


def test_argon_historical_status_refused_without_cli_call(tmp_path, monkeypatch):
    module = load(REPO / "scripts/argon_qa/argon_qa.py", "argon_fixture")
    monkeypatch.setattr(module, "HOME", tmp_path)
    (tmp_path / "run.json").write_text(json.dumps({"run_id": "old"}))
    monkeypatch.setattr(module, "valkyrie", lambda *a: pytest.fail("wrong client used"))
    with pytest.raises(RuntimeError, match="legacy transport"):
        module.cmd_status(None)


@pytest.fixture
def judge(monkeypatch, tmp_path):
    # Only transport and admission fencing are under test; frozen scientific modules are not executed.
    for name in ("common", "prompts", "build_inputs", "judge_run", "judge_pack"):
        monkeypatch.setitem(sys.modules, name, SimpleNamespace())
    monkeypatch.setattr(Transport, "identity", lambda selected: {"transport": selected.mode, "valkyrie_bin": selected.binary, "tracker_url": "https://fixture.invalid", "organization": "fixture"})
    module = load(E08 / "judge_rl4cv_e08v2.py", "judge_v2_transport_fixture")
    monkeypatch.setattr(module, "RESULTS", tmp_path)
    monkeypatch.setattr(module, "STATE", tmp_path / "state.json")
    return module


def test_judge_blocked_route_never_contacts_cli(judge, tmp_path, monkeypatch):
    pack = tmp_path / "pack.json"
    pack.write_text('{"verdict":"PASS"}')
    monkeypatch.setattr(judge, "REPO", tmp_path)
    monkeypatch.setattr(judge, "EXP", tmp_path)
    monkeypatch.setattr(judge, "suite_spec", lambda suite: {"pack_receipt": pack})
    monkeypatch.setattr(judge.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, pack.read_bytes()))
    (tmp_path / "results").mkdir()
    route = tmp_path / "results/route_identity_v2.json"
    route.write_text('{"verdict":"BLOCKED"}')
    monkeypatch.setattr(Transport, "preflight", lambda *a, **k: pytest.fail("held study contacted runtime"))
    with pytest.raises(AssertionError, match="route identity"):
        judge._admit_locked("fixture", [], 1)
    assert not judge.STATE.exists()


def test_judge_historical_poll_refused_before_mutating_state(judge, monkeypatch):
    judge.STATE.write_text(json.dumps({"runs": {"old": {"run_id": "old"}}}))
    before = judge.STATE.read_bytes()
    monkeypatch.setattr(judge, "cli", lambda *a, **k: pytest.fail("wrong client used"))
    with pytest.raises(RuntimeError, match="legacy transport"):
        judge.poll()
    assert judge.STATE.read_bytes() == before


def test_judge_ambiguous_hosted_admission_cannot_be_replayed(judge, tmp_path, monkeypatch):
    pack = tmp_path / "pack.json"
    pack.write_text(json.dumps({"verdict": "PASS", "control_cells": [{"task_id": "fixture"}]}))
    monkeypatch.setattr(judge, "REPO", tmp_path)
    monkeypatch.setattr(judge, "EXP", tmp_path)
    monkeypatch.setattr(judge, "suite_spec", lambda suite: {
        "pack_receipt": pack, "system": None, "benchmark": "fixture", "key_prefix": "controls/"})
    monkeypatch.setattr(judge.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, pack.read_bytes()))
    (tmp_path / "results").mkdir()
    (tmp_path / "results/route_identity_v2.json").write_text(json.dumps({"verdict": "PASS", **judge.transport().identity()}))
    monkeypatch.setattr(Transport, "preflight", lambda *a, **k: None)
    monkeypatch.setattr(Transport, "endpoint", lambda *a: ("https://fixture.invalid", "synthetic"))
    monkeypatch.setattr(judge, "judge_config", lambda name: {"selector": "frozen-model", "max_tokens": 42, "reasoning_effort": "high"})
    calls = []
    def ambiguous(args):
        calls.append(args)
        return subprocess.CompletedProcess(args, 1, "", "ambiguous send")
    monkeypatch.setattr(judge, "cli", ambiguous)
    assert judge._admit_locked("controls", ["frozen"], 1) == 1
    entry = judge.load_state()["runs"]["controls/frozen"]
    assert entry["transport"] == "hosted" and entry["retry_blocked"]
    assert entry["selector"] == "frozen-model" and entry["kwargs"]["reasoning_effort"] == "high"
    assert judge._admit_locked("controls", ["frozen"], 1) == 1
    assert len(calls) == 1


@pytest.mark.parametrize("failed", [False, True])
def test_e08_deploy_registers_without_yaml_and_cleans_only_new_children(tmp_path, monkeypatch, failed):
    module = load(E08 / "deploy_service_e08v2.py", "deploy_registration_fixture")
    private = tmp_path / "private"
    pack = tmp_path / "pack"
    (pack / "fixture").mkdir(parents=True)
    monkeypatch.setattr(module, "PRIVATE", private)
    monkeypatch.setattr(module, "PACK", pack)
    monkeypatch.setattr(module, "EXPECTED_TASKS", 1)
    monkeypatch.setattr(module, "PUBLIC_RECEIPT", tmp_path / "public.json")
    for key in ("SERVICE_DIR", "KERNEL_AXIOMS", "LAKE_DIR", "UVICORN", "CLOUDFLARED"):
        monkeypatch.setattr(module, key, tmp_path)
    monkeypatch.setattr(module, "HOST_CONFIG", tmp_path / "absent.yaml")
    monkeypatch.setattr(module, "listening", lambda p: False)
    monkeypatch.setattr(module, "alive", lambda pid: False)
    monkeypatch.setattr(module, "probe", lambda url, bearer: 200 if bearer else 401)
    monkeypatch.setattr(module, "task_limits", lambda *a: {"limit_ok": True})
    monkeypatch.setattr(module, "wait_for", lambda check, what, **k: "https://fixture.invalid" if what == "tunnel hostname" else True)
    children = []
    def spawn(*a, **k):
        child = SimpleNamespace(pid=1000 + len(children), poll=lambda: None)
        children.append(child)
        return child
    monkeypatch.setattr(module, "subprocess", SimpleNamespace(Popen=spawn, DEVNULL=subprocess.DEVNULL, STDOUT=subprocess.STDOUT,
        run=lambda *a, **k: SimpleNamespace(stdout="frozen-dependency")))
    killed = []
    monkeypatch.setattr(module.os, "killpg", lambda pid, sig: killed.append(pid))
    monkeypatch.setattr(Transport, "preflight", lambda *a, **k: None)
    monkeypatch.setattr(Transport, "identity", lambda selected: {"transport": selected.mode, "tracker_url": "https://fixture.invalid", "organization": "fixture"})
    registrations = []
    def register(selected, benchmark, url, bearer, host):
        registrations.append((benchmark, url, bearer))
        if failed:
            raise RuntimeError("synthetic registration failure")
        return selected.identity()
    monkeypatch.setattr(Transport, "register", register)
    if failed:
        with pytest.raises(RuntimeError, match="registration failure"):
            module.cmd_deploy(None)
        assert killed == [children[1].pid, children[0].pid]
        assert not (private / "deployment.json").exists()
    else:
        assert module.cmd_deploy(None) == 0
        receipt = json.loads((private / "deployment.json").read_text())
        assert receipt["transport"] == "hosted" and receipt["inference_calls"] == 0
        assert not killed
    assert len(registrations) == 1
    assert not (private / "valkyrie.yaml").exists()
