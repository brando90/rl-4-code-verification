"""Publish checked native results after an explicit owner handoff; no model calls or job restarts."""
from __future__ import annotations
import argparse
import csv
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from recovery_watch import ROOT, alive, identity, read, write, phase_observation, completed

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PY = '/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/.venv/bin/python'
LOCK_FDS = ()


class PublicationFailure(RuntimeError):
    """Retry only ordinary publication, under the original deadline and a finite cap."""


class NativeHandoffPending(RuntimeError):
    """An exact successful child exited before the healthy scheduler recorded DONE."""


def sent_receipt_valid(root):
    try:
        mail = read(HERE / 'results/email_done_v3.json', {})
        body = (root / 'completion_email_body.txt').read_text()
        return bool(mail.get('status') == 'SENT' and mail.get('all_recipients_accepted')
                    and mail.get('subject') == '[RUN DONE] rl4cv-e08-v3-sft-continuation: COMPLETE'
                    and mail.get('body') == body and mail.get('to') == 'brando.science@gmail.com'
                    and set(mail.get('cc', [])) == {'brandojazz@gmail.com', 'brando9@stanford.edu', 'brando@vals.ai'})
    except (OSError, ValueError, TypeError):
        return False
MARKERS = ('# rl4cv-e08-v3-recovery', '# rl4cv-e08-v3-orphan-cleanup',
           '# rl4cv-e08-v3-capacity-event', '# rl4cv-e08-v3-native-continuation')
REQUIRED_HASHES = {'native_continuation.py', 'recovery_watch.py', 'analyze_validation.py',
                   'finalize_results.py', 'notify_run.py', 'PROTOCOL.md',
                   'results/ladder_manifest_v3.json', 'results/sft_schedule_v3_E.json',
                   'results/sft_schedule_v3_R.json', 'forecasts/e08_v3_forecast.json',
                   'results/phase_a_training_verification.json', 'assess_forecast.py',
                   'remote_generation.py', 'remote_training.py', 'results/generation_prompt_hashes_v3.json',
                   'forecasts/e08_v3_forecast.sha256', 'forecasts/forecast_ledger.jsonl',
                   '../expt_v1/scripts/analyze_ladder.py', '../expt_v1/scripts/score_teacher_files.py',
                   '../../../src/rl4cv/__init__.py', '../../../src/rl4cv/rewards.py', '../../../src/rl4cv/screens.py',
                   '../../../external/veribench_scorer/scripts/scsc/run_real_eval.py',
                   '../../../external/veribench_scorer/scripts/scsc/kernel_axioms.py',
                   '../../../external/veribench_scorer/scripts/scsc/lean_public_context.py',
                   '../../../external/veribench_scorer/scripts/scsc/pbt_diagnostic.py',
                   '../../../../../../ultimate-utils/py_src/uutils/emailing.py'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def owner_key(record):
    return {k: record.get(k) for k in ('pid', 'boot_id', 'start_ticks')}


def authorization(root, config, now=None):
    now = time.time() if now is None else now
    arm = read(root / 'native_continuation_arm.json', {})
    ack = read(root / 'owner_ack.json', {})
    handoff = read(root / 'owner_handoff.json', {})
    state = read(root / 'native_continuation_state.json', {})
    if not arm.get('armed'):
        return 'UNARMED'
    if (arm.get('schema') != 1 or not ack.get('owner')
            or owner_key(arm.get('owner', {})) != owner_key(ack['owner'])
            or owner_key(handoff.get('owner', {})) != owner_key(ack['owner'])
            or arm.get('attempt') != ack.get('attempt') or handoff.get('attempt') != ack.get('attempt')
            or handoff.get('released') is not True or handoff.get('mode') != 'NATIVE_CONTINUATION'
            or arm.get('deadline_unix') != config['recovery_deadline_unix']
            or arm.get('max_recoveries') != config['max_recoveries']
            or arm.get('candidate_caps') != {c['name']: c['max_attempts'] for c in config['candidates']}):
        return 'INVALID_HANDOFF'
    if now >= config['recovery_deadline_unix']:
        return 'DEADLINE_REACHED'
    if alive(ack['owner']) or alive(read(root / 'recovery_owner_process.json', {}).get('identity')):
        return 'OWNER_ACTIVE'
    if state.get('status') == 'BLOCKED' or (state.get('status') == 'MAIL_SENDING' and not sent_receipt_valid(root)):
        return 'BLOCKED'
    hashes = arm.get('input_sha256', {})
    if (not REQUIRED_HASHES <= hashes.keys()
            or any(not (HERE / p).is_file() or sha(HERE / p) != h for p, h in hashes.items())):
        return 'SOURCE_CHANGED'
    tests = read(root / 'native_continuation_tests.json', {})
    if (tests.get('status') != 'PASS' or tests.get('input_sha256') != hashes
            or tests.get('failed') != 0 or not tests.get('full_suite_passed')):
        return 'UNTESTED_SOURCE'
    return 'AUTHORIZED'


def run(command, root, deadline, *, capture=False, binary=False, cwd=None):
    remaining = deadline - time.time()
    assert remaining > 0, 'Original recovery deadline reached'
    env = os.environ.copy(); env.pop('CODEX_HOME', None)
    env['PATH'] = str(Path(PY).parent) + ':' + env.get('PATH', '')
    if capture:
        output = subprocess.check_output(command, cwd=cwd or REPO, env=env, text=not binary,
                                         timeout=min(remaining, 3600), pass_fds=LOCK_FDS)
        return output if binary else output.strip()
    with (root / 'native_continuation_commands.log').open('a') as log:
        subprocess.run(command, cwd=cwd or REPO, env=env, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=min(remaining, 3600), pass_fds=LOCK_FDS)


@contextmanager
def publication_lock(root):
    """Keep inherited locks alive in children and restore descriptors on every exit."""
    global LOCK_FDS
    previous = LOCK_FDS
    with (root / 'results_publication.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        LOCK_FDS = previous + (lock.fileno(),)
        try:
            yield
        finally:
            LOCK_FDS = previous


def progress(root):
    phases = {p: read(root / f'phase_{p}_state.json', {}) for p in ('a', 'b')}
    jobs = {k: v for phase in phases.values() for k, v in phase.get('jobs', {}).items()}
    for p, phase in phases.items():
        assert phase and not phase.get('analysis_error'), f'Phase {p} missing or analysis failed'
        obs = phase_observation(root, p, time.time())
        assert phase['status'] == 'DONE' or (obs['scheduler_alive'] and obs['heartbeat_age_seconds'] < 180)
        assert all(j['status'] not in ('FAILED', 'CHILD_DEAD') for j in obs['jobs'].values())
        if any(j['status'] == 'EXITED_AWAITING_SCHEDULER' for j in obs['jobs'].values()):
            raise NativeHandoffPending(f'Phase {p} awaits a successful child handoff')
    # Only DONE native jobs may add artifacts to a publication.
    done = sorted(k for k, v in jobs.items() if v['status'] == 'DONE')
    for key in done:
        job = jobs[key]
        if job.get('exit_receipt'):
            receipt = read(Path(job['exit_receipt']), {})
            # Historical post-export reconciliations were explicitly accepted before this handoff.
            if receipt.get('exit_code') != 0:
                assert key in ('train_E_1p7b', 'train_R_1p7b') and receipt['exit_code'] == 2
                evidence = read(HERE / 'results/phase_a_training_verification.json')
                accepted = evidence['runs']['v3_' + key.removeprefix('train_')]
                assert evidence['status'] == 'PHASE_A_TRAINING_VERIFIED'
                assert accepted['native_exit_code'] == 2 and accepted['reconciliation'] == job['reconciled_by']
                assert sha(HERE / accepted['summary']) == accepted['summary_sha256']
            assert receipt.get('identity') == job['identity']
        assert not alive(job.get('identity')), f'{key} has a live DONE identity'
    return phases, jobs, done


def validate_partial(summary, manifest, jobs):
    from finalize_results import validate_metrics, validate_training, validate_namespace, validate_bootstrap
    from remote_generation import validate_raw, SHARED
    validate_metrics(summary, manifest)
    for label, result in summary['systems'].items():
        assert jobs['score_' + label]['status'] == 'DONE'
        scored = ROOT / f'ladder/validation/scored/scored_{label}_g8.jsonl'
        assert sha(scored) == result['scored_sha256']
        system = result['system']
        model_paths = [system['hf_path'], str(SHARED / 'sft_v3' / Path(system['hf_path']).relative_to(ROOT))]
        validate_raw(ROOT / f'ladder/validation/raw/gen_{label}_g8.jsonl', label, manifest['task_ids'],
                     read(HERE / 'results/generation_prompt_hashes_v3.json'), model_paths)
        if jobs.get('namespace_' + label, {}).get('status') == 'DONE':
            diag = read(HERE / f'results/namespace_diagnostic/{label}.json')
            rows = list(csv.DictReader((HERE / f'results/namespace_diagnostic/{label}_cells.csv').open()))
            primary = {(r['task_id'], r['sample_idx']): r for r in csv.DictReader((HERE / result['cells_csv']).open())}
            validate_namespace(diag, rows, primary)
            if not diag['unknown_cells']:
                deltas = [sum(float(r['diagnostic_kernel_binary']) - float(r['original_kernel_binary'])
                              for r in rows if r['task_id'] == task) / 8 for task in manifest['task_ids']]
                validate_bootstrap(diag['paired_task_bootstrap_delta'], deltas)
    for key, job in jobs.items():
        if key.startswith('verify_') and job['status'] == 'DONE':
            condition, size = key.removeprefix('verify_').split('_')
            label = f'v3_{condition}_{size}'
            validate_training(read(HERE / f'results/train_logs/{label}_summary.json'),
                              list(csv.DictReader((HERE / f'results/train_logs/{label}_steps.csv').open())),
                              read(HERE / f'results/sft_schedule_v3_{condition}.json'))


def publication_paths(manifest, jobs, final=False):
    paths = [HERE / p for p in ('results.md', 'CKPT_e08_v3.md', 'results/runtime_progress.md',
             'results/validation_summary_v3.json', 'results/forecast_assessment_v3.json')]
    paths.append(HERE.parent / 'results.md')
    for system in manifest['systems']:
        label = system['label']
        paths.append(HERE / f'results/coverage/{label}.csv')
        if jobs.get('score_' + label, {}).get('status') == 'DONE':
            paths.extend(HERE / f'results/ladder/{label}_{suffix}.csv'
                         for suffix in ('taxonomy', 'validation_cells', 'validation_per_task'))
        if jobs.get('namespace_' + label, {}).get('status') == 'DONE':
            paths.extend(HERE / f'results/namespace_diagnostic/{label}{suffix}'
                         for suffix in ('.json', '_cells.csv'))
        if jobs.get('gen_' + label, {}).get('status') == 'DONE':
            paths.append(HERE / f'results/remote_generation_{label}.json')
    for key, job in jobs.items():
        if key.startswith('verify_') and job['status'] == 'DONE':
            label = 'v3_' + key.removeprefix('verify_')
            paths.extend(HERE / f'results/train_logs/{label}_{suffix}'
                         for suffix in ('steps.csv', 'summary.json', 'f0p5_SHA256SUMS', 'f1p0_SHA256SUMS'))
    if final:
        paths.extend(HERE / ('results/' + p) for p in ('completion_validation_v3.json',
                     'namespace_summary_v3.json', 'error_samples_recovery02.json',
                     'email_done_v3.json', 'native_completion_v3.json'))
    return sorted({p for p in paths if p.is_file()})


def publish(paths, root, deadline, title):
    staged = run(['git', 'diff', '--cached', '--name-only'], root, deadline, capture=True).splitlines()
    prior = read(root / 'native_publication_snapshot.json', {})
    ack = read(root / 'owner_ack.json', {})
    publisher = {'owner': owner_key(ack.get('owner', {})), 'attempt': ack.get('attempt')}
    if staged:
        assert prior.get('status') == 'PREPARED' and set(staged) <= prior.get('sha256', {}).keys(), 'Existing staged work'
        assert prior.get('publisher') == publisher, 'Existing staged work belongs to another owner'
        for path in staged:
            blob = run(['git', 'show', ':' + path], root, deadline, capture=True, binary=True)
            assert hashlib.sha256(blob).hexdigest() == prior['sha256'][path], 'Existing staged work changed'
        run(['git', 'reset', 'HEAD', '--', *staged], root, deadline)
    before = {str(p.relative_to(REPO)): sha(p) for p in paths}
    snapshot = {'status': 'PREPARED', 'sha256': before, 'checked_unix': time.time(), 'title': title,
                'publisher': publisher}
    write(root / 'native_publication_snapshot.json', snapshot)
    run(['git', 'add', '--', *before], root, deadline)
    run(['git', 'diff', '--cached', '--check'], root, deadline)
    diff = run(['git', 'diff', '--cached', '--no-ext-diff'], root, deadline, capture=True)
    assert not re.search(r'sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}', diff), 'Possible credential in publication'
    assert before == {str(p.relative_to(REPO)): sha(p) for p in paths}, 'Artifact changed while staging'
    if diff:
        run(['git', 'commit', '-m', title], root, deadline)
    try:
        run(['git', 'pull', '--ff-only', 'origin', 'main'], root, deadline)
    except subprocess.CalledProcessError:
        # Preserve both histories. A conflict or changed locked source is a durable block.
        run(['git', 'merge', '--no-edit', 'origin/main'], root, deadline)
        arm = read(root / 'native_continuation_arm.json')
        assert all(sha(HERE / p) == h for p, h in arm['input_sha256'].items()), 'Merged locked source changed'
        run(['make', 'test'], root, deadline)
    arm = read(root / 'native_continuation_arm.json', {})
    assert all(sha(HERE / p) == h for p, h in arm.get('input_sha256', {}).items()), 'Published locked source changed'
    for path, expected in before.items():
        blob = run(['git', 'show', 'HEAD:' + path], root, deadline, capture=True, binary=True)
        if hashlib.sha256(blob).hexdigest() != expected:
            raise PublicationFailure('Merge changed validated artifact; revalidation required before push')
    run(['git', 'push', 'origin', 'main'], root, deadline)
    commit = run(['git', 'rev-parse', 'HEAD'], root, deadline, capture=True)
    remote = run(['git', 'ls-remote', 'origin', 'refs/heads/main'], root, deadline, capture=True).split()[0]
    assert commit == remote
    write(root / 'native_publication_snapshot.json', {**snapshot, 'status': 'PUSH_VERIFIED',
                                                     'commit': commit, 'verified_unix': time.time()})
    return commit


def checked_publish(*args):
    try:
        return publish(*args)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        raise PublicationFailure(str(error)) from error


def update_ledger(done, summary, final=False):
    from finalize_results import replace_block
    stamp = time.strftime('%m-%d-%Y %H:%M UTC', time.gmtime())
    text = f'{stamp}: deterministic native continuation verified {summary["known_cells"]:,}/17,280 primary cells. Completed native jobs: {len(done)}. Zero paid experimental calls; test split unopened.'
    path = HERE / 'results/runtime_progress.md'; path.write_text(path.read_text() + '\n\n' + text + '\n')
    path = HERE / 'CKPT_e08_v3.md'; path.write_text(path.read_text() + '\n- ' + text + '\n')
    if not final:
        parent = HERE.parent / 'results.md'
        body = f'## Matched replay versus expansion continuation: expt_v3\n\n**Last updated:** {stamp}. **INCOMPLETE: {summary["known_cells"]:,}/17,280 primary validation cells.** [Live results and task-bootstrap intervals](expt_v3/results.md), [execution ledger](expt_v3/results/runtime_progress.md). Healthy native schedulers continue the frozen manifest. Final validation, publication and DONE notification remain required. Zero paid experimental calls; test split unopened.'
        parent.write_text(replace_block(parent.read_text(), 'E08_V3_FINAL_RESULTS', body))


def retire_owned_crons(root):
    # Cleanup remains idempotent after completion, including after the workload deadline.
    deadline = time.time() + 60
    cron = run(['crontab', '-l'], root, deadline, capture=True)
    keep = '\n'.join(line for line in cron.splitlines() if not any(line.endswith(m) for m in MARKERS)) + '\n'
    if keep != cron.rstrip('\n') + '\n':
        path = root / 'crontab_after_native_completion.txt'; path.write_text(keep)
        run(['crontab', str(path)], root, deadline)


def tick(root, config):
    global LOCK_FDS
    if completed(root, HERE):
        retire_owned_crons(root)
        state_path = root / 'native_continuation_state.json'
        write(state_path, {**read(state_path, {}), 'status': 'COMPLETE', 'checked_unix': time.time()})
        return 'COMPLETE'
    status = authorization(root, config)
    state_path = root / 'native_continuation_state.json'
    state = read(state_path, {})
    if status != 'AUTHORIZED':
        # Never erase an ambiguous mail/failure checkpoint or publish as a live owner's peer.
        if state.get('status') not in ('BLOCKED', 'MAIL_SENDING'):
            write(state_path, {**state, 'status': status, 'checked_unix': time.time()})
        return status
    deadline = config['recovery_deadline_unix']
    state.update(status='RUNNING', identity=identity(os.getpid()), checked_unix=time.time())
    write(state_path, state)
    try:
        phases, jobs, done = progress(root)
        final = all(p['status'] == 'DONE' for p in phases.values())
        if done == state.get('published_jobs') and not final:
            state.update(status='WAITING_NATIVE_WORK', checked_unix=time.time()); write(state_path, state)
            return state['status']
        # The scheduler's analyzer uses the same lock; no mixed table/report snapshots.
        with publication_lock(root):
            import analyze_validation
            analyzed_done = done
            analyze_validation.main()
            phases, jobs, done = progress(root)
            manifest = read(HERE / 'results/ladder_manifest_v3.json')
            summary = read(HERE / 'results/validation_summary_v3.json')
            if any(jobs.get('score_' + label, {}).get('status') != 'DONE' for label in summary['systems']):
                state.update(status='WAITING_NATIVE_HANDOFF', checked_unix=time.time()); write(state_path, state)
                return state['status']
            validate_partial(summary, manifest, jobs)
            if final:
                import finalize_results
                finalize_results.main(checksum_runner=lambda command, cwd:
                                      run(command, root, deadline, cwd=cwd))
                run(['make', 'test'], root, deadline)
                state['final_tests'] = {'status': 'PASS', 'log': str(root / 'native_continuation_commands.log'),
                                        'completed_unix': time.time()}
            update_ledger(done, summary, final)
            commit = checked_publish(publication_paths(manifest, jobs, final), root, deadline,
                             'Publish checked E08 v3 native results' if not final else 'Complete E08 v3 validation and forecast assessment')
            # Jobs finishing during analysis remain a fresh event for the next tick.
            state.update(published_jobs=analyzed_done, published_commit=commit, checked_unix=time.time())
            if final:
                receipt_path = HERE / 'results/email_done_v3.json'
                if not receipt_path.exists():
                    state.update(status='MAIL_SENDING'); write(state_path, state)
                    run([PY, str(HERE / 'notify_run.py'), 'DONE', '--status', 'COMPLETE', '--body-file',
                         str(root / 'completion_email_body.txt')], root, deadline)
                mail = read(receipt_path)
                assert sent_receipt_valid(root), 'Completed notification receipt does not match this run'
                assert mail['status'] == 'SENT' and mail['subject'].endswith(': COMPLETE') and mail['all_recipients_accepted']
                assert mail['to'] == 'brando.science@gmail.com' and set(mail['cc']) == {
                    'brandojazz@gmail.com', 'brando9@stanford.edu', 'brando@vals.ai'}
                assert mail['body'] == (root / 'completion_email_body.txt').read_text()
                state.update(status='NOTIFIED', checked_unix=time.time()); write(state_path, state)
                validation = read(HERE / 'results/completion_validation_v3.json')
                assert validation['known_cells'] == validation['declared_cells'] == 17280 and validation['systems'] == 16
                completion = {'status': 'COMPLETE', 'published_commit': commit, 'science_commit': commit,
                    'notification_sent': True, 'final_tests': state['final_tests'],
                    'training_verified': True, 'namespace_complete': True, 'forecast_assessed': True,
                    'known_cells': 17280, 'declared_cells': 17280, 'systems': 16,
                    'validation_sha256': sha(HERE / 'results/completion_validation_v3.json'),
                    'email_sha256': sha(receipt_path), 'checked_unix': time.time()}
                write(HERE / 'results/native_completion_v3.json', completion)
                commit = checked_publish(publication_paths(manifest, jobs, True), root, deadline,
                                 'Publish E08 v3 verified completion notification')
                completion['published_commit'] = commit
                completion['notification_commit'] = commit
                write(root / 'completion_receipt.json', completion)
                retire_owned_crons(root)
                state.update(status='COMPLETE', published_commit=commit)
            else:
                state['status'] = 'PUBLISHED_NATIVE_PROGRESS'
            state['checked_unix'] = time.time(); write(state_path, state)
            return state['status']
    except NativeHandoffPending as error:
        state.update(status='WAITING_NATIVE_HANDOFF', detail=str(error), checked_unix=time.time())
        write(state_path, state)
        return state['status']
    except BaseException as error:
        # An SMTP send whose receipt was not persisted is never automatically replayed.
        failures = state.get('publication_failures', 0) + int(isinstance(error, PublicationFailure))
        status = 'RETRY_PUBLICATION' if isinstance(error, PublicationFailure) and failures < 3 else 'BLOCKED'
        state.update(status=status, publication_failures=failures,
                     error=f'{type(error).__name__}: {error}', checked_unix=time.time())
        write(state_path, state)
        raise


def supervise(action, deadline):
    """Bound the whole tick, retaining its PID until its private group is stopped.

    The unreaped leader prevents PID/group reuse. Existing schedulers and training
    children are outside this new session; only this tick and its commands stop.
    Inherited lock descriptors fence overlapping cron work through cleanup.
    """
    pid = os.fork()
    if pid == 0:
        try:
            os.setsid()
            action()
        except BaseException:
            import traceback
            traceback.print_exc()
            os._exit(1)
        os._exit(0)
    result = None
    try:
        while time.time() < deadline:
            result = os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
            if result is not None:
                break
            time.sleep(min(.1, max(0, deadline - time.time())))
        if result is None:
            raise TimeoutError('Original recovery deadline reached during native tick')
        if result.si_code != os.CLD_EXITED or result.si_status != 0:
            raise RuntimeError(f'Native worker failed: code={result.si_code}, status={result.si_status}')
    finally:
        # Do not reap the leader before killing its group, including orphan commands.
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            os.kill(pid, signal.SIGKILL)  # Forked child may not have called setsid yet.
        until = time.monotonic() + 5
        while time.monotonic() < until:
            reaped, _ = os.waitpid(pid, os.WNOHANG)
            if reaped:
                break
            time.sleep(.05)
        else:
            raise RuntimeError('Native worker did not exit after exact owned-group cleanup')


def main():
    global LOCK_FDS
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    with (args.root / 'recovery.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        LOCK_FDS = (lock.fileno(),)
        config = read(args.root / 'recovery_config.json')
        deadline = config['recovery_deadline_unix']
        # An expired tick can only reject work or retire already-verified COMPLETE
        # crons. Keep that idempotent cleanup bounded independently at 60 seconds.
        if deadline <= time.time():
            deadline = time.time() + 60
        try:
            supervise(lambda: print(tick(args.root, config), flush=True), deadline)
        except TimeoutError as error:
            path = args.root / 'native_continuation_state.json'
            state = read(path, {})
            state.update(status='BLOCKED' if state.get('status') == 'MAIL_SENDING' else 'DEADLINE_REACHED',
                         error=str(error), checked_unix=time.time())
            write(path, state)
            raise


if __name__ == '__main__':
    main()
