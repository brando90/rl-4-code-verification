"""Derive technical cost quantities from unchanged closed-stage receipts and retained files without inventing missing usage."""
from __future__ import annotations

import math
from pathlib import Path
import re

from technical_driver import read
from training_checkpoint import digest


def quantity(value):
    if type(value) not in (int,float) or not math.isfinite(value) or value<0:
        raise ValueError('finite nonnegative measured resource quantity required')
    return float(value)


def closed_stages(references):
    """Only actual waited-for processor and closed-lease counters establish measured costs."""
    if not references or len({r['path'] for r in references})!=len(references):
        raise ValueError('unique nonempty stage receipt inventory required')
    totals={'device_hours':0.,'cpu_hours':0.,'wall_hours':0.};missing=[]
    for ref in references:
        value=read(ref)
        if value.get('condition')!='v2-S2':raise ValueError('cost receipt belongs to another condition')
        for unit,key,scale in [('device_hours','device_hours',1),('cpu_hours','accounted_cpu_hours',1),('wall_hours','wall_seconds',1/3600)]:
            observed=value.get(key)
            incomplete=(unit in ('cpu_hours','wall_hours') and value.get('cumulative_timing_complete') is False)
            if observed is None or incomplete:
                missing.append({'receipt':ref,'unit':unit,'reason':'unmeasured or resumed counters'});totals[unit]=None
            elif totals[unit] is not None:totals[unit]+=quantity(observed)*scale
            else:quantity(observed)
    return {'condition':'v2-S2','status':'COMPLETE' if not missing else 'INCOMPLETE','totals':totals,'missing':missing,
        'sources':references,'scope':'sum of bound stage counters; elapsed sum is not parallel calendar time'}


def retained_files(root):
    """Record logical copy footprint and inode-deduplicated local allocation; never traverse symlink targets."""
    root=Path(root)
    if not root.is_dir() or root.is_symlink():raise ValueError('owned physical artifact directory required')
    files=sorted(p for p in root.rglob('*') if p.is_file() and not p.is_symlink())
    if not files:raise ValueError('empty retained artifact inventory')
    seen=set();logical=allocated=0;inventory=[]
    for path in files:
        stat=path.stat();logical+=stat.st_size;key=(stat.st_dev,stat.st_ino)
        if key not in seen:allocated+=stat.st_blocks*512;seen.add(key)
        inventory.append({'path':str(path.resolve()),'sha256':digest(path),'logical_bytes':stat.st_size})
    return {'root':str(root.resolve()),'logical_copy_bytes':logical,'allocated_unique_inode_bytes':allocated,
        'files':len(files),'unique_inodes':len(seen),'inventory':inventory,'symlink_targets_counted':False}


def timed_processor(reference):
    """Parse a successful retained GNU-time receipt; missing detached usage remains outside the scope."""
    path=Path(reference['path'])
    if digest(path)!=reference['sha256']:raise ValueError('processor timing receipt changed')
    fields={}
    for line in path.read_text().splitlines():
        stripped=line.strip()
        for key,label in [('user','User time (seconds)'),('system','System time (seconds)'),
                          ('elapsed','Elapsed (wall clock) time (h:mm:ss or m:ss)'),('exit','Exit status')]:
            if stripped.startswith(label+':'):fields[key]=stripped[len(label)+1:].strip()
    if set(fields)!={'user','system','elapsed','exit'} or fields['exit']!='0':
        raise ValueError('complete successful processor timing receipt required')
    pieces=fields['elapsed'].split(':')
    if len(pieces) not in (2,3) or any(not re.fullmatch(r'\d+(?:\.\d+)?',p) for p in pieces):
        raise ValueError('invalid elapsed timing field')
    seconds=0.
    for piece in pieces:seconds=60*seconds+quantity(float(piece))
    return {'cpu_hours':(quantity(float(fields['user']))+quantity(float(fields['system'])))/3600,
        'wall_hours':seconds/3600,'source':reference,'scope':'GNU time process and waited-for descendants only'}


def mandatory_measurements(*,update_costs,update_result,generation_costs,generation_result,score_costs,raw_roots,
                           native_roots,export_root,calibration_timing,evaluation_costs):
    """Derive T4's required quantities; an unknown counter is preserved for the existing gate."""
    completed=read(update_result)
    if (completed.get('condition')!='v2-S2' or completed.get('status')!='MEASURED'
            or completed.get('optimizer_updates')!=1 or completed.get('counts',{}).get('declared_slots')!=256):
        raise ValueError('one actual complete technical optimizer update required for the per-update cost')
    update=closed_stages(update_costs);generation=closed_stages(generation_costs);score=closed_stages(score_costs)
    evaluation=closed_stages(evaluation_costs);tokens=read(generation_result)
    if tokens.get('condition')!='v2-S2' or tokens.get('status')!='COMPLETE' or tokens.get('declared')!=256 or tokens.get('completed')!=256:
        raise ValueError('complete fixed 256-response technical generation required')
    n=quantity(tokens['generated_tokens']);seconds=generation['totals']['device_hours']
    throughput=n/(seconds*3600) if seconds is not None and seconds>0 else None
    if not raw_roots or not native_roots:raise ValueError('raw and native storage inventories required')
    roots=[Path(p).resolve() for p in [*raw_roots,*native_roots,export_root]]
    if len(set(roots))!=len(roots) or any(a in b.parents or b in a.parents for i,a in enumerate(roots) for b in roots[i+1:]):
        raise ValueError('storage cohorts overlap')
    raw=[retained_files(p) for p in raw_roots];native=[retained_files(p) for p in native_roots];export=retained_files(export_root)
    calibration=timed_processor(calibration_timing)
    values={'device_hours_per_update':update['totals']['device_hours'],
        'generated_tokens_per_device_second':throughput,'lean_wall_seconds':None if score['totals']['wall_hours'] is None else score['totals']['wall_hours']*3600,
        'lean_cpu_hours':score['totals']['cpu_hours'],'raw_storage_growth_bytes':sum(v['logical_copy_bytes'] for v in raw),
        'native_checkpoint_bytes':max(v['logical_copy_bytes'] for v in native),'export_bytes':export['logical_copy_bytes'],
        'calibration_cpu_hours':calibration['cpu_hours'],'evaluation_device_hours':evaluation['totals']['device_hours'],
        'evaluation_cpu_hours':evaluation['totals']['cpu_hours']}
    evidence={'update':update,'update_result':update_result,'generation':generation,'generation_result':generation_result,'score':score,'evaluation':evaluation,
        'calibration':calibration,'raw':raw,'native':native,'export':export,
        'native_size_rule':'maximum measured retained native checkpoint; projected multiplicities stay explicit in the prospective recipe',
        'raw_size_rule':'logical bytes in disjoint, retained raw-only roots; native/export directories excluded',
        'device_update_scope':'named complete scheduled-update stages; includes generation, scoring reservation, update and export where named'}
    return values,evidence
