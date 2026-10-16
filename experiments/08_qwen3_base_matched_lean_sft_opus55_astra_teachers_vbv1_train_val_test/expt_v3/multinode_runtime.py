"""Private Ray participants for the frozen eight-device continuation."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from probe_multinode_cpu import (alive, common_interpreter, environment, group_members,
                                identity, signal_exact, write, WORKER)


def expired(root, plan, now=None, *, cleanup_grace=False):
    now = time.time() if now is None else now
    heartbeat = root / 'heartbeat'
    stop = root / 'STOP'
    stopping = stop.exists() and (not cleanup_grace or now - stop.stat().st_mtime >= 30)
    startup_expired = (not (root / 'training_started').exists()
                       and now >= plan.get('startup_deadline_unix', plan['deadline_unix']))
    return (now >= plan['deadline_unix'] or startup_expired or stopping
            or not heartbeat.exists() or now - heartbeat.stat().st_mtime > 120)


def gpu_interpreter_wrapper(target):
    # Ray's custom-interpreter bootstrap can already have narrowed CUDA to one
    # assigned device. Restore this node's complete leased mask before Ray takes
    # its original-ID snapshot in the final interpreter; Ray then selects one.
    return ("#!/usr/bin/python3\nimport os,sys\n"
            "env=os.environ.copy()\nenv['CUDA_VISIBLE_DEVICES']=env['E08_NODE_GPU_MASK']\n"
            f"os.execve({str(target)!r}, [{str(target)!r}, *sys.argv[1:]], env)\n")


def aliases(host):
    interpreter = common_interpreter(host)
    common = Path(interpreter).parents[3]
    target = environment(host).parent / 'cache'
    link = common / 'cache'
    if link.is_symlink():
        assert link.resolve() == target.resolve()
    else:
        assert not link.exists()
        link.symlink_to(target, target_is_directory=True)
    gpu_root = Path(f'/tmp/e08v3_mg_{os.getuid()}')
    gpu_venvs = gpu_root / 'venvs'
    adapter = gpu_venvs / WORKER / 'bin/python'
    adapter.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    for path in (gpu_root, gpu_venvs, adapter.parent.parent, adapter.parent):
        assert not path.is_symlink() and path.stat().st_uid == os.getuid()
    body = gpu_interpreter_wrapper(interpreter)
    if adapter.exists():
        assert not adapter.is_symlink() and adapter.read_text() == body
    else:
        with adapter.open('x') as stream:
            stream.write(body)
        adapter.chmod(0o700)
    return str(adapter), str(gpu_venvs), str(link)


def watchdog(root, host):
    plan = json.loads((root / 'plan.json').read_text())
    record = json.loads((root / f'{host}.json').read_text())
    owner = record['identity']; members = []
    while alive(owner) and not expired(root, plan, cleanup_grace=True):
        assert os.getpgid(owner['pid']) == owner['pid']
        members = group_members(owner['pid'])
        time.sleep(1)
    if alive(owner):
        members = group_members(owner['pid'])
    for member in members:
        signal_exact(member, signal.SIGTERM)
    time.sleep(10)
    for member in members:
        signal_exact(member, signal.SIGKILL)
    until = time.monotonic() + 10
    while any(alive(r) for r in members) and time.monotonic() < until:
        time.sleep(.2)
    write(root / f'{host}.watchdog.json', {
        'owner': owner, 'deadline_unix': plan['deadline_unix'], 'ended_unix': time.time(),
        'terminated': members, 'remaining': [r for r in members if alive(r)]})


def keeper(root):
    from ray._private.node import Node
    from ray._private.parameter import RayParams
    host = socket.gethostname().split('.')[0]
    plan = json.loads((root / 'plan.json').read_text())
    allocation = plan['allocation'][host]
    assert os.getpgrp() == os.getpid() and not expired(root, plan)
    assert os.environ['CUDA_VISIBLE_DEVICES'] == ','.join(map(str, allocation['gpus']))
    interpreter, venvs, cache = aliases(host)
    os.environ.update(NEMO_RL_VENV_DIR=venvs, NCCL_IB_DISABLE='1',
                      NCCL_SOCKET_FAMILY='AF_INET', NCCL_SOCKET_IFNAME='=' + allocation['interface'],
                      GLOO_SOCKET_IFNAME=allocation['interface'], NCCL_CUMEM_ENABLE='1',
                      HF_HOME=cache + '/huggingface', HF_HUB_OFFLINE='1')
    os.environ['E08_NODE_GPU_MASK'] = os.environ['CUDA_VISIBLE_DEVICES']
    record = {'status': 'STARTING', 'host': host, 'identity': identity(os.getpid()),
              'gpus': ','.join(map(str, allocation['gpus'])), 'uuids': allocation['uuids'],
              'interpreter': interpreter, 'venvs': venvs, 'cache': cache,
              'started_unix': time.time(), 'deadline_unix': plan['deadline_unix']}
    write(root / f'{host}.json', record)
    guard = subprocess.Popen([sys.executable, __file__, '--watchdog', host, '--root', str(root)],
                             start_new_session=True)
    record['watchdog_identity'] = identity(guard.pid)
    write(root / f'{host}.json', record)
    node = None; children = []; remaining = []
    try:
        head = host == 'skampere1'
        params = dict(num_gpus=len(allocation['gpus']), num_cpus=len(allocation['gpus']) + 2,
                      object_store_memory=2 * 1024**3, temp_dir='/tmp/e8mt_' + root.name[-12:],
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
        while not expired(root, plan):
            time.sleep(1)
    except BaseException as error:
        record.update(status='ERROR', error=f'{type(error).__name__}: {error}')
    finally:
        try:
            if node is not None and hasattr(node, 'all_processes'):
                children.extend(identity(p.process.pid) for values in node.all_processes.values()
                                for p in values if p.process.poll() is None)
                try:
                    node.kill_all_processes(check_alive=False, allow_graceful=True, wait=True)
                except BaseException as error:
                    # Ray can raise SystemExit while disconnecting a worker node.
                    # Continue exact local cleanup and verify its actual outcome.
                    record['node_shutdown_warning'] = f'{type(error).__name__}: {error}'
            descendants = [r for r in group_members(os.getpid()) if r['pid'] != os.getpid()]
            for child in descendants:
                signal_exact(child, signal.SIGTERM)
            if descendants:
                time.sleep(2)
            for child in descendants:
                signal_exact(child, signal.SIGKILL)
            until = time.monotonic() + 10
            while time.monotonic() < until:
                remaining = [r for r in group_members(os.getpid()) if r['pid'] != os.getpid()]
                remaining += [r for r in children if alive(r) and r not in remaining]
                if not remaining:
                    break
                time.sleep(.2)
            record['remaining_children'] = remaining
            if remaining:
                record.update(status='ERROR', cleanup_error='Owned children remain; watchdog retained')
            else:
                guard.terminate(); guard.wait(timeout=5)
            record['watchdog_exit_code'] = guard.poll()
        except BaseException as error:
            record.update(status='ERROR', cleanup_error=f'{type(error).__name__}: {error}')
        record.update(status='STOPPED' if record['status'] == 'READY' else record['status'],
                      ended_unix=time.time())
        write(root / f'{host}.json', record)
    return 0 if record['status'] == 'STOPPED' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--watchdog')
    args = parser.parse_args()
    os.environ['RAY_USAGE_STATS_ENABLED'] = '0'
    os.environ.pop('RAY_ADDRESS', None)
    if args.watchdog:
        watchdog(args.root, args.watchdog)
        return 0
    return keeper(args.root)


if __name__ == '__main__':
    raise SystemExit(main())
