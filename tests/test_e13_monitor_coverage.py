"""Check unchanged three-by-two judge packing on complete 32-cell monitor snapshots without hosted calls."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import os
import sys
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));spec=importlib.util.spec_from_file_location('e13_monitor_coverage',PHASE/'monitor_coverage.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def ref(path):return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def fixture(tmp_path):
    source=tmp_path/'source.lean';source.write_text('import Mathlib\ntheorem identity (n : Nat) : n + 0 = n := Nat.add_zero n\n')
    cells=[];rows=[]
    for i in range(32):
        cell={'cell_id':f'B/1301/10/audit_{i}/0','audit_id':f'audit_{i}','task_id':f'authored__{i}',
              'group_id':f'group_{i}','split':'train','arm':'B','run_seed':1301,'update':10,'source':ref(source)}
        row={k:cell[k] for k in m.IDENTITY};row.update(compile=None,cleanup_verified=True)
        if i<2:
            oracle=tmp_path/f'oracle_{i}.json';oracle.write_text(json.dumps({'compile':i==0}))
            saved=tmp_path/f'saved_{i}.json';saved.write_text(json.dumps({'status':'measured','strict':0}))
            strict={**row,'status':'measured','compile':i==0,'source_sha256':ref(source)['sha256'],
                    'strict_receipt':ref(saved),'oracle_receipt':ref(oracle)}
            path=tmp_path/f'strict_{i}.json';path.write_text(json.dumps(strict))
            cell['strict']=ref(path);row.update(compile=i==0,strict_receipt=ref(path))
        cells.append(cell);rows.append(row)
    train=[c['task_id'] for c in cells];allow=tmp_path/'train.txt';allow.write_text('\n'.join(train)+'\n')
    return {'condition':'v2-S2','declared':32,'arm':'B','run_seed':1301,'update':10,'cells':cells},rows,train,allow


def test_monitor_compilation_and_missing_ratings_keep_all_32_cells(tmp_path):
    inputs,rows,train,_=fixture(tmp_path)
    ratings={'FSC':.6,'complete_3x2':True,'repeats_measured':dict.fromkeys(m.CONFIGS,3)}
    fsc={'cells':{inputs['cells'][0]['cell_id']+'#0':ratings}}
    out=m.combine(inputs,rows,fsc,train=train)
    assert out['declared']==len(out['rows'])==32 and out['coverage_known']==2
    assert [r['formal_specification_coverage'] for r in out['rows'][:3]]==[.6,0.,None]
    ratings['repeats_measured'][m.CONFIGS[0]]=2
    assert m.combine(inputs,rows,fsc,train=train)['rows'][0]['formal_specification_coverage'] is None


def test_mixed_snapshot_unknown_cleanup_and_changed_oracle_cannot_judge(tmp_path):
    inputs,rows,train,_=fixture(tmp_path);bad=copy.deepcopy(rows);bad[0]['update']=20
    with pytest.raises(ValueError,match='identity'):m.validate(inputs,bad,train)
    bad=copy.deepcopy(rows);bad[0]['cleanup_verified']=False
    with pytest.raises(ValueError,match='cleanup'):m.validate(inputs,bad,train)
    Path(tmp_path/'oracle_0.json').write_text('{"compile":false}')
    with pytest.raises(ValueError,match='input changed'):m.validate(inputs,rows,train)


def test_actual_monitor_pack_preserves_frozen_rendering_and_six_rating_aggregation(tmp_path,monkeypatch):
    external=PHASE.parents[3]/'external/veribench/experiments/100_karpathy_recipe_tc_judge_search_human_train_val_test/scripts/prompts.py'
    if not external.exists():
        if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION')=='1':pytest.fail('required pinned judge renderer absent')
        pytest.skip('pinned judge renderer absent')
    inputs,rows,train,allow=fixture(tmp_path)
    config={'work':str(tmp_path/'work'),'train_ids':str(allow),'benchmark_prefix':'veribench-authored-monitor',
            'private_namespace':'rl4cv_e13v2_authored_monitor','snapshot_name':'b-1301-u10'}
    h=m.helper(config);h.PRIVATE=tmp_path/'private';h.PACK=tmp_path/'reference_pack';h.relative=lambda p:str(p.resolve())
    monkeypatch.syspath_prepend(str(h.judge_pack.E/'scripts/valkyrie_judge_agent'))
    monkeypatch.setattr(h.judge_pack,'E',tmp_path);monkeypatch.setattr(h.judge_pack,'RENDERED',tmp_path/'private/rendered')
    task=h.PACK/'authored__0';(task/'tests').mkdir(parents=True)
    (task/'tests/gold.lean').write_text(Path(inputs['cells'][0]['source']['path']).read_text())
    (task/'instruction.md').write_text('Authored task\n```python\ndef identity(n):\n    return n\n```\n')
    manifest=m.build(config,inputs,rows,module=h)
    assert manifest['n_declared_ratings']==6 and manifest['compiled_files']==1
    assert manifest['round_trip']=={'n_round_trip':3,'failures':[]} and len(manifest['cells_not_judged'])==31
    assert all(r['system']==m.SYSTEM for r in manifest['cells'])
    assert all(r['system']==m.SYSTEM for r in json.loads((h.PRIVATE/'items.json').read_text()))
    assert manifest['declared_audit_cells']==32 and manifest['model_calls']==0
    assert all(r['task_id_vb']==inputs['cells'][0]['cell_id'] for r in manifest['cells'])
    with pytest.raises(FileExistsError):m.build(config,inputs,rows,module=h)
    harvest=h.RESULTS/'harvests';harvest.mkdir()
    for member,values in zip(m.CONFIGS,([0,4,5],[1,2,5])):
        records=[{'task_id_vb':inputs['cells'][0]['cell_id'],'sample_idx':0,'is_audit_only':True,'item':'audit_000',
                  'status':'measured','score_raw':value} for value in values]
        (harvest/f'cells_pilot_monitor__{member}.json').write_text(json.dumps({'cells':records,'charges_usd':0.}))
    assert h.fsc(m.SYSTEM)==0
    aggregate=json.loads((h.RESULTS/'fsc_pilot_monitor.json').read_text())
    assert m.combine(inputs,rows,aggregate,train=train)['rows'][0]['formal_specification_coverage']==.6
