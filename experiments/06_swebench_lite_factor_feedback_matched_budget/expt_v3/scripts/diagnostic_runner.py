"""Run frozen public diagnostics in disposable Docker containers with typed receipts."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid


_SPEC = importlib.util.spec_from_file_location("e06_diagnostic_validator", Path(__file__).with_name("diagnostic_validator.py"))
validator = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(validator)

RESULT_PREFIX = "E06_DIAGNOSTIC_RESULT:"
CONTAINER_PATH = "/opt/venv/bin:/opt/conda/bin:/usr/local/bin:/usr/bin:/bin"
MAX_OUTPUT_BYTES = 1_048_576
MAX_WALL_SECONDS = 1800
CONTROL_TIMEOUT_SECONDS = 30
MAX_EXEC_ARGUMENT_BYTES = 131_071  # Linux 128 KiB string limit, including trailing NUL.
MAX_EXEC_TOTAL_BYTES = 120_000  # Conservative argv/pointer bound with environment reserve.
MAX_PLUGIN_INVENTORY_BYTES = 16_384
EMPTY_PLUGIN_SHA256 = validator.sha256(validator.canonical_bytes([]))

# Trusted transport adapter. It executes ONLY inside the disposable container.
# Exception metadata is independent of user-printed traceback text. It is not a
# hostile-code attestation: authored Python can introspect its own interpreter.
CONTAINER_WRAPPER = r'''
import ast, compileall, hashlib, json, os, sys, traceback
from importlib import metadata
payload = json.loads(sys.argv[1])
argv, kind, token = payload["argv"], payload["kind"], payload["token"]
receipt = {"token": token, "kind": kind, "debug": __debug__, "event": "setup_error",
           "exception_type": None, "top_level_assertion": False,
           "checks_sha256": hashlib.sha256(json.dumps(argv, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()}
exit_code = 2
class PluginInventoryMismatch(Exception):
    pass
def plugin_inventory():
    records = [{"distribution": distribution.metadata["Name"], "version": distribution.version,
                "name": entry.name, "value": entry.value}
               for distribution in metadata.distributions() for entry in distribution.entry_points
               if entry.group == "pytest11"]
    return sorted(records, key=lambda record: (record["distribution"], record["version"], record["name"], record["value"]))
def verify_plugins():
    observed = plugin_inventory()
    receipt["pytest11_sha256"] = hashlib.sha256(json.dumps(observed, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    if observed != payload["pytest11"]:
        raise PluginInventoryMismatch("public_image_pytest_plugins_changed")
try:
    if not __debug__ or "PYTHONOPTIMIZE" in os.environ:
        raise RuntimeError("assertions_not_enabled")
    if any(key in os.environ for key in ("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "PYTEST_PLUGINS", "PYTEST_ADDOPTS")):
        raise RuntimeError("pytest_environment_not_scrubbed")
    verify_plugins()
    sys.path.insert(0, "/workspace")
    if kind == "syntax":
        ok = True
        for path in argv[4:]:
            if os.path.isdir(path):
                ok = compileall.compile_dir(path, quiet=1) and ok
            elif os.path.isfile(path):
                ok = compileall.compile_file(path, quiet=1) and ok
            else:
                ok = False
        receipt["event"] = "passed" if ok else "compile_failure"
        exit_code = 0 if ok else 2
    elif argv[0] in ("python", "python3") and argv[1] == "-c":
        tree = ast.parse(argv[2], filename="<public-diagnostic>", mode="exec")
        assertion_lines = {line for node in tree.body if isinstance(node, ast.Assert)
                           for line in range(node.lineno, getattr(node, "end_lineno", node.lineno) + 1)}
        # Explicit raises sharing a line with an assert remain ambiguous.
        assertion_lines -= {node.lineno for node in ast.walk(tree) if isinstance(node, ast.Raise)}
        code = compile(tree, "<public-diagnostic>", "exec", dont_inherit=True, optimize=0)
        sys.argv = ["-c"]
        try:
            exec(code, {"__name__": "__main__", "__builtins__": __builtins__})
        except AssertionError as error:
            tail = error.__traceback__
            while tail.tb_next is not None:
                tail = tail.tb_next
            receipt.update(event="assertion_failure", exception_type=type(error).__name__,
                           top_level_assertion=tail.tb_frame.f_code is code and tail.tb_lineno in assertion_lines)
            traceback.print_exc()
            exit_code = 1
        else:
            receipt["event"] = "passed"
            exit_code = 0
    else:
        # Verify again with the public source path present, before autoload.
        # A checkout-provided dist-info must not add undeclared entry points.
        verify_plugins()
        import pytest
        class Reports:
            collected = 0
            call_passed = 0
            call_failed = 0
            setup_errors = 0
            def pytest_collection_finish(self, session):
                self.collected = len(session.items)
            def pytest_collectreport(self, report):
                if report.failed:
                    self.setup_errors += 1
            def pytest_runtest_logreport(self, report):
                if report.when == "call" and report.passed:
                    self.call_passed += 1
                elif report.when == "call" and report.failed:
                    self.call_failed += 1
                elif report.when in ("setup", "teardown") and report.failed:
                    self.setup_errors += 1
        reports = Reports()
        arguments = argv[3:] if argv[0] in ("python", "python3") else argv[1:]
        test_exit = int(pytest.main(arguments, plugins=[reports]))
        receipt["pytest"] = {"exit_code": test_exit, "collected": reports.collected,
                             "call_passed": reports.call_passed, "call_failed": reports.call_failed,
                             "setup_errors": reports.setup_errors}
        if reports.setup_errors or test_exit not in (0, 1, 5):
            receipt["event"] = "setup_error"
        elif reports.collected == 0 or reports.call_passed + reports.call_failed == 0:
            receipt["event"] = "no_tests_executed"
        elif test_exit == 0 and reports.call_failed == 0:
            receipt["event"] = "passed"
        else:
            receipt["event"] = "test_failure"
        exit_code = 0 if receipt["event"] == "passed" else 2
except PluginInventoryMismatch as error:
    receipt.update(event="plugin_inventory_mismatch", exception_type=type(error).__name__)
except (ImportError, ModuleNotFoundError) as error:
    receipt.update(event="import_error", exception_type=type(error).__name__)
    traceback.print_exc()
except BaseException as error:
    receipt.update(event="exception", exception_type=type(error).__name__)
    traceback.print_exc()
finally:
    print("\nE06_DIAGNOSTIC_RESULT:" + json.dumps(receipt, sort_keys=True), file=sys.stderr, flush=True)
sys.exit(exit_code)
'''


@dataclass
class ProcessResult:
    returncode: int | None
    stdout: bytes = b""
    stderr: bytes = b""
    timed_out: bool = False
    output_limit: bool = False
    elapsed_seconds: float = 0.0


class DisposableSource:
    """Retain a mounted public copy when container teardown is unverified."""

    def __init__(self, scratch_root):
        self.root = Path(tempfile.mkdtemp(prefix="e06-public-check-", dir=scratch_root))
        self.safe_to_remove = True

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        if self.safe_to_remove:
            shutil.rmtree(self.root)


class LocalDockerExecutor:
    """Bound Docker client output/time; never execute authored code on the host."""

    def __init__(self, *, docker_host=None, docker_context=None, docker_config_dir):
        self.environment = docker_client_environment(docker_host=docker_host, docker_context=docker_context,
                                                     docker_config_dir=docker_config_dir)

    def run(self, argv, *, timeout, max_output_bytes=MAX_OUTPUT_BYTES):
        validate_exec_argv(argv)
        start = time.monotonic()
        process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, shell=False, start_new_session=True,
                                   env=self.environment.copy())
        captured = {"stdout": bytearray(), "stderr": bytearray()}
        timed_out = output_limit = False
        with selectors.DefaultSelector() as selector:
            for name in captured:
                selector.register(getattr(process, name), selectors.EVENT_READ, name)
            while selector.get_map():
                remaining = timeout - (time.monotonic() - start)
                if remaining <= 0:
                    timed_out = True
                    break
                for key, _ in selector.select(min(0.1, remaining)):
                    chunk = os.read(key.fileobj.fileno(), 65_536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    destination = captured[key.data]
                    room = max_output_bytes - len(destination)
                    destination.extend(chunk[:room])
                    if len(chunk) > room:
                        output_limit = True
                        break
                if output_limit:
                    break
        if timed_out or output_limit:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.stdout.close()
        process.stderr.close()
        try:
            process.wait(timeout=max(0.01, timeout - (time.monotonic() - start)))
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
        return ProcessResult(process.returncode, bytes(captured["stdout"]), bytes(captured["stderr"]),
                             timed_out, output_limit, time.monotonic() - start)


def docker_client_environment(*, docker_host=None, docker_context=None, docker_config_dir):
    """Use one explicitly selected context or Unix socket; inherit no host env."""
    if not Path(docker_config_dir).is_absolute():
        raise ValueError("Docker config directory must be an explicit absolute path")
    environment = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "DOCKER_CONFIG": str(docker_config_dir)}
    if docker_context is not None:
        if docker_host is not None or not re.fullmatch(r"[A-Za-z0-9_.-]+", docker_context):
            raise ValueError("declare one Docker context or Unix socket, not both")
        environment["DOCKER_CONTEXT"] = docker_context
    else:
        host = docker_host or "unix:///var/run/docker.sock"
        if not re.fullmatch(r"unix:///[A-Za-z0-9_./-]+", host):
            raise ValueError("direct Docker hosts must be Unix sockets; use an admitted context for other transports")
        environment["DOCKER_HOST"] = host
    return environment


def validate_exec_argv(argv):
    """Bound actual UTF-8 exec strings, including JSON escaping and wrapper code."""
    sizes = [len(argument.encode("utf-8")) for argument in argv]
    if any(size > MAX_EXEC_ARGUMENT_BYTES for size in sizes):
        raise ValueError("exec argument exceeds Linux single-string limit")
    if sum(size + 1 for size in sizes) + 8 * (len(sizes) + 1) > MAX_EXEC_TOTAL_BYTES:
        raise ValueError("assembled exec arguments exceed conservative aggregate limit")


def validate_plugin_inventory(inventory, image, python_executable):
    """Bind the complete pytest11 inventory to the frozen public image/runtime."""
    if (not isinstance(inventory, dict)
            or set(inventory) != {"schema_version", "image_id", "python_executable", "pytest11"}
            or type(inventory["schema_version"]) is not int or inventory["schema_version"] != 1
            or inventory["image_id"] != image or inventory["python_executable"] != python_executable):
        raise ValueError("plugin inventory must match the image and interpreter")
    records = inventory["pytest11"]
    if not isinstance(records, list):
        raise ValueError("plugin inventory must list all pytest11 entry points")
    for record in records:
        if (not isinstance(record, dict) or set(record) != {"distribution", "version", "name", "value"}
                or any(not isinstance(value, str) or not value or "\0" in value for value in record.values())):
            raise ValueError("invalid pytest11 inventory record")
    ordered = sorted(records, key=lambda record: (record["distribution"], record["version"], record["name"], record["value"]))
    if records != ordered or len({validator.canonical_bytes(record) for record in records}) != len(records):
        raise ValueError("plugin inventory must be sorted and unique")
    if len(validator.canonical_bytes(inventory)) > MAX_PLUGIN_INVENTORY_BYTES:
        raise ValueError("plugin inventory exceeds frozen transport bound")
    return records


def public_tree_sha256(root):
    """Hash a public export; reject Git metadata, links and special files.

    The caller must obtain the expected hash from a pinned, public-only export.
    Matching a caller-supplied hash alone does not establish that provenance.
    """
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("public export must be an ordinary directory")
    records = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            raise ValueError("public export must exclude Git metadata")
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise ValueError("public export contains a link or special file")
        records.append({"path": relative.as_posix(), "directory": path.is_dir(),
                        "executable": bool(mode & 0o111) if path.is_file() else False,
                        "sha256": validator.sha256(path.read_bytes()) if path.is_file() else None})
    if not any(not record["directory"] for record in records):
        raise ValueError("empty public export")
    return validator.sha256(validator.canonical_bytes(records))


def inspect_public_image(executor, docker, image):
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        raise ValueError("image must be an immutable local sha256 image ID")
    result = executor.run([docker, "image", "inspect", image], timeout=CONTROL_TIMEOUT_SECONDS)
    if result.returncode != 0 or result.timed_out or result.output_limit:
        raise RuntimeError("public image inspection failed")
    try:
        entries = json.loads(result.stdout)
        entry = entries[0]
        if len(entries) != 1 or entry["Id"] != image or entry["Config"].get("Volumes"):
            raise ValueError
        environment = entry["Config"].get("Env") or []
        keys = [value.split("=", 1)[0] for value in environment]
        if any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) for key in keys):
            raise ValueError
    except (ValueError, TypeError, KeyError, IndexError):
        raise RuntimeError("image metadata identity, environment or implicit volumes invalid") from None
    # Never retain or print the image's environment values: even those must be
    # removed before the entry point starts, not merely inside the wrapper.
    return sorted(set(keys))


def docker_command(*, docker, image, source, name, check, token, image_env_keys,
                   python_executable, uid, gid, pytest11=()):
    if not Path(docker).is_absolute() or not re.fullmatch(r"/[A-Za-z0-9_./-]+", python_executable):
        raise ValueError("Docker and container Python must have absolute paths")
    if python_executable.startswith(("/workspace/", "/tmp/")) or "/../" in python_executable:
        raise ValueError("Python must come from the admitted image")
    if uid <= 0 or gid < 0:
        raise ValueError("diagnostics require a nonroot container user")
    source = Path(source).resolve()
    if "," in str(source):
        raise ValueError("bind source must not contain Docker mount separators")
    command = [docker, "run", "--name", name, "--pull=never", "--network=none",
               "--read-only", "--init", "--no-healthcheck", "--log-driver=none",
               "--cpus=4", "--memory=8g", "--memory-swap=8g", "--pids-limit=256",
               "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
               "--user", f"{uid}:{gid}", "--workdir=/workspace", "--ipc=none",
               "--mount", f"type=bind,src={source},dst=/workspace,bind-propagation=rprivate",
               "--tmpfs", "/tmp:rw,nosuid,nodev,size=1g,mode=1777"]
    for key in image_env_keys:
        command += ["--env", f"{key}="]
    command += ["--entrypoint=/usr/bin/env", image, "-i", f"PATH={CONTAINER_PATH}",
                "HOME=/tmp", "TMPDIR=/tmp", "LANG=C.UTF-8", "PYTHONNOUSERSITE=1",
                "PYTHONDONTWRITEBYTECODE=1",
                python_executable, "-I", "-c", CONTAINER_WRAPPER,
                json.dumps({"argv": check["argv"], "kind": check["kind"], "token": token, "pytest11": list(pytest11)},
                           separators=(",", ":"), ensure_ascii=False)]
    validate_exec_argv(command)
    return command


def classify(check, result, container_state, token, expected_plugins_sha256=EMPTY_PLUGIN_SHA256):
    """Fail closed on missing/ambiguous typed receipts, regardless of log text."""
    if result.timed_out:
        return "timeout", None
    if result.output_limit:
        return "output_limit", None
    if (not isinstance(container_state, dict) or container_state.get("Running") is not False
            or container_state.get("Status") != "exited"):
        return "container_state_unverified", None
    if container_state.get("OOMKilled") is True:
        return "out_of_memory", None
    if container_state.get("ExitCode") != result.returncode:
        return "container_exit_mismatch", None
    lines = [line[len(RESULT_PREFIX):] for line in result.stderr.decode("utf-8", errors="replace").splitlines()
             if line.startswith(RESULT_PREFIX)]
    if len(lines) != 1:
        return "missing_or_ambiguous_execution_receipt", None
    try:
        record = validator.parse_response(lines[0])
    except (ValueError, RecursionError):
        return "invalid_execution_receipt", None
    if (not isinstance(record, dict) or record.get("token") != token or record.get("debug") is not True
            or record.get("kind") != check["kind"]
            or record.get("checks_sha256") != validator.sha256(validator.canonical_bytes(check["argv"]))):
        return "execution_receipt_identity_mismatch", record
    event = record.get("event")
    if event == "plugin_inventory_mismatch" or record.get("pytest11_sha256") != expected_plugins_sha256:
        return "plugin_inventory_unverified", record
    is_pytest = check["kind"] == "regression" and check["argv"][1:2] != ["-c"]
    if event == "passed" and is_pytest:
        tests = record.get("pytest")
        if (not isinstance(tests, dict) or tests.get("exit_code") != 0
                or tests.get("setup_errors") != 0 or tests.get("call_failed") != 0
                or type(tests.get("call_passed")) is not int or tests["call_passed"] < 1
                or type(tests.get("collected")) is not int or tests["collected"] < tests["call_passed"]):
            return "pytest_completion_unverified", record
    if event == "passed" and result.returncode == 0:
        return ("issue_not_reproduced" if check["kind"] == "issue" else f"{check['kind']}_passed"), record
    if event == "assertion_failure" and result.returncode == 1:
        if record.get("exception_type") != "AssertionError" or record.get("top_level_assertion") is not True:
            return "assertion_origin_unverified", record
        return ("issue_assertion_failure" if check["kind"] == "issue" else "regression_failed"), record
    if event in {"import_error", "setup_error", "no_tests_executed", "compile_failure", "exception", "test_failure"} and result.returncode == 2:
        return ("regression_failed" if event == "test_failure" and check["kind"] == "regression" else event), record
    return "execution_event_exit_mismatch", record


def summarize_base(checks):
    """Keep syntax viability, regression preservation and reproduction separate."""
    expected = {"syntax": "syntax_passed", "regression": "regression_passed", "issue": "issue_assertion_failure"}
    counts = {kind: {"required": sum(row["kind"] == kind for row in checks),
                     "valid": sum(row["kind"] == kind and row["classification"] == status for row in checks)}
              for kind, status in expected.items()}
    return {"denominators": counts,
            "base_diagnostics_usable": all(value["required"] > 0 and value["required"] == value["valid"] for value in counts.values()),
            "issue_semantic_fidelity": "not_established_by_execution"}


def run_bundle(bundle, *, public_export, expected_source_sha256, image, python_executable,
               output_dir, scratch_root, wall_timeout_seconds, docker="/usr/bin/docker",
               plugin_inventory, docker_host=None, docker_context=None, docker_config_dir=None,
               executor=None, uid=None, gid=None):
    """Execute an admitted public bundle, sequentially, without model/evaluator access.

    Callers own run admission, the overall processor/storage/deadline ledger,
    public-image provenance and shared two-container capacity. This primitive
    enforces only per-check bounds and stops when owned cleanup is unverified.
    Neither logs nor a failing constant assertion establish semantic relevance.
    """
    bundle = validator.validate_response(validator.canonical_bytes(bundle).decode("utf-8"), bundle["instance_id"])
    if type(wall_timeout_seconds) not in (int, float) or not 0 < wall_timeout_seconds <= MAX_WALL_SECONDS:
        raise ValueError("explicit wall timeout must be in (0, 1800] seconds")
    public_export, output_dir, scratch_root = map(Path, (public_export, output_dir, scratch_root))
    if any(path.resolve().is_relative_to(public_export.resolve())
           for path in (output_dir, scratch_root)):
        raise ValueError("scratch and output paths must be outside the public export")
    if public_tree_sha256(public_export) != expected_source_sha256:
        raise ValueError("public export hash mismatch")
    plugins = validate_plugin_inventory(plugin_inventory, image, python_executable)
    plugins_sha256 = validator.sha256(validator.canonical_bytes(plugins))
    if docker_context is not None and docker_config_dir is None:
        raise ValueError("an admitted Docker context requires its explicit config directory")
    config_directory = Path(docker_config_dir).resolve() if docker_config_dir is not None else output_dir.resolve() / "docker-client-config"
    client_environment = docker_client_environment(docker_host=docker_host, docker_context=docker_context,
                                                   docker_config_dir=config_directory)
    if docker_config_dir is not None and not config_directory.is_dir():
        raise ValueError("admitted Docker config directory is missing")
    executor = executor or LocalDockerExecutor(docker_host=docker_host, docker_context=docker_context,
                                               docker_config_dir=config_directory)
    uid, gid = os.getuid() if uid is None else uid, os.getgid() if gid is None else gid
    # Validate command policy before any daemon call.
    docker_command(docker=docker, image=image, source=public_export, name="validation-only",
                   check=bundle["checks"][0], token="validation-only", image_env_keys=[],
                   python_executable=python_executable, uid=uid, gid=gid, pytest11=plugins)
    output_dir.mkdir(parents=True, exist_ok=False)
    if docker_config_dir is None:
        config_directory.mkdir(mode=0o700)
    receipt = {"schema_version": 1, "instance_id": bundle["instance_id"],
               "bundle_sha256": validator.sha256(validator.canonical_bytes(bundle)),
               "public_source_sha256": expected_source_sha256, "image_id": image,
               "runner_sha256": validator.sha256(Path(__file__).read_bytes()),
               "wrapper_sha256": validator.sha256(CONTAINER_WRAPPER.encode()),
               "python_executable": python_executable,
               "plugin_inventory_sha256": validator.sha256(validator.canonical_bytes(plugin_inventory)),
               "pytest11_sha256": plugins_sha256,
               "docker_connection": {key: value for key, value in client_environment.items() if key.startswith("DOCKER_")},
               "limits": {"cpus": 4, "memory_gib": 8, "wall_timeout_seconds": wall_timeout_seconds,
                          "control_timeout_seconds": CONTROL_TIMEOUT_SECONDS,
                          "output_bytes_per_stream": MAX_OUTPUT_BYTES},
               "checks": [], "status": "running"}
    validator.exclusive_write(output_dir / "started.json", receipt)
    halted = None
    try:
        image_env_keys = inspect_public_image(executor, docker, image)
        for check in bundle["checks"]:
            row = {"id": check["id"], "kind": check["kind"], "argv": check["argv"],
                   "classification": "not_measured", "execution_receipt": None}
            receipt["checks"].append(row)
            if halted:
                row["not_measured_reason"] = halted
                continue
            with DisposableSource(scratch_root) as temporary:
                copied = temporary.root / "source"
                shutil.copytree(public_export, copied, symlinks=True)
                if public_tree_sha256(copied) != expected_source_sha256:
                    raise RuntimeError("disposable source hash mismatch")
                name, token = "e06-diagnostic-" + uuid.uuid4().hex, uuid.uuid4().hex
                command = docker_command(docker=docker, image=image, source=copied, name=name,
                                         check=check, token=token, image_env_keys=image_env_keys,
                                         python_executable=python_executable, uid=uid, gid=gid, pytest11=plugins)
                row["container_name"] = name
                result, container_state = ProcessResult(None), None
                cleanup_ok = False
                try:
                    temporary.safe_to_remove = False
                    result = executor.run(command, timeout=wall_timeout_seconds)
                    state_result = executor.run([docker, "inspect", "--format", "{{json .State}}", name],
                                                timeout=CONTROL_TIMEOUT_SECONDS)
                    if state_result.returncode == 0 and not state_result.timed_out and not state_result.output_limit:
                        try:
                            container_state = json.loads(state_result.stdout)
                        except ValueError:
                            pass
                    row["classification"], row["execution_receipt"] = classify(check, result, container_state, token, plugins_sha256)
                except OSError as exc:
                    row.update(classification="docker_client_error", error_type=type(exc).__name__)
                finally:
                    try:
                        cleanup = executor.run([docker, "rm", "--force", name], timeout=CONTROL_TIMEOUT_SECONDS)
                        cleanup_ok = cleanup.returncode == 0 and not cleanup.timed_out and not cleanup.output_limit
                    except OSError:
                        cleanup_ok = False
                    row.update(returncode=result.returncode, timed_out=result.timed_out,
                               output_limit=result.output_limit, elapsed_seconds=result.elapsed_seconds,
                               container_state=container_state, cleanup_verified=cleanup_ok)
                    for stream in ("stdout", "stderr"):
                        raw = getattr(result, stream)
                        (output_dir / f"{check['id']}.{stream}.log").write_bytes(raw)
                        row[f"{stream}_sha256"] = validator.sha256(raw)
                        row[f"{stream}_bytes"] = len(raw)
                    if not cleanup_ok:
                        row["classification"] = "cleanup_unverified"
                        row["retained_public_copy"] = str(copied)
                        halted = "owned_container_cleanup_unverified"
                    temporary.safe_to_remove = cleanup_ok
                    validator.exclusive_write(output_dir / f"{check['id']}.json", row)
        receipt.update(summarize_base(receipt["checks"]))
        receipt["status"] = "complete" if halted is None else "stopped"
    except (OSError, RuntimeError, ValueError) as exc:
        receipt.update(status="failed", error_type=type(exc).__name__)
        recorded = {row["id"] for row in receipt["checks"]}
        for check in bundle["checks"]:
            if check["id"] not in recorded:
                receipt["checks"].append({"id": check["id"], "kind": check["kind"],
                                          "classification": "not_measured", "not_measured_reason": "runner_failure"})
        receipt.update(summarize_base(receipt["checks"]))
    finally:
        try:
            receipt["original_public_source_unchanged"] = public_tree_sha256(public_export) == expected_source_sha256
        except (OSError, ValueError):
            receipt["original_public_source_unchanged"] = False
        if not receipt["original_public_source_unchanged"]:
            receipt.update(status="failed", base_diagnostics_usable=False)
        validator.exclusive_write(output_dir / "receipt.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--public-export", type=Path, required=True)
    parser.add_argument("--expected-source-sha256", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--python-executable", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--wall-timeout-seconds", type=float, required=True)
    parser.add_argument("--plugin-inventory", type=Path, required=True)
    parser.add_argument("--docker", default="/usr/bin/docker")
    parser.add_argument("--docker-host")
    parser.add_argument("--docker-context")
    parser.add_argument("--docker-config-dir", type=Path)
    args = parser.parse_args()
    result = run_bundle(json.loads(args.bundle.read_text()), public_export=args.public_export,
                        expected_source_sha256=args.expected_source_sha256, image=args.image,
                        python_executable=args.python_executable, output_dir=args.output_dir,
                        scratch_root=args.scratch_root, wall_timeout_seconds=args.wall_timeout_seconds,
                        plugin_inventory=validator.parse_response(args.plugin_inventory.read_text()),
                        docker=args.docker, docker_host=args.docker_host, docker_context=args.docker_context,
                        docker_config_dir=args.docker_config_dir)
    print(json.dumps({"status": result["status"], "base_diagnostics_usable": result["base_diagnostics_usable"]}))
    return 0 if result["status"] == "complete" and result["base_diagnostics_usable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
