"""Audit existing validation reward signal with the project's unchanged rho/H definitions; no model calls."""
import argparse,csv,hashlib,json,os,socket,sys,time
from pathlib import Path
import numpy as np
from rl4cv.experience import Response,measure_environment,group_masses,loo_advantages


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def boolean(s):
    assert s in ("True","False"),s
    return s=="True"
def audit(cells,ids,out):
    rows=list(csv.DictReader(Path(cells).open()));tasks=Path(ids).read_text().splitlines()
    assert len(tasks)==len(set(tasks))==135
    want={(t,k) for t in tasks for k in range(8)}
    idx={(r['task_id'],int(r['sample_idx'])):r for r in rows}
    assert len(rows)==len(idx)==1080 and set(idx)==want
    groups=[];table=[];nonzero_raw=nonzero_admitted=0
    for t in tasks:
        rr=[idx[(t,k)] for k in range(8)]
        g=[Response(float(r['binary_success']),int(r['generated_tokens']),not boolean(r['capped'])) for r in rr]
        assert all(r.reward in (0.,1.) and r.generated_tokens>0 for r in g)
        a=loo_advantages([r.reward for r in g]);raw,adm,tok=group_masses(g)
        nr=int(np.count_nonzero(np.abs(a)>1e-12))
        na=sum(bool(abs(x)>1e-12) and r.admitted for x,r in zip(a,g))
        nonzero_raw+=nr;nonzero_admitted+=na
        groups.append(g);table.append(dict(task_id=t,successes=int(sum(r.reward for r in g)),attempts=8,generated_tokens=sum(r.generated_tokens for r in g),raw_advantage_mass=raw,admitted_advantage_mass=adm,token_weighted_advantage_mass=tok,admitted_responses=sum(r.admitted for r in g),nonzero_advantages=nr,nonzero_admitted_advantages=na))
    measured=measure_environment(groups).to_dict()
    # Resample whole validation tasks, retaining all8responses and the original overlong-filter contract.
    draws=np.random.default_rng(0).integers(0,135,(10000,135))
    mass=np.array([r['admitted_advantage_mass'] for r in table]);tokens=np.array([r['generated_tokens'] for r in table]);mixed=np.array([0<r['successes']<8 for r in table])
    dm=mass[draws];dt=tokens[draws]
    rh=1e6*dm.sum(axis=1)/dt.sum(axis=1)
    den=135*(dm**2).sum(axis=1);hh=np.divide(dm.sum(axis=1)**2,den,out=np.zeros(10000),where=den>0)
    summary=dict(status='COMPLETE',verdict='NONZERO_VALIDATION_RL_SIGNAL' if measured['rho']>0 else 'NO_ADMITTED_SIGNAL',measurement=measured,ci95=dict(rho=np.quantile(rh,[.025,.975]).tolist(),H=np.quantile(hh,[.025,.975]).tolist(),mixed_share=np.quantile(mixed[draws].mean(axis=1),[.025,.975]).tolist()),bootstrap=dict(unit='validation task retaining all8responses',draws=10000,seed=0,p_value=None),nonzero_advantages=nonzero_raw,nonzero_admitted_advantages=nonzero_admitted,tasks_with_admitted_mass=int((mass>0).sum()),target_band_tasks=sum(2<=r['successes']<=6 for r in table),input_sha256=sha(cells),ids_sha256=sha(ids),analysis_sha256=sha(__file__),experience_sha256=sha(sys.modules['rl4cv.experience'].__file__),host=socket.gethostname(),slurm_job_id=os.environ.get('SLURM_JOB_ID'),observed_unix=time.time(),provider_spend_usd=0,gpu_count=0,test_split_opened=False,interpretation='Descriptive post-hoc audit of already-published validation scores; necessary reward variation, not observed RL improvement or permission to train on validation.',loss_contract='Capped responses stay in reward baseline but carry zero loss weight; all generated tokens remain in denominator.',limitations=['One checkpoint and generation run; task bootstrap does not estimate training-seed variability.','Validation estimates transfer; direct training-environment rho/H and actual RL gains are not measured.','The inherited format gates and25percent milestone remain separate and unmet.'])
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (out/'per_task_signal.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    print(json.dumps(summary),flush=True)
    return summary
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('cells');p.add_argument('ids');p.add_argument('out');a=p.parse_args();audit(a.cells,a.ids,a.out)
