"""Check version 2 test admission using an actual temporary published Git tree."""
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parents[1] / "experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/scripts"
spec = importlib.util.spec_from_file_location("admission_v2", SCRIPTS / "test_admission_e08v2.py")
admission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admission)


@pytest.fixture
def published(tmp_path):
    exp = tmp_path / "expt_v2"
    (exp / "results").mkdir(parents=True)
    model = tmp_path / "weights"
    model.mkdir()
    (model / "SHA256SUMS").write_text("frozen weights\n")
    (exp / "PROTOCOL_v2.md").write_text("locked protocol\n")
    (tmp_path / "ids.txt").write_text("test task\n")
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = {"split": "test", "n_tasks": 222, "samples_per_task": 8, "protocol_sha256": digest(exp / "PROTOCOL_v2.md"), "task_ids_file": "ids.txt", "task_ids_sha256": digest(tmp_path / "ids.txt"), "systems": [{"label": "allowed", "generation": "new", "hf_path": str(model), "step": 658, "cumulative_assistant_tokens": 5752936, "weights_sha256_manifest": digest(model / "SHA256SUMS")}]}
    (exp / "results/test_manifest_v2.json").write_text(json.dumps(manifest))
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, capture_output=True, check=True)
    git("init")
    git("add", ".")
    git("-c", "user.name=Test", "-c", "user.email=test@example.org", "commit", "-m", "Published fixture")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    return tmp_path, exp, model


def test_published_checkpoint_admitted(published):
    repo, exp, model = published
    assert admission.check("allowed", str(model), "local", repo=repo, exp=exp)["verdict"] == "PASS"


@pytest.mark.parametrize("label,revision", [("other", "local"), ("allowed", "remote")])
def test_outside_manifest_rejected(published, label, revision):
    repo, exp, model = published
    with pytest.raises(ValueError, match="outside the manifest"):
        admission.check(label, str(model), revision, repo=repo, exp=exp)


def test_weight_mismatch_rejected(published):
    repo, exp, model = published
    (model / "SHA256SUMS").write_text("changed weights\n")
    with pytest.raises(ValueError, match="Weight hash mismatch"):
        admission.check("allowed", str(model), "local", repo=repo, exp=exp)


@pytest.mark.parametrize("name", ["results/test_manifest_v2.json", "PROTOCOL_v2.md"])
def test_unpublished_artifact_rejected(published, name):
    repo, exp, model = published
    path = exp / name
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="not the exact published"):
        admission.check("allowed", str(model), "local", repo=repo, exp=exp)
