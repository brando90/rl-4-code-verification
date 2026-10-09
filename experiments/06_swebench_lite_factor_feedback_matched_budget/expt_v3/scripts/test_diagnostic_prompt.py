"""Verify exact prompt delivery hashes, including headers, whitespace and UTF-8."""

import importlib.util
import json
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("e06_diagnostic_prompt", HERE / "diagnostic_prompt.py")
prompt = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prompt)


def test_freeze_preserves_exact_template_header_context_and_whitespace(tmp_path):
    context_bytes = '{ "instance_id": "task", "problem_statement": "café" }\r\n'.encode()
    context_path = tmp_path / "context.json"
    context_path.write_bytes(context_bytes)
    receipt = prompt.freeze_prompt(context_path=context_path, instance_id="task",
                                   expected_context_sha256=prompt.validator.sha256(context_bytes),
                                   output_dir=tmp_path / "frozen")
    delivered = (tmp_path / "frozen" / "prompt.txt").read_bytes()
    assert delivered == prompt.TEMPLATE.read_bytes() + prompt.CONTEXT_SEPARATOR + context_bytes + b"\n"
    assert delivered.startswith(b"# Public diagnostic author: version 3 transport\n")
    assert b"**Doc link:**" in delivered and b"**TLDR:**" in delivered
    assert receipt["template_header_delivered"] is True
    assert receipt["delivered_utf8_bytes"] > receipt["delivered_characters"]
    assert json.loads((tmp_path / "frozen" / "prompt_receipt.json").read_text()) == receipt
    prompt.verify_delivered_prompt(delivered, receipt)
    for changed in (delivered.strip(), delivered.replace(b"\r\n", b"\n"), delivered + b"Return a diff."):
        with pytest.raises(ValueError, match="differ"):
            prompt.verify_delivered_prompt(changed, receipt)
    with pytest.raises(FileExistsError):
        prompt.freeze_prompt(context_path=context_path, instance_id="task",
                             expected_context_sha256=prompt.validator.sha256(context_bytes),
                             output_dir=tmp_path / "frozen")


def test_context_identity_hash_and_input_limit_are_enforced():
    context = b'{"instance_id":"task"}'
    with pytest.raises(ValueError, match="hash mismatch"):
        prompt.render_prompt(b"template", context, instance_id="task", expected_context_sha256="0" * 64)
    with pytest.raises(ValueError, match="identity mismatch"):
        prompt.render_prompt(b"template", context, instance_id="other", expected_context_sha256=prompt.validator.sha256(context))
    with pytest.raises(ValueError, match="input-character"):
        prompt.render_prompt(b"x" * 96_000, context, instance_id="task", expected_context_sha256=prompt.validator.sha256(context))


def test_duplicate_context_identity_is_not_silently_salvaged():
    context = b'{"instance_id":"other","instance_id":"task"}'
    with pytest.raises(ValueError, match="duplicate_json_key"):
        prompt.render_prompt(b"template", context, instance_id="task", expected_context_sha256=prompt.validator.sha256(context))
