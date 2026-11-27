"""The 11-27-2026 experiment 14 amendment pins numpy and tolerates only a tiny median drift."""
import importlib.util
from pathlib import Path

MODULE = Path("experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/expt_v1/stop_rule_amendment_11-27-2026.py")
PIN = MODULE.parent / "requirements-locked-rerun-11-27-2026.txt"
PROTOCOL = MODULE.parents[1] / "PROTOCOL.md"
ANALYZER = MODULE.parent / "analyze_e14.py"


def load():
    spec = importlib.util.spec_from_file_location("e14_amend", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def published_copy(amend):
    return {key: dict(value) for key, value in amend.PUBLISHED.items()}


def test_pin_file_and_locked_sources_stay_exact():
    text = PIN.read_text()
    assert "numpy==2.2.6" in text
    assert "scipy==1.16.3" in text
    assert "reproduces experiment 07's H2 exactly" in PROTOCOL.read_text()
    assert 'replay[k]["delta_median"] == published[k]["delta_median"]' in ANALYZER.read_text()


def test_pinned_numpy_is_exact_and_the_qa_drift_needs_the_tolerance():
    amend = load()
    exact = published_copy(amend)
    assert amend.replay_matches(exact, numpy_version="2.2.6")["ok"] is True
    drifted = published_copy(amend)
    drifted["50"]["delta_median"] = -0.012140169
    pinned = amend.replay_matches(drifted, numpy_version="2.2.6")
    assert pinned["ok"] is False and pinned["mode"] == "exact"
    amended = amend.replay_matches(drifted, numpy_version="2.5.3")
    assert amended["ok"] is True and amended["mode"] == "tolerance"
    assert amended["atol"] == 5e-6
    jumped = published_copy(amend)
    jumped["50"]["delta_median"] = -0.013
    assert amend.replay_matches(jumped, numpy_version="2.5.3")["ok"] is False
    splits = published_copy(amend)
    splits["50"]["positive_splits"] = 93
    assert amend.replay_matches(splits, numpy_version="2.5.3")["ok"] is False
