"""Cache warming is a bounded, byte-exact read before GPU admission."""
import hashlib
from pathlib import Path
import sys
import time
import pytest

HERE = Path(__file__).resolve().parents[1] / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3'
sys.path.insert(0, str(HERE))
import warm_multinode_model as warm


def test_frozen_bytes_are_read_and_unchanged(tmp_path):
    p = tmp_path / 'weights'; p.write_bytes(b'weights\x00' * 1024)
    expected = hashlib.sha256(p.read_bytes()).hexdigest()
    before = p.stat()
    result = warm.checked_read(p, expected, time.time() + 10)
    assert result == {'bytes': before.st_size, 'sha256': expected, 'mtime_ns': before.st_mtime_ns}
    assert p.stat().st_mtime_ns == before.st_mtime_ns


def test_wrong_model_hash_blocks_admission(tmp_path):
    p = tmp_path / 'weights'; p.write_bytes(b'changed')
    with pytest.raises(AssertionError, match='checksum mismatch'):
        warm.checked_read(p, '0' * 64, time.time() + 10)


def test_expired_read_has_no_success_receipt(tmp_path):
    p = tmp_path / 'weights'; p.write_bytes(b'weights')
    with pytest.raises(AssertionError, match='deadline reached'):
        warm.checked_read(p, hashlib.sha256(p.read_bytes()).hexdigest(), time.time() - 1)


def test_file_changed_during_read_is_rejected(tmp_path):
    p = tmp_path / 'weights'; p.write_bytes(b'original')
    class ChangingPath:
        calls = 0
        def stat(self):
            self.calls += 1
            if self.calls == 2:
                p.write_bytes(b'different size')
            return p.stat()
        def open(self, mode):
            return p.open(mode)
    with pytest.raises(AssertionError):
        warm.checked_read(ChangingPath(), hashlib.sha256(b'original').hexdigest(), time.time() + 10)
