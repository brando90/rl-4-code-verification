"""Test Docker isolation, typed classification and teardown using fake execution only."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("e06_v3_diagnostic_runner", HERE / "diagnostic_runner.py")
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)
IMAGE = "sha256:" + "a" * 64
TOKEN = "test-execution-token"


def frozen_plugins(records=()):
    return {"schema_version": 1, "image_id": IMAGE, "python_executable": "/opt/venv/bin/python", "pytest11": list(records)}


@pytest.fixture
def bundle():
    return {"schema_version": 1, "instance_id": "example__public-1", "checks": [
        {"id": "syntax_01", "kind": "syntax", "argv": ["python", "-m", "compileall", "-q", "package.py"]},
        {"id": "regression_01", "kind": "regression", "argv": ["python", "-m", "pytest", "tests/test_public.py", "-q"]},
        {"id": "issue_01", "kind": "issue", "argv": ["python", "-c", "from package import value; assert value() == 2"]},
    ]}


def typed_result(check, event, *, token=TOKEN, stdout=b"", top_level=True, plugins=()):
    report = {"kind": check["kind"], "token": token, "debug": True, "event": event,
              "exception_type": "AssertionError" if event == "assertion_failure" else None,
              "top_level_assertion": top_level,
              "pytest11_sha256": runner.validator.sha256(runner.validator.canonical_bytes(list(plugins))),
              "checks_sha256": runner.validator.sha256(runner.validator.canonical_bytes(check["argv"]))}
    if check["kind"] == "regression":
        report["pytest"] = {"exit_code": 0, "collected": 2, "call_passed": 2,
                            "call_failed": 0, "setup_errors": 0}
    code = 0 if event == "passed" else 1 if event == "assertion_failure" else 2
    result = runner.ProcessResult(code, stdout,
                                  (runner.RESULT_PREFIX + json.dumps(report) + "\n").encode(),
                                  elapsed_seconds=0.25)
    state = {"Running": False, "Status": "exited", "OOMKilled": False, "ExitCode": code}
    return result, state


@pytest.mark.parametrize("index,event,classification", [
    (0, "passed", "syntax_passed"), (0, "compile_failure", "compile_failure"),
    (1, "passed", "regression_passed"), (1, "test_failure", "regression_failed"),
    (1, "setup_error", "setup_error"), (1, "no_tests_executed", "no_tests_executed"),
    (2, "assertion_failure", "issue_assertion_failure"), (2, "passed", "issue_not_reproduced"),
    (2, "import_error", "import_error"), (2, "exception", "exception"),
])
def test_typed_events_preserve_base_failure_causes(bundle, index, event, classification):
    check = bundle["checks"][index]
    result, state = typed_result(check, event)
    assert runner.classify(check, result, state, TOKEN)[0] == classification


def test_printing_failure_text_does_not_establish_issue_reproduction(bundle):
    check = bundle["checks"][2]
    result, state = typed_result(check, "passed", stdout=b"AssertionError: issue reproduced\n")
    assert runner.classify(check, result, state, TOKEN)[0] == "issue_not_reproduced"
    result, state = typed_result(check, "import_error", stdout=b"AssertionError\n")
    assert runner.classify(check, result, state, TOKEN)[0] == "import_error"
    result.stderr = b"Traceback (most recent call last):\nAssertionError\n"
    assert runner.classify(check, result, state, TOKEN)[0] == "missing_or_ambiguous_execution_receipt"


def test_dependency_assertion_and_replayed_receipt_rejected(bundle):
    check = bundle["checks"][2]
    result, state = typed_result(check, "assertion_failure", top_level=False)
    assert runner.classify(check, result, state, TOKEN)[0] == "assertion_origin_unverified"
    result, state = typed_result(check, "assertion_failure", token="old-run")
    assert runner.classify(check, result, state, TOKEN)[0] == "execution_receipt_identity_mismatch"
    result, state = typed_result(check, "assertion_failure")
    result.stderr *= 2
    assert runner.classify(check, result, state, TOKEN)[0] == "missing_or_ambiguous_execution_receipt"


@pytest.mark.parametrize("mutation,classification", [
    (lambda r, s: setattr(r, "timed_out", True), "timeout"),
    (lambda r, s: setattr(r, "output_limit", True), "output_limit"),
    (lambda r, s: s.update(OOMKilled=True), "out_of_memory"),
    (lambda r, s: s.update(Running=True), "container_state_unverified"),
    (lambda r, s: s.update(ExitCode=17), "container_exit_mismatch"),
])
def test_infrastructure_failures_are_never_assertion_reproductions(bundle, mutation, classification):
    check = bundle["checks"][2]
    result, state = typed_result(check, "assertion_failure")
    mutation(result, state)
    assert runner.classify(check, result, state, TOKEN)[0] == classification


def test_pytest_no_execution_cannot_qualify_as_regression_pass(bundle):
    check = bundle["checks"][1]
    result, state = typed_result(check, "passed")
    report = json.loads(result.stderr.decode().split(runner.RESULT_PREFIX)[1])
    report["pytest"]["call_passed"] = 0
    result.stderr = (runner.RESULT_PREFIX + json.dumps(report)).encode()
    assert runner.classify(check, result, state, TOKEN)[0] == "pytest_completion_unverified"


def test_docker_command_has_only_disposable_mount_and_scrubbed_environment(bundle, tmp_path):
    command = runner.docker_command(docker="/usr/bin/docker", image=IMAGE, source=tmp_path,
                                    name="owned-container", check=bundle["checks"][2], token=TOKEN,
                                    image_env_keys=["SECRET", "PYTHONOPTIMIZE"],
                                    python_executable="/opt/venv/bin/python", uid=1001, gid=1001)
    for option in ("--network=none", "--read-only", "--cpus=4", "--memory=8g", "--memory-swap=8g",
                   "--cap-drop=ALL", "--pull=never", "--workdir=/workspace", "--pids-limit=256",
                   "--security-opt=no-new-privileges:true", "--no-healthcheck", "--ipc=none"):
        assert option in command
    assert command.count("--mount") == 1
    assert command[command.index("--mount") + 1] == f"type=bind,src={tmp_path},dst=/workspace,bind-propagation=rprivate"
    assert "SECRET=" in command and "PYTHONOPTIMIZE=" in command
    image_tail = command[command.index(IMAGE) + 1:]
    assert image_tail[0] == "-i"
    assert not any(value.startswith("PYTHONOPTIMIZE=") for value in image_tail)
    assert not any(value.startswith("PYTEST_DISABLE_PLUGIN_AUTOLOAD=") for value in image_tail)
    assert not any(value.startswith("PYTEST_PLUGINS=") for value in image_tail)
    assert command[command.index("-I") + 1] == "-c"
    assert "sh" not in command and "bash" not in command
    assert json.loads(command[-1])["argv"] == bundle["checks"][2]["argv"]


@pytest.mark.parametrize("uid,python", [(0, "/usr/bin/python3"), (1, "/workspace/python"), (1, "/tmp/python"), (1, "python")])
def test_root_and_checkout_interpreters_rejected(bundle, tmp_path, uid, python):
    with pytest.raises(ValueError):
        runner.docker_command(docker="/usr/bin/docker", image=IMAGE, source=tmp_path,
                              name="owned", check=bundle["checks"][0], token=TOKEN,
                              image_env_keys=[], python_executable=python, uid=uid, gid=1)


def test_export_hash_detects_changes_and_rejects_git_links(tmp_path):
    source = tmp_path / "public"
    source.mkdir()
    file = source / "package.py"
    file.write_text("value = 1\n")
    before = runner.public_tree_sha256(source)
    file.write_text("value = 2\n")
    assert runner.public_tree_sha256(source) != before
    link = source / "link"
    link.symlink_to(file)
    with pytest.raises(ValueError, match="link"):
        runner.public_tree_sha256(source)
    link.unlink()
    (source / ".git").mkdir()
    with pytest.raises(ValueError, match="Git metadata"):
        runner.public_tree_sha256(source)


class FakeDocker:
    def __init__(self, *, issue_event="assertion_failure", cleanup_fails=False, volumes=None):
        self.calls = []
        self.mounts = []
        self.issue_event = issue_event
        self.cleanup_fails = cleanup_fails
        self.volumes = volumes
        self.state = None

    def run(self, command, *, timeout, **_kwargs):
        self.calls.append((command, timeout))
        if command[1:3] == ["image", "inspect"]:
            value = [{"Id": IMAGE, "Config": {"Env": ["SECRET=must-not-be-retained", "PATH=/image/bin"], "Volumes": self.volumes}}]
            return runner.ProcessResult(0, json.dumps(value).encode())
        if command[1] == "run":
            payload = json.loads(command[-1])
            check = {"kind": payload["kind"], "argv": payload["argv"]}
            mount = command[command.index("--mount") + 1]
            source = Path(mount.split("src=", 1)[1].split(",dst=", 1)[0])
            self.mounts.append(source)
            assert (source / "package.py").read_text() == "value = 1\n"
            # Only this fake executor writes a marker in the disposable copy;
            # no submitted Python or trusted wrapper executes on the host.
            (source / "package.py").write_text("changed by synthetic container\n")
            event = self.issue_event if check["kind"] == "issue" else "passed"
            result, self.state = typed_result(check, event, token=payload["token"], plugins=payload["pytest11"])
            if event == "timeout":
                result.timed_out = True
            return result
        if command[1] == "inspect":
            return runner.ProcessResult(0, json.dumps(self.state).encode())
        if command[1:3] == ["rm", "--force"]:
            return runner.ProcessResult(1 if self.cleanup_fails else 0)
        raise AssertionError(f"unexpected fake operation: {command[1]}")


def execute_fake(bundle, tmp_path, fake, plugins=()):
    source = tmp_path / "public"
    source.mkdir()
    (source / "package.py").write_text("value = 1\n")
    return runner.run_bundle(bundle, public_export=source, expected_source_sha256=runner.public_tree_sha256(source),
                             image=IMAGE, python_executable="/opt/venv/bin/python", output_dir=tmp_path / "receipts",
                             scratch_root=tmp_path, wall_timeout_seconds=17, executor=fake, uid=1001, gid=1001,
                             plugin_inventory=frozen_plugins(plugins))


def test_complete_fake_run_has_fresh_copies_hashes_and_fixed_denominators(bundle, tmp_path):
    fake = FakeDocker()
    receipt = execute_fake(bundle, tmp_path, fake)
    assert receipt["status"] == "complete" and receipt["base_diagnostics_usable"]
    assert receipt["original_public_source_unchanged"]
    assert receipt["issue_semantic_fidelity"] == "not_established_by_execution"
    assert receipt["denominators"] == {kind: {"required": 1, "valid": 1} for kind in ("syntax", "regression", "issue")}
    assert len(set(fake.mounts)) == 3
    assert not any(path.exists() for path in fake.mounts)
    assert (tmp_path / "public" / "package.py").read_text() == "value = 1\n"
    for row in receipt["checks"]:
        assert row["cleanup_verified"]
        assert row["stdout_sha256"] == runner.validator.sha256((tmp_path / "receipts" / f"{row['id']}.stdout.log").read_bytes())
        assert row["stderr_sha256"] == runner.validator.sha256((tmp_path / "receipts" / f"{row['id']}.stderr.log").read_bytes())
    assert all(timeout == 17 for command, timeout in fake.calls if command[1] == "run")
    assert "must-not-be-retained" not in json.dumps(receipt)
    assert json.loads((tmp_path / "receipts" / "receipt.json").read_text()) == receipt


@pytest.mark.parametrize("event,classification", [("passed", "issue_not_reproduced"), ("import_error", "import_error"), ("timeout", "timeout")])
def test_failed_fake_issue_checks_preserve_all_denominators(bundle, tmp_path, event, classification):
    receipt = execute_fake(bundle, tmp_path, FakeDocker(issue_event=event))
    assert receipt["status"] == "complete" and not receipt["base_diagnostics_usable"]
    assert len(receipt["checks"]) == 3
    assert receipt["checks"][2]["classification"] == classification
    assert receipt["denominators"]["issue"] == {"required": 1, "valid": 0}


def test_cleanup_failure_stops_later_checks_and_preserves_live_mount(bundle, tmp_path):
    fake = FakeDocker(cleanup_fails=True)
    receipt = execute_fake(bundle, tmp_path, fake)
    assert receipt["status"] == "stopped" and not receipt["base_diagnostics_usable"]
    assert [row["classification"] for row in receipt["checks"]] == ["cleanup_unverified", "not_measured", "not_measured"]
    assert sum(command[1] == "run" for command, _ in fake.calls) == 1
    assert Path(receipt["checks"][0]["retained_public_copy"]).is_dir()


def test_implicit_image_volumes_fail_before_any_execution(bundle, tmp_path):
    fake = FakeDocker(volumes={"/hidden": {}})
    receipt = execute_fake(bundle, tmp_path, fake)
    assert receipt["status"] == "failed" and not receipt["base_diagnostics_usable"]
    assert all(command[1] != "run" for command, _ in fake.calls)
    assert len(receipt["checks"]) == 3


def test_invalid_bundle_fails_before_any_docker_action(bundle, tmp_path):
    bundle["checks"][2]["argv"][2] = "print('AssertionError')"
    fake = FakeDocker()
    with pytest.raises(runner.validator.DiagnosticValidationError):
        execute_fake(bundle, tmp_path, fake)
    assert not fake.calls


def test_wrapper_is_syntactically_valid_but_not_executed_here():
    compile(runner.CONTAINER_WRAPPER, "<container-wrapper-not-executed>", "exec")
    assert "__debug__" in runner.CONTAINER_WRAPPER
    assert '"PYTHONOPTIMIZE" in os.environ' in runner.CONTAINER_WRAPPER
    assert "tail.tb_frame.f_code is code" in runner.CONTAINER_WRAPPER


@pytest.mark.parametrize("nested", ["scratch", "output"])
def test_work_paths_inside_public_export_rejected_before_mutation(bundle, tmp_path, nested):
    source = tmp_path / "public"
    source.mkdir()
    (source / "package.py").write_text("value = 1\n")
    before = runner.public_tree_sha256(source)
    fake = FakeDocker()
    with pytest.raises(ValueError, match="outside the public export"):
        runner.run_bundle(bundle, public_export=source, expected_source_sha256=before,
                          image=IMAGE, python_executable="/opt/venv/bin/python",
                          output_dir=source / "out" if nested == "output" else tmp_path / "out",
                          scratch_root=source if nested == "scratch" else tmp_path,
                          wall_timeout_seconds=17, executor=fake, uid=1001, gid=1001,
                          plugin_inventory=frozen_plugins())
    assert not fake.calls
    assert runner.public_tree_sha256(source) == before


@pytest.mark.parametrize("payload", ['{"event":"passed","event":"assertion_failure"}',
                                    '{"nested":' + '[' * 2000 + '0' + ']' * 2000 + '}'])
def test_malformed_typed_receipt_fails_closed(bundle, payload):
    check = bundle["checks"][2]
    result, state = typed_result(check, "assertion_failure")
    result.stderr = (runner.RESULT_PREFIX + payload + "\n").encode()
    assert runner.classify(check, result, state, TOKEN) == ("invalid_execution_receipt", None)


def test_frozen_fixture_plugins_are_enabled_and_bound_to_image(bundle, tmp_path):
    plugins = [
        {"distribution": "pytest-mock", "version": "3.11.1", "name": "pytest_mock", "value": "pytest_mock"},
        {"distribution": "requests-mock", "version": "1.11.0", "name": "requests_mock", "value": "requests_mock.contrib._pytest_plugin"},
    ]
    fake = FakeDocker()
    receipt = execute_fake(bundle, tmp_path, fake, plugins)
    assert receipt["base_diagnostics_usable"]
    assert receipt["pytest11_sha256"] == runner.validator.sha256(runner.validator.canonical_bytes(plugins))
    for command, _ in fake.calls:
        if command[1] == "run":
            assert json.loads(command[-1])["pytest11"] == plugins
            assert "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1" not in command
    mismatched = frozen_plugins(plugins)
    mismatched["image_id"] = "sha256:" + "b" * 64
    with pytest.raises(ValueError, match="match the image"):
        runner.validate_plugin_inventory(mismatched, IMAGE, "/opt/venv/bin/python")


def test_unexpected_runtime_plugin_inventory_fails_closed(bundle):
    check = bundle["checks"][1]
    unexpected = [{"distribution": "host-plugin", "version": "1", "name": "host", "value": "host_plugin"}]
    result, state = typed_result(check, "passed", plugins=unexpected)
    assert runner.classify(check, result, state, TOKEN)[0] == "plugin_inventory_unverified"
    assert runner.CONTAINER_WRAPPER.count("    verify_plugins()") == 2


def test_docker_context_and_socket_are_explicit_without_inheriting_env(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", "/private/other-home")
    monkeypatch.setenv("DOCKER_HOST", "tcp://unintended.example:2375")
    monkeypatch.setenv("DOCKER_CONTEXT", "unintended-context")
    monkeypatch.setenv("PYTEST_PLUGINS", "host_plugin")
    named = runner.docker_client_environment(docker_context="admitted-context", docker_config_dir=tmp_path)
    assert named == {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "DOCKER_CONTEXT": "admitted-context", "DOCKER_CONFIG": str(tmp_path)}
    local = runner.docker_client_environment(docker_config_dir=tmp_path)
    assert local["DOCKER_HOST"] == "unix:///var/run/docker.sock"
    assert "DOCKER_CONTEXT" not in local and "HOME" not in local
    custom = runner.LocalDockerExecutor(docker_host="unix:///run/user/1001/docker.sock", docker_config_dir=tmp_path)
    assert custom.environment["DOCKER_HOST"] == "unix:///run/user/1001/docker.sock"
    with pytest.raises(ValueError, match="not both"):
        runner.docker_client_environment(docker_context="one", docker_host="unix:///other.sock", docker_config_dir=tmp_path)


def test_non_ascii_accepted_bundle_does_not_expand_past_response_limit(bundle, tmp_path):
    bundle["checks"] = bundle["checks"][:2] + [
        {"id": f"issue_{index:02d}", "kind": "issue", "argv": ["python", "-c", "assert len('" + "é" * 7900 + "') == 7900"]}
        for index in range(1, 4)
    ]
    assert len(runner.validator.canonical_bytes(bundle)) < runner.validator.MAX_RESPONSE_BYTES
    assert len(json.dumps(bundle).encode()) > runner.validator.MAX_RESPONSE_BYTES
    fake = FakeDocker()
    receipt = execute_fake(bundle, tmp_path, fake)
    assert receipt["status"] == "complete"
    for command, _ in fake.calls:
        if command[1] == "run":
            runner.validate_exec_argv(command)


def test_final_argument_limits_include_payload_wrapper_and_image_env(bundle, tmp_path):
    with pytest.raises(ValueError, match="single-string"):
        runner.validate_exec_argv(["python", "-c", "x" * 131_072])
    with pytest.raises(ValueError, match="aggregate"):
        runner.docker_command(docker="/usr/bin/docker", image=IMAGE, source=tmp_path,
                              name="owned-container", check=bundle["checks"][2], token=TOKEN,
                              image_env_keys=["ENV" + str(index) + "X" * 80 for index in range(2000)],
                              python_executable="/opt/venv/bin/python", uid=1001, gid=1001)
    escaped_payload = json.dumps({"source": "\x01" * 22_000})
    assert len(escaped_payload.encode()) > 131_071
    with pytest.raises(ValueError, match="single-string"):
        runner.validate_exec_argv(["python", "-c", runner.CONTAINER_WRAPPER, escaped_payload])
