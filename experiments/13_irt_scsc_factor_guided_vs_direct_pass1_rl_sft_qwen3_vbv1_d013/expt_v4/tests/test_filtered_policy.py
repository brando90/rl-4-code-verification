"""TLDR: Verify native sampler parity, tie information loss, fixed-support gradients and NeMo loss wiring."""
import ast
from pathlib import Path
import pytest
import torch
from filtered_policy import support, filtered_logprobs, reconstruct, ReconstructionBlocked

SAMPLER=Path('/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/lib/python3.12/site-packages/vllm/v1/sample/ops/topk_topp_sampler.py')


def installed_filter():
    # Execute the installed pure function without importing the CUDA vLLM platform.
    tree=ast.parse(SAMPLER.read_text())
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('apply_top_k_top_p','apply_top_k_only')]
    namespace={'torch':torch,'Optional':__import__('typing').Optional}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SAMPLER),'exec'),namespace)
    return namespace['apply_top_k_top_p']


@pytest.mark.parametrize('logits',[
    torch.arange(30).float()/10,torch.zeros(40),torch.tensor([100.]+[0.]*29),
    torch.tensor([2.]*21+[1.]*9),torch.randn(4,71,generator=torch.Generator().manual_seed(13))])
def test_exact_installed_native_support(logits):
    original=logits.reshape(-1,logits.shape[-1]).float()
    expected=installed_filter()(original/.6,torch.full((original.shape[0],),20),torch.full((original.shape[0],),.95))
    assert torch.equal(support(original),torch.isfinite(expected))


def test_boundary_token_retained():
    # Tail .04 removed, next .06 crosses .05 and is retained; .9 alone is below .95.
    logits=.6*torch.tensor([.04,.06,.9]).log()
    assert support(logits,k=3).tolist()==[False,True,True]


def test_singleton_gradient_is_zero():
    x=torch.tensor([100.]+[0.]*19,requires_grad=True);keep=support(x)
    lp,mass=filtered_logprobs(x,keep,torch.tensor(0));lp.backward()
    assert lp.item()==0 and keep.sum()==1 and torch.equal(x.grad,torch.zeros_like(x))


def test_old_support_fixed_after_large_current_change():
    old=torch.arange(30).float();keep=support(old)
    new=old.clone();new[0]=200;new.requires_grad_()
    lp,_=filtered_logprobs(new,keep,torch.tensor(29));lp.backward()
    assert new.grad[0]==0 and not torch.equal(support(new),keep)
    assert lp.isfinite()


def test_omitted_ties_change_distribution_and_cannot_be_reconstructed():
    # Equal raw top-20 logp is compatible with 21 or 22 equal top logits:
    # distribute the remaining full-softmax mass over the lower vocabulary.
    # Simple equal-40 example directly proves >20 retained support and omitted tokens.
    full=torch.zeros(40); keep=support(full)
    ids=torch.topk(full,20).indices;raw=full.log_softmax(-1)[ids]
    assert keep.sum()>20
    with pytest.raises(ReconstructionBlocked,match='cannot certify'):
        reconstruct(ids,raw,int(ids[0]),vocab_size=40)


def test_certified_no_tie_reconstruction():
    full=torch.arange(40).float()/10
    values,ids=torch.topk(full.log_softmax(-1),20)
    tokens,lp=reconstruct(ids,values,39,vocab_size=40,complete_topk=True)
    expected,_=filtered_logprobs(full,support(full),torch.tensor(39))
    assert set(tokens)==set(support(full).nonzero().flatten().tolist())
    assert lp==pytest.approx(float(expected),abs=2e-6)


def test_tiny_complete_vocabulary():
    tokens,lp=reconstruct([0,1,2],torch.tensor([.04,.06,.9]).log()*.6,2,vocab_size=3)
    assert tokens==[1,2] and lp==pytest.approx(__import__('math').log(.9/.96),abs=1e-6)


def loss_batch():
    old=torch.linspace(-2,2,30).reshape(1,1,30).expand(1,3,30).clone()
    keep=support(old[:,:-1]); tokens=torch.tensor([[29,28]])
    lp,_=filtered_logprobs(old[:,:-1],keep,tokens)
    indices=keep[0,0].nonzero().flatten();width=len(indices)
    sparse=indices.reshape(1,1,-1).expand(1,3,-1).clone()
    data={'input_ids':torch.tensor([[0,29,28]]),'token_mask':torch.tensor([[0.,1.,1.]]),'sample_mask':torch.ones(1),
          'advantages':torch.tensor([[0.,1.,-1.]]),'prev_logprobs':torch.cat([torch.zeros(1,1),lp],1),
          'generation_logprobs':torch.cat([torch.zeros(1,1),lp],1),'reference_policy_logprobs':torch.zeros(1,3),
          'v4_support_ids':sparse,'v4_support_mask':torch.ones_like(sparse,dtype=torch.bool)}
    return old,data


def test_actual_installed_nemo_loss_cpu_and_gradient(monkeypatch):
    from nemo_objective import FilteredClippedPGLossFn
    # Only NeMo's hard-coded target-ID .cuda() is redirected to CPU for this test.
    # No model, GPU, Policy.train or optimizer step runs.
    monkeypatch.setattr(torch.Tensor,'cuda',lambda self,*a,**kw:self)
    old,data=loss_batch();current=(old+.02*torch.arange(30)).requires_grad_()
    loss,metrics=FilteredClippedPGLossFn()(current.float()/.6,data,torch.tensor(1.),torch.tensor(2.))
    keep=support(old[:,:-1]);lp,_=filtered_logprobs(current[:,:-1],keep,data['input_ids'][:,1:])
    ratio=(lp-data['prev_logprobs'][:,1:]).exp();adv=data['advantages'][:,1:]
    expected=torch.maximum(-adv*ratio,-adv*ratio.clamp(.8,1.28)).mean()
    assert float(loss.detach())==pytest.approx(float(expected.detach()),abs=1e-7)
    loss.backward();assert torch.isfinite(current.grad).all() and current.grad.abs().sum()>0
    assert current.grad[0,0,0]==0


def test_wrapper_is_passed_to_policy_train(monkeypatch):
    from nemo_objective import train_filtered,FilteredClippedPGLossFn
    _,data=loss_batch();calls=[]
    monkeypatch.setattr('nemo_objective.install_on_policy',lambda p:calls.append('worker_hook'))
    class Policy:
        def train(self,batch,loss):
            assert batch is data and isinstance(loss,FilteredClippedPGLossFn);return 'wired'
    assert train_filtered(Policy(),data,lease_check=lambda:calls.append('guard'))=='wired'
    assert calls==['guard','worker_hook']


def test_off_support_fails(monkeypatch):
    from nemo_objective import FilteredClippedPGLossFn
    old,data=loss_batch();data['input_ids'][0,1]=0
    with pytest.raises(ValueError,match='outside'):FilteredClippedPGLossFn()(old,data,torch.tensor(1.),torch.tensor(2.))


def test_old_weight_hook_captures_actual_model_and_is_removed():
    from trainer_support import collect_old_support
    from types import SimpleNamespace
    old,data=loss_batch()
    class Model(torch.nn.Module):
        def forward(self,input_ids):return SimpleNamespace(logits=old)
    class Worker:
        cfg={'generation':{'temperature':.6}}
        model=Model()
        def get_logprobs(self,batch,micro_batch_size):
            self.model(input_ids=batch['input_ids']);return {'logprobs':torch.full((1,3),-99.)}
    worker=Worker();frozen=collect_old_support(worker,data)
    assert torch.allclose(frozen['prev_logprobs'],data['prev_logprobs'])
    assert not worker.model._forward_hooks and not frozen['prev_logprobs'].requires_grad


def test_generation_contract_requests_raw_top20_without_call():
    from generation_contract import sampling_kwargs,extract_raw
    from types import SimpleNamespace
    kw=sampling_kwargs(1301,[151643,151645])
    assert (kw['temperature'],kw['top_p'],kw['top_k'],kw['max_tokens'],kw['logprobs'])==(.6,.95,20,12288,20)
    out=SimpleNamespace(token_ids=[0],logprobs=[{i:SimpleNamespace(logprob=-3.) for i in range(20)}])
    rows=extract_raw(out);assert rows[0]['complete_topk_certified'] is False


def test_exact_top_p_tail_boundary_is_removed():
    logits=torch.zeros(4)
    assert support(logits,k=4,p=.5).tolist()==[False,False,True,True]


def test_temperature_hook_prevents_float16_rounding_and_double_scaling():
    from worker_hooks import install
    from types import SimpleNamespace
    worker=SimpleNamespace(cfg={'generation':{'temperature':.6}})
    install(worker)
    raw=torch.tensor([.3333,.7777],dtype=torch.float16,requires_grad=True)
    scaled=worker._apply_temperature_scaling(raw)
    assert scaled.dtype==torch.float32 and torch.equal(scaled,raw.float()/.6)
    scaled.sum().backward()
    assert raw.grad.float().tolist()==pytest.approx([1/.6,1/.6],abs=.001)


def test_installed_worker_scales_before_loss_and_hook_corrects_inplace_division():
    source=Path('/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/nemo_rl/models/policy/dtensor_policy_worker.py').read_text()
    tree=ast.parse(source)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='DTensorPolicyWorker')
    train=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='train')
    text=ast.get_source_segment(source,train)
    assert text.index('self._apply_temperature_scaling(logits)')<text.index('loss, loss_metrics = loss_fn_(')
