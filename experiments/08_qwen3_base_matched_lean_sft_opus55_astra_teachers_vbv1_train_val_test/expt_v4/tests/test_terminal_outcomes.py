"""Require failed, cancelled and truncated training trajectories to remain visibly incomplete."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('sherlock_terminal', Path(__file__).parents[1] / 'finalize.py')
terminal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(terminal)


def complete_inputs():
    return ([{'State': 'COMPLETED', 'ExitCode': '0:0'} for _ in range(3)],
            [{'status': 'COMPLETE', 'step': 658, 'examples': 1315, 'loss_tokens': 5752936} for _ in range(2)])


def test_complete_full_runs():
    assert terminal.classify(*complete_inputs()) == 'COMPLETE'


def test_scheduler_failure_is_not_hidden_by_old_success_files():
    for state in ['FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY', 'PENDING', 'RUNNING']:
        jobs, results = complete_inputs()
        jobs[1]['State'] = state
        assert terminal.classify(jobs, results) == 'INCOMPLETE'


def test_missing_and_truncated_runs_stay_incomplete():
    jobs, results = complete_inputs()
    assert terminal.classify(jobs, results[:1]) == 'INCOMPLETE'
    assert terminal.classify(jobs[:2], results) == 'INCOMPLETE'
    results[1]['loss_tokens'] -= 1
    assert terminal.classify(jobs, results) == 'INCOMPLETE'
