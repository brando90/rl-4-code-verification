"""Run global dataset admission after all generation workers finish, without additional model calls."""
import json
import os
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).parent
end=time.monotonic()+4500
while time.monotonic()<end:
    rows=[]
    for p in (ROOT/'runtime/status').glob('*.json'):
        try:rows.append(json.loads(p.read_text()))
        except json.JSONDecodeError:pass
    receipt={'observed_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'pid':os.getpid(),'phase':'WAITING_FOR_GENERATION','workers':len(rows),'locally_verified':sum(r['accepted'] for r in rows)}
    (ROOT/'runtime/admission_watch.json').write_text(json.dumps(receipt,indent=2))
    if len(rows)==25 and all(r['state'] in ['DONE','INCOMPLETE','BLOCKED','TIMEOUT','DEAD'] for r in rows):break
    time.sleep(15)
else:raise SystemExit('finite admission watch deadline reached')
with (ROOT/'runtime/admission.log').open('w') as log:
    p=subprocess.run([str(ROOT/'runtime/venv/bin/python'),str(ROOT/'finalize_dataset.py')],stdout=log,stderr=subprocess.STDOUT)
receipt.update(phase='FINISHED' if p.returncode==0 else 'FAILED',exit_code=p.returncode)
(ROOT/'runtime/admission_watch.json').write_text(json.dumps(receipt,indent=2))
