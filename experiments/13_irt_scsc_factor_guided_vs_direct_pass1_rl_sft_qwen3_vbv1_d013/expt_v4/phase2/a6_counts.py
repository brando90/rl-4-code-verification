"""TLDR: Reduce private v2 A6 receipts to anonymous aggregate counts and input SHA-256s."""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
from common import digest, write_new


def reduce_rows(manifest, rows):
    cells=manifest['cells']
    expected={c['cell_id']:c for c in cells}
    table={r['cell_id']:r for r in rows}
    if len(cells)!=512 or len(expected)!=512 or len(rows)!=512 or set(table)!=set(expected):
        raise ValueError('exact 512-cell A6 inventory required')
    groups=defaultdict(list)
    for key,cell in expected.items():
        r=dict(table[key])
        if 'factored_reward' not in r:
            if r.get('strict') is not None or r.get('status') not in ('deterministic_resource_limit','unresolved_measurement'):
                raise ValueError('unexpected missing A6 reward field')
            r['factored_reward']=None
        if cell['split']!='train' or any(r.get(k)!=cell[k] for k in ('task_id','sample_idx','split')):
            raise ValueError('A6 identity or split mismatch')
        if r['strict'] not in (None,0,1) or (r['factored_reward'] is not None and
            (not math.isfinite(r['factored_reward']) or not 0<=r['factored_reward']<=1)):
            raise ValueError('invalid A6 scores')
        groups[cell['task_id']].append(r)
    if len(groups)!=64 or any(sorted(r['sample_idx'] for r in g)!=list(range(8)) for g in groups.values()):
        raise ValueError('A6 requires exactly 64 groups of eight')
    histogram=Counter(); complete=0; mixed=0; varying=0; measured=0; successes=0
    for group in groups.values():
        s=sum(int(r['strict']) for r in group if r['strict'] is not None)
        histogram[s]+=1;successes+=s;measured+=sum(r['strict'] is not None for r in group)
        if all(r['strict'] is not None and r['factored_reward'] is not None for r in group):
            complete+=1;mixed+=0<s<8; varying+=len({r['factored_reward'] for r in group})>1
    return {'tldr':'Anonymous A6 counts from the complete frozen 512-slot inventory.',
            'tasks':64,'declared':512,'measured_strict':measured,'missing_strict':512-measured,
            'strict_successes':successes,'strict_success_histogram':{str(k):histogram[k] for k in range(9)},
            'histogram_missing_rule':'count known successes; missing remain separately reported',
            'complete_groups':complete,'mixed_strict_groups':mixed,'varying_B_groups':varying}


def reduce_private(root, output):
    root=Path(root)
    manifest=root/'manifest.json'; scoring=root/'scoring/result.json'
    m=json.loads(manifest.read_text()); s=json.loads(scoring.read_text())
    rows=s['rows']
    result=reduce_rows(m,rows)
    # Bind the aggregate scoring receipt and each authoritative cell result; no identities or paths per cell.
    cell_files=sorted((root/'scoring').glob('[0-9][0-9][0-9][0-9][0-9]/result.json'))
    actual=[json.loads(p.read_text()) for p in cell_files]
    reduced_actual=reduce_rows(m,actual)
    if result!=reduced_actual:raise ValueError('aggregate and individual A6 scoring receipts disagree')
    actual_by_id={r['cell_id']:r for r in actual}
    for row in rows:
        if any(row.get(k)!=actual_by_id[row['cell_id']].get(k) for k in ('strict','factored_reward','status')):
            raise ValueError('per-cell aggregate scoring mismatch')
    result['input_sha256s']={'manifest':digest(manifest),'scoring':digest(scoring),
                             'cell_results':sorted(digest(p) for p in cell_files)}
    expected={'strict_success_histogram':{'0':51,'1':2,'2':3,'3':3,'4':0,'5':2,'6':1,'7':1,'8':1},
              'complete_groups':54,'mixed_strict_groups':8,'varying_B_groups':49}
    result['protocol_differences']={k:{'protocol':v,'reducer':result[k]} for k,v in expected.items() if result[k]!=v}
    write_new(output,result)
    return {k:v for k,v in result.items() if k!='input_sha256s'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('/lfs/skampere1/0/brando9/rl4cv_e13v2/phase1/A6'))
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(reduce_private(a.root,a.output),sort_keys=True))
