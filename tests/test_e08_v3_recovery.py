"""Verify recovery fencing and harmless process recovery without touching experiment jobs."""
import importlib.util
import json
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


if __name__ == '__main__':
    unittest.main()
