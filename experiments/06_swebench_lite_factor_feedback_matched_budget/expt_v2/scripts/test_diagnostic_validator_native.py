"""Synthetic, non-executing regression tests for the recovered diagnostic validator."""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import sys


HERE = Path(__file__).resolve().parent
def load_functions():
    source = (HERE / "diagnostic_validator_native.py").read_text()
    source = "allowed=" + source.split("allowed=", 1)[1].split("items=[]", 1)[0]
    namespace = {"hashlib": hashlib, "json": json, "os": os, "re": re, "shlex": shlex,
                 "sys": sys, "Path": Path, "__name__": "validator_test"}
    exec(compile(source, "diagnostic_validator_native.py", "exec"), namespace)
    return namespace["parse"], namespace["validate"]


def test_plain_json_and_fence_are_accepted_transport_forms():
    parse, _ = load_functions()
    assert parse('{"notes":"x"}') == {"notes": "x"}
    assert parse('```json\n{"notes":"x"}\n```') == {"notes": "x"}


def test_validator_rejects_semicolon_even_inside_quoted_python_code():
    _, validate = load_functions()
    assert validate("python -c 'print(1); print(2)'") == (False, "unsafe_or_empty_command")


def test_validator_accepts_a_simple_bounded_pytest_command():
    _, validate = load_functions()
    assert validate("python -m pytest tests/test_example.py -q") == (True, None)
