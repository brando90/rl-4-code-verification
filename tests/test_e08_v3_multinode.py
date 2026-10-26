"""Check exact admission, foreign-work preservation and bounded private participants."""
import fcntl
import os
from pathlib import Path
import sys
import subprocess
import time
from contextlib import ExitStack
import pytest

HERE = Path(__file__).resolve().parents[1] / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3'
sys.path.insert(0, str(HERE))
import multinode_training as multi
import multinode_runtime as runtime

def inventory():
    return {host: {'host': host, 'interface': 'enp0', 'apps': [],
                  'devices': [{'index': i, 'uuid': f'GPU-{host}-{i}', 'total_mib': 150000,
                               'used_mib': 0, 'free_mib': 149000, 'utilization': 0}
                              for i in range(8)]} for host in multi.DEVICE_PLAN}

def test_exact_eight_device_plan_preserves_small_foreign_contexts():
    data = inventory()
    foreign = {'uuid': 'GPU-skampere2-3', 'pid': 123, 'uid': 999, 'memory_mib': 2000}
    data['skampere2']['apps'] = [foreign]
    data['skampere2']['devices'][3].update(used_mib=2000, free_mib=147000)
    result = multi.select_devices(data, [], {}, {})
    assert {host: a['gpus'] for host, a in result.items()} == multi.DEVICE_PLAN
    assert result['skampere2']['existing_contexts'] == [foreign]
    assert 0 not in result['skampere1']['gpus']

@pytest.mark.parametrize('field,value', [('used_mib', 4097), ('free_mib', 102399), ('utilization', 11)])
def test_sharing_refuses_changed_headroom_or_activity(field, value):
    data = inventory(); data['skampere2']['devices'][3][field] = value
    if field == 'used_mib': data['skampere2']['devices'][3]['free_mib'] = 140000
    with pytest.raises(multi.WaitingCapacity):
        multi.select_devices(data, [], {}, {})

def test_foreign_cuda_context_blocks_exclusive_devices_even_with_free_memory():
    data = inventory(); data['skampere1']['apps'] = [{'uuid': 'GPU-skampere1-1', 'pid': 123}]
    with pytest.raises(multi.WaitingCapacity):
        multi.select_devices(data, [], {}, {})

@pytest.mark.parametrize('host,index', [('skampere1', 1), ('skampere2', 0), ('skampere3', 0)])
def test_existing_e13_leases_fence_admission(host, index):
    lease = {'status': 'ACTIVE', 'host': host, 'index': index}
    with pytest.raises(multi.WaitingCapacity):
        multi.select_devices(inventory(), [lease], {}, {})

def test_local_and_remote_reservations_fence_admission():
    with pytest.raises(multi.WaitingCapacity):
        multi.select_devices(inventory(), [], {'x': {'gpus': [2]}}, {})
    with pytest.raises(multi.WaitingCapacity):
        multi.select_devices(inventory(), [], {}, {'skampere3': [7]})

def test_unresolved_or_duplicate_device_inventory_is_rejected():
    data = inventory(); data['skampere2']['devices'][3]['uuid'] = 'GPU-skampere1-1'
    with pytest.raises(AssertionError):
        multi.select_devices(data, [], {}, {})

def test_wrapper_preserves_native_training_and_exports():
    source = (HERE / 'train_continuation.sh').read_text()
    adapted = multi.wrapper_text(source)
    original_lines = source.splitlines(); adapted_lines = adapted.splitlines()
    changed = [(a, b) for a, b in zip(original_lines, adapted_lines) if a != b]
    assert len(original_lines) == len(adapted_lines) and len(changed) == 4
    assert all(a.lstrip().startswith(('HERE=', 'export CUDA_VISIBLE_DEVICES=', 'export RAY_ADDRESS=')) for a, _ in changed)
    assert 'export CUDA_VISIBLE_DEVICES=""' in adapted
    assert 'sft.max_num_steps="$K"' in adapted

def test_private_participant_expiry_and_normal_cleanup_grace(tmp_path):
    heartbeat = tmp_path / 'heartbeat'; heartbeat.touch()
    now = time.time(); plan = {'deadline_unix': now + 500, 'startup_deadline_unix': now + 100}
    assert not runtime.expired(tmp_path, plan, now)
    assert runtime.expired(tmp_path, plan, now + 101)
    (tmp_path / 'training_started').touch()
    assert not runtime.expired(tmp_path, plan, now + 101)
    assert runtime.expired(tmp_path, plan, now + 121)
    (tmp_path / 'STOP').touch()
    assert runtime.expired(tmp_path, plan, now + 1)
    assert not runtime.expired(tmp_path, plan, now + 1, cleanup_grace=True)
    assert runtime.expired(tmp_path, plan, now + 31, cleanup_grace=True)

def test_admission_lock_wait_has_a_finite_deadline(tmp_path):
    path = tmp_path / 'lock'
    with path.open('a') as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        with ExitStack() as stack, pytest.raises(TimeoutError):
            multi.acquire(stack, path, time.time() + .1)


def test_custom_interpreter_restores_the_full_host_lease_before_ray_import(tmp_path):
    adapter = tmp_path / 'python'
    adapter.write_text(runtime.gpu_interpreter_wrapper(sys.executable)); adapter.chmod(0o700)
    env = os.environ.copy(); env.update(CUDA_VISIBLE_DEVICES='7', E08_NODE_GPU_MASK='2,4,5,7')
    result = subprocess.check_output([str(adapter), '-c', 'import os,sys; print(os.environ["CUDA_VISIBLE_DEVICES"]); print(sys.argv[1])', 'preserved argument'],
                                     env=env, text=True)
    assert result.splitlines() == ['2,4,5,7', 'preserved argument']
    env.pop('E08_NODE_GPU_MASK')
    result = subprocess.run([str(adapter), '-c', 'raise AssertionError("must not execute")'],
                            env=env, capture_output=True, text=True)
    assert result.returncode != 0 and 'KeyError' in result.stderr
