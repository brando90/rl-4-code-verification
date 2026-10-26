"""TLDR: Exercise V4-A1 certificates, storage, installed sampling invariance and unknown correction."""
import ast
from pathlib import Path
from types import SimpleNamespace
import pytest
import torch
from filtered_policy import certificate, support, native_support
from generation_contract import extract_raw
from gates import probability_agreement
from test_gates import positions
from test_filtered_policy import SAMPLER, loss_batch


def certify(logits, token=None):
    raw, ids = logits.log_softmax(-1).topk(min(64, len(logits)))
    return certificate(ids, raw, int(logits.argmax()) if token is None else token, vocab_size=len(logits))


def test_kth_ties_complete_and_trainer_contains_all():
    logits = torch.tensor([5.]*19+[4.]*5+[0.]*50)
    c = certify(logits)
    assert c['top_k_certified'] and c['certified']
    assert set(c['generator_support']) == set(range(19))
    assert support(logits).nonzero().flatten().tolist() == list(range(19))


def test_v64_equal_v20_not_certified():
    c = certify(torch.zeros(100))
    assert not c['top_k_certified'] and not c['certified'] and c['generator_logp'] is None


def test_boundary_tie_is_uncertified_and_trainer_includes_whole_group():
    logits = .6*torch.tensor([.03,.03,.94]).log()
    c = certify(logits)
    assert c['top_k_certified'] and not c['nucleus_certified']
    assert c['reason'] == 'split_boundary_tie'
    assert support(logits,k=3).all() and native_support(logits,k=3).sum() == 2


@pytest.mark.parametrize('mass,certified',[(.05-9e-6,False),(.05+9e-6,False),(.05-2e-5,True),(.05+2e-5,True)])
def test_boundary_margin_on_either_side(mass,certified):
    assert certify(.6*torch.tensor([mass,1-mass]).log())['certified'] is certified


def test_single_token_support():
    c=certify(torch.tensor([100.]+[-float(i) for i in range(1,100)]))
    assert c['certified'] and c['support_size']==1 and c['generator_logp']==0


def test_full_and_reduced_generation_records():
    x=torch.linspace(-10,10,100);lp=x.log_softmax(-1);v,ids=lp.topk(64)
    out=SimpleNamespace(token_ids=[99],logprobs=[{int(i):SimpleNamespace(logprob=float(a)) for i,a in zip(ids,v)}])
    full=extract_raw(out,vocab_size=100)[0];small=extract_raw(out,vocab_size=100,full=False)[0]
    assert len(full['top_token_ids'])==64 and full['certified']
    assert 'top_token_ids' not in small and 'generator_support' not in small
    assert small['sampled_raw_logprob']==full['sampled_raw_logprob']
    assert small['generator_logp']==full['generator_logp']


def test_uncertified_is_disagreement_and_excluded_from_error_quantiles():
    p=positions()
    for row in p[:8]:row.update(certified=False,top_k_certified=False,nucleus_certified=False,generator_support=None,generator_logp=None)
    r=probability_agreement(p,expected_positions=800)
    assert r['status']=='PASS' and r['certified_fraction']==.99 and r['uncertified_positions']==8
    assert r['median_absolute_error']==0 and r['identical_support_fraction']==.99
    p[8].update(certified=False)
    assert probability_agreement(p,expected_positions=800)['status']=='FAIL'


def test_zero_certified_fails_without_nan():
    p=positions()
    for row in p:row.update(certified=False,generator_support=None,generator_logp=None)
    r=probability_agreement(p,expected_positions=800)
    assert r['status']=='FAIL' and r['median_absolute_error'] is None


def test_installed_forward_receipt_does_not_change_sample_or_rng():
    source=SAMPLER.parents[1]/'sampler.py'
    tree=ast.parse(source.read_text())
    cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='Sampler')
    forward=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='forward')
    # Execute the actual forward on CPU. Only the engine-bound sample/gather
    # dependencies are substituted; no claim about CUDA kernel equivalence.
    ns={'torch':torch,'SamplingMetadata':object,'SamplerOutput':lambda **kw:SimpleNamespace(**kw)}
    exec(compile(ast.Module(body=[forward],type_ignores=[]),str(source),'exec'),ns)
    class Harness:
        logprobs_mode='raw_logprobs'
        compute_logprobs=staticmethod(lambda x:x.float().log_softmax(-1))
        apply_allowed_token_ids=staticmethod(lambda x,m:x)
        apply_bad_words=staticmethod(lambda x,m:x)
        apply_penalties=staticmethod(lambda x,m:x)
        def sample(self,x,m):
            assert torch.equal(x,self.expected)
            filtered=x/.6
            kept=native_support(x)
            return torch.multinomial(filtered.masked_fill(~kept,-float('inf')).softmax(-1),1).flatten()
        gather_logprobs=staticmethod(lambda lp,k,token_ids:lp.topk(k))
    x=torch.linspace(-2,2,100).reshape(1,-1);h=Harness();h.expected=x.clone();outputs=[]
    for k in (None,64):
        torch.manual_seed(1301)
        m=SimpleNamespace(max_num_logprobs=k,logitsprocs=SimpleNamespace(non_argmax_invariant=[]))
        o=ns['forward'](h,x.clone(),m)
        outputs.append((o.sampled_token_ids,torch.get_rng_state()))
    assert torch.equal(outputs[0][0],outputs[1][0]) and torch.equal(outputs[0][1],outputs[1][1])
    assert 'max_num_logprobs' not in ast.unparse(next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='sample'))


def test_unknown_behavior_probability_cannot_enter_installed_loss(monkeypatch):
    from nemo_objective import FilteredClippedPGLossFn
    old,data=loss_batch();data['generation_logprobs'][0,1]=float('nan')
    with pytest.raises(ValueError,match='finite'):
        FilteredClippedPGLossFn()(old/.6,data,torch.tensor(1.),torch.tensor(2.))


def test_behavior_probability_changes_loss_with_identical_trainer_ratio(monkeypatch):
    from nemo_objective import FilteredClippedPGLossFn
    monkeypatch.setattr(torch.Tensor,'cuda',lambda self,*a,**kw:self)
    old,data=loss_batch();data['advantages'][:]=1
    loss=FilteredClippedPGLossFn()(old/.6,data,torch.tensor(1.),torch.tensor(2.))[0]
    data['generation_logprobs'][:,1:]-=torch.log(torch.tensor(1.5))
    changed=FilteredClippedPGLossFn()(old/.6,data,torch.tensor(1.),torch.tensor(2.))[0]
    assert float(changed)==pytest.approx(float(loss)*1.5,abs=1e-6)


def test_concrete_engine_constructor_has_max_logprobs_64():
    from generation_contract import engine_kwargs
    from test_contracts import contexts
    kw=engine_kwargs('/model','/tokenizer',contexts())
    assert kw['max_logprobs']==64 and kw['logprobs_mode']=='raw_logprobs'
    assert kw['dtype']=='float16' and kw['max_model_len']==21288


def test_generation_primitive_checks_admission_before_import_or_device(monkeypatch,tmp_path):
    import generation_runtime
    calls=[]
    def blocked(*a,**kw):calls.append('admission');raise ValueError('blocked')
    def forbidden(*a,**kw):raise AssertionError('device guard cannot be reached')
    monkeypatch.setattr(generation_runtime,'check_admission',blocked)
    monkeypatch.setattr(generation_runtime,'check',forbidden)
    with pytest.raises(ValueError,match='blocked'):generation_runtime.generate({'admission':'test'},[],root=tmp_path,full=True)
    assert calls==['admission']
