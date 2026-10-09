"""Exercise strict diagnostic transport with synthetic, never-executed checks."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("e06_v3_diagnostic_validator", HERE / "diagnostic_validator.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)
TASK = "example__public-repo-1"


@pytest.fixture
def bundle():
    return {"schema_version": 1, "instance_id": TASK, "checks": [
        {"id": "syntax_01", "kind": "syntax", "argv": ["python", "-m", "compileall", "-q", "package"]},
        {"id": "regression_01", "kind": "regression", "argv": ["python", "-m", "pytest", "tests/test_public.py", "-q"]},
        {"id": "issue_01", "kind": "issue", "argv": ["python", "-c", "from package import value; assert value() == 'a;b'"]},
    ]}


def validate(bundle):
    return validator.validate_response(json.dumps(bundle), TASK)


def test_quoted_semicolons_and_multiline_python_are_not_shell_tokens(bundle):
    bundle["checks"][2]["argv"][2] = "value = 'a; b | c $(never-execute)'\nassert ';' in value"
    assert validate(bundle) == bundle


@pytest.mark.parametrize("wrapper", [
    "```json\n{}\n```", "```\n{}\n```", "Here is the JSON:\n{}",
    "{}\nExplanation follows", "{}\n{{}}", "{}\n```diff\n+assert True\n```",
    "diff --git a/file.py b/file.py\n--- a/file.py\n+++ b/file.py\n{}",
])
def test_fences_extra_material_and_inherited_diff_prompt_mismatch_rejected(bundle, wrapper):
    with pytest.raises(validator.DiagnosticValidationError, match="^invalid_json_transport$"):
        validator.validate_response(wrapper.format(json.dumps(bundle)), TASK)


def test_duplicate_keys_and_nonfinite_numbers_rejected(bundle):
    text = json.dumps(bundle).replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1')
    with pytest.raises(validator.DiagnosticValidationError, match="^duplicate_json_key$"):
        validator.validate_response(text, TASK)
    with pytest.raises(validator.DiagnosticValidationError, match="^nonfinite_json_number$"):
        validator.parse_response('{"value": NaN}')


@pytest.mark.parametrize("source", [
    "print(value)", "print('assert actual == expected')", "# assert False\nprint(1)",
    "def never_called():\n    assert False", "if False:\n    assert False",
    "try:\n    assert False\nexcept AssertionError:\n    pass",
])
def test_print_only_comments_dead_or_caught_assertions_do_not_qualify(bundle, source):
    bundle["checks"][2]["argv"][2] = source
    with pytest.raises(validator.DiagnosticValidationError, match="^missing_top_level_assertion$"):
        validate(bundle)


@pytest.mark.parametrize("source", ["assert (", "return\nassert True", "break\nassert True"])
def test_non_compilable_python_rejected_without_execution(bundle, source):
    bundle["checks"][2]["argv"][2] = source
    with pytest.raises(validator.DiagnosticValidationError, match="^invalid_python_source$"):
        validate(bundle)


def test_static_assertion_does_not_establish_behavioral_validity(bundle):
    # These would always pass/fail respectively, but the validator never runs
    # them and cannot establish behavioral discrimination or issue fidelity.
    for source in ("assert True", "assert False", "raise ImportError('fixture'); assert True"):
        bundle["checks"][2]["argv"][2] = source
        record = validator.inspect_response(json.dumps(bundle).encode(), TASK)
        assert record["structural_status"] == "accepted"
        assert record["execution_status"] == record["behavioral_status"] == "not_measured"
        assert record["denominators"] == {"syntax": 1, "regression": 1, "issue": 1}


def test_generated_python_is_never_executed(bundle, tmp_path):
    marker = tmp_path / "must-not-exist"
    bundle["checks"][2]["argv"][2] = f"from pathlib import Path; Path({str(marker)!r}).touch(); assert True"
    assert validate(bundle) == bundle
    assert not marker.exists()


@pytest.mark.parametrize("argv", [
    "python -c 'assert True'", [], ["sh", "-c", "assert True"],
    ["/usr/bin/python", "-c", "assert True"], ["python", "-O", "-c", "assert True"],
    ["python", "-m", "pytest", "tests/test_public.py"], ["python", "-c", ""],
    ["python", "-c", "assert True\x00"], ["python", "-c", 1],
])
def test_issue_checks_require_nonempty_structured_python_assertions(bundle, argv):
    bundle["checks"][2]["argv"] = argv
    with pytest.raises(validator.DiagnosticValidationError):
        validate(bundle)


@pytest.mark.parametrize("argv", [
    ["python", "-m", "pytest"], ["pytest", "-q"], ["pytest", "../secret.py"],
    ["pytest", "/evaluator/test.py"], ["pytest", "tests/test.py", "-p", "plugin"],
    ["pytest", "tests/test.py", ";", "touch", "marker"],
    ["python", "tests/test.py"], ["pytest", "tests/../../test.py"],
])
def test_regression_entry_points_options_and_paths_bounded(bundle, argv):
    bundle["checks"][1]["argv"] = argv
    with pytest.raises(validator.DiagnosticValidationError):
        validate(bundle)


def test_regression_test_selectors_and_assertion_programs_supported(bundle):
    for argv in (["pytest", "tests/test_public.py::TestPublic::test_value", "--tb=short"],
                 ["python3", "-c", "from package import old; assert old() == 1"]):
        bundle["checks"][1]["argv"] = argv
        assert validate(bundle) == bundle


@pytest.mark.parametrize("mutation,reason", [
    (lambda b: b.update(instance_id="other-task"), "instance_id_mismatch"),
    (lambda b: b.update(schema_version=True), "unsupported_schema_version"),
    (lambda b: b.update(notes="extra"), "unexpected_bundle_fields"),
    (lambda b: b["checks"][2].update(id="regression_02"), "check_id_membership_or_order"),
    (lambda b: b["checks"][2].update(kind="unknown"), "unknown_kind"),
    (lambda b: b["checks"][2].update(timeout=10), "unexpected_check_fields"),
])
def test_schema_and_membership_are_fixed(bundle, mutation, reason):
    mutation(bundle)
    with pytest.raises(validator.DiagnosticValidationError, match=f"^{reason}$"):
        validate(bundle)


def test_nonempty_denominators_and_unique_sequential_ids(bundle):
    bundle["checks"][2] = {"id": "regression_02", "kind": "regression", "argv": ["pytest", "tests/test_other.py"]}
    with pytest.raises(validator.DiagnosticValidationError, match="^empty_kind_denominator$"):
        validate(bundle)
    bundle["checks"][2] = copy.deepcopy(bundle["checks"][1])
    with pytest.raises(validator.DiagnosticValidationError, match="^check_id_membership_or_order$"):
        validate(bundle)


def test_receipt_binds_exact_bytes_and_normalized_bundle(bundle):
    raw = json.dumps(bundle).encode()
    first = validator.inspect_response(raw, TASK)
    spaced = validator.inspect_response(raw + b"\n", TASK)
    assert first["bundle_sha256"] == spaced["bundle_sha256"]
    assert first["response_sha256"] != spaced["response_sha256"]
    assert first["validator_sha256"] == validator.sha256((HERE / "diagnostic_validator.py").read_bytes())
    assert validator.inspect_response(b"\xff", TASK)["invalid_reason"] == "invalid_utf8"


def test_limits_and_malformed_types_reject_deterministically(bundle):
    for text, reason in ((" " * 65_537, "response_size"), ("[]", "response_not_object"),
                         ('{"checks":', "invalid_json_transport")):
        with pytest.raises(validator.DiagnosticValidationError, match=f"^{reason}$"):
            validator.validate_response(text, TASK)
    bundle["checks"][2]["argv"][2] = "#" * 16_385
    with pytest.raises(validator.DiagnosticValidationError, match="^argument_too_large$"):
        validate(bundle)


def test_excessive_json_nesting_and_integer_size_are_stable_rejections():
    record = validator.inspect_response(("[" * 2_000 + "]" * 2_000).encode(), TASK)
    assert record["invalid_reason"] == "invalid_json_transport"
    # Recent Python versions limit integer decoding; older versions parse this
    # bounded integer, then deterministically reject the absent bundle fields.
    record = validator.inspect_response(('{"value":' + "1" * 5_000 + "}").encode(), TASK)
    assert record["invalid_reason"] in {"invalid_json_transport", "unexpected_bundle_fields"}


def test_cli_preserves_rejections_and_refuses_overwrite(tmp_path):
    source = tmp_path / "response.txt"
    output = tmp_path / "receipt.json"
    source.write_text("```json\n{}\n```", encoding="utf-8")
    command = [sys.executable, str(HERE / "diagnostic_validator.py"),
               "--response", str(source), "--instance-id", TASK, "--output", str(output)]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    assert completed.returncode == 1
    receipt = output.read_bytes()
    assert json.loads(receipt)["invalid_reason"] == "invalid_json_transport"
    assert subprocess.run(command, capture_output=True, check=False).returncode == 2
    assert output.read_bytes() == receipt


def test_author_prompt_has_one_transport_contract():
    prompt = (HERE.parent / "diagnostic_author_prompt.txt").read_text()
    assert "unified diff" not in prompt.lower()
    assert "Do not use Markdown fences" in prompt
    assert all(f"{kind}_01" in prompt for kind in validator.KINDS)
    assert "structural" in prompt and "assert" in prompt
