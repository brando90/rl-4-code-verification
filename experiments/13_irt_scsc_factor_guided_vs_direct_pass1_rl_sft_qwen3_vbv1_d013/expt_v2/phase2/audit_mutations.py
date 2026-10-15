"""Construct fixed padding, deletion and substitution audits from frozen Lean byte spans."""
from __future__ import annotations

import hashlib

THEOREM = 'Lean.Parser.Command.theorem'
PADDING_COUNT = 8


def identity_theorem(name):
    return (f'theorem {name} (n : _root_.Nat) : n + 0 = n := _root_.Nat.add_zero n\n').encode()


def construct(source: bytes, frontend: dict, *, expected_sha256: str):
    """No scoring or selection by outcome; original source bytes are never modified."""
    actual = hashlib.sha256(source).hexdigest()
    if actual != expected_sha256:
        raise ValueError('audit source changed')
    source.decode('utf-8')
    if frontend.get('schema') != 'e13-declaration-probe-v2' or frontend.get('terminal') is not True:
        raise ValueError('audit requires the frozen complete frontend receipt')
    commands = frontend['commands']
    last = 0
    for index, row in enumerate(commands):
        if row['index'] != index or not last <= row['start'] <= row['stop'] <= len(source):
            raise ValueError('audit command byte spans overlap or are invalid')
        source[row['start']:row['stop']].decode('utf-8')
        last = row['stop']
    indices = [i for i, row in enumerate(commands) if row['syntax'].get('declaration_kind') == THEOREM]
    recorded = [row['command_index'] for row in frontend['theorems']]
    if recorded != indices or any(not commands[i]['syntax'].get('short_name') for i in indices):
        raise ValueError('named theorem identities are incomplete')
    names = [f'e13_audit_padding_{actual[:12]}_{i}' for i in range(PADDING_COUNT)]
    if any(name.encode() in source for name in names):
        raise ValueError('fixed padding name collides with original source')

    def edit(changes):
        value = source
        for index, replacement in sorted(changes, reverse=True):
            row = commands[index]
            value = value[:row['start']] + b'\n' + replacement + value[row['stop']:]
        return value

    # Last ceil(n/2) by source order, even if a deleted theorem was easy or
    # referenced later. Dependency/compilation failures are measured outcomes.
    deleted = indices[len(indices)//2:]
    bodies = {
        'padding': source + b'\n' + b''.join(identity_theorem(name) for name in names),
        'deletion': edit([(i, b'') for i in deleted]),
        'substitution': edit([(i, identity_theorem(commands[i]['syntax']['short_name'])) for i in indices]),
    }
    changes = {'padding': PADDING_COUNT, 'deletion': len(deleted), 'substitution': len(indices)}
    return {kind: {'operator': kind, 'source': value, 'source_sha256': hashlib.sha256(value).hexdigest(),
                   'original_sha256': actual, 'status': 'changed' if value != source else 'unchanged_no_named_theorems',
                   'original_named_theorems': len(indices), 'changed_declarations': changes[kind],
                   'selection': 'fixed source order; no reward or coverage outcome used'}
            for kind, value in bodies.items()}
