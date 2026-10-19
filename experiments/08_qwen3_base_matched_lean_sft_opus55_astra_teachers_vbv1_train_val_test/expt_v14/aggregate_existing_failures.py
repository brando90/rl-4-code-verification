"""Summarize existing compiler receipts into generic categories without exporting protected task text."""
import argparse
import collections
import json
from pathlib import Path
import re
import time

PATTERNS={
    'unknown_identifier_or_constant':r'unknown (?:identifier|constant)',
    'type_mismatch':r'type mismatch|has type.*but is expected',
    'unsolved_goals':r'unsolved goals',
    'missing_instance':r'failed to synthesize|synthesiz(?:e|ation).*failed',
    'invalid_field_or_projection':r'invalid field|invalid projection',
    'parser_error':r'unexpected token|expected token|unexpected end of input|unterminated',
    'recursion_or_termination':r'termination|structural recursion|recursive application',
    'tactic_failed':r'tactic.*failed|rewrite.*failed',
    'resource_timeout':r'timed out|timeout|maximum recursion depth|maximum number of heartbeats',
    'no_goals':r'no goals to be solved',
}


def main():
    p=argparse.ArgumentParser();p.add_argument('--checks-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    counts=collections.Counter();cohorts=collections.defaultdict(collections.Counter)
    for path in sorted(args.checks_root.glob('*/result.json')):
        result=json.loads(path.read_text());cohort=result.get('cohort','unknown')
        counts['files_checked']+=1;cohorts[cohort]['files_checked']+=1
        if result.get('compiles'):
            counts['compiled']+=1;cohorts[cohort]['compiled']+=1;continue
        counts['compile_failures']+=1;cohorts[cohort]['compile_failures']+=1
        kernel_file=path.parent/'kernel.json'
        if not kernel_file.exists():counts['missing_kernel_receipt']+=1;continue
        kernel=json.loads(kernel_file.read_text())
        text='\n'.join([kernel.get('stderr_tail','')]+[str(x.get('msg','')) for x in kernel.get('probe_errors',[])])
        matched=False
        for category,pattern in PATTERNS.items():
            if re.search(pattern,text,re.I|re.S):
                counts[category]+=1;cohorts[cohort][category]+=1;matched=True
        if not matched:counts['unclassified_compile_failure']+=1;cohorts[cohort]['unclassified_compile_failure']+=1
    summary=dict(observed_unix=time.time(),source=str(args.checks_root),counts=dict(counts),
        cohorts={k:dict(v) for k,v in cohorts.items()},unit='file; categories overlap',
        protected_content_exported=False,teacher_inputs='generic category labels and counts only',
        limit='Matches stored diagnostic messages, not independently relabeled root causes')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,sort_keys=True))


if __name__=='__main__':main()
