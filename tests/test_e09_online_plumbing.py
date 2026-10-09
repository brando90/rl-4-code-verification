"""TLDR: Native compile missingness and run-bound child registration negative controls."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

E = Path(__file__).resolve().parents[1] / 'experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/expt_v1'
sys.path.insert(0, str(E))
from scorer_online_e09 import response_from_native
import owned_processes as children


def native():
    return dict(compiles=True, n_examples=1, n_theorems_stated=2,
                n_theorems_proved=1, n_vacuous=0, IC_tests=1., IC_proofs=.5,
                kernel_probe_ok=True, kernel_n_unknown=0, unparseable_theorem_types=[])


def compile_record():
    return [{'result': {'success': True, 'log': 'warning: sorry', 'errors': 0}}]


def test_partial_kernel_factor_is_preserved():
    answer, log = response_from_native(native(), compile_record(), True, False)
    assert answer.ic_proofs == .5 and answer.fsc is None
    assert log == 'warning: sorry'


@pytest.mark.parametrize('fault', ['missing', 'timeout', 'infra', 'kernel', 'unknown', 'vacuity'])
def test_missing_native_measurement_blocks(fault):
    row, records = native(), compile_record()
    if fault == 'missing':
        records = []
    elif fault in ('timeout', 'infra'):
        records[0]['result'].update(success=False, log='timeout' if fault == 'timeout' else 'process killed')
    elif fault == 'kernel':
        row['kernel_probe_ok'] = False
    elif fault == 'unknown':
        row['kernel_n_unknown'] = 1
    else:
        row['unparseable_theorem_types'] = [0]
    with pytest.raises(RuntimeError):
        response_from_native(row, records, True, False)


def test_empty_extraction_is_known_gate_zero_not_missing_judge():
    answer, log = response_from_native({}, [], False, True)
    assert answer.ic_tests == 0 and answer.ic_proofs == 0 and answer.fsc is None
    assert answer.truncated and log == ''


def test_child_registered_before_exec_and_bad_identity_never_killed(tmp_path):
    (tmp_path / 'run_identity.json').write_text(json.dumps({'run_id': 'fixture'}))
    (tmp_path / 'child_receipts.json').write_text(json.dumps({'processes': []}))
    # Child verifies its own registration as its first useful action after exec.
    code = ('import json,os,pathlib; r=json.loads(pathlib.Path("child_receipts.json").read_text()); '
            'assert any(x["pid"]==os.getpid() for x in r["processes"]); print("registered-before-exec")')
    proc = children.spawn(['/usr/bin/python3', '-c', code], kind='fixture', root=tmp_path,
                          stdout=subprocess.PIPE, text=True, start_new_session=True)
    stdout, _ = proc.communicate(timeout=15)
    assert proc.returncode == 0 and stdout.strip() == 'registered-before-exec'
    record = json.loads((tmp_path / 'child_receipts.json').read_text())['processes'][0]
    wrong = {**record, 'start_ticks': 'impossible'}
    assert not children.alive(wrong)
    children.stop(record, root=tmp_path)
    assert not json.loads((tmp_path / 'child_receipts.json').read_text())['processes']
