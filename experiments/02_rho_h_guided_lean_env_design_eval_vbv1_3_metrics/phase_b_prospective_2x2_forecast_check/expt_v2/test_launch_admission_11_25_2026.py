"""11-25-2026: verify scientific admission failures cannot reach GPU or tmux dispatch."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest


@pytest.fixture
def launcher(monkeypatch):
    path = Path(__file__).with_name("launch_admitted_11-25-2026.py")
    spec = importlib.util.spec_from_file_location("dated_launch_admission", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def forbidden_dispatch(*args, **kwargs):
        pytest.fail("GPU/process command reached before scientific admission")

    monkeypatch.setattr(module.subprocess, "check_output", forbidden_dispatch)
    monkeypatch.setattr(module.subprocess, "run", forbidden_dispatch)
    return module


def test_current_not_admitted_receipt_never_dispatches(launcher, monkeypatch, capsys):
    receipt = Path(__file__).with_name("launch_admission_11-25-2026.json")
    monkeypatch.setattr(sys, "argv", ["launch", str(receipt)])
    assert launcher.main() == 2
    assert "NOT LAUNCHED" in capsys.readouterr().out


def test_status_string_alone_cannot_admit_training(launcher, monkeypatch, tmp_path):
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"status": "ADMITTED"}))
    monkeypatch.setattr(sys, "argv", ["launch", str(receipt)])
    with pytest.raises(ValueError, match="missing hash-pinned admission artifact: protocol"):
        launcher.main()


def test_changed_protocol_cannot_dispatch(launcher, monkeypatch, tmp_path):
    protocol = tmp_path / "protocol.txt"
    protocol.write_text("modified protocol")
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({
        "status": "ADMITTED",
        "protocol": {"path": str(protocol), "sha256": "0" * 64},
    }))
    monkeypatch.setattr(sys, "argv", ["launch", str(receipt)])
    with pytest.raises(ValueError, match="changed admission artifact: protocol"):
        launcher.main()
