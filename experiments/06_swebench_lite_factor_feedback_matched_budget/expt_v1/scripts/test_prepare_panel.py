"""Verify outcome-independent panel selection, strict solver isolation, and exclusive artifact creation."""

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import prepare_panel as prep


def fixture_rows():
    return [{"instance_id": f"fixture-{i}", "repo": "fixture/project", "base_commit": "a" * 40, "problem_statement": f"Public issue {i}", "patch": f"HIDDEN_PATCH_{i}", "test_patch": f"HIDDEN_TEST_{i}", "FAIL_TO_PASS": '["HIDDEN_FTP"]', "PASS_TO_PASS": ["HIDDEN_PTP"], "hints_text": "HIDDEN_HINT", "version": "fixture"} for i in range(23)]


def bundle(rows=None, models=None):
    return prep.build_panel(rows if rows is not None else fixture_rows(), "a" * 64, "fixture/SWE-bench_Lite", "b" * 40, "validation", models or ["fixture-model"])


class PreparationTests(unittest.TestCase):
    def test_hash_order_matches_frozen_fixture_selection(self):
        self.assertEqual(bundle()[0]["task_ids"], ["fixture-3", "fixture-21", "fixture-6", "fixture-20", "fixture-15", "fixture-11", "fixture-4", "fixture-8"])

    def test_gold_changes_cannot_change_selection_or_solver_view(self):
        rows = fixture_rows()
        public, solver, private = bundle(rows)
        altered = copy.deepcopy(rows)
        for i, row in enumerate(altered):
            row["patch"] = "different-size-gold" * (i + 1)
            row["test_patch"] = ""
            row["FAIL_TO_PASS"] = []
            row["PASS_TO_PASS"] = []
            row["resolved"] = bool(i % 2)
        changed, changed_solver, _ = bundle(list(reversed(altered)))
        self.assertEqual(public["task_ids"], changed["task_ids"])
        self.assertEqual(solver, changed_solver)
        self.assertEqual(len(solver), 8)
        self.assertTrue(all(set(row) == set(prep.SOLVER_FIELDS) for row in solver))
        self.assertNotIn("HIDDEN", json.dumps(public))
        self.assertNotIn("HIDDEN", json.dumps(solver))
        self.assertIn("HIDDEN_PATCH", json.dumps(private))
        self.assertNotEqual(public["tasks"], changed["tasks"])

    def test_design_has_one_shared_initial_and_every_followup(self):
        public, _, _ = bundle(models=["model-a", "model-b"])
        cells = public["cells"]
        self.assertEqual(len(cells), 112)
        self.assertEqual(len({c["cell_id"] for c in cells}), 112)
        for model in public["models"]:
            for task_id in public["task_ids"]:
                task_cells = [c for c in cells if c["model"] == model and c["instance_id"] == task_id]
                self.assertEqual({(c["condition"], c["step"]) for c in task_cells}, {("shared_initial", 0), ("ordinary", 1), ("ordinary", 2), ("scalar", 1), ("scalar", 2), ("vector", 1), ("vector", 2)})

    def test_invalid_source_fails_even_outside_selected_panel(self):
        public, _, _ = bundle()
        unselected = next(row for row in fixture_rows() if row["instance_id"] not in public["task_ids"])
        for field in prep.SOLVER_FIELDS + prep.EVALUATOR_FIELDS:
            rows = fixture_rows()
            row = next(row for row in rows if row["instance_id"] == unselected["instance_id"])
            del row[field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                bundle(rows)
        with self.assertRaises(ValueError):
            bundle(fixture_rows() + [fixture_rows()[0]])
        with self.assertRaises(ValueError):
            bundle(fixture_rows()[:7])

    def test_unpinned_or_test_split_rejected(self):
        for revision, split, models in [("main", "validation", ["m"]), ("b" * 40, "test", ["m"]), ("b" * 40, "validation", ["m", "m"])]:
            with self.subTest(revision=revision, split=split), self.assertRaises(ValueError):
                prep.build_panel(fixture_rows(), "a" * 64, "fixture/dataset", revision, split, models)

    def test_ambiguous_json_rejected_and_source_bytes_hashed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rows.jsonl"
            path.write_text('\n'.join(json.dumps(row) for row in fixture_rows()) + '\n')
            rows, source_hash = prep.read_rows(path)
            self.assertEqual(rows, fixture_rows())
            self.assertEqual(source_hash, hashlib.sha256(path.read_bytes()).hexdigest())
            path.write_text('{"instance_id":"one","instance_id":"two"}\n')
            with self.assertRaises(ValueError):
                prep.read_rows(path)
            path.write_text('[NaN]')
            with self.assertRaises(ValueError):
                prep.read_rows(path)

    def test_output_is_byte_bound_private_and_cannot_be_overwritten(self):
        public, solver, private = bundle()
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ("public.json", "solver.json", "evaluator.json")]
            prep.write_bundle(*paths, public, solver, private)
            self.assertEqual(hashlib.sha256(paths[0].read_bytes()).hexdigest(), private["manifest_sha256"])
            self.assertEqual(paths[2].stat().st_mode & 0o777, 0o600)
            before = [p.read_bytes() for p in paths]
            with self.assertRaises(FileExistsError):
                prep.write_bundle(*paths, public, solver, private)
            self.assertEqual(before, [p.read_bytes() for p in paths])
            with self.assertRaises(ValueError):
                prep.write_bundle(paths[0], paths[1], paths[0], public, solver, private)

    def test_path_alias_and_input_overwrite_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "alias").symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                prep.write_bundle(root / "public", root / "solver", root / "alias/public", *bundle())
            with self.assertRaises(ValueError):
                prep.write_bundle(root / "public", root / "solver", root / "eval", *bundle(), input_path=root / "solver")
            self.assertFalse((root / "public").exists())

    def test_partial_output_rolls_back_without_deleting_racing_writer(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ("public", "solver", "evaluator")]
            real_open = prep.os.open

            def racing_open(path, flags, mode):
                if path == paths[2]:
                    paths[2].write_text("another writer")
                return real_open(path, flags, mode)

            with patch.object(prep.os, "open", side_effect=racing_open), self.assertRaises(FileExistsError):
                prep.write_bundle(*paths, *bundle())
            self.assertFalse(paths[0].exists())
            self.assertFalse(paths[1].exists())
            self.assertEqual(paths[2].read_text(), "another writer")


if __name__ == "__main__":
    unittest.main()
