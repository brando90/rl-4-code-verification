#!/usr/bin/env python3
"""Reconcile every declared test rating identity, unknown, repeat, and reported charge without new calls."""
import json
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'results/judge'
CONFIGS=('H2_sol_high','H2_opus55_max')
pack=json.loads((ROOT/'judge_pack_test.json').read_text())
want={(c['system'],c['task_id_vb'],int(c['sample_idx']),int(c['repeat']),config) for c in pack['cells'] for config in CONFIGS}
got={}; charges=[]; unknown=[]; systems={}
for label in pack['per_system']:
    info=dict(n_declared_ratings=0,n_measured_ratings=0,reported_charge=0.,missing_charge_receipts=0,repeat_sd={})
    for config in CONFIGS:
        path=ROOT/f'harvests/cells_{label}__{config}.json'
        data=json.loads(path.read_text())
        assert not data['receipt_inventory']['extra'], (label,config,'extra receipts')
        assert not data['receipt_inventory']['duplicates'], (label,config,'duplicate receipts')
        repeats={}
        for cell in data['cells']:
            key=(cell['system'],cell['task_id_vb'],int(cell['sample_idx']),int(cell['repeat']),cell['config'])
            assert key in want and key not in got, ('extra or duplicate rating',key)
            got[key]=cell; info['n_declared_ratings']+=1
            if cell['requests_sent'] is not None: assert 0<=cell['requests_sent']<=2,(key,'request cap')
            if cell['status']=='measured':
                assert cell['prompt_hash_matches'] and cell['transport_matches'],(key,'transport mismatch')
                info['n_measured_ratings']+=1
                repeats.setdefault(key[:3],[]).append(cell['score_raw']/5.)
            else: unknown.append(dict(system=key[0],task_id=key[1],sample_idx=key[2],rating_idx=key[3],member=key[4],status=cell['status']))
            if cell['cost_usd'] is None: info['missing_charge_receipts']+=1
            else: charges.append(cell['cost_usd']); info['reported_charge']+=cell['cost_usd']
        sd=[statistics.stdev(values) for values in repeats.values() if len(values)==3]
        info['repeat_sd'][config]=dict(mean_within_file_sd=statistics.fmean(sd) if sd else None,n_files_with_three_ratings=len(sd),ratings_per_file=3,scale='0–1 normalized raw member ratings')
    systems[label]=info
assert set(got)==want, ('missing rating identities',len(want-set(got)))
receipt=dict(verdict='PASS',n_declared_ratings=len(want),n_receipts=len(got),n_measured_ratings=sum(c['status']=='measured' for c in got.values()),n_unknown_ratings=len(unknown),unknown_ratings=unknown,reported_charge_usd=sum(charges),systems=systems,audit_files_not_replaced=pack['cells_not_judged'])
(ROOT.parent/'judge_reconciliation_v2.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ['systems','unknown_ratings']}))
