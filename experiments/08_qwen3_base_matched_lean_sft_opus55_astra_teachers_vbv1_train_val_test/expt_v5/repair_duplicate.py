"""Queue a bounded continuation for one globally duplicate counting example after its current writer exits."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).parent
topic='list_counting';tid='tiny_list_counting_14';other='tiny_list_counting_01'
worker=ROOT/'workers'/topic
feedback='''

## Global admission feedback

tiny_list_counting_14 is byte-identical to tiny_list_counting_01. Preserve both fixed Python programs and all accepted task files. For task 14, add a genuinely distinct, informative general specification: the occurrence count is at most the input list length. Prove it with an appropriate standard lemma or short proof. Preserve its existing append property and tests. A rename alone does not resolve the duplicate. Run the canonical checker on task 14, preserve the other 19 accepted examples, and finish with 20 verified examples. Keep the full response below 1000 Qwen tokens.
'''
brief=worker/'RUNBOOK.md'
if '## Global admission feedback' not in brief.read_text():brief.write_text(brief.read_text()+feedback)
end=time.monotonic()+3600
while time.monotonic()<end:
    status=json.loads((ROOT/'runtime/status'/f'{topic}.json').read_text())
    if status['state'] in ['DONE','INCOMPLETE','BLOCKED','TIMEOUT','DEAD']:break
    time.sleep(5)
else:raise SystemExit('Current writer did not exit before finite repair-watch deadline')
one=worker/'examples'/tid;two=worker/'examples'/other
if one.joinpath('Solution.lean').read_bytes()!=two.joinpath('Solution.lean').read_bytes():raise SystemExit('duplicate already resolved')
receipt=one/'receipts/verification.json';old=json.loads(receipt.read_text())
(one/'receipts/verification_before_global_repair.json').write_text(json.dumps(old,indent=2))
old.update(accepted=False,error='global duplicate: add an informative count <= length theorem')
receipt.write_text(json.dumps(old,indent=2))
attempt=status.get('attempt',0)+1
if attempt>2:raise SystemExit('Original three-invocation budget exhausted')
session='codex-rl4cv-tiny-list-counting-global'
subprocess.run(['tmux','new-session','-d','-s',session,f'env TINY_START_ATTEMPT={attempt} TINY_SESSION_NAME={session} python3 -u {ROOT}/worker_driver.py {topic} > {worker}/global_repair_driver.log 2>&1'],check=True)
print(json.dumps({'session':session,'attempt':attempt,'task_id':tid}),flush=True)
