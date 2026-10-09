"""Expand closed literal aliases used solely as implementation-call inputs, preserving every test and its expected expression."""
import re
from adapter_e12 import atom_at, signature
from extract_hidden_tests import IDENT, strip_comments

STRING=re.compile(r'"(?:\\.|[^"\\])*"')
LITERAL_TOKEN=re.compile(r'"(?:\\.|[^"\\])*"|-?(?:0[xX][0-9a-fA-F]+|[0-9]+)|\b(?:true|false|some|none|Nat|Int|String|UInt8|UInt16|UInt32|UInt64)\b|[\s\[\]()⟨⟩,:#]+')


def closed_literal(body):
    body=body.strip()
    if not body:return None
    pos=0
    for token in LITERAL_TOKEN.finditer(body):
        if token.start()!=pos:return None
        pos=token.end()
    return body if pos==len(body) else None


def input_ranges(test, definitions):
    ranges=[];statement=test['statement']
    masked=STRING.sub(lambda m:' '*len(m.group()),statement)
    for match in IDENT.finditer(masked):
        symbol=test['symbols'].get(match.group());definition=definitions.get(symbol)
        if definition is None:continue
        sig=signature(definition['header'])
        if sig is None or not sig[0]:continue
        pos=match.end()
        for _ in sig[0]:
            start=pos
            while start<len(statement) and statement[start].isspace():start+=1
            atom=atom_at(statement,start)
            if atom is None:break
            _,pos=atom;ranges.append((start,pos))
    return ranges


def expand_fixture_inputs(source, definitions, tests):
    by_name={d['full_name']:d for d in definitions};clean=strip_comments(source)
    potential={}
    for d in definitions:
        sig=signature(d['header'])
        if sig is None or sig[0]:continue
        literal=closed_literal(clean[d['body_start']:d['end']])
        if literal is not None:potential[d['full_name']]=literal
    used_inputs=set();non_inputs=set()
    for test in tests:
        ranges=input_ranges(test,by_name)
        masked=STRING.sub(lambda m:' '*len(m.group()),test['statement'])
        for match in IDENT.finditer(masked):
            symbol=test['symbols'].get(match.group())
            if symbol not in potential:continue
            if any(a<=match.start() and match.end()<=b for a,b in ranges):used_inputs.add(symbol)
            else:non_inputs.add(symbol)
    fixtures={s:potential[s] for s in sorted(used_inputs-non_inputs)}
    output=[]
    for test in tests:
        aliases={token:symbol for token,symbol in test['symbols'].items() if symbol in fixtures}
        if not aliases:output.append(test);continue
        pieces=re.split(r'("(?:\\.|[^"\\])*")',test['statement'])
        for i in range(0,len(pieces),2):
            pieces[i]=IDENT.sub(lambda m:'('+fixtures[aliases[m.group()]]+')'+test.get('symbol_suffixes',{}).get(m.group(),'') if m.group() in aliases else m.group(),pieces[i])
        output.append({**test,'statement':''.join(pieces),'statement_before_fixture_expansion':test['statement'],
                       'literal_input_aliases':{token:fixtures[symbol] for token,symbol in aliases.items()},
                       'symbols':{k:v for k,v in test['symbols'].items() if k not in aliases},
                       'symbol_suffixes':{k:v for k,v in test.get('symbol_suffixes',{}).items() if k not in aliases}})
    assert len(output)==len(tests)
    return output,fixtures
