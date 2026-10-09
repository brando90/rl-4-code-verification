"""Map gold test symbols by namespace-normalized names or a unique compatible explicit signature, rejecting ambiguity."""
import re
from extract_hidden_tests import IDENT, declarations, strip_comments


def signature(header):
    """Read explicit first-order binder types; unsupported dependent/inferred forms stay unknown."""
    header=header.strip();types=[];renames={};pos=0
    while pos<len(header) and header[pos] in '({[':
        opener=header[pos];closer={'(':')','{':'}','[':']'}[opener];depth=1;j=pos+1
        while j<len(header) and depth:
            if header[j]==opener:depth+=1
            if header[j]==closer:depth-=1
            j+=1
        if depth:return None
        group=header[pos+1:j-1]
        if ':' not in group or opener!='(':return None
        names,typ=group.split(':',1);names=names.split()
        if not names or any(not re.fullmatch(r"[A-Za-z_][\w']*",n) for n in names):return None
        for name in names:
            typ=re.sub(r'\b(?:Nat|Int|UInt8|UInt16|UInt32|UInt64)\b','NUM',typ)
            typ=IDENT.sub(lambda m:renames.get(m.group(),m.group()),typ)
            types.append(' '.join(typ.split()));renames[name]='v'+str(len(renames))
        pos=j
        while pos<len(header) and header[pos].isspace():pos+=1
    if pos>=len(header) or header[pos]!=':':return None
    result=header[pos+1:].strip()
    if not result or '\n' in result or re.search(r'\b(?:where|termination_by)\b',result):return None
    result=re.sub(r'\b(?:Nat|Int|UInt8|UInt16|UInt32|UInt64)\b','NUM',result)
    result=IDENT.sub(lambda m:renames.get(m.group(),m.group()),result)
    # Equation-style definitions spell their explicit telescope with arrows.
    arrows=[s.strip() for s in result.split('→')]
    if len(arrows)>1:
        types.extend(arrows[:-1]);result=arrows[-1]
    return (tuple(types),' '.join(result.split()))


def normalized(name):
    return name.split('.')[-1].replace('_', '').lower()


# Full declaration boundaries are needed for reference counts and private mutant copies.
TOP = re.compile(r"(?m)^[ \t]*(?:@\[[^\n]*?\]\s*)?(?:(?:private|protected|noncomputable|unsafe|partial)\s+)*(namespace|section|end|def|abbrev|example|theorem|lemma|structure|inductive|instance|open|import|variable|set_option|attribute|deriving)\b")


def reference_counts(source, candidates):
    clean = strip_comments(source)
    events = list(TOP.finditer(clean))
    counts = {d['full_name']: [0, 0] for d in candidates}
    for i, event in enumerate(events):
        kind = event.group(1)
        if kind not in ('example', 'theorem', 'lemma'):
            continue
        stop = events[i+1].start() if i+1 < len(events) else len(clean)
        block = re.sub(r'"(?:\\.|[^"\\])*"', '""', clean[event.end():stop])
        tokens = IDENT.findall(block)
        for token in tokens:
            matches = [d for d in candidates if token == d['full_name'] or token == d['name']]
            if len(matches) == 1:
                counts[matches[0]['full_name']][0 if kind == 'example' else 1] += 1
    return counts


def atom_at(source, pos):
    while pos < len(source) and source[pos].isspace(): pos += 1
    start = pos
    if pos >= len(source): return None
    if source[pos] in '([{':
        stack = []; quoted = False
        while pos < len(source):
            c = source[pos]
            if quoted:
                if c == '\\': pos += 2; continue
                if c == '"': quoted = False
            elif c == '"': quoted = True
            elif c in '([{': stack.append(c)
            elif c in ')]}':
                if not stack or '([{'.index(stack.pop()) != ')]}'.index(c): return None
                if not stack: return source[start:pos+1], pos+1
            pos += 1
        return None
    match = re.match(r'"(?:\\.|[^"\\])*"|-?(?:0x[0-9A-Fa-f]+|[0-9]+)|[A-Za-z_][\w\'.]*', source[pos:])
    return (match.group(), pos+len(match.group())) if match else None


def argument_tuples(gold, tests):
    sig = signature(gold['header'])
    if sig is None: return None
    arity = len(sig[0]); tuples = []
    for test in tests:
        for token, symbol in test['symbols'].items():
            if symbol != gold['full_name']: continue
            # Quoted strings cannot supply a symbol occurrence.
            statement = test['statement']
            strings = [(m.start(), m.end()) for m in re.finditer(r'"(?:\\.|[^"\\])*"', statement)]
            for match in IDENT.finditer(statement):
                if match.group() != token or any(a <= match.start() < b for a,b in strings): continue
                pos = match.end(); args = []
                for _ in range(arity):
                    atom = atom_at(statement, pos)
                    if atom is None: return None
                    arg, pos = atom; args.append(arg)
                if args not in tuples: tuples.append(args)
    return tuples or None


def map_symbols(gold_symbols, candidate_source, tests=(), agreement=None):
    definitions, _ = declarations(candidate_source); mapping = {}; diagnostics = []
    counts = reference_counts(candidate_source, definitions)
    for gold in gold_symbols:
        same = [d for d in definitions if normalized(d['name']) == normalized(gold['name'])]
        exact = [d for d in same if d['full_name'] == gold['full_name']]
        matches = exact or same; step = 1; agreed = None; comparisons = None
        if len(matches) != 1:
            key = signature(gold['header']); step = 2
            matches = [d for d in definitions if key is not None and signature(d['header']) == key]
        chosen = matches[0] if len(matches) == 1 else None
        if len(matches) > 1 and agreement is not None:
            tuples = argument_tuples(gold, tests)
            comparisons = agreement(gold, matches, tuples)
            agreed = comparisons.get('agrees')
            if agreed is True:
                step = 3
                chosen = max(matches, key=lambda d: (counts[d['full_name']][0], -d['start']))
            else:
                step = 4
                best = max(tuple(counts[d['full_name']]) for d in matches)
                winners = [d for d in matches if tuple(counts[d['full_name']]) == best]
                if len(winners) == 1: chosen = winners[0]
        if chosen: mapping[gold['full_name']] = chosen['full_name']
        diagnostics.append({'gold_symbol': gold['full_name'], 'step': step if chosen else None,
                            'signature': signature(gold['header']), 'set_size': len(matches),
                            'candidates': [d['full_name'] for d in matches],
                            'agreement': agreed, 'comparison_receipt': comparisons,
                            'reference_counts': {d['full_name']: counts[d['full_name']] for d in matches},
                            'status': 'mapped' if chosen else ('ambiguous' if len(matches)>1 else 'not_applicable'),
                            'reason': None if chosen else ('ambiguous_disagreeing' if len(matches)>1 else 'no_match')})
    return mapping, diagnostics


def repoint(test,mapping):
    if any(symbol not in mapping for symbol in test['symbols'].values()):return None
    # Token-level replacement avoids prefix collisions and never touches quoted string literals.
    pieces=re.split(r'("(?:\\.|[^"\\])*")',test['statement'])
    for i in range(0,len(pieces),2):
        pieces[i]=IDENT.sub(lambda m:('_root_.'+mapping[test['symbols'][m.group()]]+test.get('symbol_suffixes',{}).get(m.group(),'')) if m.group() in test['symbols'] else m.group(),pieces[i])
    return ''.join(pieces)


def bridge(module,tests,mapping):
    # Lean 4.22 has no generic Except decidable equality. This structural comparator
    # evaluates equality of the whole value; it neither unwraps results nor adds assumptions.
    lines=['import Mathlib',f'import {module}', 'deriving instance DecidableEq for Except']
    for i,test in enumerate(tests):
        statement=repoint(test,mapping)
        if statement is not None:
            lines.append(f'#eval IO.println ("E12_TEST_{i}=" ++ toString (decide ({statement})))')
    return '\n'.join(lines)+'\n'


def renamed_control(source,symbols):
    """Rename every tested implementation basename consistently, retaining types and bodies."""
    substitutions={s['name'].split('.')[-1]:f'e12renamed{i:04d}' for i,s in enumerate(symbols)}
    # The sources are private copies. Replacing names consistently in declarations, proofs,
    # examples and comments preserves meaning; no original candidate/reference file is edited.
    def replace(m):
        name=m.group();parts=name.split('.')
        parts=[substitutions.get(part,part) for part in parts]
        return '.'.join(parts)
    return IDENT.sub(replace,source),substitutions
