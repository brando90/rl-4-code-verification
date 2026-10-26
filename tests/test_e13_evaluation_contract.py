"""Match the actual historical sampler and retain complete evaluation and selection denominators."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
spec=importlib.util.spec_from_file_location('e13_evaluation_contract',PHASE/'evaluation_contract.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_sampler_equals_original_ladder_engine_arguments(monkeypatch):
    from rl4cv.veribench.generate import _VllmEngine
    monkeypatch.setitem(sys.modules,'vllm',SimpleNamespace(SamplingParams=lambda **kw:kw))
    tokenizer=SimpleNamespace(convert_tokens_to_ids=lambda _:151645,unk_token_id=None)
    seen=[]
    old=object.__new__(_VllmEngine)
    old._SamplingParams=lambda **kw:kw;old.stop_ids=[151645]
    old.args=SimpleNamespace(temperature=.6,top_p=.95,top_k=20,max_tokens=12288)
    old.llm=SimpleNamespace(generate=lambda texts,params:seen.extend(params) or [])
    old.generate(['first','second'],[91*100003,91*100003+15])
    assert [m.sampling_parameters(tokenizer,s) for s in (0,15)]==seen
    assert 'logprobs' not in seen[0] and 'include_stop_str_in_output' not in seen[0]


def test_real_frozen_prompt_builder_keeps_thinking_template_and_hashes():
    from rl4cv.veribench.exp103 import build_prompt,veribench_root
    root=veribench_root(os.environ.get('VERIBENCH_ROOT'))
    instruction='Translate the Python program.\n```python\ndef add(a,b): return a+b\n```\nWrite `/home/user/lean_project/Veribench/Add.lean`.'
    called=[]
    tokenizer=SimpleNamespace(apply_chat_template=lambda messages,**kw:called.append((messages,kw)) or json.dumps(messages))
    got=m.render(instruction,tokenizer,root);original=build_prompt(instruction,addendum='vbv1',root=root)
    assert called==[(original.messages(),{'tokenize':False,'add_generation_prompt':True,'enable_thinking':True})]
    assert got['prompt_sha256']==original.prompt_sha256
    assert got['addendum_sha256']=='a7a0fc1b7be6b4ede41fd6b31e1e1dcae3d2fd320a6cddf9b311cf55855a18f5'


def test_full_declared_validation_and_test_identity_without_opening_test_text():
    for split,n,k in [('validation',135,8),('test',222,16)]:
        cells=m.identities([f'authored_{i}' for i in range(n)],split,arm='B',run_seed=13011,boundary=2)
        assert len(cells)==n*k and len({c['cell_id'] for c in cells})==n*k
        assert cells[0]['seed']==cells[k]['seed']==91*100003
        with pytest.raises(ValueError,match='complete evaluation'):m.identities(['authored'],split,arm='B',run_seed=13011,boundary=2)


def test_missing_strict_stays_unknown_and_wrong_identity_refused():
    cells=m.identities([f'authored_{i}' for i in range(135)],'validation',arm='A',run_seed=13011,boundary=1)
    rows=[{**c,'strict':i%2} for i,c in enumerate(cells)];rows[0]['strict']=None
    result=m.strict_summary(cells,rows)
    assert result['successes']==540 and result['missing']==1 and result['measured']==1079
    assert result['strict_mean_bounds']==[.5,541/1080] and not result['imputed']
    rows[0]['run_seed']=13012
    with pytest.raises(ValueError,match='identity'):m.strict_summary(cells,rows)


def checkpoints(successes,missing=(0,0,0,0)):
    return [{'boundary':i+1,'summary':{'declared':1080,'task_count':135,'samples_per_task':8,
        'successes':n,'missing':q,'measured':1080-q}} for i,(n,q) in enumerate(zip(successes,missing))]


def test_exact_ties_select_later_and_missing_outcome_ordering_stays_unresolved():
    assert m.select(checkpoints([10,20,20,19]))['boundary']==3
    assert m.select(checkpoints([20,20,20,20]))['boundary']==4
    result=m.select(checkpoints([10,20,20,19],[0,0,0,2]))
    assert result['status']=='INCONCLUSIVE' and result['boundary'] is None and not result['test_admitted']
    assert m.select(checkpoints([10,20,20,19],[2,0,0,1]))['status']=='INCONCLUSIVE'
    assert m.select(checkpoints([10,20,20,19],[2,0,0,0]))['boundary']==3
    with pytest.raises(ValueError,match='all four'):m.select(checkpoints([10,20,20]))
