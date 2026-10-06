"""Verify paired statistics preserve the declared denominator and reject unbound or stale receipts."""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import analyze_paired as analysis
import prepare_panel as prep
from test_prepare_panel import bundle


class PairedAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.manifest, _, private = bundle()
        self.manifest_hash = private["manifest_sha256"]
        self.ids = self.manifest["task_ids"]

    def receipt(self, task_id, condition, resolved, status="completed"):
        return {"manifest_sha256": self.manifest_hash, "model": "fixture-model", "instance_id": task_id, "condition": condition, "step": 2, "status": status, "resolved": resolved}

    def test_missing_and_infrastructure_are_null_and_stay_in_denominator(self):
        receipts = [self.receipt(self.ids[0], "vector", True), self.receipt(self.ids[0], "scalar", False), self.receipt(self.ids[1], "vector", True), self.receipt(self.ids[2], "scalar", True), self.receipt(self.ids[3], "vector", None, "infrastructure_failure")]
        result = analysis.analyze(self.manifest, receipts)
        primary = result["per_model"]["fixture-model"]["primary"]
        self.assertEqual((primary["declared_tasks"], primary["complete_pairs"], primary["missing_pairs"]), (8, 1, 7))
        self.assertEqual(primary["complete_pair_mean_difference"], 1)
        self.assertEqual(primary["full_denominator_bounds"], [-5 / 8, 7 / 8])
        self.assertEqual(len(result["final_cells"]), 24)
        self.assertEqual(result["cell_coverage"]["declared_cells"], 56)
        self.assertEqual(result["cell_coverage"]["received_cells"], 5)
        self.assertEqual(len(result["non_final_cells"]), 32)
        cells = [row for row in result["final_cells"] if row["condition"] == "vector"]
        self.assertEqual(sum(row["resolved"] is None for row in cells), 6)
        counts = result["per_model"]["fixture-model"]["conditions"]["vector"]
        self.assertEqual(counts["status_counts"]["infrastructure_failure"], 1)
        self.assertEqual(counts["status_counts"]["missing"], 5)
        self.assertEqual(counts["full_denominator_rate_bounds"], [2 / 8, 1])

    def test_unmeasured_task_failure_does_not_become_zero(self):
        result = analysis.analyze(self.manifest, [self.receipt(self.ids[0], "vector", None, "task_failure"), self.receipt(self.ids[1], "vector", False, "task_failure")])
        counts = result["per_model"]["fixture-model"]["conditions"]["vector"]
        self.assertEqual(counts["measured_tasks"], 1)
        self.assertEqual(counts["unresolved_measured_tasks"], 1)
        self.assertEqual(counts["unmeasured_tasks"], 7)
        self.assertEqual(counts["status_counts"]["task_failure"], 2)

    def test_complete_positive_pairs_have_exact_swap_probability(self):
        receipts = [self.receipt(task_id, condition, condition == "vector") for task_id in self.ids for condition in prep.CONDITIONS]
        result = analysis.analyze(self.manifest, receipts)
        for name in ("primary", "secondary"):
            comparison = result["per_model"]["fixture-model"][name]
            self.assertEqual(comparison["complete_pairs"], 8)
            self.assertEqual(comparison["bootstrap_95_interval"], [1, 1])
            self.assertEqual(comparison["full_denominator_bounds"], [1, 1])
            self.assertEqual(comparison["exact_paired_swap_p_value"], 2 / 256)

    def test_exact_swap_handles_ties_and_non_significant_discordance(self):
        self.assertEqual(analysis.exact_paired_swap_test([1, 1, 1, -1, 0, 0]), 10 / 16)
        self.assertEqual(analysis.exact_paired_swap_test([1, -1, 0]), 1)
        self.assertEqual(analysis.exact_paired_swap_test([0] * 8), 1)
        self.assertIsNone(analysis.exact_paired_swap_test([]))

    def test_bootstrap_is_deterministic_and_resamples_task_differences(self):
        differences = [-1, 0, 1, 1]
        self.assertEqual(analysis.bootstrap_interval(differences), analysis.bootstrap_interval(differences))
        self.assertEqual(analysis.bootstrap_interval(differences), [-0.5, 1])

    def test_all_missing_has_no_measured_estimate(self):
        primary = analysis.analyze(self.manifest, [])["per_model"]["fixture-model"]["primary"]
        self.assertEqual(primary["complete_pairs"], 0)
        self.assertIsNone(primary["complete_pair_mean_difference"])
        self.assertIsNone(primary["bootstrap_95_interval"])
        self.assertIsNone(primary["exact_paired_swap_p_value"])
        self.assertEqual(primary["full_denominator_bounds"], [-1, 1])

    def test_undeclared_duplicate_unbound_and_misclassified_receipts_rejected(self):
        row = self.receipt(self.ids[0], "vector", True)
        bad_rows = [{**row, "instance_id": "not-declared"}, {**row, "manifest_sha256": "wrong"}, {k: v for k, v in row.items() if k != "manifest_sha256"}, {**row, "resolved": 1}, {**row, "status": "infrastructure_failure"}, {**row, "status": "task_failure"}, {**row, "resolved": None}, {**row, "step": True}, {**row, "cell_id": "wrong"}]
        for bad in bad_rows:
            with self.subTest(row=bad), self.assertRaises(ValueError):
                analysis.analyze(self.manifest, [bad])
        with self.assertRaises(ValueError):
            analysis.analyze(self.manifest, [row, row])

    def test_manifest_tampering_and_rehashed_denominator_change_rejected(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["task_ids"].pop()
        with self.assertRaises(ValueError):
            analysis.analyze(manifest, [])
        manifest["design_sha256"] = prep.digest({k: v for k, v in manifest.items() if k != "design_sha256"})
        with self.assertRaises(ValueError):
            analysis.analyze(manifest, [])
        manifest = copy.deepcopy(self.manifest)
        manifest["cells"].pop()
        manifest["design_sha256"] = prep.digest({k: v for k, v in manifest.items() if k != "design_sha256"})
        with self.assertRaises(ValueError):
            analysis.analyze(manifest, [])

    def test_models_remain_separate_task_units(self):
        manifest, _, private = bundle(models=["fixture-model", "other-model"])
        receipts = [{**self.receipt(task_id, condition, condition == "vector"), "manifest_sha256": private["manifest_sha256"]} for task_id in manifest["task_ids"] for condition in prep.CONDITIONS]
        result = analysis.analyze(manifest, receipts)
        self.assertEqual(result["per_model"]["fixture-model"]["primary"]["complete_pairs"], 8)
        self.assertEqual(result["per_model"]["other-model"]["primary"]["complete_pairs"], 0)
        self.assertEqual(len(result["final_cells"]), 48)

    def test_command_line_binds_exact_bytes_and_refuses_output_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path, outcomes_path, output_path = [root / name for name in ("manifest.json", "outcomes.json", "analysis.json")]
            manifest_path.write_bytes(prep.canonical(self.manifest) + b"\n")
            outcomes_path.write_text(json.dumps({"manifest_sha256": self.manifest_hash, "receipts": []}))
            command = [sys.executable, str(Path(analysis.__file__)), "--manifest", str(manifest_path), "--outcomes", str(outcomes_path), "--output", str(output_path)]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            before = output_path.read_bytes()
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(output_path.read_bytes(), before)
            manifest_path.write_text(json.dumps(self.manifest, indent=2))
            self.assertNotEqual(hashlib.sha256(manifest_path.read_bytes()).hexdigest(), self.manifest_hash)
            run = subprocess.run(command[:-1] + [str(root / "new-analysis.json")], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn("different manifest", run.stderr)
            self.assertFalse((root / "new-analysis.json").exists())

    def test_jsonl_requires_each_row_hash_but_envelope_can_bind_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "receipts.jsonl"
            row = self.receipt(self.ids[0], "vector", True)
            del row["manifest_sha256"]
            path.write_text(json.dumps(row) + "\n")
            receipts, _ = analysis.read_receipts(path, self.manifest_hash)
            with self.assertRaises(ValueError):
                analysis.analyze(self.manifest, receipts)
            path = root / "receipts.json"
            path.write_text(json.dumps({"manifest_sha256": self.manifest_hash, "receipts": [row]}))
            receipts, _ = analysis.read_receipts(path, self.manifest_hash)
            self.assertEqual(analysis.analyze(self.manifest, receipts)["per_model"]["fixture-model"]["conditions"]["vector"]["measured_tasks"], 1)

    def test_empty_or_unbound_receipt_files_cannot_bypass_manifest_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, contents in [("empty.jsonl", ""), ("array.json", "[]"), ("unbound.json", '{"receipts":[]}')]:
                path = root / name
                path.write_text(contents)
                with self.subTest(name=name), self.assertRaises(ValueError):
                    analysis.read_receipts(path, self.manifest_hash)


if __name__ == "__main__":
    unittest.main()
