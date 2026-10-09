"""Freeze all experiment-01 cells and the declared experiment-08 validation ladder without reading test-split candidates."""
import collections
import csv
import json
from pathlib import Path
from audit_inputs_e12 import sha, resolve_candidate
from prepare_A1 import PHASE, RESULTS
from rl4cv.forecast import verify_forecast


def main():
    for name in ('e12_phase_a_forecast', 'e12_phase_a_forecast_amendment_A1'):
        assert verify_forecast(PHASE/'forecasts'/(name+'.json'))
    dest = RESULTS/'secondary_manifest_A1.json'
    if dest.exists():
        print('Preserving frozen secondary manifest:', sha(dest)); return
    primary = json.loads((RESULTS/'input_manifest_A1.json').read_text())
    gold = {r['task_id']:r['gold_key'] for r in primary['gold']}
    sources, cells = [], []

    def read_jsonl(path, ids):
        if not path.exists(): return {}
        sources.append({'path':str(path), 'sha256':sha(path)})
        rows = {}
        for line in path.open():
            r=json.loads(line)
            if r['task_id'] not in ids: continue
            key=(r['task_id'],int(r['sample_idx'])); assert key not in rows
            rows[key]=r
        return rows

    def binding(job, task, sample):
        trial=job/ task
        receipt=trial/'receipt.json'
        expected=None
        if receipt.is_file(): expected=json.loads(receipt.read_text()).get('solution_sha256')
        return resolve_candidate([trial/'verifier/solution.lean'],expected)

    root=Path('/lfs/skampere1/0/brando9/rl4cv_e01/out')
    files=sorted((root/'scored').glob('*_g1.jsonl')); assert len(files)==9
    for f in files:
        name=f.stem.removeprefix('scored_'); rows=read_jsonl(f,gold)
        for task in sorted(gold):
            r=rows.get((task,0),{})
            cells.append({'panel':'experiment01','system':name,'task_id':task,'gold_key':gold[task], 'sample_idx':0,
                          'model':r.get('model'),'revision':r.get('revision'), 'source_status':r.get('status','factor_missing'),
                          'recorded_compiles':r.get('compiles'), 'IC_tests':r.get('IC_tests'), 'IC_proofs':r.get('IC_proofs'),
                          'FSC':r.get('FSC'), 'kernel_binary':r.get('rewards',{}).get('kernel_binary'),
                          **binding(root/'jobs'/f'{name}_s0',task,0)})
    e08=PHASE.parents[1]/'08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results'
    ladder_path=e08/'ladder_manifest.json';sources.append({'path':str(ladder_path),'sha256':sha(ladder_path)})
    ladder=json.loads(ladder_path.read_text())
    ids_path=e08/'split/vbv1_validation_task_ids.txt';sources.append({'path':str(ids_path),'sha256':sha(ids_path)})
    ids=[s.strip() for s in ids_path.read_text().splitlines() if s.strip()];assert len(ids)==135
    for system in ladder['systems']:
        label=system['label']
        if system['source']=='e05':
            root=Path('/lfs/skampere1/0/brando9/rl4cv_e05/out');name=system['e05_label']+'_g8'
        else:
            root=Path('/lfs/skampere1/0/brando9/rl4cv_e08/ladder/validation');name=label+'_g8'
        rows=read_jsonl(root/'scored'/('scored_'+name+'.jsonl'),ids)
        f=e08/'ladder'/(label+'_validation_cells.csv')
        frozen={}
        if f.exists():
            sources.append({'path':str(f),'sha256':sha(f)})
            frozen={(r['task_id'],int(r['sample_idx'])):r for r in csv.DictReader(f.open())}
        for task in ids:
            for sample in range(8):
                r=rows.get((task,sample),{});fr=frozen.get((task,sample),{})
                known=fr.get('known')=='True'
                if known:
                    assert r.get('status')=='scored'
                    assert abs(float(fr['IC_tests'])-r['IC_tests'])<1e-9
                    assert abs(float(fr['IC_proofs'])-r['IC_proofs'])<1e-9
                b=binding(root/'jobs'/f'{name}_s{sample}',task,sample)
                if fr.get('lean_sha256'): assert b.get('sha256')==fr['lean_sha256']
                cells.append({'panel':'experiment08_validation','system':label,'task_id':task,'gold_key':gold[task],
                              'sample_idx':sample,'source_status':'scored' if known else 'factor_missing',
                              'recorded_compiles':r.get('compiles') if known else None,
                              'IC_tests':float(fr['IC_tests']) if known else None,'IC_proofs':float(fr['IC_proofs']) if known else None,
                              'FSC':None,'kernel_binary':float(fr['kernel_binary']) if known else None,**b})
    assert len(cells)==8064+ladder['n_declared_cells']
    assert len({(r['panel'],r['system'],r['task_id'],r['sample_idx']) for r in cells})==len(cells)
    summaries=[]
    for panel,system in sorted({(r['panel'],r['system']) for r in cells}):
        rr=[r for r in cells if (r['panel'],r['system'])==(panel,system)]
        summaries.append({'panel':panel,'system':system,'n_declared':len(rr),'n_factor_measured':sum(r['source_status']=='scored' for r in rr),
                          'joins':dict(collections.Counter(r['join_status'] for r in rr))})
    report={'sources':sources,'systems':summaries,'cells':cells,'n_declared':len(cells),
            'scope':'experiment01 all896; experiment08 validation135 only, frozen committed ladder factors; later arrivals are not silently included'}
    dest.write_text(json.dumps(report,separators=(',',':'))+'\n')
    print(json.dumps({'n_declared':len(cells),'n_systems':len(summaries),'factor_measured':sum(r['source_status']=='scored' for r in cells)}))


if __name__=='__main__': main()
