"""Map gold test symbols by namespace-normalized names or a unique compatible explicit signature, rejecting ambiguity."""
import re
from extract_hidden_tests import IDENT, declarations


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


def map_symbols(gold_symbols,candidate_source):
    definitions,_=declarations(candidate_source);mapping={};diagnostics=[]
    for gold in gold_symbols:
        same=[d for d in definitions if d['name'].split('.')[-1]==gold['name'].split('.')[-1]]
        exact=[d for d in same if d['full_name']==gold['full_name']]
        matches=exact or same;rule='same_name'
        if not matches:
            key=signature(gold['header']);rule='unique_compatible_signature'
            matches=[d for d in definitions if key is not None and signature(d['header'])==key]
        if len(matches)==1:
            mapping[gold['full_name']]=matches[0]['full_name']
        diagnostics.append({'gold_symbol':gold['full_name'],'rule':rule,
                            'signature':signature(gold['header']),
                            'candidates':[d['full_name'] for d in matches],
                            'status':'mapped' if len(matches)==1 else ('ambiguous' if matches else 'not_applicable')})
    return mapping,diagnostics


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
