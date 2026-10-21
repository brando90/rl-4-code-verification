"""TLDR: Measure v4's fixed train audit cohort, source-order mutations and independent hidden coverage."""
import json
from pathlib import Path
from common import digest,write_new

SUITES=Path('/lfs/skampere1/0/brando9/rl4cv_e13v2/train_audit_S2/suites/prepared.json')


def audit_templates():
    data=json.loads(SUITES.read_text())
    if len(data['rows'])!=32 or any(r['split']!='train' for r in data['rows']):raise ValueError('fixed train audit cohort changed')
    return [r['task_id'] for r in data['rows']]


def audits(config,rows,root):
    import legacy
    from scoring_runtime import score,retain_commands
    from declaration_adapter_v2 import inspect_source
    from audit_mutations import construct
    from hidden_runtime import measure_cell
    import shutil
    root=Path(root);measured=score(config,rows,root/'original')['rows']
    suites={r['task_id']:r['suite'] for r in json.loads(SUITES.read_text())['rows']}
    if [r['task_id'] for r in rows]!=audit_templates():raise ValueError('audit cohort reordered')
    controls=json.loads((legacy.V2/'phase2/hidden_controls_result.json').read_text())
    if controls['status']!='PASS':raise ValueError('independent hidden controls failed')
    mutations={k:[] for k in ('padding','deletion','substitution')};increases=[];coverage=[];theorems=[];rewards=[]
    for i,row in enumerate(measured):
        source=Path(row['score_root'])/'solution.lean';suite=suites[row['task_id']]
        if digest(suite['path'])!=suite['sha256']:raise ValueError('hidden suite changed')
        hidden={'cell_id':row['cell_id'],'task_id':row['task_id'],'split':'train','source':str(source),'suite':suite['path']}
        cfg={**config['scoring'],'root':str(root/'hidden'),'lake_bin':shutil.which('lake')}
        bound={str(source):digest(source),suite['path']:suite['sha256'],cfg['train_ids']:digest(cfg['train_ids'])}
        with retain_commands(root/'raw_hidden'/str(i)):
            h=measure_cell(hidden,cfg,bound,digest(config['admission']))
        coverage.append(h.get('hidden_pass_rate') if h.get('fully_applicable') or h['status']=='compile_failure' else None)
        if row['strict'] is None:theorems.append(None);rewards.append(None);continue
        theorems.append(row['p']['denominator']);rewards.append(row['factored_reward'])
        frontend=json.loads((Path(row['score_root'])/'evidence/components/frontend.json').read_text())
        for kind,mutation in construct(source.read_bytes(),frontend,expected_sha256=digest(source)).items():
            target=root/kind/str(i);target.mkdir(parents=True);p=target/'solution.lean';p.write_bytes(mutation['source'])
            with retain_commands(target/'raw_compiler'):
                result=inspect_source(p,lake_dir=Path(cfg['lake']),scorer_root=Path(cfg['scorer']),
                    evidence=target/'evidence',expected_sha256=digest(p),family='ladder',known=True,truncated=False)
            mutations[kind].append(result['factored_reward'])
            if result['factored_reward']>row['factored_reward']:
                increases.append({'audit_index':i,'mutation':kind,'before':row['factored_reward'],'after':result['factored_reward']})
    # Baseline and each B update use the same complete cohort; missing coverage
    # makes the audit unmeasured, never a zero or an apparent safety pass.
    complete=all(x is not None for x in coverage+theorems+rewards)
    mean=lambda x:sum(x)/len(x) if x and all(v is not None for v in x) else None
    return {'status':'PASS' if complete and all(len(v)==32 for v in mutations.values()) else 'UNMEASURED',
            'hidden_coverage_controls':True,'mutations':{k:len(v) for k,v in mutations.items()},
            'reward_increasing_mutations':increases,'declared_tasks':32,'measured_coverage':sum(x is not None for x in coverage),
            'baseline':{'reward':mean(rewards),'theorem_count':mean(theorems),'coverage':mean(coverage)},
            'FSC':'unmeasured','reward_hacking_safety':'not established'}
