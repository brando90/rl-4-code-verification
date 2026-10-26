"""Extend the proof preference from the measured tactic inventory and queue only additional affected cases."""
from __future__ import annotations

import json
import fcntl
from pathlib import Path
import shutil
import time

import prefer_explicit as selection
from prefer_explicit import base
import review_flagged as review

EXTRA={'solve_by_elim','apply_rules','simp_rw','ring1','abel','grind','polyrith','finish','itauto','simp_arith','norm_num!','linarith!','nlinarith!','aesop_cat'}


def audit_locked():
    rows=base.read_rows(selection.ROOT/'selection.jsonl')
    workbook=json.loads(base.SOURCE.read_text())
    affected=[];new=[];pending=[]
    for row in rows:
        if row['kind']!='workbook':continue
        item=workbook[row['source_row']]
        folder=review.ROOT/'cases'/row['task_id']
        index=row['proof_index']
        decision=None
        if (folder/'decision.json').exists():
            decision=json.loads((folder/'decision.json').read_text())
            if decision['verified']:index=decision['proof_index']
            else:continue
        matches=set(selection.automations(item['proof'][index])) & EXTRA
        if not matches:continue
        clean=[i for i,p in enumerate(item['proof']) if not selection.automations(p)]
        affected.append(dict(task_id=row['task_id'],remaining_extra_automation=sorted(matches),qualifying_indices=clean))
        if not clean:continue
        notice=('Expanded automation-policy review: avoid '+', '.join(sorted(EXTRA))+', in addition to the original discouraged tactics. '
                'The current selected proof uses '+', '.join(sorted(matches))+'. Supplied fully explicit candidate indices: '+str(clean)+'. '
                'Select and check a suitable explicit candidate for the same statement, if one is valid. Plain exact and explicit linear_combination are allowed.')
        if not folder.exists():
            base.write(folder/'input.json',dict(row,baseline_annotation_issue=notice,all_proof_alternatives=item['proof']))
            route='TERRA_PENDING' if (review.ROOT/'routing_amendment.json').exists() else 'PENDING'
            base.write(folder/'status.json',dict(state=route,attempts=0));new.append(row['task_id'])
        elif decision and decision['verified']:
            status=json.loads((folder/'status.json').read_text())
            if status['state']!='DONE' or status.get('attempts',2)>=2:continue
            if (folder/'expanded_policy.json').exists():continue
            shutil.copy2(folder/'input.json',folder/'input_initial_policy.json')
            data=json.loads((folder/'input.json').read_text());data['baseline_annotation_issue']+='\n'+notice
            base.write(folder/'input.json',data);base.write(folder/'expanded_policy.json',dict(reason=notice,observed_unix=time.time()))
            base.write(folder/'status.json',dict(status,state='POLICY_PENDING'));pending.append(row['task_id'])
    summary=dict(avoid_tactics=list(selection.AUTOMATION),
        additional_tactics=sorted(EXTRA),affected=affected,new_review_cases=new,deferred_policy_rechecks=pending,
        preserve_original_selection_manifest=True,linear_combination_allowed=True,linsolve_occurrences=0,observed_unix=time.time())
    base.write(selection.ROOT/'automation_inventory_amendments'/f'{time.time_ns()}.json',summary)
    base.write(selection.ROOT/'automation_inventory_amendment.json',summary)
    print(json.dumps(dict(affected=len(affected),new_review_cases=len(new),policy_rechecks=len(pending))),flush=True)


def main():
    with (review.ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        audit_locked()


if __name__=='__main__':main()
