"""Exercise the prospective A6 result aggregation on a complete authored cohort only."""
from pathlib import Path
import importlib.machinery,importlib.util,sys,json,hashlib
P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2';sys.path.insert(0,str(P));sys.path.insert(0,str(P.parent/'phase1'))
import a6_processing as m

def fixture():
    cells=[{'cell_id':f'authored/{t}/{i}','task_id':str(t),'sample_idx':i}for t in range(64)for i in range(8)]
    rows=[{'cell_id':c['cell_id'],'status':'measured','compile':0,'strict':0}for c in cells]
    return {'cells':cells},{'rows':rows,'cleanup_unresolved':0,'identical_retries':0},{'declared':1080,'missing':0,'compile':{'successes':100}},{str(t):{'group_id':str(t//2)}for t in range(64)}

def test_known_zero_stops_and_discloses_degenerate_bootstrap():
    args=fixture();r=m.summarize(*args,draws=100)
    assert r['status']=='UNSOUND'and r['groups']==32 and r['intervals']['compile']['outer_envelope_95']==[0,0]
    assert 'not a population upper bound'in r['bootstrap']['scope']

def test_missing_outcomes_retain_bounds_and_no_admission():
    manifest,score,reference,features=fixture()
    for row in score['rows'][:8]:row.update(status='missing_generation',compile=None,strict=None)
    r=m.summarize(manifest,score,reference,features,draws=100)
    assert r['status']=='UNRESOLVED'and r['metrics']['compile']['missing']==8 and not r['LP_admitted']
    assert r['intervals']['compile']['outer_envelope_95'][1]>0

def test_observed_soundness_requires_clean_scoring():
    manifest,score,reference,features=fixture()
    for row in score['rows'][:8]:row.update(compile=1,strict=1)
    assert m.summarize(manifest,score,reference,features,draws=100)['status']=='SOUND'
    score['cleanup_unresolved']=1
    r=m.summarize(manifest,score,reference,features,draws=100)
    assert r['status']=='CLEANUP_REQUIRED'and not r['LP_admitted']
