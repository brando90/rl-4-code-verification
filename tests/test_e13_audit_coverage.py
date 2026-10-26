"""Validate train-only judge inputs, compile gating and the frozen six-rating aggregation without calls."""
from pathlib import Path
import copy
import importlib.util
import json
import os
import sys

import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_audit_coverage',PHASE/'audit_coverage.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(tmp_path):
    source=tmp_path/'source.lean';source.write_text('import Mathlib\ntheorem identity (n : Nat) : n + 0 = n := Nat.add_zero n\n')
    ref={'path':str(source),'sha256':m.digest(source)};cells=[];rows=[]
    for i in range(32):
        for variant in m.VARIANTS:
            cell={'cell_id':f'audit_{i}/{variant}','audit_id':f'audit_{i}','task_id':f'authored__{i}',
                  'group_id':f'group_{i}','split':'train','variant':variant,'source':ref}
            cells.append(cell)
            row={k:cell[k] for k in ('cell_id','audit_id','task_id','group_id','split','variant')}
            row.update(compile=None,cleanup_verified=True);rows.append(row)
    for index,gate in [(0,True),(1,False)]:
        receipt=tmp_path/f'strict_{index}.json';receipt.write_text(json.dumps({'status':'measured','compile':gate,'source_sha256':ref['sha256']}))
        rows[index].update(compile=gate,strict_receipt={'path':str(receipt),'sha256':m.digest(receipt)})
    train=[f'authored__{i}' for i in range(32)];allow=tmp_path/'train.txt';allow.write_text('\n'.join(train)+'\n')
    return {'condition':'v2-S2','declared_tasks':32,'cells':cells},rows,train,allow


def test_compile_failures_are_zero_unknowns_are_missing_and_no_cell_disappears(tmp_path):
    inputs,rows,train,_=fixture(tmp_path)
    ratings={'FSC':.6,'complete_3x2':True,'repeats_measured':dict.fromkeys(m.CONFIGS,3)}
    out=m.combine(inputs,rows,{'cells':{'audit_0/original#0':ratings}},train=train)
    assert len(out['rows'])==128 and out['coverage_known']==2
    assert [r['formal_specification_coverage'] for r in out['rows'][:3]]==[.6,0.,None]
    ratings['repeats_measured'][m.CONFIGS[0]]=2
    out=m.combine(inputs,rows,{'cells':{'audit_0/original#0':ratings}},train=train)
    assert out['rows'][0]['formal_specification_coverage'] is None and out['coverage_known']==1


def test_wrong_identity_changed_source_and_unresolved_cleanup_are_refused(tmp_path):
    inputs,rows,train,_=fixture(tmp_path)
    altered=copy.deepcopy(rows);altered[0]['task_id']='other'
    with pytest.raises(ValueError,match='identity'):m.validate(inputs,altered,train)
    altered=copy.deepcopy(rows);altered[0]['cleanup_verified']=False
    with pytest.raises(ValueError,match='cleanup'):m.validate(inputs,altered,train)
    altered=copy.deepcopy(inputs);altered['cells'][0]['split']='test'
    with pytest.raises(ValueError,match='train audit'):m.validate(altered,rows,train)
    Path(inputs['cells'][0]['source']['path']).write_text('changed')
    with pytest.raises(ValueError,match='input changed'):m.validate(inputs,rows,train)


def test_actual_frozen_prompt_render_pack_roundtrip_and_aggregation(tmp_path,monkeypatch):
    external=PHASE.parents[3]/'external/veribench/experiments/100_karpathy_recipe_tc_judge_search_human_train_val_test/scripts/prompts.py'
    if not external.exists():
        if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION')=='1':pytest.fail('required pinned judge renderer absent')
        pytest.skip('pinned judge renderer absent')
    inputs,rows,train,allow=fixture(tmp_path)
    config={'work':str(tmp_path/'work'),'train_ids':str(allow),'benchmark_prefix':'veribench-authored-audit',
            'private_namespace':'rl4cv_e13v2_authored_audit'}
    h=m.helper(config)
    h.PRIVATE=tmp_path/'private';h.PACK=tmp_path/'reference_pack'
    h.relative=lambda p:str(p.resolve())
    monkeypatch.syspath_prepend(str(h.judge_pack.E/'scripts/valkyrie_judge_agent'))
    monkeypatch.setattr(h.judge_pack,'E',tmp_path)
    monkeypatch.setattr(h.judge_pack,'RENDERED',tmp_path/'private/rendered')
    task=h.PACK/'authored__0';(task/'tests').mkdir(parents=True)
    (task/'tests/gold.lean').write_text(Path(inputs['cells'][0]['source']['path']).read_text())
    (task/'instruction.md').write_text('Authored task\n```python\ndef identity(n):\n    return n\n```\n')
    # Two compiled files expose accidental reuse of the rendered system prompt
    # as the experiment label on subsequent files and in manifest metadata.
    receipt=tmp_path/'strict_second.json'
    receipt.write_text(json.dumps({'status':'measured','compile':True,'source_sha256':inputs['cells'][2]['source']['sha256']}))
    rows[2].update(compile=True,strict_receipt={'path':str(receipt),'sha256':m.digest(receipt)})
    manifest=m.build(config,inputs,rows,module=h)
    assert manifest['n_declared_ratings']==12 and manifest['compiled_files']==2
    assert manifest['round_trip']=={'n_round_trip':6,'failures':[]} and len(manifest['cells_not_judged'])==126
    assert len({r['prompt_sha256'] for r in manifest['cells']})==1
    assert [r['repeat'] for r in manifest['cells']]==[1,2,3,1,2,3]
    assert {r['task_id_vb'] for r in manifest['cells']}=={'audit_0/original',inputs['cells'][2]['cell_id']}
    assert all(r['system']==m.SYSTEM for r in manifest['cells'])
    assert all(r['system']==m.SYSTEM for r in json.loads((h.PRIVATE/'items.json').read_text()))
    assert manifest['model_calls']==0
    with pytest.raises(FileExistsError):m.build(config,inputs,rows,module=h)
    harvest=h.RESULTS/'harvests';harvest.mkdir()
    for member,values in zip(m.CONFIGS,([0,4,5],[1,2,5])):
        records=[{'task_id_vb':'audit_0/original','sample_idx':0,'is_audit_only':True,'item':'audit_000',
                  'status':'measured','score_raw':v} for v in values]
        records += [{**r,'task_id_vb':inputs['cells'][2]['cell_id'],'item':'audit_002'} for r in records]
        (harvest/f'cells_train_audit__{member}.json').write_text(json.dumps({'cells':records,'charges_usd':0.}))
    assert h.fsc(m.SYSTEM)==0
    aggregate=json.loads((h.RESULTS/'fsc_train_audit.json').read_text())
    assert aggregate['cells']['audit_0/original#0']['FSC']==.6
    assert m.combine(inputs,rows,aggregate,train=train)['coverage_known']==3
