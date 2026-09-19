import importlib.util
import json
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("assemble-matching-summary.py")
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("assemble_matching_summary", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def requirement(requirement_id, category, support, conclusion):
    return {
        "requirement_id": requirement_id,
        "text": f"要求 {requirement_id}",
        "category": category,
        "category_basis_quote_ids": [f"jd-{requirement_id}"],
        "jd_quote_ids": [f"jd-{requirement_id}"],
        "candidate_evidence_ids": [] if support == "no_evidence" else [f"ev-{requirement_id}"],
        "support": support,
        "conclusion": conclusion,
        "judgment": "fixture judgment",
    }


class AssembleMatchingSummaryTests(unittest.TestCase):
    def test_counts_hard_core_plus_and_ambiguous_independently(self):
        requirements = [
            requirement("r1", "hard_qualification", "direct_support", "satisfied"),
            requirement("r2", "core_capability", "direct_support", "satisfied"),
            requirement("r3", "core_capability", "transferable", "pending"),
            requirement("r4", "plus", "no_evidence", "pending"),
            requirement("r5", "ambiguous", "no_evidence", "pending"),
        ]
        record = {"positions": [{"requirements": requirements, "requirement_summary": {}}]}

        assembled, errors, changed = MODULE.assemble(record)

        self.assertEqual(errors, [])
        self.assertEqual(
            assembled["positions"][0]["requirement_summary"],
            {
                "requirements_total": 5,
                "hard_qualification": 1,
                "core_capability": 2,
                "plus": 1,
                "ambiguous": 1,
                "core_total": 3,
                "direct_support": 2,
                "transferable": 1,
                "no_evidence": 2,
                "conflict": 0,
                "satisfied": 2,
                "not_satisfied": 0,
                "pending": 3,
            },
        )
        self.assertIn("positions[0].requirement_summary.core_total", changed)

    def test_empty_requirements_are_not_guessed(self):
        record = {"positions": [{"requirements": [], "requirement_summary": {"core_total": 99}}]}

        assembled, errors, changed = MODULE.assemble(record)

        self.assertEqual(assembled, record)
        self.assertTrue(any("REQUIREMENTS_MISSING_OR_EMPTY" in error for error in errors))
        self.assertEqual(changed, [])

    def test_damaged_requirement_is_not_dropped_or_defaulted(self):
        damaged = requirement("r1", "core_capability", "direct_support", "satisfied")
        damaged.pop("category")
        record = {"positions": [{"requirements": [damaged], "requirement_summary": {}}]}
        original = json.loads(json.dumps(record))

        assembled, errors, changed = MODULE.assemble(record)

        self.assertEqual(assembled, original)
        self.assertTrue(any("REQUIREMENT_FIELDS_MISSING=category" in error for error in errors))
        self.assertEqual(changed, [])

    def test_non_string_enum_values_are_diagnostic_not_unhashable_errors(self):
        for field in ("category", "support", "conclusion"):
            with self.subTest(field=field):
                item = requirement("r1", "core_capability", "direct_support", "satisfied")
                item[field] = [] if field != "conclusion" else {}
                record = {"positions": [{"requirements": [item], "requirement_summary": {}}]}

                assembled, errors, changed = MODULE.assemble(record)

                self.assertEqual(assembled, record)
                self.assertTrue(any(f".{field}: REQUIREMENT_{field.upper()}_INVALID" in error for error in errors))
                self.assertEqual(changed, [])

    def test_invalid_summary_containers_are_rebuilt_as_derived_data(self):
        requirements = [
            requirement("r1", "hard_qualification", "direct_support", "satisfied"),
            requirement("r2", "core_capability", "transferable", "pending"),
            requirement("r3", "core_capability", "no_evidence", "pending"),
        ]
        expected_core_total = 3
        boolean_summary = {
            "requirements_total": True,
            "hard_qualification": True,
            "core_capability": False,
            "plus": False,
            "ambiguous": False,
            "core_total": True,
            "direct_support": False,
            "transferable": True,
            "no_evidence": True,
            "conflict": False,
            "satisfied": False,
            "not_satisfied": True,
            "pending": True,
        }
        for old_summary in (None, [], "invalid", {"core_total": False}, boolean_summary):
            with self.subTest(old_summary=old_summary):
                record = {"positions": [{"requirements": requirements, "requirement_summary": old_summary}]}
                assembled, errors, changed = MODULE.assemble(record)

                self.assertEqual(errors, [])
                self.assertEqual(assembled["positions"][0]["requirement_summary"]["core_total"], expected_core_total)
                self.assertTrue(all(type(value) is int for value in assembled["positions"][0]["requirement_summary"].values()))
                self.assertTrue(changed)

    def test_cli_writes_structured_diagnostics_for_invalid_requirement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = {"positions": [{"requirements": [{"category": []}], "requirement_summary": None}]}
            source = root / "matching.json"
            output = root / "assembled.json"
            diagnostics = root / "diagnostics.json"
            diff = root / "diff.json"
            original = json.dumps(record, ensure_ascii=False, indent=2) + "\n"
            source.write_text(original, encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(SCRIPT),
                    str(source),
                    str(output),
                    "--diagnostics",
                    str(diagnostics),
                    "--diff",
                    str(diff),
                ],
                capture_output=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertEqual(output.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))
            report = json.loads(diagnostics.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("positions[0].requirements[0].category" in error for error in report["errors"]))
            self.assertEqual(json.loads(diff.read_text(encoding="utf-8"))["changed_paths"], [])


if __name__ == "__main__":
    unittest.main()
