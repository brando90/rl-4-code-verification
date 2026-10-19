"""Exercise budget termination and dead-driver recovery with harmless ordinary-code children."""
import json
from pathlib import Path
import sys
import tempfile
import time
import budget_ledger as budget
import watch_cleaned as watch
from clean_existing import base

def main():
    old_path=budget.PATH;old_root=watch.clean.ROOT
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);budget.PATH=root/'budget.json';profile=root/'profile'
        code='''import json,pathlib,time
p=pathlib.Path('''+repr(str(profile))+''')/'sessions/control.jsonl';p.parent.mkdir(parents=True)
p.write_text(json.dumps(dict(type='event_msg',payload=dict(type='token_count',info=dict(total_token_usage=dict(input_tokens=300000,cached_input_tokens=0,output_tokens=1),model_context_window=121600))))+'\\n')
time.sleep(20)
'''
        receipt=budget.run_cli([sys.executable,'-c',code],dict(__import__('os').environ),'','cleanup','control',profile,root,root/'child.log',stop_at=1.2)
        assert receipt['stop_reason']=='conservative_configured_price_stop'
        assert receipt['returncode']!=0 and receipt['conservative_charge_usd']>1.2
        assert not budget.snapshot()['reservations']
        watch.clean.ROOT=root/'watch';folder=watch.clean.ROOT/'cases/dead_control'
        row=dict(task_id='dead_control',state='CLAIMED',driver_pid=99999999,attempts=2)
        base.write(folder/'status.json',row);watch.recover([row])
        assert json.loads((folder/'status.json').read_text())['state']=='FALLBACK'
    budget.PATH=old_path;watch.clean.ROOT=old_root
    result=dict(state='PASS',ordinary_child_usage_guard_killed=True,settlement_releases_exposure=True,dead_driver_recovery=True,no_model_calls=True,observed_unix=time.time())
    base.write(old_root/'guard_controls.json',result);print(json.dumps(result))

if __name__=='__main__':main()
