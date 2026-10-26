"""Exercise complete-cohort/group-bootstrap and missing-cell rejection using synthetic constant group means."""
from pathlib import Path
import importlib.util,csv,json,tempfile,hashlib
import numpy as np
repo=Path('/lfs/skampere1/0/brando9/rl4cv_e20'); e=repo/'experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013'
spec=importlib.util.spec_from_file_location('summary',e/'expt_v1/summarize_phase0_cells_e20.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
pins=json.loads((repo/'experiments/19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013/expt_v1/input_pins_e19.json').read_text())
split=list(csv.DictReader((repo/pins['paths']['split_manifest']).open()));tasks=[{'task_id':r['task_id'],'group_id':r['group_id']} for r in split if r['split']=='train']
root=Path(tempfile.mkdtemp(prefix='e20_summary_fixture_'));score=root/'scores.csv';task=root/'tasks.csv'
rows=[dict(task_id=r['task_id'],sample_idx=k,status='measured',partial_status='measured',strict=0,adapter_strict=0,factored_reward=.25 if k<4 else .75,IC_tests=1,IC_proofs=0,FSC='unmeasured',compiles=0,capped='True' if k%2 else 'False',lean_sha256='',generated_tokens=0) for r in tasks for k in range(8)]
def write(p,rs):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rs[0]);w.writeheader();w.writerows(rs)
write(score,rows);write(task,tasks);r=m.summarize(score,task)
for key,mean in [('strict',0),('factored_reward',.5),('IC_tests',1),('IC_proofs',0),('capped',.5)]:
 assert r['metrics'][key]['mean']==mean
 assert r['metrics'][key]['lo']==r['metrics'][key]['hi']==mean
assert np.isclose(r['metrics']['factored_reward']['sd_across_eight_sample_index_means'],np.sqrt(8*.25**2/7))
assert r['active_tasks']==r['successes']==r['scorer_adapter_disagreements']==0
rejected=[]
for name,change in [('missing',lambda:rows.pop()),('unresolved',lambda:rows[0].update(partial_status='unresolved')),('parse_nonzero',lambda:rows[0].update(partial_status='parse_failure_zero_credit'))]:
 old=[x.copy() for x in rows];change();write(score,rows)
 try:m.summarize(score,task)
 except ValueError:rejected.append(name)
 else:raise AssertionError(name)
 rows=old
assert len(rejected)==3
print(json.dumps(dict(status='PASS',synthetic_cells=4312,groups=400,constant_group_bootstrap_intervals_exact=True,rejections=rejected,source_sha256=hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest())))
