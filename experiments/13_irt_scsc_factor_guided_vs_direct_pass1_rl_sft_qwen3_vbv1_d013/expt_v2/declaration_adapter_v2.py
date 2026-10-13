#!/usr/bin/env python3
"""Measure unchanged-source component fractions while preserving the independent historical oracle."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from historical_oracle_v2 import oracle

PROBE = HERE / 'DeclarationProbe_v2.lean'
ALLOWED = {'propext', 'Classical.choice', 'Quot.sound'}
IMPLEMENTATIONS = {'Lean.Parser.Command.definition', 'Lean.Parser.Command.abbrev', 'Lean.Parser.Command.opaque'}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def components(source, *, lake_dir, evidence, timeout=900):
    evidence = Path(evidence)
    evidence.mkdir(parents=True, exist_ok=False)
    output = evidence / 'frontend.json'
    cmd = ['lake', 'env', 'lean', '--run', str(PROBE), str(source), str(output.resolve())]
    (evidence / 'command.json').write_text(json.dumps(cmd) + '\n')
    try:
        result = subprocess.run(cmd, cwd=lake_dir, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        for name in ('stdout', 'stderr'):
            (evidence / name).write_bytes(getattr(exc, name) or b'')
        raise
    (evidence / 'stdout').write_bytes(result.stdout)
    (evidence / 'stderr').write_bytes(result.stderr)
    (evidence / 'returncode').write_text(str(result.returncode) + '\n')
    if result.returncode != 0 or not output.is_file():
        raise RuntimeError('frontend process failed; full private evidence retained')
    raw = json.loads(output.read_text())
    if raw.get('terminal') is not True or raw.get('schema') != 'e13-declaration-probe-v2':
        raise RuntimeError('frontend protocol incomplete')
    commands = raw['commands']
    byte_count = Path(source).stat().st_size
    for index, row in enumerate(commands):
        if row['index'] != index or not 0 <= row['start'] < row['stop'] <= byte_count:
            raise RuntimeError('invalid command span')
    implementation = [c for c in commands if c['syntax'].get('is_example') or
                      c['syntax'].get('declaration_kind') in IMPLEMENTATIONS]
    examples = sum(bool(c['syntax'].get('is_example')) for c in commands)
    proofs = raw['theorems']
    proved = sum(t['resolved'] and commands[t['command_index']]['clean'] and
                 set(t['axioms']).issubset(ALLOWED) for t in proofs)
    clean = sum(c['clean'] for c in commands)
    # A failed import is one failed header command, not an absent denominator.
    count = len(commands) + (not raw['header_clean'])
    t_ok = bool(examples and implementation and all(c['clean'] for c in implementation) and raw['header_clean'])
    return {'e': int(bool(Path(source).read_text(encoding='utf-8').strip())),
            'd': {'numerator': clean, 'denominator': count},
            't': int(t_ok), 'p': {'numerator': proved, 'denominator': len(proofs)},
            'n_examples': examples, 'raw': raw}


def fraction(count):
    return count['numerator'] / count['denominator'] if count['denominator'] else 0.0


def inspect_source(source, *, lake_dir, scorer_root, evidence, expected_sha256,
                   family='ladder', known=True, truncated=False):
    source = Path(source).resolve()
    if sha256(source) != expected_sha256:
        raise ValueError('integrity defect: source hash mismatch')
    evidence = Path(evidence)
    evidence.mkdir(parents=True, exist_ok=False)
    old = oracle(source, lake_dir=lake_dir, scorer_root=scorer_root, evidence=evidence / 'oracle',
                 family=family, known=known, truncated=truncated)
    parts = components(source, lake_dir=lake_dir, evidence=evidence / 'components')
    raw_hits = old['vacuity']['n_vacuous']
    # Each stated obligation gets a separate screen. Aggregate historical hits never become
    # the distinct-theorem count and cannot overflow the theorem denominator.
    from historical_oracle_v2 import load, E08
    vacuity = load('e13v2_component_vacuity', E08 / 'score_teacher_files.py')
    vacuity.SCORER = scorer_root
    source_bytes = source.read_bytes()
    distinct = 0
    for proof in parts['raw']['theorems']:
        command = parts['raw']['commands'][proof['command_index']]
        snippet = source_bytes[command['start']:command['stop']].decode('utf-8')
        distinct += vacuity.vacuity(snippet)['n_vacuous'] > 0
    d, p = fraction(parts['d']), fraction(parts['p'])
    maximum = parts['e'] == d == parts['t'] == p == 1
    reason = 'consistent'
    if old['value'] == 1 and not maximum:
        reason = 'untyped_strict_success_component_deficit'
    elif old['value'] == 0 and maximum:
        if raw_hits or old['vacuity']['unparseable']:
            reason = 'vacuity'
        elif not old['kernel'].get('probe_ok', False):
            reason = 'kernel_probe_rejection'
        else:
            reason = 'untyped_maximum_components_strict_failure'
    reward = 0.0
    if parts['e'] and parts['n_examples'] and parts['p']['denominator'] and not raw_hits:
        reward = (max(.01, d) * max(.01, parts['t']) * max(.01, p)) ** (1 / 3)
    if old['value'] == 1:
        reward = 1.0
    result = {'source_sha256': expected_sha256, 'strict': old['value'], 'strict_status': old['status'],
              'family': family, 'truncated': truncated,
              **{k: v for k, v in parts.items() if k != 'raw'},
              'raw_vacuity_hits': raw_hits, 'distinct_vacuous_theorems': distinct,
              'factored_reward': reward, 'consistency': reason}
    if sha256(source) != expected_sha256:
        raise ValueError('integrity defect: source changed during measurement')
    (evidence / 'measurement.json').write_text(json.dumps(result, indent=2) + '\n')
    return result
