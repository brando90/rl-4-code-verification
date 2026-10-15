"""Validate the frozen train-only A6 diagnostic and its sharp full-denominator admission bounds."""
import hashlib,math
from fractions import Fraction


def validate_manifest(manifest,allowlist):
    cells=manifest['cells'];allowed=set(allowlist)
    if manifest.get('condition')!='v2-S2' or manifest.get('purpose')!='A6_pipeline_diagnostic':raise ValueError('A6 train diagnostic required')
    if len(cells)!=512 or len({c['cell_id']for c in cells})!=512:raise ValueError('all 512 unique A6 slots required')
    tasks=sorted({c['task_id']for c in cells})
    if len(tasks)!=64 or not set(tasks)<=allowed:raise ValueError('64 distinct frozen train tasks required')
    if hashlib.sha256(''.join(t+'\n'for t in tasks).encode()).hexdigest()!=manifest['task_ids_sha256']:raise ValueError('A6 cohort changed')
    expected={(t,i)for t in tasks for i in range(8)}
    if {(c['task_id'],c['sample_idx'])for c in cells}!=expected:raise ValueError('A6 sample population changed')
    for c in cells:
        if c.get('split')!='train' or c['seed']!=91*100003+c['sample_idx']:raise ValueError('A6 split or historical sample seed changed')
        if c['cell_id']!=f"A6/sft_4B_f1p0/{c['task_id']}/{c['sample_idx']}":raise ValueError('A6 cell identity changed')
        if (c.get('arm'),c.get('run_seed'),c.get('boundary'))!=('diagnostic',1302601,0):raise ValueError('A6 identity changed')
        if not isinstance(c['prompt_text'],str) or hashlib.sha256(c['prompt_text'].encode()).hexdigest()!=c['chat_text_sha256']:raise ValueError('prompt text changed')
        tokens=c['prompt_token_ids']
        if not tokens or len(tokens)>20480 or any(type(t)is not int or t<0 for t in tokens):raise ValueError('A6 prompt exceeds context')
        if not c.get('required_paths'):raise ValueError('A6 extraction contract absent')
    return cells


def verdict(manifest,rows,reference):
    expected={c['cell_id']for c in manifest['cells']};table={r['cell_id']:r for r in rows}
    if len(expected)!=512 or len(table)!=len(rows) or set(table)!=expected:raise ValueError('all A6 outcomes must be accounted')
    if reference.get('declared')!=1080 or reference.get('missing')!=0:raise ValueError('complete historical validation reference required')
    minimum=Fraction(reference['compile']['successes'],reference['declared']*10)
    metrics={}
    for name in ('compile','strict'):
        observed=[]
        for row in rows:
            x=row.get(name) if row.get('status')=='measured' else None
            if x is not None and (type(x)not in(int,float,bool)or x not in(0,1)):raise ValueError('invalid binary diagnostic outcome')
            if x is not None:observed.append(int(x))
        n=sum(observed);missing=512-len(observed)
        metrics[name]={'successes':n,'measured':len(observed),'missing':missing,'full_denominator_bounds':[n/512,(n+missing)/512]}
    sound=metrics['strict']['successes']>0 and Fraction(metrics['compile']['successes'],512)>=minimum
    impossible=(metrics['strict']['successes']+metrics['strict']['missing']==0 or
        Fraction(metrics['compile']['successes']+metrics['compile']['missing'],512)<minimum)
    return {'condition':'v2-S2','purpose':'A6_pipeline_diagnostic','status':'SOUND'if sound else 'UNSOUND'if impossible else 'UNRESOLVED',
        'LP_admitted':sound,'declared':512,'metrics':metrics,'historical_compile_minimum':float(minimum),
        'criterion':'strict successes > 0 and compile rate >= historical compile rate / 10',
        'comparison_statistic_eligible':False,'retries':0}
