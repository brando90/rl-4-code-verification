"""Check isolated cross-host Ray scheduling and native interpreters without GPUs or models."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import socket
import subprocess
import sys
import time

SHARED = Path('/dfs/scratch0/brando9/rl4cv_e08_v3_remote/sft_v3')
HOSTS = ('skampere1', 'skampere2', 'skampere3')
WORKER = 'nemo_rl.models.policy.dtensor_policy_worker.DTensorPolicyWorker'


def write(path, value):
    temp = path.with_suffix(f'.{os.getpid()}.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def identity(pid):
    stat = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
    return {'pid': pid, 'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'start_ticks': stat[19]}


def alive(record):
    try:
        return identity(record['pid']) == record and Path(f'/proc/{record["pid"]}/stat').read_text().rsplit(')', 1)[1].split()[0] != 'Z'
    except (FileNotFoundError, ProcessLookupError):
        return False


def group_members(leader):
    members = []
    for path in Path('/proc').glob('[0-9]*/stat'):
        try:
            fields = path.read_text().rsplit(')', 1)[1].split()
            if int(fields[2]) == leader and fields[0] != 'Z' and path.stat().st_uid == os.getuid():
                members.append(identity(int(path.parent.name)))
        except (FileNotFoundError, ProcessLookupError):
            pass
    return members


def signal_exact(record, sig):
    if not alive(record):
        return
    try:
        fd = os.pidfd_open(record['pid'])
    except OSError:
        if not alive(record):
            return
        raise
    try:
        if alive(record):
            try:
                signal.pidfd_send_signal(fd, sig)
            except ProcessLookupError:
                pass
    finally:
        os.close(fd)


def watchdog(root, host):
    """Bound a private keeper group even if the Ray constructor or cleanup hangs."""
    record = json.loads((root / f'{host}.json').read_text())
    owner = record['identity']
    deadline = record['started_unix'] + 240
    members = []
    while alive(owner) and time.time() < deadline:
        try:
            assert os.getpgid(owner['pid']) == owner['pid']
        except ProcessLookupError:
            break
        members = group_members(owner['pid'])
        time.sleep(1)
    if alive(owner):
        members = group_members(owner['pid'])
    for member in members:
        signal_exact(member, signal.SIGTERM)
    time.sleep(10)
    for member in members:
        signal_exact(member, signal.SIGKILL)
    write(root / f'{host}.watchdog.json', {
        'owner': owner, 'deadline_unix': deadline, 'ended_unix': time.time(),
        'terminated': members, 'remaining': [r for r in members if alive(r)]})


def environment(host):
    if host == 'skampere1':
        return Path('/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl')
    return Path(f'/lfs/{host}/0/brando9/rl4cv_e08_v3_env/nemo_rl')


def common_interpreter(host):
    common = Path(f'/tmp/e08v3_mn_{os.getuid()}')
    common.mkdir(mode=0o700, exist_ok=True)
    assert not common.is_symlink() and common.stat().st_uid == os.getuid()
    link = common / 'venvs'
    target = environment(host) / 'venvs'
    assert (target / WORKER / 'bin/python').is_file()
    if link.is_symlink():
        assert link.resolve() == target.resolve()
    else:
        assert not link.exists()
        link.symlink_to(target, target_is_directory=True)
    return link / WORKER / 'bin/python'


def keeper(root, head):
    from ray._private.node import Node
    from ray._private.parameter import RayParams
    host = socket.gethostname().split('.')[0]
    assert host in HOSTS and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    assert os.getpgrp() == os.getpid(), 'Keeper must own its process group'
    interpreter = common_interpreter(host)
    record = {'status': 'STARTING', 'host': host, 'identity': identity(os.getpid()),
              'interpreter': str(interpreter), 'gpu_count': 0, 'started_unix': time.time()}
    write(root / f'{host}.json', record)
    guard = subprocess.Popen([sys.executable, __file__, '--watchdog', host, '--root', str(root)],
                             start_new_session=True)
    node = None
    children = []
    try:
        params = dict(num_gpus=0, num_cpus=1, object_store_memory=134217728,
                      temp_dir=f'/tmp/e8mc_{os.getuid()}_{root.name[-8:]}',
                      node_ip_address=socket.gethostbyname(socket.gethostname()),
                      include_dashboard=False, include_log_monitor=False, no_monitor=True,
                      node_manager_port=0, object_manager_port=0,
                      dashboard_agent_listen_port=None, metrics_agent_port=None,
                      metrics_export_port=None, runtime_env_agent_port=None)
        params.update(gcs_server_port=0) if head else params.update(
            gcs_address=json.loads((root / 'skampere1.json').read_text())['gcs_address'])
        node = Node.__new__(Node)
        Node.__init__(node, RayParams(**params), head=head, shutdown_at_exit=True, spawn_reaper=True)
        children = [identity(p.process.pid) for values in node.all_processes.values() for p in values]
        record.update(status='READY', node_id=node.node_id, gcs_address=node.gcs_address,
                      session_name=node.session_name, children=children)
        write(root / f'{host}.json', record)
        deadline = record['started_unix'] + 240
        while time.time() < deadline and not (root / 'STOP').exists():
            time.sleep(1)
    except BaseException as error:
        record.update(status='ERROR', error=f'{type(error).__name__}: {error}')
    finally:
        try:
            if node is not None and hasattr(node, 'all_processes'):
                for values in node.all_processes.values():
                    for process in values:
                        if process.process.poll() is None:
                            children.append(identity(process.process.pid))
                node.kill_all_processes(check_alive=False, allow_graceful=True, wait=True)
            descendants = [r for r in group_members(os.getpid()) if r['pid'] != os.getpid()]
            record['terminated_remaining_group_members'] = descendants
            for child in descendants:
                signal_exact(child, signal.SIGTERM)
            if descendants:
                time.sleep(2)
            for child in descendants:
                signal_exact(child, signal.SIGKILL)
            limit = time.time() + 10
            while time.time() < limit:
                remaining = [r for r in group_members(os.getpid()) if r['pid'] != os.getpid()]
                remaining += [r for r in children if alive(r) and r not in remaining]
                if not remaining:
                    break
                time.sleep(.2)
            record['remaining_children'] = remaining
            if remaining:
                record.update(status='ERROR', cleanup_error='Owned children remain; watchdog retained')
            else:
                guard.terminate()
                guard.wait(timeout=5)
            record['watchdog_exit_code'] = guard.poll()
        except BaseException as error:
            record.update(status='ERROR', cleanup_error=f'{type(error).__name__}: {error}')
        record.update(status='STOPPED' if record['status'] == 'READY' else record['status'], ended_unix=time.time())
        write(root / f'{host}.json', record)
    return 0 if record['status'] == 'STOPPED' else 1


def wait_ready(root, host, deadline):
    while time.time() < deadline:
        path = root / f'{host}.json'
        record = json.loads(path.read_text()) if path.exists() else {}
        if record.get('status') == 'READY':
            return record
        if record.get('status') in ('ERROR', 'STOPPED'):
            raise RuntimeError(record)
        time.sleep(1)
    raise TimeoutError(f'{host} did not become ready')


def inspect_worker():
    import ray
    import torch
    import nemo_rl
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    source = Path(nemo_rl.__file__).parent
    return {'host': socket.gethostname().split('.')[0], 'python': sys.executable,
            'resolved_python': str(Path(sys.executable).resolve()), 'ray': ray.__version__,
            'torch': torch.__version__, 'nemo_source': str(source),
            'nemo_worker_sha256': hashlib.sha256((source / 'models/policy/dtensor_policy_worker.py').read_bytes()).hexdigest(),
            'gpu_ids': ray.get_gpu_ids(), 'cuda_initialized': torch.cuda.is_initialized()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keeper', action='store_true')
    parser.add_argument('--head', action='store_true')
    parser.add_argument('--root', type=Path)
    parser.add_argument('--watchdog', choices=HOSTS)
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['RAY_USAGE_STATS_ENABLED'] = '0'
    os.environ.pop('RAY_ADDRESS', None)
    if args.watchdog:
        watchdog(args.root, args.watchdog)
        return
    if args.keeper:
        return keeper(args.root, args.head)
    assert socket.gethostname().split('.')[0] == 'skampere1'
    root = SHARED / f'multinode_cpu_{int(time.time())}'
    root.mkdir()
    snapshot = root / Path(__file__).name
    snapshot.write_bytes(Path(__file__).read_bytes())
    processes = {}
    result = {'status': 'RUNNING', 'root': str(root), 'script_sha256': hashlib.sha256(snapshot.read_bytes()).hexdigest(),
              'gpu_count': 0, 'model_calls': 0, 'scientific_settings_changed': False, 'started_unix': time.time()}
    print(str(root), flush=True)
    import ray
    try:
        records = {}
        for host in HOSTS:
            command = ['setsid', '--wait', str(environment(host) / '.venv/bin/python'), str(snapshot), '--keeper', '--root', str(root)]
            if host == 'skampere1':
                command += ['--head']
            else:
                command = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', host, shlex.join(command)]
            with (root / f'{host}.log').open('w') as log:
                processes[host] = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            records[host] = wait_ready(root, host, time.time() + 60)
        result['keepers'] = records
        ray.init(address=records['skampere1']['gcs_address'], log_to_driver=False)
        assert ray.cluster_resources().get('GPU', 0) == 0
        assert len([n for n in ray.nodes() if n['Alive']]) == 3
        from ray.util.scheduling_strategies import NodeAffinitySchedulingStrategy
        interpreter = records['skampere1']['interpreter']
        assert {r['interpreter'] for r in records.values()} == {interpreter}
        fn = ray.remote(num_cpus=1, num_gpus=0)(inspect_worker)
        futures = [fn.options(scheduling_strategy=NodeAffinitySchedulingStrategy(r['node_id'], soft=False),
                              runtime_env={'py_executable': interpreter,
                                           'env_vars': {'CUDA_VISIBLE_DEVICES': '', 'NEMO_RL_VENV_DIR': str(Path(interpreter).parents[2])}}).remote()
                   for r in records.values()]
        result['workers'] = ray.get(futures, timeout=60)
        assert {r['host'] for r in result['workers']} == set(HOSTS)
        assert all(not r['gpu_ids'] and not r['cuda_initialized'] for r in result['workers'])
        assert len({(r['ray'], r['torch'], r['nemo_worker_sha256']) for r in result['workers']}) == 1
        result['status'] = 'PASS'
    except BaseException as error:
        result.update(status='FAIL', error=f'{type(error).__name__}: {error}')
    finally:
        cleanup_errors = []
        try:
            ray.shutdown()
        except BaseException as error:
            cleanup_errors.append(f'Ray driver shutdown failed: {error}')
        (root / 'STOP').touch()
        result['transport_exits'] = {}
        for host, process in processes.items():
            try:
                result['transport_exits'][host] = process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                cleanup_errors.append(f'{host} keeper transport {process.pid} has not exited; independent 240-second watchdog remains active')
        result['cleanup'] = {host: json.loads((root / f'{host}.json').read_text()) for host in HOSTS if (root / f'{host}.json').exists()}
        if (set(result['cleanup']) != set(processes) or set(result['transport_exits']) != set(processes)
                or any(code != 0 for code in result['transport_exits'].values())
                or not all(r['status'] == 'STOPPED' and r.get('remaining_children') == []
                           and r.get('watchdog_exit_code') is not None for r in result['cleanup'].values())):
            cleanup_errors.append('Some keepers failed or their exact child cleanup is unresolved')
        if cleanup_errors:
            result.update(status='FAIL', cleanup_errors=cleanup_errors)
        result['ended_unix'] = time.time()
        write(root / 'result.json', result)
        print(json.dumps(result, indent=2), flush=True)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
