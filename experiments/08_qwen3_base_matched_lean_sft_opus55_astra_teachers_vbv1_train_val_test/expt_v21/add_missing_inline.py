"""Insert truthful proof comments with exact two-source provenance; no Lean/model calls."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'expt_v8'))
from comment_integrity import safe_line_starts
EXPLANATIONS={
 'rfl':'Both sides reduce to the same expression.',
 'exact':'Use the displayed explicit proof term to close this obligation.',
 'apply':'Apply the displayed lemma and prove its required premises.',
 'refine':'Construct the displayed proof term and fill its remaining goals.',
 'rw':'Rewrite using the displayed equalities.',
 'erw':'Rewrite using the displayed equalities and their elaborated arguments.',
 'unfold':'Expand the displayed definitions before proving the obligation.',
 'change':'Restate the goal as the displayed definitionally equal expression.',
 'intro':'Introduce the quantified arguments or hypotheses.',
 'rintro':'Introduce and unpack the displayed arguments or hypotheses.',
 'constructor':'Construct the required value and prove its fields.',
 'cases':'Separate the displayed value or hypothesis into constructor cases.',
 'rcases':'Unpack the displayed hypothesis into its given components.',
 'induction':'Use induction on the displayed object and prove each case.',
 'have':'Establish the displayed intermediate fact for the following steps.',
 'calc':'Chain the displayed equality or order steps.',
 'show':'State the next goal explicitly before proving it.',
 'subst':'Substitute the displayed equality into the remaining goal.',
 'funext':'Prove the function equality pointwise on the displayed arguments.',
}
def sha(value):return hashlib.sha256(value.encode()).hexdigest()
def require(condition,message):
 if not condition:raise ValueError(message)
def meaningful_comments(proof):
 return any(re.search(r'[A-Za-z]{3}',line) for line in re.findall(r'(?m)^\s*--([^\n]+)',proof))
def insertion(proof,strip_comments,base_indent=''):
 require(not meaningful_comments(proof),'Meaningful inline comment already exists')
 match=re.match(r'\s*by([ \t]*\n|[ \t]+)',proof)
 require(match is not None,'Unsupported non-by proof')
 code=strip_comments(proof)[match.end():]
 first=next((line.strip() for line in code.splitlines() if line.strip()),'')
 tactic=re.match(r'(?:·\s*)?([A-Za-z_]+)\b',first)
 require(tactic is not None and tactic[1] in EXPLANATIONS,'Unsupported visible first tactic')
 explanation=EXPLANATIONS[tactic[1]]
 if '\n' in match[1]:
  line=next((line for line in proof[match.end():].splitlines() if line.strip()),'  ')
  indent=re.match(r'[ \t]*',line)[0] or base_indent+'  '
  text=indent+'-- '+explanation+'\n'
 else:
  indent=base_indent+'  ';text='\n'+indent+'-- '+explanation+'\n'+indent
 return dict(at=match.end(),text=text,tactic=tactic[1],comment=explanation)
def annotate_checked_source(source,proof_spans,strip_comments):
 safe_line_starts(source)
 edits=[];unsupported=[]
 for span in proof_spans:
  start,end=span['start'],span['end'];proof=source[start:end]
  require(sha(proof)==span['proof_sha256'],'Proof-span source hash differs')
  if meaningful_comments(proof):continue
  try:
   indent=re.match(r'[ \t]*',source[:start].rsplit('\n',1)[-1])[0]
   item=insertion(proof,strip_comments,indent)
  except ValueError as exc:
   unsupported.append(dict(index=span['index'],reason=str(exc)));continue
  edits.append(dict(index=span['index'],at=start+item['at'],text=item['text'],tactic=item['tactic'],comment=item['comment']))
 require(edits,'No supported visible operation for truthful comment insertion')
 annotated=source
 for edit in sorted(edits,key=lambda row:row['at'],reverse=True):
  annotated=annotated[:edit['at']]+edit['text']+annotated[edit['at']:]
 safe_line_starts(annotated)
 old_tokens=strip_comments(source).split();new_tokens=strip_comments(annotated).split()
 require(old_tokens==new_tokens,'Non-comment proof tokens changed')
 require(meaningful_comments(annotated),'Inserted inline comment missing')
 binding=dict(method='deterministic_comment_insertions_describing_visible_first_tactic',
  checked_source_sha256=sha(source),annotated_source_sha256=sha(annotated),
  original_bytes_preserved=True,noncomment_tokens_unchanged=True,
  noncomment_tokens_sha256=sha(json.dumps(old_tokens,ensure_ascii=False)),
  balanced_lexical_contexts=True,insertions=edits,unsupported_proof_operations=unsupported,
  compiler_calls=0,model_calls=0)
 return annotated,binding
def controls():
 strip=lambda value:re.sub(r'--[^\n]*','',value)
 for source in ['by\n  rfl','by rfl','by\n  unfold ident\n  rfl']:
  span=dict(index=0,start=0,end=len(source),proof_sha256=sha(source))
  annotated,binding=annotate_checked_source(source,[span],strip)
  require(binding['original_bytes_preserved'] and binding['noncomment_tokens_unchanged'],'Insertion control failed')
  replay=source
  for item in sorted(binding['insertions'],key=lambda row:row['at'],reverse=True):
   replay=replay[:item['at']]+item['text']+replay[item['at']:]
  require(replay==annotated,'Exact insertion replay failed')
 for source in ['by\n  unsupported_tactic','by\n  -- Existing explanation.\n  rfl']:
  try:annotate_checked_source(source,[dict(index=0,start=0,end=len(source),proof_sha256=sha(source))],strip)
  except ValueError:pass
  else:raise AssertionError('Unsupported/already-commented control accepted')
 print(json.dumps(dict(passed=True,insertion_controls=3,rejection_controls=2,exact_insertion_replay=True,compiler_calls=0,model_calls=0)))
if __name__=='__main__':
 require(sys.argv[1:]==['--controls'],'This adapter is called only by finalize_tiny.py; --controls is the only standalone command')
 controls()
