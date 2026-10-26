"""Admit the fixed TP8 continuation across three prepared hosts with exact leases."""
from __future__ import annotations
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import socket
import subprocess
import sys
import threading
import time
from recovery_watch import ROOT, alive, identity, read, write
from probe_multinode_cpu import environment, wait_ready, group_members, signal_exact

HERE = Path(__file__).resolve().parent
SHARED = Path('/dfs/scratch0/brando9/rl4cv_e08_v3_remote')
RUNTIME = SHARED / 'sft_v3'
LOCAL_PIPELINE = Path('/lfs/skampere1/0/brando9/rl4cv_e08/pipeline')
E13 = Path('/lfs/skampere1/0/brando9/rl4cv_e13v2/leases')
DEVICE_PLAN = {'skampere1': [1, 2], 'skampere2': [3, 5], 'skampere3': [2, 4, 5, 7]}

class WaitingCapacity(RuntimeError):
    pass

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ssh(host, command, timeout=45):
    return subprocess.check_output(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                                    host, shlex.join(command)], text=True, timeout=timeout)

def acquire(stack, path, deadline):
    lock = stack.enter_context(path.open('a'))
    while time.time() < deadline:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return lock
        except BlockingIOError:
            time.sleep(.1)
    raise TimeoutError('Original admission deadline reached while acquiring locks')

def inspect_host(host):
    code = """
import json,os,socket,subprocess
from pathlib import Path
def run(*args):return subprocess.check_output(args,text=True,timeout=20)
devices=[]
for line in run('nvidia-smi','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits').splitlines():
 a=[x.strip() for x in line.split(',')]
 devices.append(dict(index=int(a[0]),uuid=a[1],total_mib=int(a[2]),used_mib=int(a[3]),free_mib=int(a[4]),utilization=int(a[5])))
apps=[]
for line in run('nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits').splitlines():
 a=[x.strip() for x in line.split(',')];p=Path('/proc')/a[1]
 fields=(p/'stat').read_text().rsplit(')',1)[1].split()
 apps.append(dict(uuid=a[0],pid=int(a[1]),memory_mib=int(a[2]),uid=p.stat().st_uid,start_ticks=fields[19],boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()))
ip=socket.gethostbyname(socket.gethostname())
interfaces=json.loads(run('ip','-j','-4','addr','show'))
interface=next(x['ifname'] for x in interfaces if any(v.get('local')==ip for v in x['addr_info']))
print(json.dumps(dict(host=socket.gethostname().split('.')[0],devices=devices,apps=apps,interface=interface)))
"""
    return json.loads(ssh(host, ['/usr/bin/python3', '-c', code]))

def select_devices(inventories, e13, local_leases, reserved):
    allocation = {}
    for host, chosen in DEVICE_PLAN.items():
        if any(r['status'] != 'RELEASED' and r['host'].split('.')[0] == host
               and (host != 'skampere1' or int(r['index']) in chosen) for r in e13):
            raise WaitingCapacity(f'{host}: existing E13 reservation')
        if host == 'skampere1' and any(set(chosen) & set(r['gpus']) for r in local_leases.values()):
            raise WaitingCapacity('Local E08 reservation')
        if set(chosen) & set(reserved.get(host, [])):
            raise WaitingCapacity(f'{host}: existing remote reservation')
        inventory = inventories[host]; devices = {d['index']: d for d in inventory['devices']}
        assert inventory['host'] == host and len(inventory['devices']) == 8 and set(devices) == set(range(8))
        assert len({d['uuid'] for d in devices.values()}) == 8
        assert all(d['uuid'].startswith('GPU-') and 0 <= d['used_mib'] + d['free_mib'] <= d['total_mib']
                   and 0 <= d['utilization'] <= 100 for d in devices.values())
        assert all(a['uuid'] in {d['uuid'] for d in devices.values()} for a in inventory['apps'])
        selected = [devices[i] for i in chosen]
        assert all(d['total_mib'] >= 79000 for d in selected)
        contexts = [a for a in inventory['apps'] if a['uuid'] in {d['uuid'] for d in selected}]
        if host == 'skampere2':
            # Cooperative sharing retains headroom for the existing small contexts.
            # Their processes and allocations are never changed or terminated.
            if any(d['used_mib'] > 4096 or d['free_mib'] < 102400 or d['utilization'] > 10 for d in selected):
                raise WaitingCapacity('H200 sharing headroom/low-utilization criterion unmet')
        elif contexts or any(d['used_mib'] != 0 for d in selected):
            raise WaitingCapacity(f'{host}: required exclusive devices busy')
        allocation[host] = {'gpus': chosen, 'uuids': [d['uuid'] for d in selected],
            'interface': inventory['interface'], 'inventory': selected,
            'existing_contexts': contexts, 'cooperative_sharing': host == 'skampere2'}
    assert sum(len(r['gpus']) for r in allocation.values()) == 8
    assert len({u for r in allocation.values() for u in r['uuids']}) == 8
    return allocation

def live_remote_reservations():
    result = {}; records = [read(p, {}) for p in RUNTIME.glob('remote_*.json')]
    for host in DEVICE_PLAN:
        candidates = [r for r in records if r.get('host') == host and r.get('identity') and r.get('gpus')]
        code = ("import sys,json;sys.path.insert(0," + repr(str(SHARED / 'code/expt_v3')) + ");"
                "from recovery_watch import alive;records=" + repr(candidates) + ";"
                "print(json.dumps([r['gpus'] for r in records if alive(r['identity'])]))")
        result[host] = [int(x) for group in json.loads(ssh(host, ['/usr/bin/python3', '-c', code]))
                        for x in group.split(',') if x]
    return result

def probe_cluster(records, plan):
    import ray
    from ray.util.scheduling_strategies import NodeAffinitySchedulingStrategy
    class Probe:
        def inspect(self):
            import torch
            import socket
            import os
            from pathlib import Path
            self.torch = torch; torch.cuda.set_device(0)
            assert torch.cuda.device_count() == 1
            stat = Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')', 1)[1].split()
            return {'host': socket.gethostname().split('.')[0],
                'uuid': 'GPU-' + str(torch.cuda.get_device_properties(0).uuid).removeprefix('GPU-'),
                'pid': os.getpid(), 'start_ticks': stat[19],
                'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                'torch': torch.__version__, 'nccl': list(torch.cuda.nccl.version()),
                'interface': os.environ.get('NCCL_SOCKET_IFNAME')}
        def collective(self, rank, address):
            import torch.distributed as dist
            from datetime import timedelta
            torch = self.torch
            dist.init_process_group('nccl', init_method='tcp://' + address, rank=rank,
                                    world_size=8, timeout=timedelta(seconds=45))
            try:
                x = torch.full((262144,), float(rank + 1), device='cuda', dtype=torch.bfloat16)
                dist.all_reduce(x); torch.cuda.synchronize(); assert torch.all(x == 36).item()
                values = [torch.empty(1, device='cuda') for _ in range(8)]
                dist.all_gather(values, torch.tensor([float(rank)], device='cuda'))
                assert [v.item() for v in values] == list(range(8))
                x = torch.tensor([42. if rank == 0 else -1.], device='cuda')
                dist.broadcast(x, 0); assert x.item() == 42.; dist.barrier()
                return {'rank': rank, 'status': 'PASS'}
            finally:
                dist.destroy_process_group()
    actors = []; workers = []
    try:
        for host, record in records.items():
            for _ in plan['allocation'][host]['gpus']:
                actor = ray.remote(num_cpus=1, num_gpus=1)(Probe).options(
                    scheduling_strategy=NodeAffinitySchedulingStrategy(record['node_id'], soft=False),
                    runtime_env={'py_executable': record['interpreter'],
                                 'env_vars': {'NEMO_RL_VENV_DIR': record['venvs']}}).remote()
                actors.append(actor)
        workers = ray.get([a.inspect.remote() for a in actors], timeout=90)
        expected = {(host, uuid) for host, a in plan['allocation'].items() for uuid in a['uuids']}
        assert len(workers) == len(expected) == 8 and {(w['host'], w['uuid']) for w in workers} == expected
        with socket.socket() as s:
            s.bind(('', 0)); port = s.getsockname()[1]
        address = f'{socket.gethostbyname(socket.gethostname())}:{port}'
        outcomes = ray.get([a.collective.remote(i, address) for i, a in enumerate(actors)], timeout=90)
        return {'status': 'PASS', 'workers': workers, 'collectives': outcomes,
                'world_size': 8, 'tensor_parallel_size': 8, 'training_updates': 0}
    finally:
        for actor in actors:
            ray.kill(actor, no_restart=True)
        until = time.time() + 30
        while time.time() < until and ray.available_resources().get('GPU', 0) < 8:
            time.sleep(.2)
        assert ray.available_resources().get('GPU', 0) == 8, 'Probe actors did not release their resources'
        for host in records:
            selected = [w for w in workers if w['host'] == host]
            code = ("import sys,json,time;sys.path.insert(0," + repr(str(SHARED / 'code/expt_v3')) + ");"
                    "from recovery_watch import alive;workers=" + repr(selected) + ";"
                    "print(json.dumps([w for w in workers if alive(w)]))")
            assert not json.loads(ssh(host, ['/usr/bin/python3', '-c', code])), 'Probe process still alive'

def wrapper_text(source):
    assert source.count('export RAY_ADDRESS=local') == 1
    assert source.count('export CUDA_VISIBLE_DEVICES="$GPUS"') == 2
    source = source.replace('export RAY_ADDRESS=local', 'export RAY_ADDRESS="$E08_RAY_ADDRESS"')
    source = source.replace('export CUDA_VISIBLE_DEVICES="$GPUS"', 'unset CUDA_VISIBLE_DEVICES')
    return '\n'.join('HERE=' + shlex.quote(str(HERE)) if line.startswith('HERE=') else line
                     for line in source.splitlines()) + '\n'

def run_once(condition, probe_only=False):
    import ray
    sys.path.insert(0, str(HERE.parent / 'expt_v1/scripts'))
    import gpu_lease_e08 as leases
    assert leases.P == LOCAL_PIPELINE
    deadline = read(ROOT / 'recovery_config.json')['recovery_deadline_unix']
    assert time.time() < deadline
    canonical = RUNTIME / f'remote_{condition}_14b.json'
    if canonical.exists():
        raise WaitingCapacity('Canonical admission exists; preserve its owner')
    model_cache = None
    if not probe_only:
        from warm_multinode_model import warm
        model_cache = warm(deadline)
    root = RUNTIME / f'multinode_{condition}_14b_{time.time_ns()}'; root.mkdir()
    plan = {'condition': condition, 'deadline_unix': deadline, 'probe_only': probe_only,
            'identity': identity(os.getpid()), 'created_unix': time.time(),
            'startup_deadline_unix': min(deadline, time.time() + 300),
            'planning_peak_memory_gib_per_rank': 73.18, 'memory_estimate_is_upper_bound': False,
            'foreign_process_changes_authorized': False, 'scientific_configuration_changed': False,
            'model_cache_read': model_cache}
    stop = threading.Event()
    def heartbeat():
        while not stop.is_set():
            (root / 'heartbeat').touch(); stop.wait(5)
    (root / 'heartbeat').touch()
    pulse = threading.Thread(target=heartbeat, daemon=True); pulse.start()
    processes = {}; records = {}; participant_paths = []; local_lease = None; child = None; training_members = []
    result = {'status': 'STARTING', 'root': str(root), 'started_unix': time.time(), 'condition': condition}
    try:
        with ExitStack() as stack:
            for path in (E13 / 'registry.lock', leases.LOCK, RUNTIME / 'remote_admission.lock'):
                acquire(stack, path, plan['startup_deadline_unix'])
            if canonical.exists():
                raise WaitingCapacity('Canonical admission appeared; preserve it')
            inventory = {host: inspect_host(host) for host in DEVICE_PLAN}
            ready = read(RUNTIME / 'remote_ready.json')
            assert ready['status'] == 'PASS' and {'skampere2', 'skampere3'} <= set(ready['verified_hosts'])
            for name in (f'configs/e08_v3_{condition}_14B.yaml', f'results/sft_schedule_v3_{condition}.json'):
                assert digest(HERE / name) == ready['input_hashes'][name]
            data_name = f's_v3_{condition}_nemo.jsonl'
            assert digest(RUNTIME / data_name) == ready['input_hashes'][data_name]
            plan['allocation'] = select_devices(inventory, read(E13 / 'registry.json')['leases'],
                                                leases.live_leases(leases.load()), live_remote_reservations())
            assert os.statvfs(SHARED).f_bavail * os.statvfs(SHARED).f_frsize >= 1100 * 1024**3
            plan['source_sha256'] = {name: digest(HERE / name) for name in
                ('multinode_training.py', 'multinode_runtime.py', 'probe_multinode_cpu.py', 'train_continuation.sh',
                 f'configs/e08_v3_{condition}_14B.yaml')}
            write(root / 'plan.json', plan)
            for name in ('multinode_training.py', 'multinode_runtime.py', 'probe_multinode_cpu.py'):
                (root / name).write_bytes((HERE / name).read_bytes())
            for host, allocation in plan['allocation'].items():
                command = ['setsid', '--wait', 'env', 'CUDA_VISIBLE_DEVICES=' + ','.join(map(str, allocation['gpus'])),
                    str(environment(host) / '.venv/bin/python'), str(root / 'multinode_runtime.py'), '--root', str(root)]
                argv = command if host == 'skampere1' else ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', host, shlex.join(command)]
                with (root / f'{host}.log').open('w') as log:
                    processes[host] = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=log,
                                                        stderr=subprocess.STDOUT, start_new_session=True)
                records[host] = wait_ready(root, host, min(deadline, time.time() + 90))
                participant = RUNTIME / f'remote_multinode_{condition}_14b_{host}.json'
                old = read(participant, {})
                if old:
                    assert old.get('status') == 'RELEASED', 'Prior participant requires reconciliation'
                write(participant, {'status': 'RUNNING', 'host': host, 'gpus': records[host]['gpus'],
                    'identity': records[host]['watchdog_identity'], 'root': str(root),
                    'deadline_unix': deadline, 'keeper': records[host]['identity']})
                participant_paths.append(participant)
            local_lease = 'e08-v3-multinode-' + root.name
            registry = leases.load(); guard = records['skampere1']['watchdog_identity']
            registry[local_lease] = {'owner': 'e08-v3', 'stage': f'train_{condition}_14b_multinode',
                'gpus': DEVICE_PLAN['skampere1'], 'identity': leases.identity(guard['pid']), 'since': leases.ts(),
                'expires_utc': datetime.fromtimestamp(deadline, timezone.utc).isoformat(),
                'boundary': 'one frozen continuation and verified exports', 'released': False}
            leases.save(registry)
        os.environ.pop('CUDA_VISIBLE_DEVICES', None)
        for key in ('NCCL_SOCKET_IFNAME', 'GLOO_SOCKET_IFNAME', 'NCCL_IB_HCA', 'E08_NODE_GPU_MASK'):
            os.environ.pop(key, None)
        ray.init(address=records['skampere1']['gcs_address'], log_to_driver=False)
        assert ray.cluster_resources().get('GPU') == 8
        proof = probe_cluster(records, plan); write(root / 'gpu_proof.json', proof); result['gpu_proof'] = proof
        print(json.dumps({'status': 'EIGHT_DEVICE_PROOF_PASS', 'root': str(root)}), flush=True)
        if not probe_only:
            wrapper = root / 'train_multinode.sh'; wrapper.write_text(wrapper_text((HERE / 'train_continuation.sh').read_text()))
            env = os.environ.copy(); env.update(E08_WORK=str(SHARED), E08_NEMO_ROOT=str(environment('skampere1')),
                E08_CACHE_ROOT=records['skampere1']['cache'], NEMO_RL_VENV_DIR=records['skampere1']['venvs'],
                E08_RAY_ADDRESS=records['skampere1']['gcs_address'], NCCL_IB_DISABLE='1', NCCL_SOCKET_FAMILY='AF_INET')
            receipt = RUNTIME / f'remote_{condition}_14b.exit.json'
            with (RUNTIME / 'remote_admission.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX); assert not canonical.exists()
                with (RUNTIME / f'remote_{condition}_14b.log').open('a') as log:
                    child = subprocess.Popen(['/usr/bin/python3', str(HERE / 'job_process.py'), '--receipt', str(receipt),
                        '--', 'bash', str(wrapper), condition, '14b', '0,1,2,3,4,5,6,7'], env=env,
                        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                write(canonical, {'status': 'RUNNING', 'host': 'skampere1', 'identity': identity(child.pid),
                    'gpus': '1,2', 'tensor_parallel_size': 8, 'route': 'multinode_2_2_4',
                    'allocation': plan['allocation'], 'started_unix': time.time(), 'receipt': str(receipt),
                    'wrapper_snapshot': str(wrapper), 'wrapper_sha256': digest(wrapper), 'root': str(root),
                    'gpu_proof_sha256': digest(root / 'gpu_proof.json')})
                (root / 'training_started').touch()
            while child.poll() is None and time.time() < deadline:
                training_members = group_members(child.pid)
                assert all(read(root / f'{host}.json').get('status') == 'READY' for host in records)
                time.sleep(5)
            assert child.poll() == 0, 'Native training failed or original deadline reached; reconcile exact receipt'
            result['native_exit'] = read(receipt)
        result['status'] = 'PASS'
    except WaitingCapacity:
        result['status'] = 'WAITING_CAPACITY'; raise
    except BaseException as error:
        result.update(status='FAIL', error=f'{type(error).__name__}: {error}'); raise
    finally:
        (root / 'STOP').touch()
        for member in training_members:
            signal_exact(member, signal.SIGTERM)
        ray.shutdown()
        exits = {}
        for host, process in processes.items():
            try:
                exits[host] = process.wait(timeout=40)
            except subprocess.TimeoutExpired:
                exits[host] = None
        for member in training_members:
            signal_exact(member, signal.SIGKILL)
        cleanup = {host: read(root / f'{host}.json', {}) for host in processes}
        clean = (all(v == 0 for v in exits.values()) and all(r.get('status') == 'STOPPED'
                 and r.get('remaining_children') == [] and r.get('watchdog_exit_code') is not None for r in cleanup.values()))
        if clean:
            with (RUNTIME / 'remote_admission.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                for path in participant_paths:
                    record = read(path); record.update(status='RELEASED', released_unix=time.time()); write(path, record)
            if local_lease:
                with leases.LOCK.open('a') as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX); registry = leases.load()
                    registry[local_lease].update(released=True, released_at=leases.ts()); leases.save(registry)
        else:
            result.update(status='FAIL', cleanup_error='Unresolved owned participants; exact reconciliation required')
        result.update(transport_exits=exits, cleanup=cleanup, ended_unix=time.time())
        write(root / 'result.json', result); stop.set(); pulse.join(timeout=6)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('condition', choices=['E', 'R'])
    parser.add_argument('--probe-only', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run_once(args.condition, args.probe_only), indent=2), flush=True)

if __name__ == '__main__':
    main()
