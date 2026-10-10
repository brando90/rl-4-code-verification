"""Counterexamples for Experiment 13 scoring, sealed splits and receipt admission."""

from dataclasses import asdict, replace
import itertools
import pytest

from rl4cv.e13 import PartialCredit, verify_control_rows, placebo_reward
from rl4cv.rewards import ScoredResponse, reward_kernel_binary


def complete(**changes):
    fields = dict(extracted=True, compiles=True, n_examples=1, theorem_count=2,
                  proved_count=2, vacuous_count=0, declarations_ok=1.0,
                  implementation_and_examples_ok=True, proved_fraction=1.0, truncated=False)
    fields.update(changes)
    return PartialCredit(**fields)


def manifest(**changes):
    value = dict(cell_id="policy/task/0", task_id="task", split="validation",
                 response_sha256="a" * 64, kernel_binary=1)
    value.update(changes)
    return value


def row(**changes):
    value = {**manifest(), **asdict(complete()), "status": "measured"}
    value.update(changes)
    return value


def test_existing_strict_contract_exhaustive_small_counts():
    # Independent legacy public scorer is the oracle, not a copied new formula.
    for extracted, compiles, examples, theorems, truncated in itertools.product([False, True], [False, True], range(3), range(3), [False, True]):
        for proved in range(theorems + 1):
            for vacuous in range(theorems + 1):
                pc = complete(extracted=extracted, compiles=compiles, n_examples=examples,
                              theorem_count=theorems, proved_count=proved, vacuous_count=vacuous,
                              proved_fraction=proved / theorems if theorems else 0.0, truncated=truncated)
                old = ScoredResponse(extracted, compiles, examples, theorems, proved,
                                     vacuous_theorems=vacuous, truncated=truncated)
                assert pc.strict == reward_kernel_binary(old)


def test_valid_cap_completion_and_missing_example_counterexamples():
    assert complete(truncated=True).strict == 1
    assert complete(n_examples=0).strict == 0
    assert complete(n_examples=0).factored_reward() == 0
    assert complete(compiles=False).strict == 0  # top-level command can fail outside counted declarations
    # Declaration diagnostics never replace the official post-probe status.
    # The actual pinned probe can reject printed error text despite Lean exit 0.
    assert complete(declarations_ok=0.5).strict == 1
    assert complete(compiles=False, proved_count=0, proved_fraction=0.0).strict == 0


def test_partial_proof_diagnostic_does_not_replace_official_failed_file_count():
    pc = complete(compiles=False, proved_count=0, proved_fraction=0.5, declarations_ok=0.75)
    assert pc.strict == 0 and 0 < pc.factored_reward() < 1


@pytest.mark.parametrize("changes", [
    {"extracted": "false"}, {"compiles": 1}, {"truncated": None},
    {"n_examples": 1.5}, {"theorem_count": True}, {"proved_count": 3},
    {"declarations_ok": float("nan")}, {"proved_fraction": float("inf")},
    {"proved_fraction": 0.5}, {"vacuous_count": -1},
])
def test_malformed_evidence_rejected(changes):
    with pytest.raises(ValueError):
        complete(**changes)


@pytest.mark.parametrize("changes", [
    {"cell_id": "replacement"}, {"task_id": "different"}, {"response_sha256": "b" * 64},
    {"split": "test"}, {"status": "missing"}, {"compiles": False},
])
def test_identity_and_independent_label_counterexamples(changes):
    with pytest.raises(ValueError):
        verify_control_rows([row(**changes)], [manifest()])


def test_empty_missing_duplicate_and_sealed_manifests_rejected():
    for rows, expected in [([], []), ([], [manifest()]), ([row(), row()], [manifest()]),
                           ([row()], [manifest(), manifest()]), ([row(split="test")], [manifest(split="test")]),
                           ([row()], [manifest(kernel_binary=None)])]:
        with pytest.raises(ValueError):
            verify_control_rows(rows, expected)


def test_receipt_binds_content_not_just_cell_ids():
    a = verify_control_rows([row()], [manifest()])
    b = verify_control_rows([row(truncated=True)], [manifest()])
    assert a["manifest_sha256"] == b["manifest_sha256"]
    assert a["rows_sha256"] != b["rows_sha256"]


def test_placebo_stream_has_group_key_and_no_response_or_task_input():
    dist = (0.0, 0.2, 0.5, 1.0)
    draws = [placebo_reward(dist, seed=42, update=0, group=g, slot=0) for g in range(32)]
    assert len(set(draws)) > 1  # catches repeated draw across all prompt groups
    assert draws == [placebo_reward(dist, seed=42, update=0, group=g, slot=0) for g in range(32)]
    with pytest.raises(TypeError):
        placebo_reward(dist, seed=42, update=0, group=0, slot=0, task_id="leak")


def test_dense_fraction_is_not_a_coverage_guarantee():
    # A concrete known vulnerability, retained to prevent claims of immunity:
    # adding easy valid declarations can increase reward without fixing failure.
    a = complete(compiles=False, proved_count=0, proved_fraction=0.5, declarations_ok=0.5)
    b = replace(a, declarations_ok=0.9, proved_fraction=0.9)
    assert b.strict == a.strict == 0
    assert b.factored_reward() > a.factored_reward()
