"""Retain measured device, processor, storage and elapsed costs and explicit prospective projections."""
from __future__ import annotations

import math
from pathlib import Path
import resource
import time


def snapshot(root):
    """Measure owned-directory bytes and this controller's waited-for child CPU usage."""
    root = Path(root)
    files = [p for p in root.rglob('*') if p.is_file() and not p.is_symlink()] if root.exists() else []
    stats = [p.stat() for p in files]
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {'monotonic_seconds': time.monotonic(), 'unix_seconds': time.time(),
            'own_user_seconds': own.ru_utime, 'own_system_seconds': own.ru_stime,
            'waited_child_user_seconds': children.ru_utime, 'waited_child_system_seconds': children.ru_stime,
            'logical_bytes': sum(s.st_size for s in stats), 'allocated_bytes': sum(s.st_blocks*512 for s in stats),
            'files': len(files), 'scope': str(root.resolve())}


def difference(before, after):
    if before['scope'] != after['scope']: raise ValueError('storage accounting scope changed')
    values = {k: after[k]-before[k] for k in ('monotonic_seconds', 'own_user_seconds', 'own_system_seconds',
              'waited_child_user_seconds', 'waited_child_system_seconds', 'logical_bytes', 'allocated_bytes', 'files')}
    if any(not math.isfinite(x) for x in values.values()) or any(values[k] < 0 for k in values if k.endswith('seconds')):
        raise ValueError('invalid elapsed or processor counters')
    return {'wall_seconds': values.pop('monotonic_seconds'), **values,
            'accounted_cpu_hours': sum(values[k] for k in values if k.endswith('seconds'))/3600,
            'cpu_scope': 'controller plus waited-for child usage; detached/unreaped service usage is not inferred',
            'storage_scope': before['scope'], 'storage_counts_symlink_targets': False}


def device_cost(leases, *, expected_ids, cleanup_receipts):
    expected = set(expected_ids)
    if not expected or len(expected) != len(expected_ids): raise ValueError('unique complete device lease cohort required')
    table = {r['id']: r for r in leases}
    if len(table) != len(leases) or set(table) != expected: raise ValueError('device lease accounting cohort changed')
    if set(cleanup_receipts) != expected:
        raise ValueError('every closed lease requires its retained cleanup evidence')
    total = 0.
    for row in leases:
        if row['owner'] != 'e13v2' or row['status'] != 'RELEASED' or cleanup_receipts[row['id']].get('verified') is not True:
            raise ValueError('all owned device leases must be closed with verified cleanup')
        hours = row['device_hours']
        if type(hours) not in (int, float) or not math.isfinite(hours) or hours < 0:
            raise ValueError('invalid measured lease duration')
        duration = (row['released_unix']-row['started_unix'])/3600
        if not math.isfinite(duration) or duration < 0 or abs(duration-hours) > 1e-9:
            raise ValueError('recorded device hours differ from the owned lease interval')
        total += hours
    return {'device_hours': total, 'leases': len(leases),
            'includes': 'all wall time between owned claim and verified release, including initialization, idle reservation and cleanup'}


def stage_cost(before, after, *, stage, lease=None, cleanup=None):
    """An absent or incomplete device receipt stays unknown; processor-only stages explicitly use no device."""
    result = {'condition': 'v2-S2', 'stage': stage, **difference(before, after),
              'admission_statistics_computed': False, 'status': 'RECORDED'}
    if lease is None:
        result.update(device_hours=0., device_scope='processor-only stage; no device lease')
    else:
        result['lease_id'] = lease['id']
        try:
            result.update(device_cost([lease], expected_ids=[lease['id']],
                                      cleanup_receipts={lease['id']: cleanup or {}}))
        except (ValueError, KeyError, TypeError) as exc:
            result.update(device_hours=None, status='INCOMPLETE_DEVICE_COST',
                          device_cost_error=str(exc))
    return result


REQUIRED = {'anchors', 'calibration_and_ability_fits', 'technical_gates', 'learning_pilot',
            'main_training', 'validation', 'selected_tests', 'coverage_and_audits'}
UNITS = ('device_hours', 'cpu_hours', 'wall_hours', 'storage_bytes')


def project(components, *, reserve_fraction=.25):
    """Project from explicit measured quantities; unknown costs prevent a claimed complete T4 plan."""
    if reserve_fraction != .25: raise ValueError('protocol requires 25 percent reserve')
    if {r['category'] for r in components} != REQUIRED:
        raise ValueError('all protocol cost categories must be explicitly accounted')
    names = [r['name'] for r in components]
    if len(names) != len(set(names)): raise ValueError('duplicate projected cost component')
    totals = dict.fromkeys(UNITS, 0.)
    rows = []; missing = []
    for entry in components:
        if entry.get('not_applicable'):
            if not entry.get('reason') or entry.get('planned_units') != 0:
                raise ValueError('omitted component needs an explicit zero-unit reason')
            rows.append({**entry, 'projected': dict.fromkeys(UNITS, 0.)}); continue
        n = entry['planned_units']; measured = entry['measured_units']
        if (type(n) not in (int, float) or type(measured) not in (int, float)
                or not math.isfinite(n) or not math.isfinite(measured) or n < 0 or measured <= 0):
            raise ValueError('nonnegative planned and positive measured denominators required')
        if not entry.get('evidence'): raise ValueError('cost projection requires measurement provenance')
        projected = {}
        for unit in UNITS:
            value = entry['measured_cost'].get(unit)
            if value is None:
                missing.append({'component': entry['name'], 'unit': unit}); projected[unit] = None; continue
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError('invalid measured cost')
            projected[unit] = value*n/measured
            totals[unit] += projected[unit]
        rows.append({**entry, 'projected': projected})
    # A subtotal must never be mistaken for an all-component allocation.
    partial = totals.copy()
    for unit in UNITS:
        if any(x['unit'] == unit for x in missing): totals[unit] = None
    return {'condition': 'v2-S2', 'status': 'COMPLETE_ESTIMATE' if not missing else 'INCOMPLETE_COSTS',
            'components': rows, 'missing': missing, 'measured_component_subtotals': partial,
            'totals_before_reserve': totals,
            'with_reserve': {k: None if v is None else 1.25*v for k, v in totals.items()},
            'reserve_fraction': .25, 'allocation_granted': False,
            'uncertainty': 'linear projections from named measured denominators; no population interval or guaranteed runtime',
            'wall_time_interpretation': 'sum of component wall times, not a parallel calendar-duration forecast'}
