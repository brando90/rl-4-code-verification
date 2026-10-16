"""Analyze the complete v2 panel, four prespecified sensitivities, paired changes and every frozen prediction."""
import argparse
from collections import Counter
import json
from pathlib import Path
import numpy as np
from adapter_v2 import map_symbols, is_helper
from support_v2 import PHASE, V1, WORK, V1_WORK, digest, verify_inputs, atomic_json
from analyze_e12 import SEED, DRAWS, FACTORS, scsc, p1, p23 as p23_v1, system_table as table_v1, interval


def cohort(rows, any_evaluable=False):
    """Retain the entire resampling frame while marking the prespecified measured cohort."""
    return [{**r, 'applicable':r['applicable'] if any_evaluable else r['fully_applicable'],
             'hidden_all_pass':r['hidden_all_evaluable_pass'] if any_evaluable else r['hidden_all_pass']}
            for r in rows]


def p23(rows, rng, draws=DRAWS, any_evaluable=False, **kwargs):
    result = p23_v1(cohort(rows, any_evaluable), rng, draws=draws, **kwargs)
    result['cohort'] = 'at least one evaluable' if any_evaluable else 'fully applicable'
    result['unambiguous_steps'] = [1, '2a', '2b'] if kwargs.get('unambiguous') else None
    return result


def system_table(rows):
    result = table_v1(rows)
    for out in result:
        rr = [r for r in rows if (r['panel'],r['system']) == (out['panel'],out['system'])]
        comp = [r for r in rr if r['compiles'] is True and r['n_tests'] > 0]
        out.update(n_compiling_with_tests=len(comp), n_fully_applicable=sum(r['fully_applicable'] for r in comp),
                   n_any_evaluable=sum(r['applicable'] for r in comp))
        out['fully_applicable_share'] = out['n_fully_applicable']/len(comp) if comp else None
        out['any_evaluable_share'] = out['n_any_evaluable']/len(comp) if comp else None
        out['mapping_step_counts'] = dict(Counter(str(s) for r in rr for s in r['mapping_steps']))
        passes=sum(r['hidden_all_pass']==1 for r in rr)
        unknown=sum(r['hidden_all_pass'] is None for r in rr)
        out['hidden_bounds_all_declared']=[passes/len(rr),(passes+unknown)/len(rr)]
    return result


def fraction_ci(rows, numerator, denominator, rng, draws=DRAWS):
    tasks = sorted({r['task_id'] for r in rows}); idx = {t:i for i,t in enumerate(tasks)}
    a = np.zeros(len(tasks)); b = a.copy()
    for r in rows:
        if denominator(r):
            b[idx[r['task_id']]] += 1
            a[idx[r['task_id']]] += int(numerator(r))
    values = []
    for _ in range(draws):
        ii = rng.integers(0,len(tasks),len(tasks)); den = b[ii].sum()
        values.append(float(a[ii].sum()/den) if den else None)
    return {'n':int(a.sum()), 'denominator':int(b.sum()), 'fraction':float(a.sum()/b.sum()) if b.sum() else None,
            'task_bootstrap_95':interval(values), 'p_value':'n/a'}


def paired_rows(rows, old, suites):
    changed = []; inspected = []; census = Counter()
    inspections = json.loads((V1/'results/disagreements_e12.json').read_text())['rows']
    lookup = {(r['system'],r['task_id']):r for r in inspections}
    for row in rows:
        key = (row['system'],row['task_id']); before = old[key]
        if not row.get('receipt'):
            continue
        old_receipt = json.loads(Path(before['receipt']).read_text())
        static, diag, _ = map_symbols(suites[row['task_id']]['symbols'],Path(row['path']).read_text())
        census['n_cells'] += 1
        census['fully_mapped'] += len(static) == len(suites[row['task_id']]['symbols'])
        census['probe'] += any(d['status']=='needs_probe' for d in diag)
        census['none'] += not bool(static) and not any(d['status']=='needs_probe' for d in diag)
        common = static.keys() & old_receipt['mapping'].keys()
        is_changed = any(static[k] != old_receipt['mapping'][k] for k in common)
        pair = {'system':row['system'],'task_id':row['task_id'],'scsc':scsc(row),
                'v1_hidden_all_pass':before['hidden_all_pass'],'v2_hidden_all_pass':row['hidden_all_pass'],
                'v1_hidden_pass_rate':before['hidden_pass_rate'],'v2_hidden_pass_rate':row['hidden_pass_rate'],
                'v1_fully_applicable':before['n_applicable']==before['n_tests'],
                'v2_fully_applicable':row['fully_applicable'],
                'v1_mapping':old_receipt['mapping'],'v2_mapping':row['mapping'],
                'v2_n_pass':row['n_pass'],'v2_n_evaluable':row['n_evaluable'],
                'v2_helper_mapped_failure':row['hidden_all_pass']==0 and any(is_helper(v) for v in row['mapping'].values())}
        if is_changed:
            changed.append(pair)
        if key in lookup:
            inspected.append({**pair,'v1_category':lookup[key]['category'],'v1_group':lookup[key]['group']})
    assert len(changed)==379 and len(inspected)==20
    return changed, inspected, dict(census)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--work',type=Path,default=WORK)
    args=parser.parse_args();verify_inputs()
    complete=json.loads((PHASE/'results/evaluation_complete_v2.json').read_text())
    source=args.work/'cells_v2.jsonl'
    assert complete['complete'] and digest(source)==complete['outcomes_sha256']
    rows=[json.loads(line) for line in source.read_text().splitlines()]
    assert len(rows)==9856 and len({(r['system'],r['task_id']) for r in rows})==9856
    rng=np.random.default_rng(SEED)
    result={'settings':{'seed':SEED,'draws':DRAWS,'bootstrap_unit':'paired task clusters; all systems retained',
                       'p_value':'n/a','repeat_scoring':'one frozen saved candidate per cell; no new scoring',
                       'P1_definition':'version-1 common score-factor cohort, hidden mean over its observed subset',
                       'P2_definition':'pooled ROC area on within-system normalized midranks, recomputed in each draw',
                       'P3_definition':'pooled correlation of within-system normalized score and graded-outcome midranks'},
            'outcomes_sha256':digest(source),'systems':system_table(rows)}
    result['P1']=p1(rows,rng);print('P1 complete',flush=True)
    result['P2_P3']=p23(rows,rng);print('P2/P3 complete',flush=True)
    result['S_V2a']=p23(rows,rng,any_evaluable=True)
    result['S_V2b']=p23(rows,rng,unambiguous=True)
    result['S_V2c']=p1(rows,rng,sensitivity=True);print('S-V2a through c complete',flush=True)
    old_path=V1_WORK/'cells_e12.jsonl'
    old_completion=json.loads((V1/'results/evaluation_complete.json').read_text())
    assert digest(old_path)==old_completion['outcomes_sha256']
    old_all=[json.loads(line) for line in old_path.read_text().splitlines()]
    old={(r['system'],r['task_id']):r for r in old_all if r['panel']=='primary'}
    assert len(old)==9856
    common={(r['system'],r['task_id']) for r in rows if r['fully_applicable']
            and old[r['system'],r['task_id']]['n_applicable']==old[r['system'],r['task_id']]['n_tests']}
    # Preserve all task clusters in the frame; mask scores/outcomes outside the paired cohort.
    def common_rows(rr, version1=False):
        out=[]
        for r in rr:
            keep=(r['system'],r['task_id']) in common
            r={**r,'fully_applicable':keep,'applicable':keep}
            if not keep:r.update({f:None for f in FACTORS});r.update(hidden_all_pass=None,hidden_pass_rate=None)
            if version1:r['hidden_all_evaluable_pass']=r['hidden_all_pass']
            out.append(r)
        return out
    paired_v1=common_rows(list(old.values()),True);paired_v2=common_rows(rows)
    result['S_V2d']={'n_common_cells':len(common),'v1':{'P1':p1(paired_v1,np.random.default_rng(SEED)),
        'P2_P3':p23(paired_v1,np.random.default_rng(SEED))},'v2':{'P1':p1(paired_v2,np.random.default_rng(SEED)),
        'P2_P3':p23(paired_v2,np.random.default_rng(SEED))}}
    suites={r['task_id']:r for r in json.loads((V1/'results/hidden_tests_manifest.json').read_text())['tasks']}
    changed,inspected,census=paired_rows(rows,old,suites)
    result['S_V2d'].update(changed_entry_points=changed,inspected_v1_rows=inspected)
    result['census_consistency']={'observed':census,'expected':{'n_cells':4626,'fully_mapped':3121,'probe':263,'none':927},
                                 'holds':census=={'n_cells':4626,'fully_mapped':3121,'probe':263,'none':927},'p_value':'n/a'}
    comp=lambda r:r['compiles'] is True and r['n_tests']>0 and r['join_status'] not in ('file_missing','join_ambiguous')
    result['G_A']=fraction_ci(rows,lambda r:r['fully_applicable'],comp,rng)
    result['applicability_any_evaluable']=fraction_ci(rows,lambda r:r['applicable'],comp,rng)
    result['failing_share']=fraction_ci(rows,lambda r:r['hidden_all_pass']==0,
        lambda r:r['compiles'] is True and r['fully_applicable'] and scsc(r) is not None,rng)
    result['subsets']={}
    for subset in ('Core614','IndustrySet282'):
        result['subsets'][subset]={'P1':p1(rows,rng,subset=subset),'P2_P3':p23(rows,rng,subset=subset),
                                  'systems':system_table([r for r in rows if r['subset']==subset])}
    result['mapping_steps']=dict(Counter(str(s) for r in rows for s in r['mapping_steps']))
    q=result['P2_P3'];p1value=result['P1']['spearman']
    result['verdicts']={'P1_holds':p1value is not None and p1value>=.8,
        'P2_holds':q['auc'] is not None and q['auc']>=.6 and q['auc_bootstrap_95']['low'] is not None and q['auc_bootstrap_95']['low']>.5,
        'P3_holds':q['spearman_within_system'] is not None and q['spearman_within_system']>0 and q['spearman_bootstrap_95']['low'] is not None and q['spearman_bootstrap_95']['low']>0,
        'coverage_verdict':'PASS' if result['G_A']['fraction']>=.5 else 'LIMITED COVERAGE'}
    helpers=[r for r in inspected if r['v1_category']=='helper_mapping']
    partial=[r for r in inspected if r['v1_category']!='helper_mapping' and r['v1_group']=='high_score_failing']
    low=[r for r in inspected if r['v1_group']=='low_score_passing']
    result['inspected_prediction']={'helper_resolved_or_missing':sum(r['v2_hidden_all_pass'] in (1,None) for r in helpers),
        'n_helper_rows':len(helpers),'remaining_helper_failures':sum(r['v2_helper_mapped_failure'] for r in helpers),
        'partial_missing_and_evaluable_pass':sum(r['v2_hidden_all_pass'] is None and r['v2_n_pass']==r['v2_n_evaluable'] for r in partial),
        'n_partial_rows':len(partial),'low_still_passing':sum(r['v2_hidden_all_pass']==1 for r in low),'n_low_rows':len(low)}
    pred=result['inspected_prediction'];pred['holds']=(pred['helper_resolved_or_missing']>=5 and pred['remaining_helper_failures']==0 and pred['partial_missing_and_evaluable_pass']==4 and pred['low_still_passing']==10)
    forecasts=json.loads((PHASE/'forecasts/e12_v2_forecast.json').read_text())['predictions']
    result['forecast_checks']={}
    for key,value in [('P1',p1value),('P2',q['auc']),('P3',q['spearman_within_system']),('G-A',result['G_A']['fraction']),
                      ('applicability_any_evaluable',result['applicability_any_evaluable']['fraction']),('failing_share',result['failing_share']['fraction'])]:
        forecast=forecasts[key];lo,hi=forecast['plausible_range']
        result['forecast_checks'][key]={'measured':value,'forecast':forecast,'within_plausible_range':value is not None and lo<=value<=hi,'p_value':'n/a'}
    result['forecast_checks']['failing_share']['direction_holds']=result['failing_share']['fraction'] is not None and result['failing_share']['fraction']<200/3199
    result['forecast_checks']['P2']['direction_holds']=q['auc'] is not None and q['auc']>.640
    result['forecast_checks']['P3']['direction_holds']=q['spearman_within_system'] is not None and q['spearman_within_system']>.151
    result['forecast_checks']['applicability_any_evaluable']['direction_holds']=result['applicability_any_evaluable']['fraction']>=3224/4626
    eligible=[r for r in rows if r['compiles'] is True and r['fully_applicable'] and scsc(r) is not None]
    high=sorted([r for r in eligible if r['hidden_all_pass']==0],key=lambda r:(-scsc(r),r['system'],r['task_id']))[:10]
    low=sorted([r for r in eligible if r['hidden_all_pass']==1],key=lambda r:(scsc(r),r['system'],r['task_id']))[:10]
    result['disagreement_selection']=[{**r,'scsc':scsc(r),'group':label} for label,rr in [('high_score_failing',high),('low_score_passing',low)] for r in rr]
    atomic_json(PHASE/'results/analysis_e12_v2.json',result)
    # Committed per-cell table is sufficient to recompute primary statistics without cluster access.
    (PHASE/'results/cells_v2.jsonl').write_bytes(source.read_bytes())
    atomic_json(PHASE/'results/paired_changed_entry_points_v2.json',changed)
    atomic_json(PHASE/'results/paired_inspected_v1_rows_v2.json',inspected)
    atomic_json(PHASE/'results/systems_v2.json',result['systems'])
    (PHASE/'results/common_fully_applicable_v1.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in paired_v1))
    print(json.dumps(result['verdicts']),flush=True)


if __name__=='__main__':main()
