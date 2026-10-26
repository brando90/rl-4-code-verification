"""Check the complete A6 diagnostic, admission boundaries, single attempt and preserved missing neighbors."""
import hashlib,json,sys,types
from pathlib import Path
import pytest
P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P))
import a6_contract as contract
import a6_generation as gen


def manifest():
    ids=[f'authored_{i:02d}'for i in range(64)];cells=[]
    for t in ids:
        for k in range(8):cells.append({'cell_id':f'A6/sft_4B_f1p0/{t}/{k}','task_id':t,'sample_idx':k,'seed':91*100003+k,
            'split':'train','arm':'diagnostic','run_seed':1302601,'boundary':0,'prompt_text':'authored',
            'chat_text_sha256':hashlib.sha256(b'authored').hexdigest(),'prompt_token_ids':[1],'required_paths':['solution.lean']})
    return {'condition':'v2-S2','purpose':'A6_pipeline_diagnostic','task_ids_sha256':hashlib.sha256(''.join(t+'\n'for t in ids).encode()).hexdigest(),'cells':cells},ids


def test_complete_train_only_population_and_frozen_cohort():
    m,ids=manifest();assert len(contract.validate_manifest(m,ids))==512
    m['cells'][-1]['split']='test'
    with pytest.raises(ValueError):contract.validate_manifest(m,ids)
    m,ids=manifest();m['cells'][-1]['sample_idx']=6
    with pytest.raises(ValueError):contract.validate_manifest(m,ids)
    m,ids=manifest();m['task_ids_sha256']='other'
    with pytest.raises(ValueError):contract.validate_manifest(m,ids)


@pytest.mark.parametrize('compiles,strict,status',[(4,1,'UNSOUND'),(5,1,'SOUND'),(5,0,'UNSOUND'),(512,512,'SOUND')])
def test_exact_one_tenth_reference_and_positive_strict(compiles,strict,status):
    m,_=manifest();rows=[{'cell_id':c['cell_id'],'status':'measured','compile':int(i<compiles),'strict':int(i<strict)}for i,c in enumerate(m['cells'])]
    r=contract.verdict(m,rows,{'declared':1080,'missing':0,'compile':{'successes':100}})
    assert r['status']==status and r['LP_admitted']==(status=='SOUND') and r['comparison_statistic_eligible']is False


def test_missing_results_are_not_zero_or_resampled():
    m,_=manifest();rows=[{'cell_id':c['cell_id'],'status':'measured','compile':0,'strict':0}for c in m['cells']]
    for r in rows[:5]:r.update(status='missing_generation',compile=None,strict=None)
    out=contract.verdict(m,rows,{'declared':1080,'missing':0,'compile':{'successes':100}})
    assert out['status']=='UNRESOLVED' and out['metrics']['compile']['full_denominator_bounds']==[0,5/512]
    with pytest.raises(ValueError):contract.verdict(m,rows[:-1],{'declared':1080,'missing':0,'compile':{'successes':100}})


def test_generation_preserves_valid_neighbors_and_refuses_restart(tmp_path,monkeypatch):
    m,ids=manifest();allow=tmp_path/'ids';allow.write_text('\n'.join(ids))
    calls=[]
    class Engine:
        def generate(self,prompts,params,**kwargs):
            calls.append(prompts)
            if len(calls)==1:return [types.SimpleNamespace(outputs=[types.SimpleNamespace(token_ids=[2])])]
            outputs=[]
            for i in range(len(prompts)):
                output=types.SimpleNamespace(token_ids=[2],finish_reason='stop',text='authored response')
                outputs.append(types.SimpleNamespace(outputs=[]if i==0 else[output],prompt_token_ids=[1]))
            return outputs
    monkeypatch.setattr(gen,'build_engine',lambda c:Engine());monkeypatch.setattr(gen,'check_lease',lambda c:None)
    monkeypatch.setattr(gen,'sampling_parameters',lambda t,k:{'sample':k})
    monkeypatch.setitem(sys.modules,'vllm',types.SimpleNamespace(SamplingParams=lambda **kw:kw))
    monkeypatch.setitem(sys.modules,'transformers',types.SimpleNamespace(AutoTokenizer=types.SimpleNamespace(from_pretrained=lambda *a,**kw:types.SimpleNamespace(encode=lambda t:[1]))))
    config={'allowlist':str(allow),'tokenizer':'authored','model':'authored'};root=tmp_path/'generation'
    with pytest.raises(ValueError,match='invalid receipts'):gen.generate(config,m,list(range(512)),root=root)
    assert len(list(root.glob('*.generation.json')))==31
    assert json.loads((root/'error.json').read_text())['completed']==31
    assert len(calls)==2 and calls[0]==['Reply with one word: ready.']
    with pytest.raises(FileExistsError):gen.generate(config,m,list(range(512)),root=root)
    assert len(calls)==2


def test_original_sampler_and_oracle_are_reused():
    assert gen.sampling_parameters.__module__=='evaluation_contract'
    import a6_score,score_evaluation
    assert a6_score.inspect_source is score_evaluation.inspect_source
    assert 'for number in (1,):'in (P/'a6_score.py').read_text()


def test_transient_scoring_failure_is_retained_without_retry(tmp_path):
    import a6_score as scorer
    m,ids=manifest();cell=m['cells'][0];source=tmp_path/'generation.json';source.write_text(json.dumps(cell))
    config={'root':str(tmp_path/'scores')};binding={cell['cell_id']:{'path':str(source),'sha256':scorer.digest(source)}};calls=[]
    def execute(job,root,attempt,slots):
        calls.append(1);row={**job['identity'],'status':'unresolved_measurement','error_type':'OSError','cleanup_verified':True}
        scorer.write_new(root/'result.json',row);return row
    result=scorer.score_cell(cell,0,config,binding,'fixed',None,executor=execute)
    assert result['strict']is None and result['attempts']==1 and len(calls)==1
    assert scorer.score_cell(cell,0,config,binding,'fixed',None,executor=lambda *a:pytest.fail('repeated'))==result


def test_real_frozen_oracle_on_authored_train_diagnostic(tmp_path):
    import os,a6_score as scorer
    required=('VERIBENCH_ROOT','E13_LAKE_DIR','E13_SCORER_ROOT')
    if not all(os.environ.get(k)and Path(os.environ[k]).exists()for k in required):
        if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION')=='1':pytest.fail('required Lean routes missing')
        pytest.skip('pinned Lean routes unavailable')
    m,ids=manifest();cell=m['cells'][0];allow=tmp_path/'ids';allow.write_text('\n'.join(ids))
    cell.update(completion='```lean\n'+(P.parent/'R0_attempt_2/fixtures/valid.lean').read_text()+'\n```',at_token_cap=True)
    config={'purpose':'A6_pipeline_diagnostic','split':'train','allowlist':str(allow),
        'veribench':os.environ['VERIBENCH_ROOT'],'lake':os.environ['E13_LAKE_DIR'],'scorer':os.environ['E13_SCORER_ROOT']}
    result=scorer.score_one(cell,tmp_path,config)
    assert result['strict']==1 and result['compile']is True and result['at_token_cap']is True
