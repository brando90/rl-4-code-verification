"""Create an owned tokenizer runtime and verify four supplementary prototypes on the cluster."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).parent
venv=ROOT/'runtime/venv'
subprocess.run([sys.executable,'-m','venv',str(venv)],check=True)
python=venv/'bin/python'
subprocess.run([str(python),'-m','pip','install','--disable-pip-version-check','transformers==4.56.2','jinja2==3.1.6'],check=True)
subprocess.run([str(python),'-c',"from transformers import AutoTokenizer;AutoTokenizer.from_pretrained('Qwen/Qwen3-8B-Base',revision='49e3418fbbbca6ecbdf9608b4d22e5a407081db4',cache_dir="+repr(str(ROOT/'runtime/huggingface'))+")"],check=True)
tasks={t['task_id']:t for t in map(json.loads,(ROOT/'manifest.jsonl').read_text().splitlines())}
mapping={'addition':'tiny_integer_arithmetic_01','boolean':'tiny_boolean_logic_07','concatenation':'tiny_list_concatenation_01','default_head':'tiny_safe_indexing_02'}
reports=[]
for name,tid in mapping.items():
    folder=ROOT/'prototype_checks'/name;folder.mkdir(parents=True,exist_ok=True)
    (folder/'Solution.lean').write_text((ROOT/'prototypes'/f'{name}.lean').read_text())
    p=subprocess.run([str(python),str(ROOT/'check_example.py'),'--task',tid,'--folder',str(folder)],cwd=ROOT,text=True,capture_output=True)
    reports.append({'prototype':name,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
(ROOT/'runtime/setup_report.json').write_text(json.dumps(reports,indent=2))
print(json.dumps(reports),flush=True)
if not all(r['exit']==0 for r in reports):raise SystemExit(1)
(ROOT/'runtime/READY').write_text('tokenizer and four prototypes verified\n')
