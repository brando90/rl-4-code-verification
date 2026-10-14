#!/usr/bin/env python3
"""Inventory persisted generations and every missing fixed-audit/control rating after a blocked closeout."""
import importlib.util
import json
import subprocess
from pathlib import Path

EXP=Path(__file__).resolve().parents[1]
ROOT=EXP/'results'
WORK=Path('/lfs/skampere1/0/brando9/rl4cv_e08/v2')
spec=importlib.util.spec_from_file_location('judge_v2',EXP/'scripts/judge_rl4cv_e08v2.py')
judge=importlib.util.module_from_spec(spec)
spec.loader.exec_module(judge)
manifest=json.loads((ROOT/'test_manifest_v2.json').read_text())
ids=judge.read_ids(EXP.parent/'expt_v1/results/split/vbv1_test_task_ids.txt')
want={(t,k) for t in ids for k in range(8)}
audit=judge.audit_cells(ids)
assert len(audit)==len(set(audit))==60
systems={}; unknown=[]; eligibility=[]
for system in manifest['systems']:
    if system['generation']!='new': continue
    label=system['label']; paths=sorted((WORK/'ladder/test/raw').glob(f'gen_{label}_g8.shard*of*.jsonl'))
    rows=[json.loads(line) for path in paths for line in path.read_text().splitlines() if line.strip()]
    got=[(r['task_id'],int(r['sample_idx'])) for r in rows]
    assert len(got)==len(set(got)) and set(got)<=want
    systems[label]=dict(n_declared=1776,n_persisted_generations=len(got),n_missing_generations=len(want-set(got)),missing_generations=[f'{t}#{k}' for t,k in sorted(want-set(got))],raw_shard_paths=list(map(str,paths)),n_scored_shards=len(list((WORK/'ladder/test/scores').glob(f'{label}_g8_s*/*_per_task.csv'))))
    # This terminal route failed before any scoring or test-pack admission.
    assert systems[label]['n_scored_shards']==0
    for task,k in sorted(want): eligibility.append(dict(system=label,task_id=task,sample_idx=k,reason='IC_tests not measured; compile-gated judge eligibility unknown'))
    for task,k in audit:
        for repeat in judge.REPEATS:
            for member in judge.CONFIGS:
                unknown.append(dict(suite='test_fixed_audit',system=label,task_id=task,sample_idx=k,rating_idx=repeat,member=member,status='not_admitted_missing_candidate',receipt_available=False))
controls=json.loads((ROOT/'judge/judge_pack_controls.json').read_text())
for cell in controls['control_cells']:
    for member in judge.CONFIGS:
        unknown.append(dict(suite='controls',task_id=cell['task_id'],kind=cell['kind'],rating_idx=cell['repeat'],member=member,status='admission_rejected_unserved',receipt_available=False))
out=dict(recorded_at=subprocess.check_output(['date','--iso-8601=seconds'],text=True).strip(),status='PARTIAL',systems=systems,n_new_declared_cells=5328,n_new_persisted_generations=sum(s['n_persisted_generations'] for s in systems.values()),n_control_ratings_declared=50,n_control_ratings_measured=0,n_fixed_audit_files=180,n_fixed_audit_ratings_declared=1080,n_fixed_audit_ratings_measured=0,additional_main_rating_eligibility_unknown_cells=eligibility,unknown_ratings=unknown,test_pack_frozen=False,model_requests_served=0,reported_charges_usd=None,charge_note='No model requests were admitted; no charge receipts exist. Host compute cost unmeasured.')
(ROOT/'terminal_coverage_v2.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('systems','unknown_ratings','additional_main_rating_eligibility_unknown_cells')}))
