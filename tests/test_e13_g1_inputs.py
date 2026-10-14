"""Refuse changed/sealed inputs and propagate canonical A3 exclusions to every policy alias."""
import copy
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1'
sys.path.insert(0,str(ROOT))
import g1_inputs as M


def fixture():
    systems=[{'label':'base-alias'},{'label':'full'}];manifest=[];receipts=[]
    for policy in ('canonical-base','full'):
        alias='base-alias' if policy=='canonical-base' else policy
        for sample in range(8):
            row={'cell_id':f'{policy}/task/{sample}','split':'validation','task_id':'task',
                 'group_id':'group','sample_idx':sample,'source_sha256':'fixed',
                 'expectations':[{'family':'ladder','policy':alias}]}
            manifest.append(row)
            receipts.append({**{k:v for k,v in row.items() if k!='expectations'},'status':'measured',
                'components':{'consistency':'consistent'},'q1':1,'compile':1,'honest':sample%2,
                'readbacks':[{'family':'ladder','policy':alias,'equal':True,'status':'scored',
                             'value':sample%2,'factored_reward':.5,'consistency':'consistent'}]})
    exclusions=[{'cell_id':'canonical-base/task/0','split':'validation'}]
    return manifest,receipts,exclusions,systems


def test_excluded_canonical_measurement_is_unread_and_alias_is_missing():
    args=list(fixture())
    args[1][0]={'cell_id':'canonical-base/task/0','split':'validation'}
    rows,aliases,groups=M.grid(*args,task_count=1,expected_exclusions=1)
    assert aliases=={'base-alias/task/0'} and groups=={'task':'group'}
    assert len(rows)==16
    excluded=next(r for r in rows if r['policy']=='base-alias' and r['sample_idx']==0)
    assert excluded['strict'] is None and excluded['q1'] is None and excluded['strict_status']=='excluded'
    assert sum(r['strict'] is None for r in rows)==1


@pytest.mark.parametrize('mutation', ['unknown','missing','duplicate','unequal','source','sealed','denominator'])
def test_unlisted_defects_never_become_missing_completion_variables(mutation):
    manifest,rows,exclusions,systems=fixture()
    if mutation=='unknown':rows[1]['status']='unresolved_measurement'
    if mutation=='missing':rows.pop(1)
    if mutation=='duplicate':rows.append(copy.deepcopy(rows[1]))
    if mutation=='unequal':rows[1]['readbacks'][0]['equal']=False
    if mutation=='source':rows[1]['source_sha256']='changed'
    if mutation=='sealed':rows[1]['split']='test'
    if mutation=='denominator':manifest.pop()
    with pytest.raises(ValueError):M.grid(manifest,rows,exclusions,systems,task_count=1,expected_exclusions=1)


def test_changed_bytes_refused_before_json_parse_or_outcome_access(tmp_path):
    path=tmp_path/'not_json';path.write_text('must not parse this')
    with pytest.raises(ValueError,match='hash mismatch'):
        M.load({'ordinary_results':{'path':str(path),'sha256':'0'*64}},[])


def test_frozen_exclusion_identity_is_exactly_256_bits():
    assert len(M.EXCLUSION_SHA256)==64
    assert M.EXCLUSION_SHA256=='c00b35abaecda874820d4b1b29015655e248c19f319fa574fefa3d0804124128'
