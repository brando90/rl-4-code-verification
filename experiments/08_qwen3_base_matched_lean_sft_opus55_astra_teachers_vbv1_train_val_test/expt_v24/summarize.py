"""Apply a common error classifier to retained diagnostics; never compile or change a scored verdict."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
from classify_diagnostics import OUT, ERROR, classify, write, sha

original=json.loads((OUT/'summary.json').read_text());assert original['state']=='COMPLETE'
rows=list(csv.DictReader((OUT/'all_cells.csv').open()));assert len(rows)==3240
for row in rows:
    v=int(row['run']);sample=int(row['sample_idx']);tid=row['task_id']
    if row['first_category'] in ['success','no_extracted_lean']:continue
    folder=OUT/f'v{v}'/'cells'/f's{sample}'/tid
    d=json.loads((folder/'diagnostic.json').read_text())
    a=(folder/'stdout.log').read_bytes();b=(folder/'stderr.log').read_bytes()
    assert sha(a)==d['stdout_sha256'] and sha(b)==d['stderr_sha256']
    source=Path(d['source_path']).read_bytes();assert sha(source)==d['source_sha256']
    text=a.decode(errors='replace')+'\n'+b.decode(errors='replace')
    category,first,flags=classify(text,d['returncode'])
    m=ERROR.search(text);line=''
    if m:
        lines=source.decode().splitlines();n=int(m.group(1));line=lines[n-1] if 0<n<=len(lines) else ''
        if re.search(r'\bnative_decide\b',line):flags.append('native_decide_at_first_error_location')
        if re.search(r'(?<!\w)decide(?!\w)',line):flags.append('decide_at_first_error_location')
        if re.search(r'\bDecidable(?:Pred|Eq)?\b',first):flags.append('decidable_instance_in_first_error')
    row.update(first_category=category,first_error=first,first_error_source_line=line,error_flags=json.dumps(sorted(set(flags))))
summaries={}
for v in [12,20,23]:
    rs=[r for r in rows if int(r['run'])==v];assert len(rs)==1080
    summaries[str(v)]=dict(declared=1080,first_diagnostic_categories=dict(collections.Counter(r['first_category'] for r in rs)),overlapping_error_flags=dict(collections.Counter(f for r in rs for f in json.loads(r.get('error_flags') or '[]'))))
fields=list(rows[0])
with (OUT/'classified_cells.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
result=dict(state='COMPLETE',runs=summaries,classification_source_sha256=sha(Path(__file__).with_name('classify_diagnostics.py').read_bytes()),all_cells_sha256=sha((OUT/'classified_cells.csv').read_bytes()),first_diagnostic_not_proven_root_cause=True,diagnostic_timeout_seconds=20,diagnostic_timeouts_not_official_timeouts=True,official_verdicts_changed=False,model_calls=0)
write(OUT/'classified_summary.json',result);print(json.dumps(result,indent=2))
