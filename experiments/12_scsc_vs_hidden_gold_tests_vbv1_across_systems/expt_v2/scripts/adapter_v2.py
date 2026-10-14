"""Experiment 12 version 2 adapter: a Lean-faithful identifier lexer, entry-point selection with an explicit priority order that never prefers helpers, and per-test applicability bookkeeping; version-1 helpers are imported read-only."""
import re
import sys
from pathlib import Path

V1_SCRIPTS = Path(__file__).resolve().parents[2] / 'expt_v1' / 'scripts'
if str(V1_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(V1_SCRIPTS))
from extract_hidden_tests import strip_comments, header_end, COMMAND  # noqa: E402  (frozen version-1 helpers, read-only)
from adapter_e12 import atom_at, TOP  # noqa: E402  (frozen version-1 helpers, read-only)

# ---------------------------------------------------------------------------
# Lexer. Lean 4 identifiers: a part starts with a letter, `_` or a letter-like
# symbol (Greek except lambda, Pi and Sigma; Coptic; letter-like block; math
# script letters) and continues with alphanumerics, `_`, `'`, `!`, `?` and
# subscripts; a french-quoted part «...» may hold anything; parts join with `.`;
# a trailing numeric part is a positional projection (`p.1`).
# ---------------------------------------------------------------------------
_LETTER_LIKE = 'α-κμ-ωΑ-Π΢-Ωϊ-ϻ℀-⅏\U0001d49c-\U0001d59f'
_SUBSCRIPT = '₀-₉ₐ-ₜᵢ-ᵪ'
_START = f'[A-Za-z{_LETTER_LIKE}]'
_REST = f"[A-Za-z0-9_'!?{_LETTER_LIKE}{_SUBSCRIPT}]"
# A bare `_` is a hole, not an identifier; `_x` and `__` are identifiers.
_PART = f'(?:«[^»]*»|{_START}{_REST}*|_{_REST}+)'
IDENT = re.compile(f'{_PART}(?:\\.(?:{_PART}|[0-9]+))*')
NUMERIC = re.compile(r'\b(?:Nat|Int|UInt8|UInt16|UInt32|UInt64)\b')
STRING = re.compile(r'"(?:\\.|[^"\\])*"')
# Helper names: pre/post prefixes followed by a word boundary, or condition/check/prop/spec/harness suffixes.
HELPER_PREFIX = re.compile(r'^(?:[Pp]re|[Pp]ost)(?:$|[A-Z_0-9]|[Cc]ond|[Cc]heck|[Bb]$)')
HELPER_SUFFIXES = ('condition', 'cond', 'check', 'prop', 'spec', 'harness')


def unquote(part):
    return part[1:-1] if part.startswith('«') and part.endswith('»') else part


def parts_of(name):
    """Split a dotted identifier into parts, unquoting french quotes."""
    return [unquote(p) for p in re.findall(_PART + '|[0-9]+', name)]


def normalized(name):
    """Namespace-stripped, case-insensitive, underscore-free basename (version-1 rule, corrected lexer)."""
    return parts_of(name)[-1].replace('_', '').lower()


def basename(name):
    return parts_of(name)[-1]


def is_helper(name):
    b = basename(name)
    return bool(HELPER_PREFIX.match(b)) or normalized(b).endswith(HELPER_SUFFIXES)


def name_affine(gold_name, candidate_name):
    """The candidate's normalized basename is contained in the gold's (e.g. `canFree` in `MyHazardPointerCanFree`)."""
    g, c = normalized(gold_name), normalized(candidate_name)
    return len(c) >= 3 and c in g


# ---------------------------------------------------------------------------
# Declarations and signatures with the corrected lexer.
# ---------------------------------------------------------------------------
def declarations(source):
    """Version-1 declaration walk with the corrected identifier lexer; returns (defs, examples, counts)."""
    clean = strip_comments(source)
    events = list(COMMAND.finditer(clean))
    stack, defs, examples = [], [], []
    for idx, m in enumerate(events):
        kind = m.group(1)
        tail = clean[m.end():].lstrip()
        name_match = IDENT.match(tail)
        ns = '.'.join(name for mode, name in stack if mode == 'namespace')
        if kind in ('namespace', 'section'):
            stack.append((kind, name_match.group() if name_match else ''))
            continue
        if kind == 'end':
            if stack:
                stack.pop()
            continue
        end = header_end(clean, m.end())
        next_start = events[idx + 1].start() if idx + 1 < len(events) else len(clean)
        equation_body = None
        if (end is None or end >= next_start) and kind in ('def', 'abbrev'):
            equation_body = re.search(r'\n[ \t]*\|', clean[m.end():next_start])
            if equation_body:
                end = m.end() + equation_body.start()
        if end is None or end >= next_start:
            continue
        header = clean[m.end():end].strip()
        if kind in ('def', 'abbrev') and name_match:
            name = name_match.group()
            full = ('.'.join([ns, name]) if ns else name).removeprefix('_root_.')
            defs.append({'name': name, 'full_name': full, 'namespace': ns, 'header': header[len(name):].strip(),
                         'start': m.start(), 'body_start': end if equation_body else end + 2, 'end': next_start})
        elif kind == 'example' and header.startswith(':'):
            examples.append({'statement': header[1:].strip(), 'namespace': ns,
                             'line': clean.count('\n', 0, m.start()) + 1})
    counts = {'n_examples': len(examples),
              'n_eval_commands': len(re.findall(r'(?m)^[ \t]*#(?:eval|guard|guard_msgs|print)\b', clean))}
    return defs, examples, counts


def signature(header):
    """Explicit binder types and result type (NUM-generalized); implicit and instance binders are skipped and flagged."""
    header = header.strip()
    types, renames, pos, has_implicit = [], {}, 0, False
    while pos < len(header) and header[pos] in '({[⦃':
        opener = header[pos]
        closer = {'(': ')', '{': '}', '[': ']', '⦃': '⦄'}[opener]
        depth, j = 1, pos + 1
        while j < len(header) and depth:
            if header[j] == opener:
                depth += 1
            if header[j] == closer:
                depth -= 1
            j += 1
        if depth:
            return None
        group = header[pos + 1:j - 1]
        if opener != '(':
            has_implicit = True
            if ':' in group:
                for n in group.split(':', 1)[0].split():
                    renames[n] = 'i' + str(len(renames))
        else:
            if ':' not in group:
                return None
            names, typ = group.split(':', 1)
            names = names.split()
            if not names or any(not re.fullmatch(r"[A-Za-z_][\w'!?₀-₉]*", n) for n in names):
                return None
            for name in names:
                t = NUMERIC.sub('NUM', typ)
                t = IDENT.sub(lambda mm: renames.get(mm.group(), mm.group()), t)
                types.append(' '.join(t.split()))
                renames[name] = 'v' + str(len(renames))
        pos = j
        while pos < len(header) and header[pos].isspace():
            pos += 1
    if pos >= len(header) or header[pos] != ':':
        return None
    result = header[pos + 1:].strip()
    if not result or '\n' in result or re.search(r'\b(?:where|termination_by)\b', result):
        return None
    result = NUMERIC.sub('NUM', result)
    result = IDENT.sub(lambda mm: renames.get(mm.group(), mm.group()), result)
    arrows = [s.strip() for s in result.split('→')]
    if len(arrows) > 1:
        types.extend(arrows[:-1])
        result = arrows[-1]
    return {'args': tuple(types), 'result': ' '.join(result.split()), 'arity': len(types), 'has_implicit': has_implicit}


def reference_counts(source, definitions):
    """Count unambiguous references to each definition from the candidate's own examples and theorems (corrected lexer)."""
    clean = strip_comments(source)
    events = list(TOP.finditer(clean))
    counts = {d['full_name']: [0, 0] for d in definitions}
    by_full = {d['full_name']: d for d in definitions}
    by_base = {}
    for d in definitions:
        by_base.setdefault(d['name'], []).append(d)
    for i, event in enumerate(events):
        kind = event.group(1)
        if kind not in ('example', 'theorem', 'lemma'):
            continue
        stop = events[i + 1].start() if i + 1 < len(events) else len(clean)
        block = STRING.sub('""', clean[event.end():stop])
        for token in IDENT.findall(block):
            if token in by_full:
                matches = [by_full[token]]
            else:
                matches = by_base.get(token, [])
            if len(matches) == 1:
                counts[matches[0]['full_name']][0 if kind == 'example' else 1] += 1
    return counts


# ---------------------------------------------------------------------------
# Entry-point selection (explicit priority order; see expt_v2/DESIGN.md).
# ---------------------------------------------------------------------------
def _compatible(gold_sig, cand_sig):
    return gold_sig is not None and cand_sig is not None and gold_sig['args'] == cand_sig['args'] and gold_sig['result'] == cand_sig['result']


def select_entry_point(gold, definitions, counts):
    """Static selection: steps 1, 2a, 2b resolve without Lean; several survivors are `needs_probe` for steps 3/4."""
    gold_sig = signature(gold['header'])
    sigs = {d['full_name']: signature(d['header']) for d in definitions}
    diag = {'gold_symbol': gold['full_name'], 'gold_signature': gold_sig, 'step': None, 'status': None,
            'chosen': None, 'candidates': [], 'helpers_excluded': [], 'reason': None,
            'arity_match': None, 'result_type_compatible': None, 'argument_types_compatible': None}

    def finish(chosen, step, status='mapped', reason=None):
        diag.update(step=step, status=status, reason=reason, chosen=chosen['full_name'] if chosen else None)
        if chosen is not None:
            cs = sigs[chosen['full_name']]
            diag['arity_match'] = (None if gold_sig is None or cs is None else gold_sig['arity'] == cs['arity'])
            diag['result_type_compatible'] = (None if gold_sig is None or cs is None else gold_sig['result'] == cs['result'])
            diag['argument_types_compatible'] = (None if gold_sig is None or cs is None else gold_sig['args'] == cs['args'])
        return diag

    # Step 1: same normalized name; prefer exact full name, then equal arity, then compatible signature, then file order.
    same = [d for d in definitions if normalized(d['name']) == normalized(gold['name'])]
    if same:
        def rank(d):
            cs = sigs[d['full_name']]
            arity_ok = gold_sig is not None and cs is not None and cs['arity'] == gold_sig['arity']
            return (d['full_name'] != gold['full_name'], not arity_ok, not _compatible(gold_sig, cs), d['start'])
        same.sort(key=rank)
        best = same[0]
        cs = sigs[best['full_name']]
        if gold_sig is not None and cs is not None and cs['arity'] != gold_sig['arity']:
            # A same-name definition with a different explicit arity is not the entry point; fall through to step 2.
            diag['reason'] = 'same_name_arity_mismatch'
        else:
            diag['candidates'] = [d['full_name'] for d in same]
            return finish(best, 1)
    # Step 2: signature-compatible set, helpers removed unless nothing else remains.
    if gold_sig is None:
        diag['candidates'] = []
        return finish(None, None, 'not_applicable', 'gold_signature_unknown')
    S = [d for d in definitions if _compatible(gold_sig, sigs[d['full_name']])]
    non_helpers = [d for d in S if not is_helper(d['name'])]
    if non_helpers and len(non_helpers) < len(S):
        diag['helpers_excluded'] = [d['full_name'] for d in S if is_helper(d['name'])]
        S = non_helpers
    diag['candidates'] = [d['full_name'] for d in S]
    if not S:
        return finish(None, None, 'not_applicable', 'no_match')
    if len(S) == 1:
        return finish(S[0], '2a')
    affine = [d for d in S if name_affine(gold['name'], d['name'])]
    if len(affine) == 1:
        return finish(affine[0], '2b')
    if affine:
        S = affine
        diag['candidates'] = [d['full_name'] for d in S]
    diag['status'] = 'needs_probe'
    diag['reference_counts'] = {d['full_name']: counts[d['full_name']] for d in S}
    return diag


def _argument_tuples(gold, tests):
    sig = signature(gold['header'])
    if sig is None:
        return None
    tuples = []
    for test in tests:
        for token, symbol in test['symbols'].items():
            if symbol != gold['full_name']:
                continue
            statement = test['statement']
            strings = [(m.start(), m.end()) for m in STRING.finditer(statement)]
            for match in IDENT.finditer(statement):
                if match.group() != token or any(a <= match.start() < b for a, b in strings):
                    continue
                pos, args = match.end(), []
                for _ in range(sig['arity']):
                    atom = atom_at(statement, pos)
                    if atom is None:
                        return None
                    arg, pos = atom
                    args.append(arg)
                if args not in tuples:
                    tuples.append(args)
    return tuples or None


def map_symbols(gold_symbols, candidate_source, tests=(), agreement=None):
    """Map every gold symbol; `agreement(gold, members, tuples)` runs the Lean probe for steps 3/4 when supplied."""
    definitions, examples, decl_counts = declarations(candidate_source)
    counts = reference_counts(candidate_source, definitions)
    by_full = {d['full_name']: d for d in definitions}
    mapping, diagnostics = {}, []
    for gold in gold_symbols:
        diag = select_entry_point(gold, definitions, counts)
        if diag['status'] == 'needs_probe':
            members = [by_full[n] for n in diag['candidates']]
            if agreement is None:
                diag['reason'] = 'needs_probe_static_census'
            else:
                tuples = _argument_tuples(gold, tests)
                comparisons = agreement(gold, members, tuples)
                agreed = comparisons.get('agrees')
                diag['agreement'] = agreed
                diag['comparison_receipt'] = comparisons
                if agreed is True:
                    chosen = max(members, key=lambda d: (counts[d['full_name']][0], -d['start']))
                    diag.update(step=3, status='mapped', chosen=chosen['full_name'])
                else:
                    best = max(tuple(counts[d['full_name']]) for d in members)
                    winners = [d for d in members if tuple(counts[d['full_name']]) == best]
                    if len(winners) == 1:
                        diag.update(step=4, status='mapped', chosen=winners[0]['full_name'])
                    else:
                        diag.update(status='not_applicable', reason='ambiguous_disagreeing')
        if diag['status'] == 'mapped':
            mapping[gold['full_name']] = diag['chosen']
        diagnostics.append(diag)
    summary = {'n_definitions': len(definitions), **decl_counts}
    return mapping, diagnostics, summary


def repoint(test, mapping):
    """Re-point a hidden test at the candidate's symbols; None when a symbol is unmapped (the test is `unmapped`)."""
    if any(symbol not in mapping for symbol in test['symbols'].values()):
        return None
    pieces = re.split(r'("(?:\\.|[^"\\])*")', test['statement'])
    for i in range(0, len(pieces), 2):
        pieces[i] = IDENT.sub(lambda m: ('_root_.' + mapping[test['symbols'][m.group()]] + test.get('symbol_suffixes', {}).get(m.group(), ''))
                              if m.group() in test['symbols'] else m.group(), pieces[i])
    return ''.join(pieces)


def per_test_plan(tests, mapping):
    """Per-test mapping status before any Lean run: `mapped` tests enter the bridge, `unmapped` tests are reported, never counted as failures."""
    plan = []
    for i, test in enumerate(tests):
        statement = repoint(test, mapping)
        plan.append({'index': i, 'status': 'mapped' if statement is not None else 'unmapped', 'statement': statement})
    return plan


def bridge(module, tests, mapping):
    """Same bridge shape as version 1 (one `#eval` per test, E12_TEST_i markers) so the version-1 runtime parses it unchanged."""
    lines = ['import Mathlib', f'import {module}', 'deriving instance DecidableEq for Except']
    for row in per_test_plan(tests, mapping):
        if row['status'] == 'mapped':
            lines.append(f'#eval IO.println ("E12_TEST_{row["index"]}=" ++ toString (decide ({row["statement"]})))')
    return '\n'.join(lines) + '\n'


def cell_outcome(n_tests, outputs, plan):
    """Version-2 per-cell bookkeeping from per-test outputs {index: bool}; unevaluable tests stay listed, never zero."""
    n_mapped = sum(r['status'] == 'mapped' for r in plan)
    n_evaluable = len(outputs)
    n_pass = sum(bool(v) for v in outputs.values())
    return {'n_tests': n_tests, 'n_mapped': n_mapped, 'n_evaluable': n_evaluable, 'n_pass': n_pass,
            'n_unmapped': n_tests - n_mapped, 'n_type_unknown': n_mapped - n_evaluable,
            'applicable': n_evaluable > 0, 'fully_applicable': n_evaluable == n_tests and n_tests > 0,
            'hidden_all_pass': (n_pass == n_tests) if n_evaluable == n_tests and n_tests > 0 else None,
            'hidden_all_evaluable_pass': (n_pass == n_evaluable) if n_evaluable else None,
            'hidden_pass_rate': (n_pass / n_evaluable) if n_evaluable else None,
            'per_test': [{'index': r['index'], 'status': ('pass' if outputs.get(r['index']) is True else 'fail' if outputs.get(r['index']) is False
                                                           else 'type_unknown' if r['status'] == 'mapped' else 'unmapped')} for r in plan]}
