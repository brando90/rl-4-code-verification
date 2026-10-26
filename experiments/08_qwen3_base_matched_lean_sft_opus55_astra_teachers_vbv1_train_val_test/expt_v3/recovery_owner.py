"""Launch one fixed authenticated continuation, recording its process identity and native outcome."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
from recovery_watch import identity, read, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--attempt', required=True)
    args = parser.parse_args()
    config = read(args.root / 'recovery_config.json')
    candidate = next(c for c in config['candidates'] if c['name'] == args.candidate and c['eligible'])
    experiment = Path(config['experiment'])
    prompt = (experiment / 'RUNBOOK_continuation_owner.md').read_text().splitlines()[2] + '\n\n'
    prompt += f'''Continue the already-authorized E08 v3 experiment end to end as its sole writer, attempt {args.attempt}.
Read {experiment}/CKPT_e08_v3.md and RUNBOOK_continuation_owner.md, then {args.root}/recovery_dispatch.json.
For this recovery verify the current hashes in recovery_dispatch.json; continuation_dispatch_v3.json remains the immutable initial transfer record and its old checkpoint hash is historical.
Verify your actual model, effort, full access and training token counts and write {args.root}/owner_ack.json using the existing schema with your current process identity and attempt. The previous writer has exited or explicitly released ownership. Preserve/adopt healthy scheduler and training children; reconcile exact identities before any restart.
Inspect recovery_state.json, recovery_config.json and native error evidence. Write recovery owner process identity using boot_id/start_ticks, and verify first useful workload output. All required experiment work remains authorized: complete Phase A and implement/complete Phase B, validation, namespace diagnostic, paired bootstrap, forecast assessment, publication and DONE notification. Never stop at acknowledgement.
The experiment results.md is the live ledger: update, commit and push it whenever a meaningful result lands. Scientific data/model/sampling/token budgets are frozen; zero paid model calls and test split unopened. Complete every declared one of 17,280 cells; preserve missing/failed cells and do not alter scientific caps on recovery.
You are the persistent owner. The host cron watch survives your process; inspect it and keep its finite route inventory current at meaningful events. Use direct commands for deterministic work and reserve coordination allowance. Finish authorized work; only report an external blocker after independent work is complete, with a real event-driven continuation. Final success requires checked results, publication and actual completion notification.
'''
    env = os.environ.copy()
    for key in ('OPENAI_API_KEY', 'OPENAI_BASE_URL', 'CODEX_API_KEY', 'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN'):
        env.pop(key, None)
    env.update(candidate.get('env', {}))
    env['E08_V3_OWNER_ATTEMPT'] = args.attempt
    record = {'identity': identity(os.getpid()), 'attempt': args.attempt, 'candidate': candidate['name'],
              'started_unix': time.time(), 'status': 'STARTING'}
    write(args.root / 'recovery_owner_process.json', record)
    with (args.root / f'{args.attempt}_events.jsonl').open('w') as output, (args.root / f'{args.attempt}_stderr.log').open('w') as error:
        process = subprocess.Popen([*candidate['command'], prompt], cwd=config['checkout'], env=env,
                                   stdin=subprocess.DEVNULL, stdout=output, stderr=error)
        record.update(child=identity(process.pid), status='RUNNING')
        write(args.root / 'recovery_owner_process.json', record)
        code = process.wait()
    record.update(exit_code=code, ended_unix=time.time(), status='EXITED')
    write(args.root / 'recovery_owner_process.json', record)
    write(args.root / f'{args.attempt}_exit.json', record)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
