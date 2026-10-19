"""Count tactic words in actual generated Lean after removing nested comments and strings, retaining every cell."""
import csv
import hashlib
import json
import re
from assemble import ROOT,write

TACTICS=['exact?','apply?','simp?','simpa?','simp','simpa','simp_all','omega','aesop','linarith','nlinarith','norm_num','ring','native_decide']

def masked(source):
    out=[];i=0;depth=0;line=False;string=False
    while i<len(source):
        char=source[i];pair=source[i:i+2]
        if line:
            if char=='\n':line=False;out.append('\n')
            i+=1
        elif depth:
            if pair=='/-':depth+=1;i+=2
            elif pair=='-/':depth-=1;i+=2
            else:i+=1
        elif string:
            if char=='\\':i+=2
            elif char=='"':string=False;i+=1
            else:i+=1
        elif pair=='--':line=True;i+=2;out.append(' ')
        elif pair=='/-':depth=1;i+=2;out.append(' ')
        elif char=="'" and i+2<len(source) and source[i+2]=="'":i+=3;out.append(' ')
        elif char=="'" and i+3<len(source) and source[i+1]=='\\' and source[i+3]=="'":i+=4;out.append(' ')
        elif char=='"':string=True;i+=1;out.append(' ')
        else:out.append(char);i+=1
    return ''.join(out)

def main():
    folder=ROOT/'analysis/failure_diagnostics_current'
    raw=[json.loads(s) for s in (ROOT/'validation/v12_current/raw.jsonl').read_text().splitlines()]
    scores={(r['task_id'],r['sample_idx']):r for r in map(json.loads,(ROOT/'validation/v12_current/scored.jsonl').read_text().splitlines())}
    assert len(raw)==len(scores)==1080
    counts={t:dict(extracted_outputs=0,failed_outputs=0,compiled_outputs=0) for t in TACTICS};rows=[]
    patterns={t:re.compile(r"(?<![A-Za-z0-9_'])"+re.escape(t)+r"(?![A-Za-z0-9_'?])") for t in TACTICS}
    for row in raw:
        lean=row.get('lean') or '';code=masked(lean);compiled=scores[row['task_id'],row['sample_idx']]['compiles']
        result=dict(task_id=row['task_id'],sample_idx=row['sample_idx'],extracted=bool(lean.strip()),compiles=compiled,source_sha256=hashlib.sha256(lean.encode()).hexdigest() if lean else '')
        for tactic,pattern in patterns.items():
            present=bool(pattern.search(code));result[tactic]=present
            if present:
                counts[tactic]['extracted_outputs']+=1;counts[tactic]['compiled_outputs' if compiled else 'failed_outputs']+=1
        rows.append(result)
    with (folder/'tactic_presence_cells.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(sorted(rows,key=lambda r:(r['task_id'],r['sample_idx'])))
    summary=dict(state='DONE',declared=1080,extracted=sum(r['extracted'] for r in rows),failed_extracted=sum(r['extracted'] and not r['compiles'] for r in rows),compiled=sum(r['compiles'] for r in rows),tactic_presence_counts=counts,scope='Lexical occurrences in actual extracted Lean after nested comments and quoted strings removed; categories overlap, presence is not blame. Unextracted/truncated partial source is not counted as an extracted Lean file.')
    write(folder/'tactic_presence.json',summary);print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
