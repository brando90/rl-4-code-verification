"""Reject incomplete final evidence and preserve other content on repeat publication."""
import importlib.util
import json
from pathlib import Path
import sys
import pytest

HERE = Path(__file__).resolve().parents[1] / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3'
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('e08_finalize', HERE / 'finalize_results.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def test_incomplete_evidence_cannot_finalize(tmp_path, monkeypatch):
    monkeypatch.setattr(m, 'HERE', tmp_path)
    (tmp_path / 'results').mkdir()
    (tmp_path / 'results/ladder_manifest_v3.json').write_text('{}')
    (tmp_path / 'results/validation_summary_v3.json').write_text(json.dumps({'known_cells': 1080, 'declared_cells': 17280}))
    with pytest.raises(AssertionError, match='incomplete'):
        m.validate()
    assert not (tmp_path / 'results/completion_validation_v3.json').exists()


def test_owned_block_replacement_preserves_later_other_results():
    text = m.replace_block('prior report\n', 'OWNED', 'first result') + '\nother owner result\n'
    replaced = m.replace_block(text, 'OWNED', 'updated result')
    assert replaced.startswith('prior report\n') and replaced.endswith('\nother owner result\n')
    assert 'first result' not in replaced and replaced.count('updated result') == 1


def test_unknown_namespace_cells_cannot_claim_completion():
    with pytest.raises(AssertionError, match='diagnostic remains incomplete'):
        m.validate_namespace({'declared_cells': 1080, 'unknown_cells': 1}, [], {})


def test_reduced_bootstrap_cannot_claim_frozen_analysis():
    with pytest.raises(AssertionError):
        m.validate_bootstrap({'draws': 999, 'seed': 0})
