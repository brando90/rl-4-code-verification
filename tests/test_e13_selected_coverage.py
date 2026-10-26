"""Use the unchanged judge renderer and six-rating aggregation on every fixed selected-test sample."""
from pathlib import Path
import copy,json,os,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
import selected_coverage as m
import selected_coverage_inputs as inputs_module
from test_e13_selected_coverage_inputs import fixture as scoring_fixture,put


def fixture(tmp_path):
    tasks,data,root,run=scoring_fixture(tmp_path)
    inputs=inputs_module.normalize(tasks,data,root,run,output=tmp_path/'normalized')
    allowed=[t['task_id'] for t in tasks];allow=tmp_path/'test_ids.txt';allow.write_text('\n'.join(allowed)+'\n')
    return inputs,allowed,allow


def test_compile_gate_and_all_six_ratings_preserve_every_selected_sample(tmp_path):
    inputs,allowed,_=fixture(tmp_path);key=inputs['cells'][1]['cell_id']+'#0'
    ratings={'FSC':.6,'complete_3x2':True,'repeats_measured':dict.fromkeys(m.CONFIGS,3)}
    out=m.combine(inputs,{'cells':{key:ratings}},test_ids=allowed)
    assert out['declared']==222 and len(out['rows'])==222 and out['coverage_known']==2
    assert [r['formal_specification_coverage'] for r in out['rows'][:3]]==[None,.6,0.]
    ratings['repeats_measured'][m.CONFIGS[0]]=2
    assert m.combine(inputs,{'cells':{key:ratings}},test_ids=allowed)['coverage_known']==1


@pytest.mark.parametrize('change',('sample','checkpoint','compile','source','missing_task'))
def test_changed_fixed_sample_or_physical_gate_is_refused(tmp_path,change):
    inputs,allowed,_=fixture(tmp_path)
    if change=='sample':inputs['cells'][0]['sample_idx']=1
    elif change=='checkpoint':inputs['cells'][0]['boundary']=3
    elif change=='missing_task':allowed.pop()
    elif change=='source':Path(inputs['cells'][1]['source']['path']).write_text('changed')
    else:
        cell=inputs['cells'][1];strict=m.read(cell['strict']);strict['compile']=False
        cell['strict']=put(Path(cell['strict']['path']),strict)
    with pytest.raises(ValueError):m.validate(inputs,allowed)


def test_unchanged_renderer_roundtrip_and_real_aggregation_on_authored_test_files(tmp_path,monkeypatch):
    external=PHASE.parents[3]/'external/veribench/experiments/100_karpathy_recipe_tc_judge_search_human_train_val_test/scripts/prompts.py'
    if not external.exists():
        if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION')=='1':pytest.fail('required pinned judge renderer absent')
        pytest.skip('pinned judge renderer absent')
    inputs,allowed,allow=fixture(tmp_path)
    config={'work':str(tmp_path/'work'),'test_ids':str(allow),'benchmark_prefix':'veribench-authored-selected',
        'private_namespace':'rl4cv_e13v2_authored_selected'}
    helper=m.helper(config);helper.PRIVATE=tmp_path/'judge';helper.PACK=tmp_path/'reference_pack';helper.relative=lambda p:str(p.resolve())
    monkeypatch.syspath_prepend(str(helper.judge_pack.E/'scripts/valkyrie_judge_agent'))
    monkeypatch.setattr(helper.judge_pack,'E',tmp_path)
    task=helper.PACK/allowed[1];(task/'tests').mkdir(parents=True)
    (task/'tests/gold.lean').write_text('import Mathlib\ntheorem authored (n : Nat) : n = n := rfl\n')
    (task/'instruction.md').write_text('Authored\n```python\ndef identity(n):\n    return n\n```\n')
    manifest=m.build(config,inputs,module=helper)
    assert manifest['split']=='test' and manifest['declared']==222 and manifest['compiled_files']==1
    assert manifest['n_declared_ratings']==6 and manifest['round_trip']=={'n_round_trip':3,'failures':[]}
    assert len(manifest['cells_not_judged'])==221 and all(not c['is_audit_only'] for c in manifest['cells'])
    assert all(c['system']==m.SYSTEM for c in manifest['cells']) and manifest['model_calls']==0
    with pytest.raises(FileExistsError):m.build(config,inputs,module=helper)
    harvest=helper.RESULTS/'harvests';harvest.mkdir()
    for member,values in zip(m.CONFIGS,([0,4,5],[1,2,5])):
        rows=[{'task_id_vb':inputs['cells'][1]['cell_id'],'sample_idx':0,'is_audit_only':False,'item':'selected_001',
            'status':'measured','score_raw':value} for value in values]
        (harvest/f'cells_selected_test__{member}.json').write_text(json.dumps({'cells':rows,'charges_usd':0.}))
    assert helper.fsc(m.SYSTEM)==0
    result=m.combine(inputs,json.loads((helper.RESULTS/'fsc_selected_test.json').read_text()),test_ids=allowed)
    assert result['rows'][1]['formal_specification_coverage']==.6 and result['coverage_known']==2
