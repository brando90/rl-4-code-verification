"""TLDR: Execute each real component in an owned leased subprocess and retain launch/exit evidence."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from common import digest,write_new

CPU_STAGES={'score','audit_score','export'}


def command(config_path,*,synthetic=False):
    env={**os.environ,'HF_HUB_OFFLINE':'1','PYTHONDONTWRITEBYTECODE':'1',
         'VLLM_USE_FLASHINFER_SAMPLER':'0','VLLM_USE_V1':'1',
         'PATH':os.pathsep.join([str(Path.home()/'.elan/bin'),os.environ.get('PATH','/usr/bin:/bin')]),
         'PYTHONPATH':os.pathsep.join([str(Path(__file__).parent),str(Path(__file__).resolve().parents[4]/'src'),os.environ.get('PYTHONPATH','')])}
    argv=[sys.executable,str(Path(__file__).with_name('stage_worker.py')),'--config',str(config_path)]
    if synthetic:argv.append('--stub-engines');env['CUDA_VISIBLE_DEVICES']=''
    return argv,env


@contextmanager
def cpu_lease(root,synthetic):
    now=time.time();identity=f'e13v4-cpu-{os.getpid()}-{time.time_ns()}'
    path=Path(root)/'cpu.lease.json'
    write_new(path,{'owner':'e13v4','id':identity,'kind':'cpu','synthetic':synthetic,'status':'ACTIVE',
                    'started_unix':now,'expires_unix':now+4*3600})
    try:yield path
    finally:write_new(path.with_suffix('.end.json'),{'id':identity,'ended_unix':time.time(),'device_hours':0})


@contextmanager
def wait_allocation(work,admit):
    from device_lease import allocation
    from device_guard import Busy
    deadline=time.monotonic()+7*86400
    while True:
        manager=allocation(work,admit)
        try:lease=manager.__enter__()
        except Busy:
            if time.monotonic()>=deadline:raise
            print('waiting for an idle GPU',flush=True);time.sleep(30);continue
        try:yield lease
        except BaseException:
            if not manager.__exit__(*sys.exc_info()):raise
        else:manager.__exit__(None,None,None)
        return


MAX_LEASE_TRIALS = 120
LEASE_RETRY_SECONDS = 30


def execute(config, root, *, synthetic=False):
    from admission import check_admission
    from effect_receipts import LeaseRefused, worker_proof
    root = Path(root); root.mkdir(parents=True, exist_ok=False)
    check_admission(config['admission'], require_launch=not synthetic)
    for number in range(1, MAX_LEASE_TRIALS + 1):
        trial = root/'lease_trials'/f'trial_{number:04d}'
        trial.mkdir(parents=True)
        lease_context = cpu_lease(trial, synthetic) if synthetic or config['stage'] in CPU_STAGES else wait_allocation(
            Path(config['work']).parent/'leases', lambda: check_admission(config['admission'], require_launch=True))
        with lease_context as lease:
            cfg = {**config, 'lease_path': str(lease), 'stage_root': str(root/'output'),
                   'effect_root': str(trial), 'ray_temp': str(root/'ray'), 'synthetic': synthetic}
            write_new(trial/'runtime.json', cfg)
            argv, env = command(trial/'runtime.json', synthetic=synthetic)
            if synthetic or config['stage'] in CPU_STAGES: env['CUDA_VISIBLE_DEVICES'] = ''
            env['E13V4_EXECUTION_ID'] = json.loads(lease.read_text())['id']
            start = time.time()
            with (trial/'run.log').open('x') as log:
                child = subprocess.Popen(argv, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    ticks = Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
                    write_new(trial/'launch.json', {'argv': argv,
                        'environment': {k: env.get(k) for k in ('CUDA_VISIBLE_DEVICES', 'HF_HUB_OFFLINE',
                            'VLLM_USE_FLASHINFER_SAMPLER', 'VLLM_USE_V1', 'E13V4_EXECUTION_ID', 'PYTHONPATH', 'PATH')},
                        'pid': child.pid, 'start_ticks': ticks, 'started_unix': start, 'lease': str(lease),
                        'config_sha256': digest(trial/'runtime.json')})
                    code = child.wait(timeout=4*3600)
                except BaseException:
                    if child.poll() is None:
                        os.killpg(child.pid, signal.SIGTERM)
                        try: child.wait(timeout=30)
                        except subprocess.TimeoutExpired: os.killpg(child.pid, signal.SIGKILL); child.wait()
                    # Without a terminal worker proof this remains STOP_PARTIAL.
                    write_new(trial/'execution.json', {'exit_code': child.returncode,
                        'wall_seconds': time.time()-start, 'synthetic': synthetic, 'interrupted': True,
                        'device_seconds': 0 if synthetic or config['stage'] in CPU_STAGES else time.time()-start})
                    raise
            execution = {'exit_code': code, 'wall_seconds': time.time()-start, 'synthetic': synthetic,
                         'device_seconds': 0 if synthetic or config['stage'] in CPU_STAGES else time.time()-start}
            write_new(trial/'execution.json', execution)
            refused = bool(code) and worker_proof(trial, pre_engine=True)
            if not refused:
                # Keep existing component-cost and replay consumers compatible.
                write_new(root/'execution.json', execution)
                write_new(root/'runtime.json', cfg)
                if code: raise RuntimeError(f'{config["stage"]} failed ({code}); retained {trial / "run.log"}')
                result = json.loads((root/'output/component_result.json').read_text())
                if result.get('synthetic', False) != synthetic: raise ValueError('component mode mismatch')
                if not synthetic and config['stage'] not in CPU_STAGES:
                    from device_guard import census
                    uuid = json.loads(lease.read_text())['uuid']
                    for _ in range(30):
                        if not any(u == uuid for u, p in census()[1]): break
                        time.sleep(1)
                    else: raise RuntimeError('stage GPU workers remain; no next stage admitted')
                return result
        # The allocator has released both the lease and locks before the wait.
        write_new(trial/'retry.json', {'trial': number, 'limit': MAX_LEASE_TRIALS,
                  'lease_released': True, 'delay_seconds': LEASE_RETRY_SECONDS,
                  'consumed_a4_attempt': False})
        print(f'lease refused before engine: {trial}; retry {number}/{MAX_LEASE_TRIALS}', flush=True)
        if number < MAX_LEASE_TRIALS: time.sleep(LEASE_RETRY_SECONDS)
    raise LeaseRefused(f'pre-engine lease refusal cap ({MAX_LEASE_TRIALS}) reached; retained {root}')
