"""Project resource costs from explicit bound receipt fields, retaining unknown quantities and every required category."""
from __future__ import annotations

import json
import math
from pathlib import Path

from training_checkpoint import digest
from costs import project,UNITS


def number(value,*,nonnegative=True):
    if type(value) not in (int,float) or not math.isfinite(value) or nonnegative and value<0:
        raise ValueError('cost receipt must contain a finite numeric quantity')
    return float(value)


def resolve(term,sources):
    """A missing recorded field remains unknown; a zero needs an explicit scope reason."""
    if 'zero_reason' in term:
        if set(term)!={'zero_reason'} or not isinstance(term['zero_reason'],str) or not term['zero_reason']:
            raise ValueError('zero cost requires its explicit non-applicable scope')
        return 0.,{'zero_reason':term['zero_reason']}
    if set(term)!={'source','field','scale'} or term['source'] not in sources:
        raise ValueError('cost term needs a bound receipt field and unit conversion')
    ref=sources[term['source']];path=Path(ref['path'])
    if digest(path)!=ref['sha256']:raise ValueError('measured cost receipt changed')
    value=json.loads(path.read_text())
    for key in term['field']:
        if isinstance(value,dict) and key in value:value=value[key]
        elif isinstance(value,list) and type(key) is int and 0<=key<len(value):value=value[key]
        else:value=None;break
    scale=number(term['scale'])
    if scale<=0:raise ValueError('cost unit conversion must be positive')
    result=None if value is None else number(value)*scale
    return result,{'receipt':ref,'field':term['field'],'scale':scale,'value':result}


def materialize(recipe,sources):
    """The recipe's planned populations and transformations must be frozen before gate measurements."""
    if recipe.get('condition')!='v2-S2' or recipe.get('reserve_fraction')!=.25:raise ValueError('cost recipe condition or reserve changed')
    components=[]
    for row in recipe['components']:
        if set(row['measured_cost'])!=set(UNITS):raise ValueError('every projected resource unit must remain explicit')
        denominator,denominator_evidence=resolve(row['measured_units'],sources)
        if denominator is None or denominator<=0:raise ValueError('positive measured projection denominator required')
        measured={};evidence=[denominator_evidence]
        for unit,terms in row['measured_cost'].items():
            if not terms:raise ValueError('cost unit cannot have an empty implicit-zero expression')
            quantities=[]
            for term in terms:
                value,receipt=resolve(term,sources);quantities.append(value);evidence.append(receipt)
            measured[unit]=sum(quantities) if all(v is not None for v in quantities) else None
        components.append({'name':row['name'],'category':row['category'],'planned_units':number(row['planned_units']),
            'measured_units':denominator,'measured_cost':measured,'evidence':evidence,
            'scope':row['scope'],'projection_assumption':row['projection_assumption']})
    result=project(components,reserve_fraction=.25)
    result['unreported_external_costs']=recipe.get('unreported_external_costs',[])
    return result


def gate(projection,measurements):
    """Cost completeness is the technical measurement gate; this does not invent a future idle allocation."""
    required={'device_hours_per_update','generated_tokens_per_device_second','lean_wall_seconds',
              'lean_cpu_hours','raw_storage_growth_bytes','native_checkpoint_bytes','export_bytes',
              'calibration_cpu_hours','evaluation_device_hours','evaluation_cpu_hours'}
    if set(measurements)!=required:raise ValueError('T4 lacks its mandatory measured quantities')
    missing=[]
    for name,value in measurements.items():
        if value is None:missing.append(name)
        else:number(value)
    if measurements['generated_tokens_per_device_second'] is not None and measurements['generated_tokens_per_device_second']<=0:
        missing.append('nonpositive generated-token throughput')
    if projection.get('condition')!='v2-S2' or projection.get('reserve_fraction')!=.25:raise ValueError('T4 projection changed')
    return {'condition':'v2-S2','gate':'T4','status':'PASS' if not missing and projection['status']=='COMPLETE_ESTIMATE' else 'INCONCLUSIVE',
            'admission_statistics_computed':True,'measurements':measurements,'missing_measurements':missing,
            'full_cost_projection':projection,'learning_allocation_admitted':False,
            'required_next':'publish a bounded learning-pilot allocation from these measured costs and current resource observations; re-estimate with actual per-arm pilot lengths before main',
            'threshold_source':'PROTOCOL section 6 and PLAN section 6: measure every named resource category, include 25 percent reserve; no fixed 260–350-hour cutoff',
            'uncertainty':'linear resource projection, not a statistical efficacy test or guarantee of future device availability'}
