"""Verify recovery fencing and harmless process recovery without touching experiment jobs."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1] / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3'
spec = importlib.util.spec_from_file_location('e08_v3_recovery', HERE / 'recovery_watch.py')
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = {'experiment': str(HERE), 'checkout': str(HERE.parents[2]), 'python': sys.executable,
                       'recovery_deadline_unix': time.time() + 60, 'max_recoveries': 2,
                       'candidates': [{'name': 'fake', 'eligible': True, 'max_attempts': 2}]}

    def tearDown(self):
        self.temp.cleanup()

    def test_live_owner_fences_launch(self):
        child = subprocess.Popen(['sleep', '30'])
        try:
            watch.write(self.root / 'owner_ack.json', {'owner': watch.identity(child.pid), 'attempt': 'fake'})
            with patch.object(watch.subprocess, 'run') as launch:
                state = watch.tick(self.root, self.config)
                self.assertEqual(state['status'], 'OBSERVING')
                launch.assert_not_called()
                self.assertIsNone(child.poll())
        finally:
            child.terminate(); child.wait()

    def test_fake_owner_failure_recovers_once_preserving_work(self):
        owner = subprocess.Popen(['true'])
        rec = watch.identity(owner.pid)
        owner.wait()
        work = subprocess.Popen(['sleep', '30'])
        try:
            watch.write(self.root / 'owner_ack.json', {'owner': rec, 'attempt': 'fake'})
            watch.write(self.root / 'phase_a_state.json', {'pid': work.pid, 'status': 'RUNNING',
                        'jobs': {'train_fake': {'pid': work.pid, 'identity': watch.identity(work.pid), 'status': 'RUNNING'}}})
            with patch.object(watch.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')) as launch:
                state = watch.tick(self.root, self.config)
                self.assertEqual(state['status'], 'RECOVERY_STARTED_UNVERIFIED')
                self.assertEqual(launch.call_count, 1)
                state = watch.tick(self.root, self.config)
                self.assertEqual(state['status'], 'AWAITING_RECOVERY_PROCESS')
                self.assertEqual(launch.call_count, 1)
                self.assertIsNone(work.poll())
        finally:
            work.terminate(); work.wait()

    def test_stale_progress_and_analysis_error_are_visible(self):
        watch.write(self.root / 'phase_a_state.json', {'pid': 999999999, 'status': 'NEEDS_RECOVERY',
                    'analysis_error': 1, 'jobs': {'score_fake': {'pid': 999999999, 'status': 'RUNNING'}}})
        state = watch.tick(self.root, self.config, launch=False)
        self.assertIn('phase_a:analysis_error', state['issues'])
        self.assertIn('score_fake:CHILD_DEAD', state['issues'])
        self.assertEqual(state['status'], 'RECOVERY_NEEDED')

    def test_pid_reuse_and_false_completion(self):
        rec = watch.identity(__import__('os').getpid())
        rec['start_ticks'] = str(int(rec['start_ticks']) + 1)
        self.assertFalse(watch.alive(rec))
        watch.write(self.root / 'completion_receipt.json', {'status': 'COMPLETE'})
        self.assertFalse(watch.completed(self.root, HERE))

    def test_live_recovery_runner_fences_launch(self):
        watch.write(self.root / 'recovery_owner_process.json', {'identity': watch.identity(__import__('os').getpid())})
        with patch.object(watch.subprocess, 'run') as launch:
            self.assertEqual(watch.tick(self.root, self.config)['status'], 'OBSERVING')
            launch.assert_not_called()

    def test_scheduler_pid_reuse_is_not_liveness(self):
        record = watch.identity(__import__('os').getpid())
        record['start_ticks'] = str(int(record['start_ticks']) + 1)
        watch.write(self.root / 'phase_a_state.json', {'pid': record['pid'], 'identity': record,
                                                     'status': 'RUNNING', 'jobs': {}})
        observed = watch.phase_observation(self.root, 'a', time.time())
        self.assertFalse(observed['scheduler_alive'])

    def arm_resource_wait(self):
        now = time.time()
        owner = {'pid': 999999999, 'boot_id': 'dead-owner-boot', 'start_ticks': '1'}
        live = watch.identity(os.getpid())
        watch.write(self.root / 'owner_ack.json', {'owner': owner, 'attempt': 'recovery-01'})
        watch.write(self.root / 'owner_handoff.json', {'owner': owner, 'attempt': 'recovery-01',
                    'released': True, 'mode': 'EXTERNAL_RESOURCE_WAIT'})
        watch.write(self.root / 'recovery_state.json', {'attempts': [
            {'attempt': 'recovery-01', 'candidate': 'fake', 'started_unix': now - 20}]})
        watch.write(self.root / 'phase_a_state.json', {'status': 'DONE', 'identity': live, 'jobs': {}})
        watch.write(self.root / 'phase_b_state.json', {'status': 'RUNNING', 'identity': live,
                    'jobs': {'train_E_14b': {'status': 'RUNNING', 'pid': live['pid'], 'identity': live}}})
        self.config['remote_runtime'] = str(self.root / 'shared')
        (self.root / 'shared').mkdir()
        record = {'schema': 1, 'status': 'EXTERNAL_RESOURCE_WAIT', 'owner': owner,
                  'attempt': 'recovery-01', 'recorded_unix': now - 1,
                  'deadline_unix': self.config['recovery_deadline_unix'],
                  'independent_work_complete': True, 'admissions_absent_at_recording': True,
                  'phase_snapshot': watch.resource_snapshot(self.root),
                  'expected_remote_admissions': ['remote_E_14b.json'], 'reason': 'eight devices required',
                  'capacity_baseline': {'sequence': 0, 'fingerprint': 'previous'}}
        watch.write(self.root / 'external_resource_wait.json', record)
        return record

    def test_completed_phase_old_heartbeat_is_not_a_failure(self):
        self.arm_resource_wait()
        os.utime(self.root / 'phase_a_state.json', (time.time() - 1000,) * 2)
        state = watch.tick(self.root, self.config, launch=False)
        self.assertNotIn('phase_a:stale_heartbeat', state['issues'])
        self.assertEqual(state['status'], 'DEFERRED_EXTERNAL_RESOURCE')

    def test_resource_wait_defers_without_spending_attempts_or_poll_churn(self):
        self.arm_resource_wait()
        path = self.root / 'phase_b_state.json'
        phase = watch.read(path); phase['updated_unix'] = time.time(); watch.write(path, phase)
        (self.root / 'phase_b_logs').mkdir()
        (self.root / 'phase_b_logs/train_E_14b.log').write_text('WAITING_DEVICES\n')
        with patch.object(watch.subprocess, 'run') as launch:
            state = watch.tick(self.root, self.config)
            self.assertEqual(state['status'], 'DEFERRED_EXTERNAL_RESOURCE')
            self.assertEqual(len(state['attempts']), 1)
            launch.assert_not_called()

    def test_invalid_wait_metadata_never_suppresses_recovery(self):
        original = self.arm_resource_wait()
        for field, value in [('attempt', 'older'), ('owner', {}), ('deadline_unix', 0),
                             ('expected_remote_admissions', ['../unrelated.json']),
                             ('independent_work_complete', False), ('recorded_unix', 'bad')]:
            with self.subTest(field=field):
                watch.write(self.root / 'external_resource_wait.json', {**original, field: value})
                state = watch.tick(self.root, self.config, launch=False)
                self.assertEqual(state['status'], 'RECOVERY_NEEDED')
        (self.root / 'external_resource_wait.json').write_text('{malformed')
        self.assertEqual(watch.tick(self.root, self.config, launch=False)['status'], 'RECOVERY_NEEDED')
        watch.write(self.root / 'external_resource_wait.json', original)
        (self.root / 'owner_handoff.json').write_text('{malformed')
        self.assertEqual(watch.tick(self.root, self.config, launch=False)['status'], 'RECOVERY_NEEDED')

    def test_resource_wait_cannot_extend_deadline_or_attempt_cap(self):
        self.arm_resource_wait()
        self.config['max_recoveries'] = 1
        self.assertEqual(watch.tick(self.root, self.config, launch=False)['status'], 'RECOVERY_ATTEMPTS_EXHAUSTED')
        self.config['recovery_deadline_unix'] = time.time() - 1
        self.assertEqual(watch.tick(self.root, self.config, launch=False)['status'], 'RECOVERY_DEADLINE_REACHED')

    def test_actual_remote_admission_wakes_once_without_local_pid_check(self):
        self.arm_resource_wait()
        foreign = {'pid': os.getpid(), 'boot_id': 'remote-not-local', 'start_ticks': '42'}
        watch.write(self.root / 'shared/remote_E_14b.json', {
            'status': 'RUNNING', 'host': 'skampere3', 'gpus': '0,1,2,3,4,5,6,7',
            'identity': foreign, 'receipt': '/shared/remote_E_14b.exit.json'})
        with patch.object(watch, 'alive', wraps=watch.alive) as alive, patch.object(
                watch.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')) as launch:
            state = watch.tick(self.root, self.config)
            self.assertEqual(state['status'], 'RECOVERY_STARTED_UNVERIFIED')
            self.assertEqual(state['resource_wait_observation']['reason'], 'remote_admitted')
            self.assertFalse(any(call.args == (foreign,) for call in alive.call_args_list))
            self.assertEqual(watch.tick(self.root, self.config)['status'], 'AWAITING_RECOVERY_PROCESS')
            self.assertEqual(launch.call_count, 1)
            self.assertEqual(len(state['attempts']), 2)

    def test_resource_wait_wakes_on_execution_change_failure_and_scheduler_death(self):
        self.arm_resource_wait()
        path = self.root / 'phase_b_state.json'; original = watch.read(path)
        for status in ('DONE', 'FAILED'):
            phase = json.loads(json.dumps(original)); phase['jobs']['train_E_14b']['status'] = status
            watch.write(path, phase)
            self.assertEqual(watch.tick(self.root, self.config, launch=False)['status'], 'RECOVERY_NEEDED')
        original['identity'] = {'pid': 999999998, 'boot_id': 'gone', 'start_ticks': '1'}
        watch.write(path, original)
        state = watch.tick(self.root, self.config, launch=False)
        self.assertIn('phase_b:scheduler_dead', state['issues'])
        self.assertEqual(state['status'], 'RECOVERY_NEEDED')

    def test_capacity_event_requires_new_valid_eligible_fingerprint(self):
        wait = self.arm_resource_wait()
        route = {'route_id': 'verified-slurm-route', 'eligible': True, 'free_gpus': 8, 'required_gpus': 8}
        fingerprint = hashlib.sha256(json.dumps(route, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        event = {'sequence': 0, 'route': route, 'fingerprint': fingerprint}
        path = self.root / 'external_capacity_event.json'; watch.write(path, event)
        self.assertEqual(watch.tick(self.root, self.config, launch=False)['status'], 'DEFERRED_EXTERNAL_RESOURCE')
        event['sequence'] = 1; event['fingerprint'] = 'invalid'; watch.write(path, event)
        self.assertEqual(watch.tick(self.root, self.config, launch=False)['status'], 'DEFERRED_EXTERNAL_RESOURCE')
        event['fingerprint'] = fingerprint; watch.write(path, event)
        self.assertEqual(watch.tick(self.root, self.config, launch=False)['status'], 'RECOVERY_NEEDED')
        wait['capacity_baseline'] = {'sequence': 1, 'fingerprint': fingerprint}
        watch.write(self.root / 'external_resource_wait.json', wait)
        self.assertEqual(watch.tick(self.root, self.config, launch=False)['status'], 'DEFERRED_EXTERNAL_RESOURCE')
        path.write_text('{malformed')
        self.assertEqual(watch.tick(self.root, self.config, launch=False)['status'], 'DEFERRED_EXTERNAL_RESOURCE')

    def test_corrupt_expected_admission_is_a_recovery_event(self):
        self.arm_resource_wait()
        (self.root / 'shared/remote_E_14b.json').write_text('{malformed')
        state = watch.tick(self.root, self.config, launch=False)
        self.assertEqual(state['status'], 'RECOVERY_NEEDED')
        self.assertEqual(state['resource_wait_observation']['reason'], 'remote_record_needs_inspection')
        watch.write(self.root / 'shared/remote_E_14b.json', {
            'status': 'RUNNING', 'host': 'skampere3', 'gpus': '0,1,2,3,4,5,6,7',
            'identity': None, 'receipt': 'malformed-identity'})
        state = watch.tick(self.root, self.config, launch=False)
        self.assertEqual(state['status'], 'RECOVERY_NEEDED')
        self.assertEqual(state['resource_wait_observation']['reason'], 'remote_record_needs_inspection')

    def test_released_live_resource_owner_must_exit_before_replacement(self):
        wait = self.arm_resource_wait()
        current = watch.identity(os.getpid()); wait['owner'] = current
        watch.write(self.root / 'external_resource_wait.json', wait)
        watch.write(self.root / 'owner_ack.json', {'owner': current, 'attempt': 'recovery-01'})
        watch.write(self.root / 'owner_handoff.json', {'owner': current, 'attempt': 'recovery-01',
                    'released': True, 'mode': 'EXTERNAL_RESOURCE_WAIT'})
        with patch.object(watch.subprocess, 'run') as launch:
            self.assertEqual(watch.tick(self.root, self.config)['status'], 'AWAITING_RELEASED_OWNER_EXIT')
            launch.assert_not_called()

    def test_capacity_idle_progress_can_defer_but_dead_child_cannot(self):
        self.arm_resource_wait()
        log = self.root / 'ckpt/fake/driver_logs/progress.log'; log.parent.mkdir(parents=True)
        log.write_text('old useful output'); os.utime(log, (time.time() - 8000,) * 2)
        state = watch.tick(self.root, self.config, launch=False)
        self.assertIn('phase_b:stale_work_progress', state['issues'])
        self.assertEqual(state['status'], 'DEFERRED_EXTERNAL_RESOURCE')
        path = self.root / 'phase_b_state.json'; phase = watch.read(path)
        phase['jobs']['train_E_14b']['identity'] = {'pid': 999999998, 'boot_id': 'dead', 'start_ticks': '1'}
        watch.write(path, phase)
        state = watch.tick(self.root, self.config, launch=False)
        self.assertIn('train_E_14b:CHILD_DEAD', state['issues'])
        self.assertEqual(state['status'], 'RECOVERY_NEEDED')


if __name__ == '__main__':
    unittest.main()
