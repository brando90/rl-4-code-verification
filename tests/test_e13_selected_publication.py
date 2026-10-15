"""Check prospective coverage input freezing on authored tasks only; no measured evaluation."""
from pathlib import Path
import importlib.util,importlib.machinery,json,sys
import pytest
R=Path(__file__).resolve().parents[1]
P=R/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path[:0]=[str(R/'tests'),str(P)]
from test_e13_selected_coverage_inputs import plan_fixture,put
from technical_driver import read,reference
path=P/'selected_publication.py'
loader=importlib.machinery.SourceFileLoader('authored_selected_publication',str(path))
spec=importlib.util.spec_from_loader(loader.name,loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m)


def fixture(tmp_path,monkeypatch,*,post_main=False,failed_control=False):
    selection=plan_fixture(tmp_path/'run',monkeypatch)
    # Prospective lock files remain isolated from the repository in authored tests.
    phase=tmp_path/'version/phase2';phase.mkdir(parents=True);(phase.parent/'locks').mkdir()
    for name in ('selected_hidden.py','hidden_runtime.py','selected_coverage_inputs.py','selected_coverage.py','selected_hosted.py','hosted_coverage.py','coverage_pack.py','coverage_controls.py'):
        (phase/name).write_bytes((P/name).read_bytes())
    monkeypatch.setattr(m,'HERE',phase);monkeypatch.setattr(m,'published',lambda ref,repo:read(ref))
    sources=[path,*phase.iterdir(),m.E12/'expt_v1/scripts/extract_hidden_tests.py']
    L2=read(selection['L2']);L2['bindings'] += [reference(p) for p in sources if not(post_main and p==path)]
    selection['L2']=put(Path(selection['L2']['path']),L2)
    for key in ('selection','score_lock','score'):
        value=read(selection[key]);value['L2_sha256']=selection['L2']['sha256']
        if key=='score':value['scoring_lock_sha256']=selection['score_lock']['sha256']
        selection[key]=put(Path(selection[key]['path']),value)
    pack=tmp_path/'authored_pack'
    for task in read(read(selection['method'])['tasks']):
        gold=pack/task['task_id']/'tests/gold.lean';gold.parent.mkdir(parents=True)
        gold.write_text('def authoredIdentity (n : Nat) : Nat := n\nexample : authoredIdentity 1 = 1 := by rfl\n')
    original=put(tmp_path/'control_lock.json',{'configuration':{'pack':str(pack),'lake':'unused','lake_bin':'unused'},'bindings':[]})
    controls=put(tmp_path/'controls.json',{'status':'FAIL' if failed_control else 'PASS','cleanup_verified':True})
    return {'selection_plan':selection,'hidden_controls_lock':original,'hidden_controls_result':controls},pack


def test_all_fixed_samples_and_gold_sources_are_bound_before_hidden_execution(tmp_path,monkeypatch):
    plan,pack=fixture(tmp_path,monkeypatch);result=m.prepare_hidden(plan);lock=read(result['lock'])
    inputs=read(lock['inputs']);bound={b['path']:b['sha256'] for b in lock['bindings']}
    assert lock['declared']==len(inputs['cells'])==222 and lock['maximum_attempts_per_cell']==1
    assert result['model_calls']==0 and all(c['sample_idx']==0 for c in inputs['cells'])
    assert inputs['cells'][0]['source'] is None
    assert not Path(lock['configuration']['root']).exists()
    for c in inputs['cells']:
        assert bound[c['gold']['path']]==c['gold']['sha256'] and bound[c['suite']['path']]==c['suite']['sha256']
        assert read(c['suite'])['n_tests']==1
    with pytest.raises(FileExistsError):m.prepare_hidden(plan)


@pytest.mark.parametrize('change',['post_main','failed_control','gold_changed_after_lock'])
def test_preparation_authority_or_changed_inputs_cannot_reach_hosted_calls(tmp_path,monkeypatch,change):
    plan,pack=fixture(tmp_path,monkeypatch,post_main=change=='post_main',failed_control=change=='failed_control')
    if change!='gold_changed_after_lock':
        with pytest.raises(ValueError):m.prepare_hidden(plan)
        assert not list((tmp_path/'version').glob('locks/*.json'))
    else:
        result=m.prepare_hidden(plan);lock=read(result['lock']);gold=Path(read(lock['inputs'])['cells'][0]['gold']['path']);gold.write_text('changed')
        # Input verification must precede route preparation or model calls.
        monkeypatch.setattr(m,'source_authority',lambda *_:(None,None,None,None,None))
        with pytest.raises(ValueError,match='shared coverage inputs changed'):
            m.prepare_hosted({'repository':'authored','cpu_lock':result['lock']})


def test_hosted_pack_uses_same_fixed_samples_and_never_needs_hidden_outcomes(tmp_path,monkeypatch):
    import selected_coverage
    plan,pack=fixture(tmp_path,monkeypatch);cpu=m.prepare_hidden(plan)
    for folder in pack.iterdir():
        (folder/'instruction.md').write_text('Authored\n```python\ndef authoredIdentity(n):\n    return n\n```\n')
    bundle=tmp_path/'bundle';bundle.mkdir()
    for name in ('judge_call.py','setup.sh','contract.yaml'):(bundle/name).write_text('authored '+name)
    route=put(tmp_path/'route.json',{'verdict':'PASS'})
    migration=put(tmp_path/'migration.json',{})
    # Actual renderer, with every reference file confined to authored fixtures.
    cache={};real_helper=selected_coverage.helper
    def helper(config):
        if not cache:
            h=real_helper(config);h.PRIVATE=tmp_path/'judge';h.PACK=pack;h.relative=lambda p:str(p.resolve())
            monkeypatch.syspath_prepend(str(h.judge_pack.E/'scripts/valkyrie_judge_agent'))
            monkeypatch.setattr(h.judge_pack,'E',tmp_path)
            monkeypatch.setattr(h.judge_run,'worst_cost',lambda model,length,tokens:.25)
            cache['h']=h
        return cache['h']
    # Read only the already-installed scientific selector definitions.
    template=real_helper({'work':str(tmp_path/'unused'),'benchmark_prefix':'authored','private_namespace':'rl4cv_e13v2_authored_draft'})
    models={template.judge_config(c)['selector']:{'provider_properties':{},'default_parameters':{'reasoning_effort':template.judge_config(c).get('reasoning_effort')}} for c in m.CONFIGS}
    catalog=put(tmp_path/'catalog.json',{'models':models})
    config={'bundle':str(bundle),'route_identity':route['path'],'registry_catalog':catalog['path'],'migration_provenance':migration['path']}
    original=put(tmp_path/'hosted_control_lock.json',{'configuration':config,'bindings':[]})
    controls=put(tmp_path/'hosted_controls.json',{'status':'PASS','actual_bundle_verified':True})
    monkeypatch.setattr(m,'helper',helper)
    monkeypatch.setattr(m,'build',lambda config,inputs:selected_coverage.build(config,inputs,module=helper(config)))
    result=m.prepare_hosted({'repository':'authored','cpu_lock':cpu['lock'],'coverage_controls_lock':original,'coverage_controls_result':controls})
    lock=read(result['lock']);prepared=json.loads(Path(lock['configuration']['prepared']).read_text())
    assert lock['declared']==222 and lock['declared_ratings']==6 and lock['repeats_per_member']==3
    assert prepared['model_calls']==0 and result['estimated_maximum_two_attempt_usd']==3.
    assert lock['configuration']['inputs']==read(cpu['lock'])['inputs']['path']
    assert not Path(read(cpu['lock'])['configuration']['root']).exists()
    assert all(m.digest(b['path'])==b['sha256'] for b in lock['bindings'])
