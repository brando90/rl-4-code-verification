"""Freeze and verify the exact delivered diagnostic-author prompt bytes."""

import argparse
import importlib.util
import json
from pathlib import Path


_SPEC = importlib.util.spec_from_file_location("e06_prompt_validator", Path(__file__).with_name("diagnostic_validator.py"))
validator = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(validator)
TEMPLATE = Path(__file__).resolve().parent.parent / "diagnostic_author_prompt.txt"
CONTEXT_SEPARATOR = b"\n\nPUBLIC_CONTEXT_JSON\n"
MAX_INPUT_CHARACTERS = 96_000


def render_prompt(template_bytes, context_bytes, *, instance_id, expected_context_sha256):
    """Preserve all template/context bytes, including the visible document header.

    Public projection provenance is the caller's responsibility. This mechanism
    binds exact delivered text, not model receipt or absence of hidden client
    prompts; those require separate verification of the actual invocation.
    """
    if validator.sha256(context_bytes) != expected_context_sha256:
        raise ValueError("public context hash mismatch")
    context_text = context_bytes.decode("utf-8")
    context = json.loads(context_text, object_pairs_hook=validator._unique_object,
                         parse_constant=validator._no_constant)
    if not isinstance(context, dict) or context.get("instance_id") != instance_id:
        raise ValueError("public context identity mismatch")
    payload = template_bytes + CONTEXT_SEPARATOR + context_bytes + b"\n"
    text = payload.decode("utf-8")
    if len(text) > MAX_INPUT_CHARACTERS:
        raise ValueError("delivered prompt exceeds the frozen input-character limit")
    receipt = {"schema_version": 1, "instance_id": instance_id,
               "template_sha256": validator.sha256(template_bytes),
               "public_context_sha256": expected_context_sha256,
               "delivered_prompt_sha256": validator.sha256(payload),
               "delivered_utf8_bytes": len(payload), "delivered_characters": len(text),
               "template_header_delivered": True,
               "delivery_contract": "Transmit prompt.txt verbatim; no strip, interpolation or appended reminder."}
    return payload, receipt


def verify_delivered_prompt(payload, receipt):
    """Call immediately before delivery; reject any stripped/reformatted bytes."""
    if (validator.sha256(payload) != receipt.get("delivered_prompt_sha256")
            or len(payload) != receipt.get("delivered_utf8_bytes")
            or len(payload.decode("utf-8")) != receipt.get("delivered_characters")):
        raise ValueError("delivered prompt bytes differ from the frozen receipt")


def freeze_prompt(*, context_path, instance_id, expected_context_sha256, output_dir, template_path=TEMPLATE):
    payload, receipt = render_prompt(Path(template_path).read_bytes(), Path(context_path).read_bytes(),
                                     instance_id=instance_id, expected_context_sha256=expected_context_sha256)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    with (output_dir / "prompt.txt").open("xb") as stream:
        stream.write(payload)
    validator.exclusive_write(output_dir / "prompt_receipt.json", receipt)
    verify_delivered_prompt((output_dir / "prompt.txt").read_bytes(), receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-context", type=Path, required=True)
    parser.add_argument("--instance-id", required=True)
    parser.add_argument("--expected-context-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze_prompt(context_path=args.public_context, instance_id=args.instance_id,
                                  expected_context_sha256=args.expected_context_sha256,
                                  output_dir=args.output_dir), sort_keys=True))


if __name__ == "__main__":
    main()
