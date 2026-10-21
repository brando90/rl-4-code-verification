"""TLDR: Exercise v4 command-line stage order, six trajectories, crash recovery and a no-resampling stop on CPU."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from common import digest, write_new
from stage_ledger import read
from runner import STAGES


def single_pause(root,admission):
    """Exercise the real pause/timing functions with fake processes and a private pause list."""
    from admission import launch_timing,check_admission
    from operational_pause import admitted_config
    from pause_v3 import pause,VETO_END
    root=Path(root);(root/'phase2/pilot').mkdir(parents=True,exist_ok=False)
    operational=admitted_config(check_admission(admission,require_launch=True))
    timing=lambda:launch_timing(root/'phase2/pilot',now=VETO_END+1,
                               veto_not_issued=True,operational=operational)
    signals=[];probes=[];running=True
    runner={'kind':'runner','pid':123456789,'pgid':123456789,'start_ticks':'123','start_unix':1}
    def probe(key,work):
        assert key=='A_1302' and Path(work)==root
        probes.append(key)
        return {'trajectory':key,'pane_text':'waiting for an idle GPU',
                'processes':[runner,*([{'kind':'stage'}] if running else [])],'leases':[]}
    def attempt():
        return pause(admission,work=root,trajectory='A_1302',now=VETO_END+1,veto_not_issued=True,
                     probe=probe,inspect=lambda pid:runner,
                     kill=lambda pgid,sig:signals.append([pgid,int(sig)]))
    before=timing();waiting=attempt();after_wait=timing()
    assert waiting=={'A_1302':'WAIT_STAGE_RUNNING'} and not signals
    assert not (root/'phase2/autoresume_paused.json').exists()
    running=False
    paused=attempt();after_pause=timing()
    assert paused=={'A_1302':'PAUSED'}
    assert not before['released'] and not after_wait['released'] and after_pause['released']
    assert not launch_timing(root/'phase2/pilot',phase='pilot',now=VETO_END+1,
                            veto_not_issued=True,operational=operational)['released']
    return {'synthetic':True,'pause_tool_reports':[waiting,paused],
            'gates_released':[before['released'],after_wait['released'],after_pause['released']],
            'pilot_released':False,'probed_trajectories':probes,'simulated_signals':signals,
            'real_signals':0,'fake_pause_file':str(root/'phase2/autoresume_paused.json')}


def run(root,admission,*,real_adapters=False):
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('CUDA_VISIBLE_DEVICES must be empty')
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    runner=Path(__file__).with_name('runner.py');commands=[]
    def call(stage,scenario,extra=(),expected=0):
        argv=[sys.executable,str(runner),stage,'--work',str(root/scenario),
              '--admission',str(admission),'--engine','local-stub' if real_adapters and scenario=='full' else 'stub',*extra]
        p=subprocess.run(argv,capture_output=True,text=True,timeout=7200)
        name=f'{len(commands):02d}_{scenario}_{stage}'
        (root/(name+'.stdout')).write_text(p.stdout);(root/(name+'.stderr')).write_text(p.stderr)
        commands.append({'argv':argv,'returncode':p.returncode,'expected':expected,'log':name})
        if p.returncode!=expected:raise RuntimeError(f'dry-run command failed: {name}: {p.stderr[-1000:]}')
        return p
    call('G0_GENERATE','order',expected=1)
    call('sequence','full')
    call('T1','crash',('--crash','probe'),expected=1)
    call('T1','crash',('--recover',))
    call('sequence','stop',('--no-signal',))
    call('T3','stop',expected=1)
    receipts={stage:{'path':str(root/'full'/stage/'receipt.json'),
                     'sha256':digest(root/'full'/stage/'receipt.json'),
                     'status':read(root/'full'/stage/'receipt.json')['status']} for stage in STAGES}
    rows=read(root/'full/PILOT30/receipt.json')['result']['rows']+read(root/'full/PILOT60/receipt.json')['result']['rows']
    summary={'tldr':'Synthetic CPU stage sequence, extension, order rejection, crash recovery, and no-signal stop verified.',
             'synthetic':True,'CUDA_VISIBLE_DEVICES':os.environ['CUDA_VISIBLE_DEVICES'],
             'admission_sha256':digest(admission),'commands':commands,'stage_receipts':receipts,
             'synthetic_completed_updates':len(rows),'real_optimizer_steps':0,'model_generations':0,'gpu_allocations':0,
             'trajectories':sorted({f"{r['arm']}/{r['seed']}" for r in rows}),
             'T5_30':read(root/'full/T5_30/receipt.json')['result']['decision']['action'],
             'T5_60':read(root/'full/T5_60/receipt.json')['result']['decision']['action'],
             'T2_no_signal':read(root/'stop/T2/receipt.json')['status'],
             'crash_attempts':len(list((root/'crash/T1/probe').glob('attempt_*'))),
             'api_spend_usd':0,'is_gate_evidence':False}
    summary['single_pause']=single_pause(root/'single_pause_fixture',admission)
    if real_adapters:
        from local_engine import LocalEngine
        from pause_v3 import pause,VETO_END
        engine=LocalEngine(root/'full',admission,stub_engines=True)
        payload=read(root/'full/T2/update/intent.json')['payload']
        for row in [r for g in payload['groups'] for r in g][:3]:
            row['receipt'][0].update(certified=False,generator_logp=None)
        a4root=root/'A4_stop';a4root.mkdir()
        stopped=engine.measure('update',a4root,payload)
        assert stopped['status']=='STOP_V4_A4' and not (a4root/'export').exists()
        fake_v3=root/'pause_fixture';(fake_v3/'phase2').mkdir(parents=True)
        def busy(key,work):return {'pane_text':'waiting for an idle GPU','processes':[{'kind':'runner'},{'kind':'stage'}],'leases':[]}
        refused=pause(admission,work=fake_v3,veto_not_issued=True,now=VETO_END+1,probe=busy,
                      kill=lambda *a:(_ for _ in ()).throw(AssertionError('no process may be signalled')))
        assert set(refused.values())=={'WAIT_STAGE_RUNNING'} and not (fake_v3/'phase2/autoresume_paused.json').exists()
        summary.update(real_adapter_composition=True,A4_stop=stopped,pause_refusal=refused,
                       stage_subprocesses=len(list((root/'full').glob('**/launch.json'))))
    write_new(root/'summary.json',summary)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--admission',type=Path,required=True);p.add_argument('--real-adapters',action='store_true');a=p.parse_args()
    result=run(a.root,a.admission,real_adapters=a.real_adapters)
    print(json.dumps({k:v for k,v in result.items() if k not in ('commands','stage_receipts')}))
