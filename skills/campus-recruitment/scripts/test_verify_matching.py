import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("verify-matching.py")


class MatchingValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "raw.json").write_text('[{"id":"one"}]', encoding="utf-8")
        self.base = {
            "company": "Fixture Company",
            "date": "2026-01-01",
            "scope": "Fixture only",
            "raw_catalog": {"file": "raw.json", "total_positions": 1},
            "catalog_index": [{"id": "one", "title": "Fixture Role", "city": "Fixture City", "in_scope": True}],
            "positions": [{
                "id": "one",
                "jd_evidence": ["First source quote", "Second source quote"],
                "grade": "A",
                "coverage_estimate": "60% (fixture)",
                "resume_version": "fixture-version",
                "match_reasons": "Fixture reason",
                "gaps": "Fixture gap",
            }],
        }

    def run_case(self, data, passed):
        path = self.root / "matching.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0 if passed else 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["passed"], passed)

    def test_valid(self):
        self.run_case(self.base, True)

    def test_missing_evidence(self):
        data = copy.deepcopy(self.base)
        data["positions"][0]["jd_evidence"] = ["only one"]
        self.run_case(data, False)

    def test_missing_position(self):
        data = copy.deepcopy(self.base)
        data["positions"] = []
        self.run_case(data, False)


if __name__ == "__main__":
    unittest.main()

