"""Test endpoint schema, adversarial syntax rejection, and unknown-versus-false semantics without Lean."""
import copy
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("endpoint_under_test", HERE / "check_endpoint.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)


class EndpointTests(unittest.TestCase):
    def test_entire_frozen_manifest_and_candidates(self):
        manifest = E.load_manifest(HERE / "manifest.json")
        self.assertEqual(len(manifest["tasks"]), 3)
        self.assertEqual(len(manifest["cells"]), 24)
        for cell in manifest["cells"]:
            E.load_candidate(HERE / cell["candidate"], cell["candidate_sha256"], cell["task"])

    def test_manifest_rejects_empty_requirements_duplicates_and_path_traversal(self):
        original = E.load_json(HERE / "manifest.json")
        mutations = []
        m = copy.deepcopy(original); m["tasks"][0]["tests"] = []; mutations.append(m)
        m = copy.deepcopy(original); m["tasks"][0]["obligations"] = []; mutations.append(m)
        m = copy.deepcopy(original); m["cells"].append(m["cells"][0]); mutations.append(m)
        m = copy.deepcopy(original); m["cells"][0]["candidate"] = "../../candidate.json"; mutations.append(m)
        m = copy.deepcopy(original); m["tasks"][0]["tests"][0]["expected"] = 100; mutations.append(m)
        for mutation in mutations:
            with self.subTest(mutation=mutations.index(mutation)), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "manifest.json"
                path.write_text(json.dumps(mutation))
                with self.assertRaises(ValueError):
                    E.load_manifest(path)

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.json"
            path.write_text('{"op":"var","op":"nat"}')
            with self.assertRaises(ValueError):
                E.load_json(path)

    def test_no_arbitrary_lean_syntax_or_boolean_literals(self):
        bad_nodes = ["n\nend Candidate\nimport Evil", {"op": "var", "text": "#eval IO.println"},
                     {"op": "import Mathlib"}, {"op": "nat", "value": True},
                     {"op": "nat", "value": "0; axiom x : False"}, {"op": []}]
        for node in bad_nodes:
            with self.subTest(node=node), self.assertRaises(ValueError):
                E.expression(node)

    def test_hash_or_signature_mismatch_rejected(self):
        cell = E.load_manifest(HERE / "manifest.json")["cells"][0]
        path = HERE / cell["candidate"]
        with self.assertRaises(ValueError):
            E.load_candidate(path, "0" * 64, cell["task"])
        with self.assertRaises(ValueError):
            E.load_candidate(path, cell["candidate_sha256"], "double")

    def test_unknown_and_unmeasured_never_become_false(self):
        for status in ("unknown", "unmeasured"):
            self.assertIsNone(E.endpoint(status, "missing")["value"])
            combined = E.conjunction(E.endpoint("pass", "checked"), E.endpoint(status, "missing"))
            self.assertEqual(combined["status"], "unknown")
            self.assertIsNone(combined["value"])
        self.assertFalse(E.conjunction(E.endpoint("fail", "witness"), E.endpoint("unknown", "missing"))["value"])

    def report(self, axioms=(), **overrides):
        report = {"probe_ok": True, "compile_rc": 0, "inspect_rc": 0, "probe_rc": 0,
                  "source_sha256": "a" * 64, "compiled_module_sha256": "b" * 64,
                  "allow_native_decide": False,
                  "theorems": [{"full_name": "certificate", "resolution": "source_position",
                                "axioms": list(axioms), "category": "honest" if not axioms else "sorryAx",
                                "kernel_honest": not axioms}]}
        report.update(overrides)
        return report

    def test_forbidden_transitive_axioms_false_but_compile_failures_unknown(self):
        for axiom in ["sorryAx", "user_axiom", "Lean.ofReduceBool", "Lean.ofReduceNat", "Lean.trustCompiler"]:
            result = E.kernel_verdict(self.report([axiom]), ["certificate"], "a" * 64)
            self.assertEqual(result["status"], "fail")
        for overrides in [{"probe_ok": False, "compile_rc": 1},
                          {"probe_ok": False, "probe_rc": 124},
                          {"compiled_module_sha256": None}, {"theorems": []},
                          {"source_sha256": "c" * 64}, {"allow_native_decide": True}]:
            result = E.kernel_verdict(self.report(**overrides), ["certificate"], "a" * 64)
            self.assertEqual(result["status"], "unknown")
        self.assertEqual(E.kernel_verdict(self.report(), ["certificate"], "a" * 64)["status"], "pass")

    def test_allowed_axioms_are_permitted(self):
        report = self.report()
        report["theorems"][0]["axioms"] = sorted(E.ALLOWED_AXIOMS)
        self.assertEqual(E.kernel_verdict(report, ["certificate"], "a" * 64)["status"], "pass")

    def test_reference_source_links_candidate_and_ignores_submitted_spec(self):
        m = E.load_manifest(HERE / "manifest.json")
        task = m["tasks"][0]
        cell = next(c for c in m["cells"] if c["id"] == "increment_vacuous_spec")
        candidate = E.load_candidate(HERE / cell["candidate"], cell["candidate_sha256"], cell["task"])
        reference = E.obligation(task, "exact")
        own, names = E.submitted_source(candidate, task)
        self.assertIn("Candidate.impl n", reference)
        self.assertNotIn("False", reference)
        self.assertIn("False →", own)
        self.assertEqual(names, ["submitted_certificate"])

    def test_missing_candidate_retains_every_declared_unmeasured_cell(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            manifest_path.write_bytes((HERE / "manifest.json").read_bytes())
            output = root / "receipt"
            with patch.object(E, "preflight", side_effect=AssertionError("Lean must not run")), contextlib.redirect_stdout(io.StringIO()):
                code = E.main(["--manifest", str(manifest_path), "--scorer-repo", str(root),
                               "--lake-dir", str(root), "--output", str(output)])
            receipt = json.loads((output / "results.json").read_text())
            self.assertEqual(code, 1)
            self.assertEqual(receipt["status"], "INFRASTRUCTURE_OR_INPUT_FAILURE")
            self.assertEqual(len(receipt["rows"]), 24)
            self.assertTrue(all(r["reference_verified_success"]["value"] is None for r in receipt["rows"]))


if __name__ == "__main__":
    unittest.main()
