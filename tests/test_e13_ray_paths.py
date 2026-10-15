"""Reproduce the installed Ray socket-path failure and verify the owned short-alias preflight without a device."""
from pathlib import Path
import hashlib
import json
import os
import socket
import subprocess
import sys

import pytest

PHASE = Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0, str(PHASE))
import ray_paths as m


def test_real_kernel_rejects_long_path_and_short_alias_preserves_target(tmp_path):
    target = tmp_path/('long-owned-directory-'*8)/'probabilities/ray'
    long_socket = target/m.SOCKET_SUFFIX
    long_socket.parent.mkdir(parents=True)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
        with pytest.raises(OSError): stream.bind(str(long_socket))
    # The fixture above remains untouched; the preflight uses its own empty target.
    destination = target/'next-stage'
    with m.short_directory(destination) as alias:
        assert alias.resolve() == destination.resolve()
        (alias/'retained.log').write_text('authored evidence')
        result = m.check_socket(alias)
        assert result['status'] == 'PASS' and result['socket_path_bytes'] <= 107
        assert not result['admission_statistics_computed'] and result['model_calls'] == 0
    assert not alias.exists()
    assert (destination/'retained.log').read_text() == 'authored evidence'
    assert long_socket.parent.exists()


def test_alias_conflict_is_preserved_and_exception_cleans_only_owned_alias(tmp_path):
    target = (tmp_path/'owned').resolve()
    token = hashlib.sha256(os.fsencode(target)).hexdigest()[:16]
    alias = Path('/tmp')/f'e13ray-{os.getuid()}-{token}'
    alias.write_text('other owner artifact')
    try:
        with pytest.raises(ValueError, match='another path or owner'):
            with m.short_directory(target): pass
        assert alias.read_text() == 'other owner artifact'
    finally:
        alias.unlink()
    with pytest.raises(RuntimeError, match='authored startup failure'):
        with m.short_directory(target) as owned:
            raise RuntimeError('authored startup failure')
    assert not owned.exists() and target.exists()


def test_installed_ray_validator_reproduces_exact_failure_and_accepts_preflight(tmp_path):
    python = Path(os.environ.get('E13_NEMO_PYTHON', '/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'))
    if not python.exists():
        if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION') == '1': pytest.fail('required installed Ray unavailable')
        pytest.skip('installed Ray unavailable')
    code = r'''
import sys
from pathlib import Path
from ray._private.utils import validate_socket_filepath
sys.path.insert(0, sys.argv[1])
import ray_paths
original='/lfs/skampere1/0/brando9/rl4cv_e13v2/phase2/technical/T1/attempt_1/probabilities/ray/session_2026-10-15_15-43-20_975929_2719354/sockets/plasma_store'
assert len(original.encode()) == 148
try: validate_socket_filepath(original)
except OSError as exc:
 assert 'AF_UNIX path length cannot exceed 107 bytes' in str(exc)
else: raise AssertionError('original installed failure not reproduced')
with ray_paths.short_directory(sys.argv[2]) as alias:
 validate_socket_filepath(str(alias/ray_paths.SOCKET_SUFFIX))
 assert ray_paths.check_socket(alias)['status']=='PASS'
 import ray
 try:
  ray.init(address='local',num_gpus=0,num_cpus=1,include_dashboard=False,
           object_store_memory=100*1024**2,_temp_dir=str(alias))
  assert ray.get(ray.remote(lambda: 'owned-cpu-health').remote())=='owned-cpu-health'
 finally:ray.shutdown()
print('original OSError reproduced; installed Ray and real socket preflight PASS; CPU actor completed; no device/model call')
'''
    result = subprocess.run([str(python), '-c', code, str(PHASE), str(tmp_path/'owned-ray')],
                            capture_output=True, text=True, timeout=90,
                            env={**os.environ, 'CUDA_VISIBLE_DEVICES': ''})
    assert result.returncode == 0, result.stdout+result.stderr
