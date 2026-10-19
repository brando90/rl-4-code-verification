"""Recover source-bound compiler diagnostics for three completed runs without changing their official scores."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

RUN = Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
OUT = RUN / 'failure_diagnostics_v24'
SEARCH = r'exact\?|apply\?|simp(?:_all|_rw|_arith|\?)?|simpa\??|omega\??|aesop\??|linarith!?|nlinarith!?|ring(?:_nf)?|norm_num!?|grind|tauto|solve_by_elim'
ERROR = re.compile(r'^.*?:(\d+):(\d+): error:\s*(.*)$', re.M)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)

def classify(text, rc):
    matches = list(ERROR.finditer(text))
    if not matches:
        return ('diagnostic_timeout' if rc == 124 else 'diagnostic_recompile_passed' if rc == 0 else 'other_no_formatted_error'), '', []
    first = text[matches[0].start():matches[1].start() if len(matches) > 1 else len(text)]
    t = first.lower()
    if re.search(r'unknown (?:identifier|constant|tactic|namespace)|environment does not contain|invalid field|invalid dotted identifier', t):
        category = 'unknown_name_tactic_or_member'
    elif 'type mismatch' in t or 'has type' in t and 'expected to have type' in t:
        category = 'type_mismatch'
    elif re.search(r'unexpected|expected token|unterminated|invalid syntax|invalid constructor|invalid notation', t):
        category = 'syntax_or_notation'
    elif re.search(r'(?:native_decide|decide).*?(?:evaluated|proved|determined).*?proposition', t, re.S) and re.search(r'false|not true', t):
        category = 'decision_procedure_false_proposition'
    elif re.search(r'synthesize|typeclass|failed to infer|cannot infer|don.t know how to infer', t):
        category = 'instance_or_type_inference'
    elif re.search(r'\b(?:native_decide|decide)\b', t) and re.search(r'failed|cannot|could not|error|not reduc|not support', t):
        category = 'failed_decision_procedure'
    elif re.search(r'\b(?:' + SEARCH + r')\b', t) and re.search(r'failed|could not|made no progress|unsolved', t):
        category = 'failed_proof_search'
    elif 'unsolved goals' in t:
        category = 'unsolved_goals'
    elif re.search(r'heartbeat|recursion|termination|maximum number', t):
        category = 'recursion_termination_or_resource'
    elif 'tactic' in t or 'no goals to be solved' in t:
        category = 'other_failed_proof_step'
    else:
        category = 'other_first_diagnostic'
    flags = []
    for m in matches:
        block = text[m.start():text.find('\n', m.end()) if text.find('\n', m.end()) >= 0 else len(text)]
        if re.search(r'\b(?:native_decide|decide)\b', block):
            flags.append('decision_procedure_reported_in_error')
        if re.search(r"tactic\s+['`‘’]?(?:" + SEARCH + r")(?!\w).*?(?:failed|could not|made no progress)|(?<!\w)(?:" + SEARCH + r")(?!\w)\s+(?:could not prove|made no progress)", block, re.I):
            flags.append('proof_search_reported_failed')
    return category, first[:6000], sorted(set(flags))
