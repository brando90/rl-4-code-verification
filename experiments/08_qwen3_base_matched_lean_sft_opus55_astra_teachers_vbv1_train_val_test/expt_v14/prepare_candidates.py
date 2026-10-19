"""Prepare pinned public Lean source candidates without model calls or claiming training admission."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
AUTOMATION = json.loads((HERE/'automation_policy.json').read_text())['avoid_tactics']

MATHLIB_REV = '79e94a093aff4a60fb1b1f92d9681e407124c2ca'
DEEPSEEK_REV = '1ee889f608fb12ba3596757ee91a60acd663ea81'
DEEPSEEK_SHA = 'a2cdac64d011eee00836ce1a2c5511dfa5567346afabe897c3309ac17771b92b'
TACTICS = re.compile(r"(?<![A-Za-z0-9_'])("+'|'.join(re.escape(t) for t in sorted(AUTOMATION,key=len,reverse=True))+r")(?![A-Za-z0-9_'])")
DECL = re.compile(r'^(?:(?:private|protected|noncomputable)\s+)?(?:theorem|lemma)\s+([A-Za-z_][A-Za-z_0-9\'.]*)\b', re.M)
LATER_COMMAND = re.compile(r'^(?:def|abbrev|instance|class|structure|inductive|axiom|opaque|syntax|macro|elab|attribute|initialize|set_option|export|#)\b', re.M)


def sha(value):
    return hashlib.sha256(value if isinstance(value,bytes) else value.encode()).hexdigest()


def mask_comments_strings(text):
    """Preserve offsets while masking nested comments and quoted strings for conservative discovery."""
    out=list(text);i=0;depth=0;string=False
    while i<len(text):
        if depth:
            if text.startswith('/-',i):out[i:i+2]='  ';depth+=1;i+=2
            elif text.startswith('-/',i):out[i:i+2]='  ';depth-=1;i+=2
            else:
                if text[i]!='\n':out[i]=' '
                i+=1
        elif string:
            if text[i]=='\\' and i+1<len(text):out[i:i+2]='  ';i+=2
            elif text[i]=='"':out[i]=' ';string=False;i+=1
            else:
                if text[i]!='\n':out[i]=' '
                i+=1
        elif text.startswith('/-',i):out[i:i+2]='  ';depth=1;i+=2
        elif text.startswith('--',i):
            end=text.find('\n',i)
            if end<0:end=len(text)
            out[i:end]=' '*(end-i);i=end
        elif text[i]=='"':out[i]=' ';string=True;i+=1
        else:i+=1
    if depth or string:raise ValueError('Unclosed comment/string')
    return ''.join(out)


def assignment(code,start):
    """Find a declaration's top-level assignment; reject unsupported delimiter syntax conservatively."""
    stack=[];pairs={')':'(',']':'[','}':'{','⟩':'⟨'};i=start
    while i<len(code):
        c=code[i]
        if c in '([{⟨':stack.append(c)
        elif c in ')]}⟩':
            if not stack or stack.pop()!=pairs[c]:raise ValueError('Unsupported binder delimiters')
        elif not stack and code.startswith(':=',i):return i
        i+=1
    raise ValueError('No top-level declaration assignment')


def envelope(task_id,lean_source,statement,prefix,**provenance):
    path=f'/home/lean_project/Veribench/{task_id}.lean'
    system='You write clear complete Lean 4 files. Return only the requested FILE marker and one lean code fence. Preserve the supplied declarations and context, with no sorry, admit, new axioms, or native_decide.'
    user=f'Complete the final theorem proof in the following Lean source prefix. Preserve its statement, original imports and context; close any open namespaces or sections. Write the complete file at `{path}`.\n\n```lean\n{prefix.rstrip()}\n-- proof omitted\n```\n\nReturn FILE: {path} followed by one lean code fence containing the complete file.'
    assert lean_source.endswith('\n'), 'Candidate source must end in a newline'
    answer=f'FILE: {path}\n```lean\n{lean_source}```\n'
    return dict(task_id=task_id,formal_statement=statement,source_sha256=sha(lean_source),
                response_sha256=sha(answer),messages=[dict(role='system',content=system),dict(role='user',content=user),dict(role='assistant',content=answer)],
                training_admitted=False,current_kernel_verified=False,needs_comment_policy_check=True,
                admission_pending=['pinned_kernel','target_context','comments','file_template_tokens','global_protected_screen','global_dedup'],**provenance)


def mathlib(args):
    revision=subprocess.check_output(['git','-C',str(args.source),'rev-parse','HEAD'],text=True).strip()
    assert revision==MATHLIB_REV,revision
    # Frozen dependency clone can have generated build products; tracked source changes are forbidden.
    assert not subprocess.check_output(['git','-C',str(args.source),'status','--porcelain','--untracked-files=no'],text=True).strip()
    rows=[];counts=collections.Counter()
    for path in sorted((args.source/'Mathlib').rglob('*.lean')):
        counts['modules_seen']+=1
        original=path.read_text();relative=path.relative_to(args.source).as_posix()
        if len(original)>args.max_chars:counts['too_long']+=1;continue
        code=mask_comments_strings(original)
        matches=list(DECL.finditer(code))
        if not matches:counts['no_named_theorem']+=1;continue
        if TACTICS.search(code):counts['automation_present']+=1;continue
        if re.search(r'\b(?:sorry|admit|axiom|native_decide)\b',code):counts['forbidden_source']+=1;continue
        target=matches[-1]
        try:split=assignment(code,target.end())
        except ValueError:counts['unsupported_statement']+=1;continue
        if LATER_COMMAND.search(code,split+2):counts['later_commands']+=1;continue
        if len(original[split+2:])>args.max_proof_chars:counts['proof_too_long']+=1;continue
        # Imports and all context stay byte-identical; no aggregate Mathlib import is introduced.
        tid='mathlib_'+sha(relative)[:16]
        rows.append(envelope(tid,original,original[target.start():split].strip(),original[:split+2],
            source='mathlib4',source_revision=MATHLIB_REV,source_path=relative,
            theorem_name=target.group(1),license_status='Apache-2.0',source_bytes=len(original.encode())))
        counts['candidates']+=1
        if len(rows)>=args.limit:break
    return rows,dict(counts)


def deepseek(args):
    assert sha(args.source.read_bytes())==DEEPSEEK_SHA,'Pinned source hash mismatch'
    rows=[];counts=collections.Counter()
    for index,line in enumerate(args.source.open()):
        item=json.loads(line);counts['rows_seen']+=1
        assert item['split']=='train'
        statement=item['formal_statement'];proof=item['formal_proof'];header=item['header']
        original=header+'\n'+statement+'\n'+proof+'\n'
        if len(original)>args.max_chars:counts['too_long']+=1;continue
        if len(proof)>args.max_proof_chars:counts['proof_too_long']+=1;continue
        code=mask_comments_strings(original)
        if TACTICS.search(code):counts['automation_present']+=1;continue
        if re.search(r'\b(?:sorry|admit|axiom|native_decide)\b',code):counts['forbidden_source']+=1;continue
        if not DECL.search(mask_comments_strings(statement)):counts['unsupported_statement']+=1;continue
        tid=f'deepseek_v1_{index:06d}'
        rows.append(envelope(tid,original,statement,header+'\n'+statement,
            source='deepseek_prover_v1',source_revision=DEEPSEEK_REV,source_row=index,
            source_name=item['name'],source_split=item['split'],source_artifact_sha256=DEEPSEEK_SHA,
            license_status='license_unresolved_user_authorized',source_bytes=len(original.encode())))
        counts['candidates']+=1
        if len(rows)>=args.limit:break
    return rows,dict(counts)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('kind',choices=['mathlib','deepseek'])
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--limit',type=int,default=512);parser.add_argument('--max-chars',type=int,default=6000)
    parser.add_argument('--max-proof-chars',type=int,default=2500);args=parser.parse_args()
    if args.limit<1:parser.error('--limit must be positive')
    rows,counts=(mathlib if args.kind=='mathlib' else deepseek)(args)
    args.output.mkdir(parents=True,exist_ok=True)
    data=''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows)
    (args.output/'candidates.jsonl').write_text(data)
    summary=dict(source_kind=args.kind,source=str(args.source),counts=counts,candidates=len(rows),
        training_admitted=0,candidates_sha256=sha(data),limits=dict(max_chars=args.max_chars,max_proof_chars=args.max_proof_chars,limit=args.limit),
        selection='short_complete_original_files_without_automation; candidate_discovery_only')
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True))


if __name__=='__main__':main()
