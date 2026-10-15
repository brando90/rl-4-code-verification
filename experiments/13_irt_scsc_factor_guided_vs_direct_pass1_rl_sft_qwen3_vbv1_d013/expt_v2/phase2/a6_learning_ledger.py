"""Admit pilot/main runs only from published gates and keep immutable update-stage reservations."""
from __future__ import annotations

import json
from pathlib import Path
import time

from technical_ledger import published, pilot_lock, signature, fence
from training_checkpoint import digest, write_new
from a6_phase2_admission import select_arms_a6

PILOT_SEEDS = {'A': (1301, 1302), 'B': (1301,), 'C': (1301,), 'P': (1301,)}
MAIN_SEEDS = (13011, 13012, 13013)


def verify_learning(plan):
    repo = plan['repository']; lp, science = pilot_lock(plan['LP'], repo)
    phase = plan['phase']; arm = plan['arm']; seed = plan['run_seed']
    if phase not in ('pilot', 'main') or arm not in PILOT_SEEDS:
        raise ValueError('unknown learning run')
    phase1 = {key: published(ref, repo) for key, ref in lp['phase1_results'].items()}
    eligible = select_arms_a6(*(phase1[k] for k in ('G0', 'LP1', 'calibration', 'G1', 'H2', 'A6')))['eligible_arms']
    if arm not in eligible or seed not in (PILOT_SEEDS[arm] if phase == 'pilot' else MAIN_SEEDS):
        raise ValueError('arm or seed is not prospectively admitted')
    for gate in ('T1', 'T2', 'T3', 'T4'):
        value = published(plan['technical_results'][gate], repo)
        if (value.get('gate'), value.get('status'), value.get('condition'), value.get('science_sha256')) != (gate, 'PASS', 'v2-S2', science):
            raise ValueError('technical prerequisite failed or belongs to different science')
    audit = published(plan['train_audit'], repo)
    if (audit.get('condition') != 'v2-S2' or audit.get('declared') != 128 or audit.get('accounted') != 128
            or not audit.get('audits_ran') or not audit.get('independent_checks_functioning')
            or audit.get('cleanup_unresolved') != 0 or 'reward_increasing_mutations' not in audit):
        raise ValueError('train mutation audit and independent checks have not been accounted')
    execution = published(plan['execution_lock'], repo)
    wanted = 'LEARNING_PILOT' if phase == 'pilot' else 'L2'
    if (execution.get('gate'), execution.get('condition'), execution.get('status')) != (wanted, 'v2-S2', 'FROZEN'):
        raise ValueError('published learning execution lock required')
    if execution['LP_sha256'] != plan['LP']['sha256'] or execution['train_audit_sha256'] != plan['train_audit']['sha256']:
        raise ValueError('learning execution prerequisite hashes changed')
    source_bindings = {b['path']: b['sha256'] for b in execution['bindings']}
    if len(source_bindings) != len(execution['bindings']): raise ValueError('duplicate learning execution binding')
    for name in ('a6_learning_ledger.py', 'a6_phase2_admission.py', 'learning_runtime.py', 'learning_generation.py', 'audit_monitor.py', 'MONITOR_S2_METHOD.md'):
        source = Path(__file__).resolve().parent/name
        if source_bindings.get(str(source)) != digest(source): raise ValueError('learning or monitor implementation unbound')
    for binding in execution['bindings']:
        if digest(binding['path']) != binding['sha256']: raise ValueError('learning execution binding changed')
    if phase == 'main':
        t5 = published(plan['T5'], repo)
        if ((t5.get('gate'), t5.get('condition'), t5.get('status')) != ('T5', 'v2-S2', 'PASS')
                or t5.get('arm')!='B' or t5.get('seeds')!=[1301] or t5.get('metric')!='own train reward'):
            raise ValueError('B own-reward pilot feasibility did not pass')
        if execution['T5_sha256'] != plan['T5']['sha256'] or not execution['token_budget']['one_percent_matching_feasible']:
            raise ValueError('main token-matching admission missing')
        budget=published(plan['A_budget'],repo)
        expected={'condition':'v2-S2','gate':'A_PILOT_TOKEN_BUDGET','status':'FROZEN',
            'arm':'A','seeds':[1301,1302],'horizon':30,'pilot_slots':15360,'LP_sha256':plan['LP']['sha256'],
            'pilot_execution_sha256':t5['pilot_execution_sha256']}
        if (any(budget.get(k)!=v for k,v in expected.items())
                or execution.get('A_budget_sha256')!=plan['A_budget']['sha256']
                or execution['token_budget']!=budget['token_budget']):
            raise ValueError('main budget must equal the published complete A-pilot budget')
        if execution['main_seeds'] != list(MAIN_SEEDS): raise ValueError('main seed blocks changed')
    return lp, execution, science


def admit(plan):
    lp, lock, science = verify_learning(plan)
    root = Path(lock['configuration']['ledger'])/plan['phase']/plan['arm']/str(plan['run_seed'])
    with fence(root):
        identity = {k: plan[k] for k in ('phase', 'arm', 'run_seed')}
        binding = {**identity, 'condition': 'v2-S2', 'LP_sha256': plan['LP']['sha256'],
                   'execution_lock_sha256': plan['execution_lock']['sha256'], 'science_sha256': science}
        path = root/'admission.json'
        if path.exists():
            old = json.loads(path.read_text())
            if any(old.get(k) != v for k, v in binding.items()): raise ValueError('learning admission binding changed')
            return old
        row = {**binding, 'status': 'ADMITTED', 'automatic_retry': False, 'admitted_unix': time.time()}
        write_new(path, row); return row


def reserve_stage(root, *, update, stage, execution_sha, inputs):
    """A second dispatch never follows a missing summary; recovery must use existing artifacts."""
    if type(update) is not int or update < 0 or stage not in ('preflight', 'generate', 'score', 'update', 'export', 'ability', 'monitor', 'validation'):
        raise ValueError('unregistered learning stage')
    root = Path(root)
    with fence(root):
        admission = json.loads((root/'admission.json').read_text())
        if admission['status'] != 'ADMITTED' or admission['execution_lock_sha256'] != execution_sha:
            raise ValueError('learning run not admitted under this lock')
        if (root/'terminal.json').exists(): raise ValueError('learning run already terminal')
        folder = root/f'update_{update:05d}'; folder.mkdir(exist_ok=True)
        path = folder/(stage+'.json')
        write_new(path, {'condition': 'v2-S2', 'update': update, 'stage': stage,
                        'execution_sha256': execution_sha, 'inputs': inputs,
                        'inputs_sha256': signature(inputs), 'reserved_unix': time.time(), 'automatic_retry': False})
        return path
