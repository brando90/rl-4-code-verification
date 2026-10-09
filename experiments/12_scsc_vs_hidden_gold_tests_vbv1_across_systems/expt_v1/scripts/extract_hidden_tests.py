"""Extract ground example statements and their referenced definitions without copying gold implementations into bridges."""
import hashlib
import json
import re
from pathlib import Path

from rl4cv.forecast import verify_forecast

PHASE = Path(__file__).resolve().parents[1]
IDENT = re.compile(r"[A-Za-z_\u0080-\uffff][\w'.]*")
COMMAND = re.compile(r"(?m)^[ \t]*(?:@\[[^\n]*?\]\s*)?(?:(?:private|protected|noncomputable|unsafe|partial)\s+)*(namespace|section|end|def|abbrev|example)\b")


def strip_comments(source):
    """Mask nested Lean comments while preserving strings, line numbers and character offsets."""
    out=list(source); i=0; depth=0; quoted=False
    while i<len(source):
        if depth:
            if source.startswith('/-',i): out[i:i+2]='  ';depth+=1;i+=2
            elif source.startswith('-/',i):out[i:i+2]='  ';depth-=1;i+=2
            else:
                if source[i]!='\n':out[i]=' '
                i+=1
        elif quoted:
            if source[i]=='\\':i+=2
            elif source[i]=='"':quoted=False;i+=1
            else:i+=1
        elif source[i]=='"':quoted=True;i+=1
        elif source.startswith('/-',i):out[i:i+2]='  ';depth=1;i+=2
        elif source.startswith('--',i):
            j=source.find('\n',i)
            if j<0:j=len(source)
            out[i:j]=' '*(j-i);i=j
        else:i+=1
    return ''.join(out)


def header_end(source,start):
    """Locate a declaration body separator outside brackets and strings."""
    stack=[];quoted=False;i=start
    while i<len(source):
        c=source[i]
        if quoted:
            if c=='\\':i+=2;continue
            if c=='"':quoted=False
        elif c=='"':quoted=True
        elif not stack and source.startswith(':=',i):return i
        elif c in '([{':stack.append(c)
        elif c in ')]}':
            if stack:stack.pop()
        i+=1
    return None


def declarations(source):
    clean=strip_comments(source);events=list(COMMAND.finditer(clean));stack=[];defs=[];examples=[]
    for idx,m in enumerate(events):
        kind=m.group(1);tail=clean[m.end():];name_match=IDENT.match(tail.lstrip())
        ns='.'.join(name for mode,name in stack if mode=='namespace')
        if kind in ('namespace','section'):
            stack.append((kind,name_match.group() if name_match else ''));continue
        if kind=='end':
            if stack:stack.pop()
            continue
        end=header_end(clean,m.end())
        next_start=events[idx+1].start() if idx+1<len(events) else len(clean)
        equation_body=None
        if (end is None or end>=next_start) and kind in ('def','abbrev'):
            equation_body=re.search(r'\n[ \t]*\|',clean[m.end():next_start])
            if equation_body:end=m.end()+equation_body.start()
        if end is None or end>=next_start:continue
        header=clean[m.end():end].strip()
        if kind in ('def','abbrev') and name_match:
            name=name_match.group();full=('.'.join([ns,name]) if ns else name).removeprefix('_root_.')
            defs.append({'name':name,'full_name':full,'namespace':ns,'header':header[len(name):].strip(),
                         'start':m.start(),'body_start':end if equation_body else end+2,'end':next_start})
        elif kind=='example' and header.startswith(':'):
            examples.append({'statement':header[1:].strip(),'namespace':ns,'line':clean.count('\n',0,m.start())+1})
    return defs,examples


def extract(source):
    defs,examples=declarations(source);by_name={r['full_name']:r for r in defs};tests=[];excluded=[]
    clean=strip_comments(source)
    # Section variables make an otherwise binder-free example potentially open.
    variables=set()
    for line in clean.splitlines():
        if re.match(r'\s*variables?\s',line):
            for names in re.findall(r'[({]([^:]+):',line):variables.update(IDENT.findall(names))
    for row in examples:
        s=row['statement'];tokens=IDENT.findall(re.sub(r'"(?:\\.|[^"\\])*"','""',s))
        reason=None
        if any(c in s for c in ('∀','∃','→','↔')) or re.search(r'\b(forall|fun|let|by)\b',s):reason='not_ground_computational_shape'
        elif variables.intersection(tokens):reason='section_variable'
        references={};suffixes={}
        for token in tokens:
            parts=row['namespace'].split('.') if row['namespace'] else []
            token_parts=token.split('.')
            for count in range(len(token_parts),0,-1):
                prefix='.'.join(token_parts[:count])
                options=['.'.join(parts[:i]+[prefix]) for i in range(len(parts),-1,-1)]
                match=next((n for n in options if n in by_name),None)
                if match:
                    references[token]=match
                    suffixes[token]='.'+'.'.join(token_parts[count:]) if count<len(token_parts) else ''
                    break
        if not references:reason=reason or 'no_gold_implementation_symbol'
        if reason:excluded.append({**row,'reason':reason});continue
        tests.append({**row,'symbols':references,'symbol_suffixes':suffixes})
    used={n for t in tests for n in t['symbols'].values()}
    return {'tests':tests,'symbols':[r for r in defs if r['full_name'] in used],
            'excluded':excluded,'n_tests':len(tests),'status':'tests' if tests else 'no_tests'}


def main():
    for name in ('e12_phase_a_forecast','e12_phase_a_forecast_amendment_A1'):
        assert verify_forecast(PHASE/'forecasts'/(name+'.json'))
    gate=json.loads((PHASE/'results/compile_reproduction_A1.json').read_text());assert gate['passes']
    inputs=json.loads((PHASE/'results/input_manifest_A1.json').read_text());tasks=[]
    for gold in inputs['gold']:
        source=Path(gold['path']).read_text();assert hashlib.sha256(source.encode()).hexdigest()==gold['sha256']
        result=extract(source)
        suite=hashlib.sha256(json.dumps(result['tests'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
        tasks.append({**gold,**result,'suite_sha256':suite})
    report={'extraction_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'n_tasks':len(tasks),'n_tests':sum(r['n_tests'] for r in tasks),
            'no_tests':[r['task_id'] for r in tasks if not r['n_tests']], 'tasks':tasks}
    dest=PHASE/'results/hidden_tests_manifest.json'
    if dest.exists():assert json.loads(dest.read_text())==report,'Refuse to overwrite a different extracted suite'
    else:dest.write_text(json.dumps(report,separators=(',',':'))+'\n')
    print(json.dumps({k:report[k] for k in ('n_tasks','n_tests','no_tests')}))


if __name__=='__main__':main()
