#!/usr/bin/env python3
"""Independently recompute every factor mean and conjunctive score from the published cell CSV."""
import csv
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'results'
rows=list(csv.DictReader((ROOT/'test_factor_cells_v2.csv').open()))
report=json.loads((ROOT/'test_eval_v2.json').read_text())
checks=[]
for label,result in report['systems'].items():
    for scope,summary in result['scopes'].items():
        cohort=[r for r in rows if r['system']==label and r['known']=='True' and (scope=='all' or int(r['core'])==int(scope=='core'))]
        assert len(cohort)==summary['n_known_cells']
        means={key:math.fsum(float(r[key]) for r in cohort)/len(cohort) if cohort else None for key in ('IC_tests','IC_proofs','fsc_compiled')}
        means['SCSC']=math.prod(means.values())**(1/3) if cohort else None
        for key,value in means.items():
            expected=summary['point_common_cohort'][key]
            assert (value is None and expected is None) or math.isclose(value,expected,rel_tol=1e-12,abs_tol=1e-12),(label,scope,key,value,expected)
        checks.append(dict(system=label,scope=scope,n=len(cohort),means=means))
receipt=dict(verdict='PASS',method='independent CSV reader, math.fsum factor means and geometric mean; absolute/relative tolerance 1e-12',n_cells=len(rows),checks=checks)
(ROOT/'independent_factor_check_v2.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(verdict='PASS',system_scope_checks=len(checks),factor_and_score_checks=4*len(checks),cells=len(rows))))
