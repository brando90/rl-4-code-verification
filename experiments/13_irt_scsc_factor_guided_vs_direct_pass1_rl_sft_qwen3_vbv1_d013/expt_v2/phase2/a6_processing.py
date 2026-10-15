"""Score the complete published A6 generation inventory once and retain bounded full-population conclusions."""
import argparse,json,sys,time
from collections import Counter
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'phase1'))
from g1_driver import verify_publication
from panel import digest
from anchor_storage import write_new
from a6_score import score_manifest
from a6_contract import validate_manifest,verdict


def summarize(manifest,scored,reference,features,draws=10000):
    result=verdict(manifest,scored['rows'],reference)
    if scored['cleanup_unresolved']!=0:result.update(status='CLEANUP_REQUIRED',LP_admitted=False)
    cells=manifest['cells'];tasks=sorted({c['task_id']for c in cells});rows={r['cell_id']:r for r in scored['rows']}
    groups={t:features[t]['group_id']for t in tasks};unique=sorted(set(groups.values()))
    blocks=[np.array([i for i,t in enumerate(tasks)if groups[t]==g])for g in unique]
    rng=np.random.default_rng(1302603);samples=rng.integers(0,len(blocks),size=(draws,len(blocks)))
    intervals={}
    for metric in ('compile','strict'):
        values=[]
        for task in tasks:
            own=[rows[c['cell_id']]for c in cells if c['task_id']==task]
            measured=[r[metric]for r in own if r['status']=='measured'and r.get(metric)is not None]
            values.append([sum(measured),8-len(measured)])
        a=np.array(values);bounds=[]
        for sample in samples:
            ix=np.concatenate([blocks[i]for i in sample]);counts=a[ix].sum(axis=0);bounds.append([counts[0]/(len(ix)*8),sum(counts)/(len(ix)*8)])
        quantiles=np.quantile(bounds,[.025,.975],axis=0)
        intervals[metric]={'lower_endpoint_interval_95':quantiles[:,0].tolist(),'upper_endpoint_interval_95':quantiles[:,1].tolist(),
            'outer_envelope_95':[float(quantiles[0,0]),float(quantiles[1,1])]}
    result.update(task_count=64,groups=len(unique),samples_per_task=8,intervals=intervals,
        bootstrap={'draws':draws,'seed':1302603,'unit':'whole selected train task groups, retaining all eight samples',
            'scope':'descriptive conditional fixed policy/cohort; no training-run uncertainty; a degenerate zero bootstrap is not a population upper bound'},
        p_value=None,test='A6 operational criterion, not a hypothesis test',
        missing_statuses=dict(Counter(r['status']for r in scored['rows']if r['status']!='measured')),
        extraction_counts=dict(Counter(r.get('extraction','unavailable')for r in scored['rows'])),
        cleanup_unresolved=scored['cleanup_unresolved'],identical_retries=scored['identical_retries'])
    return result


def run(plan):
    lock=verify_publication(plan['lock'],plan['repository'],plan['published_revision'])
    if lock.get('gate')!='A6_DIAGNOSTIC_SCORE'or lock.get('status')!='FROZEN':raise ValueError('published A6 scoring input lock required')
    table={b['path']:b['sha256']for b in lock['bindings']}
    for path,sha in table.items():
        if digest(path)!=sha:raise ValueError('A6 scoring source/input changed')
    for p in [Path(__file__).resolve(),HERE/'a6_score.py',HERE/'a6_contract.py']:
        if table.get(str(p))!=digest(p):raise ValueError('A6 scoring/analysis executable not bound')
    cfg=lock['configuration'];manifest=json.loads(Path(cfg['manifest']).read_text());validate_manifest(manifest,Path(cfg['scoring']['allowlist']).read_text().splitlines())
    generations=json.loads(Path(cfg['generation_index']).read_text())
    if table.get(cfg['generation_index'])!=digest(cfg['generation_index']):raise ValueError('A6 generation index not bound')
    if set(generations)!={c['cell_id']for c in manifest['cells']}:raise ValueError('A6 generation population changed')
    for g in generations.values():
        if g is not None and table.get(g['path'])!=g['sha256']:raise ValueError('A6 generation not bound')
    root=Path(cfg['root']);root.mkdir(exist_ok=True,parents=True)
    write_new(root/'analysis_attempt.json',{'condition':'v2-S2','started_unix':time.time(),'lock_sha256':digest(plan['lock']),'retries':0})
    scored=score_manifest(manifest,cfg['scoring'],generations,digest(plan['lock']))
    result=summarize(manifest,scored,json.loads(Path(cfg['reference']).read_text()),json.loads(Path(cfg['features']).read_text()))
    result.update(scoring_sha256=digest(Path(cfg['scoring']['root'])/'result.json'),lock_sha256=digest(plan['lock']),ended_unix=time.time())
    write_new(root/'result.json',result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);a=p.parse_args()
    print(json.dumps(run(json.loads(a.plan.read_text())),sort_keys=True))
