"""TLDR: Materialize concrete v4 launch/watchdog argument vectors without sessions or cron changes."""
import argparse
from pathlib import Path
from common import write_new
from runner import STAGES

PYTHON='/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'
BASE=Path('/lfs/skampere1/0/brando9/rl4cv_e13v4')


def plans(root, *, base=BASE, admission_name="admission_dispatch8.json", deployment_suffix="_dispatch8"):
    root=Path(root).resolve();phase=root/'phase2';base=Path(base).resolve()
    admission=str(phase/admission_name);work=str(base/'run');session='rl4cv-e13v4-stages'
    common=['--work',work,'--admission',admission,'--engine','local']
    prefix=['env','HF_HUB_OFFLINE=1','PYTHONDONTWRITEBYTECODE=1','VLLM_USE_FLASHINFER_SAMPLER=0',
            'PYTHONPATH='+str(root.parents[2]/'src'),PYTHON,str(phase/'runner.py')]
    commands={stage:[*prefix,stage,*common] for stage in STAGES}
    launch={'tldr':'A3: gates after veto window and designated A_1302 pause; pilot after B_1301 verdict and all gates.',
            'condition':'e13v4','status':'PREPARED','admission':admission,'work':work,'session':session,
            'checkout':str(root.parents[2]),'v3_pilot_read_only':'/lfs/skampere1/0/brando9/rl4cv_e13v3/phase2/pilot',
            'stage_argv':commands,'sequence_argv':[*prefix,'sequence',*common,'--recover'],
            'gates_argv':[*prefix,'gates',*common],'pilot_argv':[*prefix,'pilot',*common],
            'progress_argv':[*prefix,'progress',*common],
            'recovery_inspect_argv':[PYTHON,str(phase/'recovery.py'),'--work',work],
            'device_lease':{'module':str(phase/'device_lease.py'),'callable':'allocation',
                            'guard':str(phase/'device_guard.py'),'locks':str(base/'leases'),
                            'hosts':{'skampere1':[0,5,7],'skampere2':'idle only','skampere3':'idle only'},
                            'duration_seconds':14400,'status':'connected to leased subprocesses'},
            'operational_pause':str(phase/'operational_pause.json'),'pilot_required_idle_devices':3,
            'schedule_amendment':'V4-A3','veto_end':'2026-10-21T12:00:00-07:00','master_go_required':True,'api_spend_usd':0}
    watchdog={'tldr':'One v4 stage controller; no cron or tmux session is installed by preparation.',
              'kind':'stage-controller','admission':admission,'work':work,'session':session,
              'resume_argv':[PYTHON,str(phase/'launch_control.py'),'--plan',str(base/f'launch_plan{deployment_suffix}.json')],
              'cadence_minutes':10,'infrastructure_attempt_cap':3,
              'stop':'failed gate, no signal, ambiguous effects, A4 cap, or terminal T5 decision'}
    return launch,watchdog


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--admission-name',default='admission_dispatch8.json')
    p.add_argument('--deployment-suffix',default='_dispatch8')
    a=p.parse_args()
    for name,value in zip(('launch_plan','watchdog_plan'),plans(a.root,admission_name=a.admission_name,deployment_suffix=a.deployment_suffix)):
        write_new(a.root/'phase2'/f'{name}.json',value)
        write_new(BASE/f'{name}{a.deployment_suffix}.json',value)
