"""Preserve held-out selection, full populations and resource cleanup under the A6 admission route."""
from pathlib import Path
import ast
import importlib
import inspect
import sys
import pytest

P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P))
NAMES=('evaluation_authority','evaluation_snapshot','evaluation_driver','evaluation_supervisor','evaluation_processing')
MODULES={name:importlib.import_module('a6_'+name)for name in NAMES}
ORIGINAL_TESTS={name:importlib.import_module('test_e13_'+name)for name in NAMES}
CASES=[(name,key)for name,module in ORIGINAL_TESTS.items()for key,value in vars(module).items()
       if key.startswith('test_')and callable(value)
       and key!='test_complete_authored_evaluation_recovers_only_missing_neighbors_and_then_stays_closed']

@pytest.mark.parametrize('name,test',CASES)
def test_original_selection_accounting_and_cleanup_guards(tmp_path,monkeypatch,name,test):
    module=ORIGINAL_TESTS[name];monkeypatch.setattr(module,'m',MODULES[name])
    method=getattr(module,test)
    args={'tmp_path':tmp_path,'monkeypatch':monkeypatch}
    method(**{k:args[k]for k in inspect.signature(method).parameters})

@pytest.mark.parametrize('name',NAMES)
def test_all_functions_unchanged_except_explicit_source_names(name):
    def functions(path):
        return {n.name:ast.dump(n,include_attributes=False)for n in ast.parse(path.read_text()).body
                if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    before=functions(P/(name+'.py'));after=functions(P/('a6_'+name+'.py'))
    after={k:v.replace('a6_evaluation_','evaluation_').replace('a6_learning_','learning_')for k,v in after.items()}
    assert before==after

def test_routing_reaches_a6_authority_and_unchanged_runtime():
    import a6_learning_driver,a6_learning_resources
    import evaluation_generation,evaluation_contract,score_evaluation
    assert MODULES['evaluation_authority'].learning_authority is a6_learning_driver.authorize
    assert MODULES['evaluation_snapshot'].learning_authority is a6_learning_driver.authorize
    assert MODULES['evaluation_driver'].authorize is MODULES['evaluation_authority'].authorize
    assert MODULES['evaluation_driver'].reserve is a6_learning_resources.reserve
    assert MODULES['evaluation_supervisor'].snapshot_authority is MODULES['evaluation_authority'].authorize
    assert MODULES['evaluation_processing'].authorize is MODULES['evaluation_authority'].authorize
    assert MODULES['evaluation_processing'].score_manifest is score_evaluation.score_manifest
    assert MODULES['evaluation_snapshot'].validate_manifest is evaluation_generation.validate_manifest
    assert MODULES['evaluation_processing'].strict_summary is evaluation_contract.strict_summary
