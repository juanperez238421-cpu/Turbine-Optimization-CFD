import csv
import json
import tempfile
import unittest
from pathlib import Path

from article_audit.audit_results import (
    audit_registry,
    load_policy,
    load_registry,
    normalize_doi,
    safe_eval,
)


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "article_audit" / "config" / "classification_policy.json"
REGISTRY = ROOT / "article_audit" / "data" / "santiago_results_registry.csv"


class TestResultAudit(unittest.TestCase):
    def test_normalize_doi(self):
        self.assertEqual(
            normalize_doi("https://doi.org/10.1016/J.RSER.2015.04.030."),
            "10.1016/j.rser.2015.04.030",
        )

    def test_safe_eval_power_delta(self):
        self.assertAlmostEqual(safe_eval("37.48 - 28.24"), 9.24, places=8)

    def test_safe_eval_positive_count(self):
        expression = (
            "count_positive(38.41,17.12,29.98,35.02,24.86,19.18,"
            "32.01,29.86,11.20,30.47,10.37,16.94,33.89,1.20,"
            "33.16,-3.08,-2.05,26.61)"
        )
        self.assertEqual(safe_eval(expression), 16)

    def test_registry_has_unique_ids(self):
        rows = load_registry(REGISTRY)
        ids = [r["result_id"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_denominator_inconsistency_blocks_efficiency_delta(self):
        policy = load_policy(POLICY)
        results, _ = audit_registry(load_registry(REGISTRY), policy)
        row = next(x for x in results if x["result_id"] == "BASIN_EFF_DELTA_PP")
        self.assertEqual(row["audit_state"], "BLOCKED")
        self.assertIn("DENOMINATOR_INCONSISTENCY", {i["code"] for i in row["issues"]})

    def test_power_delta_is_reproduced(self):
        policy = load_policy(POLICY)
        results, _ = audit_registry(load_registry(REGISTRY), policy)
        row = next(x for x in results if x["result_id"] == "BASIN_POWER_DELTA_W")
        self.assertAlmostEqual(row["reproduced_value"], 9.24, places=8)
        self.assertNotEqual(row["audit_state"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
