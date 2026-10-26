"""Verify the extended cleanup budget on a private mock ledger and reuse actual frozen proof-policy controls."""
import json
import argparse
import os
from pathlib import Path
import tempfile
import sys
import time
import repair_batches as repair
from repair_batches import budget,write

def main(mock_only=False):
    old=budget.PATH
    with tempfile.TemporaryDirectory() as td:
        budget.PATH=Path(td)/'budget.json'
        write(budget.PATH,dict(total_authorized=900,tranche2activated=True,reservations={},charges={'prior':dict(purpose='cleanup',usd=469.99)},events=[]))
        assert budget.reserve('one','cleanup',10)
        assert not budget.snapshot().get('tranche3activated')
        assert budget.reserve('two','cleanup',10)
        assert budget.snapshot()['tranche3activated']
        assert not budget.reserve('purpose_overflow','cleanup',310)
        assert not budget.reserve('adaptation_overflow','adaptation',121)
        budget.settle('one',dict(input_tokens=1000,cached_input_tokens=0,output_tokens=100))
        budget.settle('one',dict(input_tokens=1000,cached_input_tokens=0,output_tokens=100))
        assert not budget.snapshot().get('hard_hold')
        profile=Path(td)/'profile'
        code='import json,pathlib,time; p=pathlib.Path('+repr(str(profile))+')/"sessions/control.jsonl"; p.parent.mkdir(parents=True); p.write_text(json.dumps(dict(type="event_msg",payload=dict(type="token_count",info=dict(total_token_usage=dict(input_tokens=300000,cached_input_tokens=0,output_tokens=1),model_context_window=121600))))+"\\n"); time.sleep(20)'
        run=budget.run_cli([sys.executable,'-c',code],dict(os.environ),'','cleanup','ordinary_child_control',profile,Path(td),Path(td)/'child.log',model='gpt-5.6-terra')
        assert run['stop_reason']=='conservative_configured_price_stop' and run['returncode']!=0
        assert 'ordinary_child_control' not in budget.snapshot()['reservations']
        saved=(repair.INSPECTOR_SHA,repair.prior.FROZEN,repair.ROOT)
        try:
            fixture=Path(td)/'inspector.py';fixture.write_text('pinned test fixture\n')
            repair.INSPECTOR_SHA=repair.base.sha(fixture.read_bytes());repair.prior.FROZEN=fixture;repair.ROOT=Path(td)/'fixture_run'
            repair.assert_inspector()
            fixture.write_text('mutated test fixture\n')
            try:repair.assert_inspector()
            except AssertionError:pass
            else:raise AssertionError('Changed inspector bytes must fail closed.')
        finally:repair.INSPECTOR_SHA,repair.prior.FROZEN,repair.ROOT=saved
    budget.PATH=old
    if mock_only:
        result=dict(state='PASS',mock_third_tranche_activation=True,mock_caps_reject=True,idempotent_settlement=True,actual_harmless_child_usage_stop=True,inspector_mutation_fixture_rejected=True,no_model_calls=True,observed_unix=time.time())
        write(repair.HERE/'results/mock_controls.json',result);print(json.dumps(result));return
    repair.assert_inspector()
    oldroot=repair.prior.ROOT
    oldmain=repair.ROOT
    try:
        repair.prior.selftest()
        repair.ROOT=repair.prior.ROOT
        repair.salvage('control',repair.ROOT/'workers/lane_00/control')
        assert repair.read(repair.ROOT/'cases/control/status.json')['verified']
    finally:repair.prior.ROOT=oldroot;repair.ROOT=oldmain
    result=dict(state='PASS',mock_third_tranche_activation=True,mock_caps_reject=True,idempotent_settlement=True,actual_frozen_kernel_positive_negative=True,automation_policy_negative=True,saved_kernel_success_survives_bad_final_draft=True,no_model_calls=True,observed_unix=time.time())
    write(repair.ROOT/'controls.json',result);print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mock-only',action='store_true');a=p.parse_args();main(a.mock_only)
