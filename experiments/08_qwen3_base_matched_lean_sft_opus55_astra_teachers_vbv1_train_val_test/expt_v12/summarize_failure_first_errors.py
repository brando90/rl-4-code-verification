"""Classify the first retained compiler diagnostic per failed validation output without revealing task source to teachers."""
import collections
import csv
import json
from pathlib import Path
import re
from assemble import ROOT,write

def category(line):
    text=line.lower()
    if "tactic 'native_decide' evaluated that the proposition" in text:return 'native_decide_false_proposition'
    if 'type mismatch' in text:return 'type_mismatch'
    if 'unknown' in text:return 'unknown_name_or_tactic'
    if any(t in text for t in ['unexpected','expected token','invalid field','invalid constructor']):return 'syntax_or_invalid_notation'
    if 'unsolved goals' in text:return 'unsolved_goals'
    if 'synthesize' in text or 'typeclass' in text:return 'instance_inference'
    if 'tactic' in text or 'simp made no progress' in text:return 'tactic_failure'
    return 'other_first_diagnostic'

def main():
    folder=ROOT/'analysis/failure_diagnostics_current';rows=[];representatives={}
    for path in (folder/'cells').glob('*/*/diagnostic.json'):
        result=json.loads(path.read_text());text=(path.parent/'compile.log').read_text()
        match=re.search(r'^.*?:\d+:\d+: error:\s*(.*)$',text,re.M)
        first=category(match.group(1)) if match else 'diagnostic_timeout' if result['returncode']==124 else 'diagnostic_recompile_passed' if result['returncode']==0 else 'other_no_formatted_error'
        row=dict(task_id=result['task_id'],sample_idx=result['sample_idx'],first_diagnostic_category=first,source_sha256=result['source_sha256'],returncode=result['returncode']);rows.append(row)
        representatives.setdefault(first,dict(task_id=result['task_id'],sample_idx=result['sample_idx'],source_sha256=result['source_sha256'],analysis_only_log=str(path.parent/'compile.log')))
    assert len(rows)==851,'Classify the full frozen failure cohort; do not report a partial sweep as complete'
    with (folder/'first_error_cells.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(sorted(rows,key=lambda r:(r['task_id'],r['sample_idx'])))
    summary=dict(state='DONE',declared_failed_outputs=851,checked=len(rows),mutually_exclusive_first_diagnostic_categories=dict(collections.Counter(r['first_diagnostic_category'] for r in rows)),representatives_analysis_only=representatives,interpretation='First reported diagnostic is a useful local symptom, not a proven causal root cause. False native_decide propositions can reflect an incorrect implementation, test or theorem; this label does not identify which.',validation_content_sent_to_teachers=False)
    write(folder/'first_error_summary.json',summary);print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
