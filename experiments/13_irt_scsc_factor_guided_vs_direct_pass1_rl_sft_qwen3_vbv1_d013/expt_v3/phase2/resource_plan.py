"""Project and cap the requested local pilot from retained train measurements with 25 percent reserve."""
from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

from technical import ROOT, V3, T2, T3, SOURCE
from cohort import digest
from training_checkpoint import write_new


def project(update_hours, generation_hours, evaluation_hours, native_bytes, export_bytes, raw_bytes):
    values = (update_hours, generation_hours, evaluation_hours, native_bytes, export_bytes, raw_bytes)
    if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError('positive finite measured resource quantities required')
    # Six matched 30-update runs, plus one possible 30-update extension for each B seed.
    # Validation: six 30-update checkpoints plus two possible extended B checkpoints.
    updates, validation_cells = 240, 8 * 135 * 8
    device = updates * (update_hours + generation_hours) + validation_cells / 8 * evaluation_hours
    # Latest native before/after and current export per run; one extra transition
    # per concurrent device. Raw generations, scores and batches are never retired.
    storage = 18 * native_bytes + 9 * export_bytes + updates * raw_bytes
    return {'condition': 'v3-A7', 'scope': 'requested local paired pilot and validation strict scoring',
            'maximum_updates': updates, 'maximum_validation_cells': validation_cells,
            'reserve_fraction': .25, 'projected_device_hours': device * 1.25,
            'device_hour_budget': 2100,
            'budget_derivation': 'fixed prospective ceiling: 240 updates times two GPU stages plus 40 validation segments, each bounded to four hours plus two minutes cleanup; rounded up to 2,100 hours, never an expected runtime',
            'projected_storage_bytes': math.ceil(storage * 1.25),
            'per_update_device_hours': update_hours + generation_hours,
            'api_spend_usd': 0,
            'official_SCSC': 'not included: validated coverage judge unavailable under local-only restriction',
            'main_and_sealed_test': 'outside this dispatch; no generation or allocation',
            'uncertainty': 'linear train-probe projection, not guaranteed runtime or GPU availability; 25 percent projection reserve; separate fixed stage-derived execution ceiling'}


def size(root):
    return sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())


def prepare():
    t4 = ROOT / 'phase2/technical/T4/attempt_1'
    for directory in (T2, T3):
        if json.loads((directory / 'result.json').read_text())['status'] != 'PASS':
            raise ValueError('preceding technical gate did not pass')
    probe = json.loads((t4 / 'result.json').read_text())
    if probe['status'] != 'COST_PROBE_MEASURED' or probe['declared'] != 8 or probe['measured'] != 8:
        raise ValueError('complete eight-cell cost probe required')
    update = json.loads((T2 / 'update/execution.json').read_text())
    generated = json.loads((SOURCE / 'costs/generate_update.json').read_text())
    plan = project(update['device_hours'], generated['device_hours'], probe['generation_cost']['device_hours'],
                   max(size(T2 / 'update/output/before'), size(T2 / 'update/output/after')),
                   size(T2 / 'export/output'),
                   size(SOURCE / 'generate_update/output') + size(SOURCE / 'score/cells')
                   + (T2 / 'update/output/batch.pt').stat().st_size)
    plan['measured_lean_cpu_hours_per_256'] = json.loads((SOURCE / 'costs/score.json').read_text())['accounted_cpu_hours']
    plan['projected_scoring_cpu_hours'] = 1.25 * (
        240 * plan['measured_lean_cpu_hours_per_256']
        + plan['maximum_validation_cells'] / 8 * probe['scoring_cost']['accounted_cpu_hours'])
    plan['free_storage_bytes_at_gate'] = shutil.disk_usage(ROOT).free
    plan['storage_fits'] = plan['projected_storage_bytes'] <= plan['free_storage_bytes_at_gate']
    sources = [T2 / 'result.json', T3 / 'result.json', t4 / 'result.json',
               T2 / 'update/execution.json', SOURCE / 'costs/generate_update.json', SOURCE / 'costs/score.json']
    plan['evidence'] = [{'path': str(p), 'sha256': digest(p)} for p in sources]
    write_new(t4 / 'pilot_projection.json', plan)
    fits = plan['storage_fits'] and plan['projected_device_hours'] <= plan['device_hour_budget']
    gate = {'condition': 'v3-A7', 'gate': 'T4', 'status': 'PASS' if fits else 'FAIL',
            'scope': plan['scope'], 'projection': plan, 'api_spend_usd': 0,
            'official_SCSC_status': 'UNMEASURED_COVERAGE_JUDGE_UNAVAILABLE',
            'full_original_phase2_allocation': False}
    write_new(t4 / 'gate.json', gate)
    write_new(V3 / 'results/T4_v3_local_cost_gate.json', gate)
    if gate['status'] != 'PASS': return gate
    admission = {'condition': 'v3-A7', 'status': 'ADMITTED', 'arms': ['B', 'A', 'P'], 'seeds': [1301, 1302],
                 'api_spend_usd': 0, 'projected_device_hours': plan['projected_device_hours'],
                 'device_hour_budget': plan['device_hour_budget'],
                 'gates': {name: {'path': str(p), 'sha256': digest(p)} for name, p in
                           [('T2', T2 / 'result.json'), ('T3', T3 / 'result.json'), ('T4', t4 / 'gate.json')]},
                 'bindings': [{'path': str(p), 'sha256': digest(p)} for p in sorted((V3 / 'phase2').glob('*.py'))],
                 'authority': 'explicit user dispatch of paired local-only pilot; original hosted coverage/mutation admission is not claimed',
                 'official_SCSC_status': 'PENDING_VALIDATED_LOCAL_OR_CACHED_COVERAGE'}
    write_new(ROOT / 'phase2/pilot_admission.json', admission)
    write_new(V3 / 'results/pilot_admission.json', admission)
    return gate


if __name__ == '__main__':
    print(json.dumps(prepare(), sort_keys=True))
