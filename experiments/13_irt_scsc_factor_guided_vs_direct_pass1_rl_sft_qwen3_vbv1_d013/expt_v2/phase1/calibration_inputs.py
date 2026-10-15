"""Build aligned train-anchor counts with explicit missingness and unchanged output denominators."""
from __future__ import annotations

import numpy as np

BATCHES=('base','half','full1')
POLICIES=('base_4B','sft_4B_f0p5','sft_4B_f1p0')


def anchor_arrays(rows,tasks):
    """Require every declared slot, retaining unmeasured cells as zero trials, not failures."""
    tasks=list(tasks)
    if not tasks or len(tasks)!=len(set(tasks)):raise ValueError('invalid train task allowlist')
    table={}
    for row in rows:
        key=(row['batch'],row['task_id'],row['sample_idx'])
        if (row['batch'] not in BATCHES or row['policy']!=POLICIES[BATCHES.index(row['batch'])]
                or row['split']!='train' or row['task_id'] not in tasks
                or type(row['sample_idx']) is not int or not 0<=row['sample_idx']<8 or key in table):
            raise ValueError('duplicate, held-out or misidentified anchor cell')
        if row['cell_id']!=f"{key[0]}/{key[1]}/{key[2]}":raise ValueError('anchor cell identity changed')
        table[key]=row
    expected={(b,t,s) for b in BATCHES for t in tasks for s in range(8)}
    if set(table)!=expected:raise ValueError('missing declared anchor receipt')
    shape=(3,len(tasks),8);observed=np.zeros(shape,dtype=bool)
    values={k:np.zeros(shape,dtype=int) for k in ('strict','q1','compile','honest')}
    components={k:(np.zeros(shape,dtype=int),np.zeros(shape,dtype=int)) for k in ('d','t','p')}
    for i,batch in enumerate(BATCHES):
        for j,task in enumerate(tasks):
            for sample in range(8):
                row=table[(batch,task,sample)];at=(i,j,sample)
                if row['status']!='measured':continue
                observed[at]=True
                for k in values:
                    if row[k] not in (False,True,0,1):raise ValueError('nonbinary observed strict/hurdle label')
                    values[k][at]=row[k]
                for k,(y,n) in components.items():
                    if k=='t':
                        if row[k] not in (False,True,0,1):raise ValueError('nonbinary observed implementation label')
                        numerator,denominator=int(row[k]),1
                    else:
                        numerator,denominator=row[k]['numerator'],row[k]['denominator']
                        if (type(numerator) is not int or type(denominator) is not int
                                or not 0<=numerator<=denominator):
                            raise ValueError('fraction counts must retain integer denominators')
                    y[at]=numerator;n[at]=denominator
    return {'observed':observed,'components':components,**values,'table':table,'tasks':tasks}


def history(arrays):
    observed=arrays['observed'];p,j,s=np.indices(observed.shape)
    return {**{k:arrays[k].ravel() for k in ('strict','q1','compile','honest')},
            'observed':observed.ravel(),'policy_index':p.ravel(),'item_index':j.ravel()}


def pattern_report(arrays):
    out={'declared':int(arrays['observed'].size),'measured':int(arrays['observed'].sum()),
         'missing':int((~arrays['observed']).sum()),'components':{}}
    for k,(y,n) in arrays['components'].items():
        total=n.sum(axis=(0,2));success=y.sum(axis=(0,2))
        out['components'][k]={'denominator':int(n.sum()),'zero_denominator_outputs':int((n==0).sum()),
            'empty_items':np.flatnonzero(total==0).tolist(),
            'constant_items':np.flatnonzero((total>0)&((success==0)|(success==total))).tolist(),
            'empty_policies':np.flatnonzero(n.sum(axis=(1,2))==0).tolist()}
    return out
