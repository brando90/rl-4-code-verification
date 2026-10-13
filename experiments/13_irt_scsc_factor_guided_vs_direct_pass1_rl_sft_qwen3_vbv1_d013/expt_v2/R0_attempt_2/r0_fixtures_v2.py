#!/usr/bin/env python3
"""Define independent authored expectations and execute the single version-2 R0 fixture gate."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from declaration_adapter_v2 import inspect_source, sha256
from historical_oracle_v2 import load

GOOD = 'import Mathlib\nexample : 1 + 1 = 2 := by decide\ntheorem good : 1 + 1 = 2 := by decide\n'
EXAMPLE = 'import Mathlib\nexample : 1 + 1 = 2 := by decide\n'


def definitions():
    """Integer expectations written from the authored programs, never probe outputs."""
    old = load('e13v2_authored_v1', HERE.parent.parent / 'expt_v1/phase0_prepare.py')
    count = {
        'valid': (2,2,1,1,1), 'valid_at_cap': (2,2,1,1,1), 'no_example': (1,1,0,1,1),
        'no_theorem': (1,1,1,0,0), 'empty': (0,0,0,0,0), 'truncated_syntax': (2,3,0,1,1),
        'failed_then_valid': (2,3,1,1,2), 'sorry': (2,2,1,0,1), 'helper_sorry': (3,3,1,0,2),
        'native_theorem': (2,2,1,0,1), 'native_example': (2,2,1,1,1),
        'declared_axiom': (3,3,1,0,1), 'vacuous': (2,2,1,1,1),
        'top_level_error': (2,3,1,1,1), 'printed_error': (3,3,1,1,1),
    }
    rows = []

    def add(name, source, strict, counts, *, truncated=False, known=True, family='ladder', reason='consistent'):
        dn, dd, t, pn, pd = counts
        rows.append({'name':name, 'source':source, 'family':family, 'known':known, 'truncated':truncated,
                     'expected': {'strict':strict, 'strict_status':'scored' if known else 'unmeasured',
                                  'e':int(bool(source.strip())), 'd':{'numerator':dn,'denominator':dd},
                                  't':t,'p':{'numerator':pn,'denominator':pd}, 'consistency':reason}})
    for name, (source, expected, truncated) in old.FIXTURES.items():
        add(name,source,expected,count[name],truncated=truncated,
            reason={'printed_error':'kernel_probe_rejection','vacuous':'vacuity'}.get(name,'consistent'))
    add('unknown_valid', GOOD, None, (2,2,1,1,1), known=False)
    add('unknown_empty', '', None, (0,0,0,0,0), known=False)
    add('unparseable_compiling', GOOD.replace('good :','good:'), 0, (2,2,1,1,1), reason='vacuity')
    add('unparseable_noncompiling', GOOD.replace('good :','good:')+'#check missing_e13v2\n',0,(2,3,1,1,1))
    long_print = '#eval IO.println ' + json.dumps('x' * 5000) + '\n'
    add('error_beyond_4000',GOOD+long_print+'theorem bad : False := by decide\n'+long_print,0,(4,5,1,1,2))
    add('unused_axiom', EXAMPLE+'axiom unused : False\ntheorem good : 1 + 1 = 2 := by decide\n',1,(3,3,1,1,1))
    add('namespaces_multiline', EXAMPLE+'/- outer /- nested -/ comment -/\nnamespace Outer\n@[simp] theorem first\n : 1 + 1 = 2 := by decide\nnamespace Inner\ntheorem second : 2 + 2 = 4 := by decide\nend Inner\nend Outer\n',1,(7,7,1,2,2))
    add('duplicate_obligation',GOOD+'theorem good : 1 + 1 = 2 := by decide\n',0,(2,3,1,1,2))
    add('stderr_capture',GOOD+'#eval IO.eprintln "e13v2-stderr-evidence"\n',1,(3,3,1,1,1))
    add('base_vacuity_status',EXAMPLE+'theorem vac : True := by trivial\n',1,(2,2,1,1,1),family='base')
    add('unresolved_type',EXAMPLE+'theorem broken : MissingType := by trivial\n',0,(1,2,1,0,1))
    add('admit',GOOD.replace('by decide\n', 'by decide\n', 1).replace('theorem good : 1 + 1 = 2 := by decide','theorem good : 1 + 1 = 2 := by admit'),0,(2,2,1,0,1))
    for name, completion in [
        ('multiple_blocks_longest', '```lean\nexample : True := by trivial\n```\n```lean\n'+GOOD+'```'),
        ('multiple_blocks_labelled', '```lean\n'+GOOD+('-- longer discarded block\n'*10)+'```\nFILE: solution.lean\n```lean\n'+GOOD+'```')]:
        add(name,GOOD,1,(2,2,1,1,1))
        rows[-1]['completion']=completion
    return rows


def freeze(output):
    output.mkdir(parents=True,exist_ok=False)
    fixtures=definitions()
    for row in fixtures:
        p=output/(row['name']+'.lean')
        p.write_text(row.pop('source'))
        row['source_path']=str(p.resolve());row['source_sha256']=sha256(p)
    lock={'created':datetime.now(timezone.utc).isoformat(), 'stage':'R0', 'fixtures':fixtures,
          'old_contract_tests':30, 'fixture_count':len(fixtures),
          'implementation_sha256':{p.name:sha256(p) for p in [HERE/'DeclarationProbe_v2.lean',HERE/'declaration_adapter_v2.py',HERE/'historical_oracle_v2.py',Path(__file__)]},
          'rule':'All fixtures match and required Lean integration runs; failure stops downstream under PLAN section 4.'}
    (output/'lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    print(json.dumps({'lock_sha256':sha256(output/'lock.json'),'fixtures':len(fixtures)}))


def run(output,lake,scorer):
    lock=json.loads((output/'lock.json').read_text())
    for name,expected in lock['implementation_sha256'].items():
        if sha256(HERE/name)!=expected: raise ValueError('R0 implementation changed after freeze')
    results=output/'results.jsonl'
    # Opening with x prevents any silent gate retry or overwritten result.
    with results.open('x') as f:
        for row in lock['fixtures']:
            try:
                if 'completion' in row:
                    from rl4cv.veribench.exp103 import load_single_call
                    extractor=load_single_call(os.environ['VERIBENCH_ROOT'])
                    files,method=extractor.extract_files(row['completion'],['solution.lean'])
                    if files.get('solution.lean')!=Path(row['source_path']).read_text():
                        raise ValueError('pinned extraction selection mismatch')
                actual=inspect_source(Path(row['source_path']),lake_dir=lake,scorer_root=scorer,
                    evidence=output/'evidence'/row['name'],expected_sha256=row['source_sha256'],
                    family=row['family'],known=row['known'],truncated=row['truncated'])
                mismatches={k:{'expected':v,'actual':actual.get(k)} for k,v in row['expected'].items() if actual.get(k)!=v}
                if row['name']=='vacuous' and (actual['raw_vacuity_hits']!=2 or actual['distinct_vacuous_theorems']!=1):
                    mismatches['vacuity_counts']=actual
                if row['name']=='error_beyond_4000':
                    raw=json.loads((output/'evidence'/row['name']/'components/frontend.json').read_text())
                    if not any(m['severity']=='error' for c in raw['commands'] for m in c['messages']):
                        mismatches['full_diagnostics']='error missing'
                if row['name']=='stderr_capture':
                    raw=json.loads((output/'evidence'/row['name']/'components/frontend.json').read_text())
                    if 'e13v2-stderr-evidence' not in ''.join(c['stderr'] for c in raw['commands']):
                        mismatches['stderr']='not retained per command'
                result={'fixture':row['name'],'actual':actual,'mismatches':mismatches,'pass':not mismatches}
            except Exception as exc:
                result={'fixture':row['name'],'pass':False,'exception':type(exc).__name__,'message':str(exc)}
            f.write(json.dumps(result)+'\n');f.flush();os.fsync(f.fileno())
            print(json.dumps({'fixture':row['name'],'pass':result['pass']}),flush=True)
    rows=[json.loads(line) for line in results.read_text().splitlines()]
    receipt={'stage':'R0','passed':sum(r['pass'] for r in rows),'declared':len(lock['fixtures']),
             'status':'PASS' if all(r['pass'] for r in rows) else 'FAIL',
             'lock_sha256':sha256(output/'lock.json'),'results_sha256':sha256(results)}
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))
    return 0 if receipt['status']=='PASS' else 1


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze','run']);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--lake',type=Path,default=Path(os.environ.get('E13_LAKE_DIR','/nonexistent')))
    ap.add_argument('--scorer',type=Path,default=Path(os.environ.get('E13_SCORER_ROOT','/nonexistent')))
    a=ap.parse_args()
    if a.action=='freeze':freeze(a.output)
    else:raise SystemExit(run(a.output,a.lake,a.scorer))
