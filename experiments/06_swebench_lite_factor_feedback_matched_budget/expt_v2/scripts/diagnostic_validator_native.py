"""Reproduce the exact diagnostic-check validator recovered from the first native coordinator log."""
import hashlib,json,os,re,shlex,sys
from pathlib import Path
receipts, output=map(Path,sys.argv[1:])
if output.exists() or output.is_symlink(): raise SystemExit('refusing to overwrite frozen checks')
allowed={'python','python3','pytest','py.test'}
forbidden=re.compile(r'[;&|<>"'"'`$"'"\\n\\r]')
def parse(result):
    text=result.strip()
    if text.startswith('```'):
        text='\n'.join(text.splitlines()[1:-1])
    return json.loads(text)
def validate(command):
    if not isinstance(command,str) or not command or len(command)>400 or forbidden.search(command): return False,'unsafe_or_empty_command'
    try: words=shlex.split(command)
    except ValueError: return False,'invalid_shell_quoting'
    if not words or words[0] not in allowed: return False,'unapproved_executable'
    if any(word.startswith('/') or word == '..' or word.startswith('../') for word in words): return False,'unsafe_path'
    return True,None
items=[]
for path in sorted(receipts.glob('diagnostic_author_*.json')):
    r=json.loads(path.read_text())
    task=path.stem.removeprefix('diagnostic_author_')
    record={'instance_id':task,'author_receipt_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'status':r['status'],'checks':None,'invalid_reason':None}
    try:
        raw=r['native_response']['result']; candidate=parse(raw)
        if set(candidate)!={'syntax_commands','regression_commands','issue_commands','notes'}: raise ValueError('unexpected_json_schema')
        if not isinstance(candidate['notes'],str): raise ValueError('notes_not_string')
        checked={}
        invalid=[]
        for name in ('syntax_commands','regression_commands','issue_commands'):
            commands=candidate[name]
            if not isinstance(commands,list) or not commands: invalid.append(name+'_empty'); continue
            accepted=[]
            for command in commands:
                ok,reason=validate(command)
                if ok: accepted.append(command)
                else: invalid.append(name+':'+reason)
            checked[name]=accepted
        if invalid or any(not checked.get(name) for name in ('syntax_commands','regression_commands','issue_commands')):
            record['status']='invalid_check_definition';record['invalid_reason']=';'.join(invalid or ['empty_after_validation'])
        else:
            record['checks']={**checked,'notes':candidate['notes']}
    except Exception as exc:
        record['status']='invalid_check_definition';record['invalid_reason']=type(exc).__name__+':'+str(exc)
    items.append(record)
if len(items)!=8 or len({x['instance_id'] for x in items})!=8: raise SystemExit('expected exactly eight unique author receipts')
value={'schema_version':1,'panel_manifest_sha256':'68dc55c9a0ea1bf7191fe23dd28fbc0a655f0a718a2dc487bbedb72b638bba46','author_calls':8,'tasks':items}
payload=json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()+b'\n'
fd=os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as f:f.write(payload);f.flush();os.fsync(f.fileno())
print(json.dumps({'sha256':hashlib.sha256(payload).hexdigest(),'valid':sum(x['checks'] is not None for x in items),'invalid':sum(x['checks'] is None for x in items),'statuses':{x['instance_id']:x['status'] for x in items}},sort_keys=True))
